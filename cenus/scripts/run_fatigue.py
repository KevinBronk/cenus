import os, sys, json, argparse, datetime, random
from collections import defaultdict
from typing import List, Dict

# allow `src` imports when running from repo root
sys.path.insert(0,
                os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.meta_client import fetch_insights_for_account, transform_rows_to_kpis
from src.notion import get_settings, upsert_record, update_fatigue_fields, add_alert_row
from src.alerts import send_slack_alert
from src.fatigue import rolling_baseline, evaluate_rules


def demo_kpis(level: str, days: int, since: str, until: str):
    start = datetime.datetime.strptime(since, "%Y-%m-%d").date()
    rows = []
    for i in range(days):
        d = start + datetime.timedelta(days=i)
        rows.append({
            "timestamp": d.strftime("%Y-%m-%d"),
            "level": level,
            "name": f"Demo {level} {i}",
            "campaign_id": "cmp_demo",
            "adset_id": "adset_demo",
            "ad_id": "ad_demo",
            "kpis_roas": round(random.uniform(0.7, 2.5), 2),
            "kpis_ctr": round(random.uniform(0.5, 3.0), 2),
            "kpis_cpm": round(random.uniform(3.0, 25.0), 2),
            "kpis_cpc": round(random.uniform(0.2, 2.5), 2),
            "kpis_spend": round(random.uniform(5, 120), 2),
            "kpis_results": random.randint(0, 40),
        })
    return rows


CLIENTS_FILE = "clients.json"


def load_clients() -> List[Dict]:
    with open(CLIENTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def date_str(d: datetime.date) -> str:
    return d.strftime("%Y-%m-%d")


def slice_days(rows: List[Dict], last_n: int) -> List[Dict]:
    # rows are daily; ensure sorted by timestamp ascending
    s = sorted(rows, key=lambda r: r.get("timestamp"))
    return s[-last_n:]


def group_by_entity(rows: List[Dict], level: str) -> Dict[str, List[Dict]]:
    # group key by entity id at the chosen level
    key_field = {
        "campaign": "campaign_id",
        "adset": "adset_id",
        "ad": "ad_id"
    }[level]
    g = defaultdict(list)
    for r in rows:
        eid = r.get(key_field)
        if eid:
            # normalize timestamp to the record['timestamp'] (already set)
            g[eid].append(r)
    return g


def run_for_client(client: Dict, level: str, days: int, baseline_days: int):
    global args
    name = client["client_name"]
    account_id = client["ad_account_id"]
    notion_db = client["notion_db_id"]
    settings_db = client.get("notion_settings_db_id")

    slack_webhook = (client.get("slack_webhook") or "").strip()
    if slack_webhook == "__FROM_SECRET__":
        import os
        slack_webhook = os.getenv("SLACK_WEBHOOK_URL", "").strip()

    alerts_db = client.get("notion_alerts_db_id")

    print(f"\n[Fatigue] Client={name} | {account_id} | level={level}")

    # Determine date window (latest N days)
    end = datetime.date.today() - datetime.timedelta(
        days=1)  # use yesterday as 'latest' day
    start = end - datetime.timedelta(days=days - 1)
    since, until = date_str(start), date_str(end)

    # Pull raw and transform
    if getattr(args, "demo", False):
        print("🧪 Running in DEMO MODE — generating fake KPI data")
        rows = demo_kpis(level, days, since, until)
    else:
        raw = fetch_insights_for_account(account_id,
                                         level=level,
                                         since=since,
                                         until=until)
        rows = transform_rows_to_kpis(raw, level=level)

    # Group by entity
    grouped = group_by_entity(rows, level)
    if not grouped:
        print("[Fatigue] No rows found in window.")

    # Load thresholds from settings (or defaults will be used)
    th = get_settings(settings_db) if settings_db else {}

    flagged = 0
    checked = 0

    for eid, series in grouped.items():
        series = slice_days(series, days)
        if len(series) < baseline_days + 1:
            continue  # need baseline_days + latest

        # split: latest day vs previous baseline_days
        latest = series[-1]
        baseline_rows = series[-(baseline_days + 1):-1]
        base = rolling_baseline(baseline_rows)

        fatigued, reasons, actions = evaluate_rules(latest, base, th)
        checked += 1

        # Upsert the KPI record (ensures page exists), then update fatigue fields
        action, page_id = upsert_record(notion_db, latest)

        reason_txt = ""
        actions_txt = ""

        if fatigued:
            flagged += 1
            reason_txt = " | ".join(reasons)[:1800]
            actions_txt = " • " + " • ".join(actions)
            update_fatigue_fields(page_id, True, reason_txt, actions_txt)
            print(
                f"  [FLAG] {level}:{eid} on {latest['timestamp']} — {reason_txt}"
            )
        else:
            update_fatigue_fields(page_id, False, "", "")
            print(f"  [OK]   {level}:{eid} on {latest['timestamp']}")

    # --- Slack + Notion Alerts ---
    if slack_webhook:
        kpis = {
            "roas": latest.get("kpis_roas"),
            "cpm": latest.get("kpis_cpm"),
            "ctr": latest.get("kpis_ctr"),
            "spend": latest.get("kpis_spend"),
            "res": latest.get("kpis_results"),
        }
        send_slack_alert(slack_webhook, name,
                         latest.get("level", level).title(),
                         latest.get("name") or "",
                         latest.get("timestamp") or "", reason_txt, actions,
                         kpis)
        print("    → Slack alert sent")

    if alerts_db:
        add_alert_row(alerts_db,
                      ts=latest.get("timestamp") or "",
                      level=latest.get("level", level).title(),
                      entity_id=eid,
                      name=latest.get("name") or "",
                      reason=reason_txt,
                      actions=actions_txt)
        print("    → Notion alert row added")

    print(
        f"[Summary] checked={checked}, flagged={flagged}, window={since}..{until}, baseline_days={baseline_days}"
    )


def main():
    global args
    ap = argparse.ArgumentParser(
        description="Run fatigue detection and write flags to Notion.")
    ap.add_argument("--client",
                    help="Specific client name (default: all)",
                    default=None)
    ap.add_argument("--level", help="campaign|adset|ad", default="ad")
    ap.add_argument("--days",
                    type=int,
                    default=14,
                    help="Total days to fetch (>= baseline_days+1)")
    ap.add_argument("--baseline_days",
                    type=int,
                    default=7,
                    help="Days used for rolling baseline")
    ap.add_argument("--demo",
                    action="store_true",
                    help="Use demo data instead of Meta API")
    args = ap.parse_args()

    if args.days < args.baseline_days + 1:
        raise SystemExit("--days must be >= baseline_days + 1")

    clients = load_clients()
    if args.client:
        clients = [
            c for c in clients
            if c["client_name"].strip().lower() == args.client.strip().lower()
        ]
        if not clients:
            raise SystemExit(
                f"No client named '{args.client}' found in clients.json")

    for c in clients:
        run_for_client(c,
                       level=args.level,
                       days=args.days,
                       baseline_days=args.baseline_days)


if __name__ == "__main__":
    main()
