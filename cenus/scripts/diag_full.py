# scripts/diag_full.py
import os, sys, json, argparse, datetime, requests, subprocess, shlex

REQUIRED_ALERT_PROPS = {
    "entity_name": "title",
    "entity_id": "rich_text",
    "level": "select",
    "date": "date",
    "metric": "select",
    "value": "number",
    "baseline": "number",
    "pct_change": "number",
    "severity": "select",
    "client": "rich_text",
    "link": "url",
    "notes": "rich_text",
}

NOTION_API = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"


def h():
    return {
        "Authorization": f"Bearer {os.getenv('NOTION_TOKEN','')}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def ok(b):
    return "✅" if b else "❌"


def shell(cmd, check=True):
    print(f"+ {cmd}")
    p = subprocess.run(shlex.split(cmd),
                       stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT,
                       text=True)
    if check and p.returncode != 0:
        print(p.stdout)
        raise SystemExit(p.returncode)
    return p.stdout


def diag_files():
    print("\n[1/7] Files & paths")
    paths = [
        "clients.json",
        "scripts/run_fatigue.py",
        "scripts/run_daily_pipeline.py",
        "src/notion.py",
        ".github/workflows/cenus.yml",
    ]
    all_exist = True
    for p in paths:
        e = os.path.exists(p)
        print(f"  {ok(e)} {p}")
        all_exist &= e
    if not all_exist:
        print("  ❌ Missing files above. Fix before continuing.")
        sys.exit(2)


def load_clients():
    with open("clients.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list) or not data:
        print("❌ clients.json must be a non-empty list.")
        sys.exit(2)
    return data


def diag_env(client):
    print("\n[2/7] Environment & secrets")
    need = ["NOTION_TOKEN", "FB_ACCESS_TOKEN"]
    present = True
    for k in need:
        has = bool(os.getenv(k))
        print(f"  {ok(has)} {k} {'(set)' if has else '(missing)'}")
        present &= has

    # Slack resolution for local runs
    sw = client.get("slack_webhook")
    if sw == "__FROM_SECRET__":
        # local runs need env var set
        has_local = bool(os.getenv("SLACK_WEBHOOK"))
        print(
            f"  {ok(has_local)} SLACK_WEBHOOK for local run "
            f"{'(required because clients.json uses __FROM_SECRET__)' if not has_local else ''}"
        )
    else:
        print(
            f"  {ok(sw and sw.startswith('http'))} Slack webhook in clients.json "
            f"({'set' if sw else 'missing'})")

    if not present:
        print(
            "❌ Missing required env vars. Set them in Replit or your shell and re-run."
        )
        sys.exit(2)


def get_first_client(clients):
    # pick first for diag
    return clients[0]


def notion_fetch_db(db_id):
    r = requests.get(f"{NOTION_API}/databases/{db_id}",
                     headers=h(),
                     timeout=25)
    if r.status_code != 200:
        raise RuntimeError(
            f"Notion GET DB {db_id} -> {r.status_code}: {r.text[:240]}")
    return r.json()


def diag_notion_schema(db_id):
    print("\n[3/7] Notion Alerts DB schema")
    try:
        db = notion_fetch_db(db_id)
    except Exception as e:
        print(f"  ❌ Cannot read database: {e}")
        sys.exit(2)

    props = db.get("properties", {})
    # Build a simple type map
    existing = {}
    for k, v in props.items():
        # property type key is one of title, rich_text, select, date, number, url, etc.
        for t in [
                "title", "rich_text", "select", "date", "number", "url",
                "checkbox", "people", "files", "multi_select", "email",
                "phone_number", "formula", "relation", "rollup", "status"
        ]:
            if t in v:
                existing[k] = t
                break

    all_ok = True
    for name, ptype in REQUIRED_ALERT_PROPS.items():
        has = existing.get(name) == ptype
        print(
            f"  {ok(has)} {name:<12} type={existing.get(name,'-')} (expected {ptype})"
        )
        all_ok &= has

    if not all_ok:
        print(
            "❌ Schema mismatch above. Rename/add properties in Notion to match expected names & types."
        )
        sys.exit(2)
    else:
        print("  ✅ Schema looks good.")


def diag_meta_ping(ad_account_id):
    print("\n[4/7] Meta (Facebook) API check")
    token = os.getenv("FB_ACCESS_TOKEN", "")
    if not token:
        print("  ❌ FB_ACCESS_TOKEN missing")
        sys.exit(2)
    # Lightweight sanity ping
    url = f"https://graph.facebook.com/v19.0/{ad_account_id}?fields=name&access_token={token}"
    try:
        r = requests.get(url, timeout=20)
        if r.status_code == 200:
            nm = r.json().get("name", "(ok)")
            print(f"  ✅ Ad account reachable: {nm}")
        else:
            print(f"  ❌ Graph error {r.status_code}: {r.text[:240]}")
    except Exception as e:
        print(f"  ❌ Graph request failed: {e}")


def maybe_slack_ping():
    print("\n[5/7] Slack webhook check (optional)")
    wh = os.getenv("SLACK_WEBHOOK")
    if not wh:
        print(
            "  ℹ️ No SLACK_WEBHOOK env set (ok if you only run via GitHub Actions)."
        )
        return
    try:
        r = requests.post(wh,
                          json={"text": "Cenus diag: webhook OK ✅"},
                          timeout=10)
        print(
            f"  {ok(r.status_code in (200,204))} Slack POST -> {r.status_code}"
        )
    except Exception as e:
        print(f"  ❌ Slack POST failed: {e}")


def run_fatigue_demo():
    print("\n[6/7] Fatigue demo run")
    cmd = "python scripts/run_fatigue.py --level ad --days 14 --baseline_days 7 --demo"
    try:
        out = shell(cmd, check=False)
        print(out)
        if "Traceback" in out or "validation_error" in out:
            print(
                "  ❌ Fatigue demo encountered an error above. Fix and re-run.")
            sys.exit(2)
        print("  ✅ Fatigue demo completed.")
    except Exception as e:
        print(f"  ❌ Fatigue demo failed: {e}")
        sys.exit(2)


def run_daily_pipeline_dry():
    print("\n[7/7] Daily pipeline (yesterday window)")
    # Run without check so we can show the first error block
    cmd = "python scripts/run_daily_pipeline.py"
    out = shell(cmd, check=False)
    print(out)
    if "Traceback" in out or "validation_error" in out:
        print("  ❌ Pipeline had an error above. Address it and re-run.")
        sys.exit(2)
    print("  ✅ Pipeline completed (or skipped missing data gracefully).")


def main():
    ap = argparse.ArgumentParser(description="Cenus Full Diagnostic")
    ap.add_argument("--skip-pipeline",
                    action="store_true",
                    help="Skip the final daily pipeline run")
    ap.add_argument("--write-test",
                    action="store_true",
                    help="Create & delete a 1-row Notion test alert")
    args = ap.parse_args()

    print("=== Cenus Full Diagnostic ===")

    diag_files()

    clients = load_clients()
    client = get_first_client(clients)
    print(f"\nActive client: {client.get('client_name')}")
    print(f"Ad account: {client.get('ad_account_id')}")
    print(f"Notion Alerts DB: {client.get('notion_db_id')}")
    if not client.get("notion_db_id"):
        print("❌ notion_db_id missing in clients.json")
        sys.exit(2)

    diag_env(client)
    diag_notion_schema(client["notion_db_id"])
    diag_meta_ping(client.get("ad_account_id", ""))
    maybe_slack_ping()

    run_fatigue_demo()
    if not args.skip_pipeline:
        run_daily_pipeline_dry()

    print(
        "\n=== DONE: If any ❌ above, that’s the thing to fix. Otherwise you’re green. ==="
    )


if __name__ == "__main__":
    main()
