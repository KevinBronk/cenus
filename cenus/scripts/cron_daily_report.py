# cenus/scripts/cron_alerts.py  (and same for cron_daily_report.py)
import sys, os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
# scripts/cron_daily_report.py
import os
import sys
import json
import traceback
from datetime import datetime

# src/reports.py: build_daily_summary(kpi_batch, client_cfg) -> dict
# src/notion.py: append_daily_report_to_notion(report_doc, client_cfg)
from src.meta_client import pull_kpis_for_all_clients
from src.reports import build_daily_summary
from src.notion import append_daily_report_to_notion


def load_clients():
    path = "clients.json"
    if not os.path.exists(path):
        print("[WARN] clients.json not found. Using empty set.")
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("clients", data) if isinstance(data, dict) else data


def run_once():
    clients = load_clients()
    if not clients:
        print("[INFO] No clients configured. Exiting cleanly.")
        return

    print(
        f"[INFO] Daily report at {datetime.utcnow().isoformat()}Z for {len(clients)} client(s)."
    )
    kpi_batch = pull_kpis_for_all_clients(clients)

    for c in clients:
        try:
            summary_doc = build_daily_summary(
                kpi_batch.get(c["ad_account_id"], []), c)
            append_daily_report_to_notion(summary_doc, c)
            print(f"[OK] Report posted → {c.get('name')}")
        except Exception as e:
            print(f"[ERROR] Report failed for {c.get('name')}: {e}")
            traceback.print_exc()


if __name__ == "__main__":
    try:
        required = ["FB_LONG_LIVED_TOKEN", "NOTION_TOKEN", "NOTION_VERSION"]
        missing = [k for k in required if not os.getenv(k)]
        if missing:
            print(f"[FATAL] Missing env(s): {', '.join(missing)}")
            sys.exit(1)
        run_once()
    except Exception as e:
        print(f"[FATAL] Uncaught error: {e}")
        traceback.print_exc()
        sys.exit(1)
