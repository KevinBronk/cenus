# cenus/scripts/cron_alerts.py  (and same for cron_daily_report.py)
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# scripts/cron_alerts.py
import os
import sys
import json
import traceback
from datetime import datetime

# Expect these modules already exist in your repo per earlier steps:
# src/meta_client.py: pull_kpis_for_all_clients()
# src/fatigue.py: run_fatigue_rules(kpi_batch, client_cfg)
# src/alerts.py: send_alerts_to_notion_and_slack(findings, client_cfg)

from src.meta_client import pull_kpis_for_all_clients
from src.fatigue import run_fatigue_rules
from src.alerts import send_alerts_to_notion_and_slack


def load_clients():
    path = "clients.json"
    if not os.path.exists(path):
        # Safe fallback so scheduler never crashes the whole workflow
        print("[WARN] clients.json not found. Using empty set.")
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # Supports both {"clients":[...]} and bare [...]
    return data.get("clients", data) if isinstance(data, dict) else data


def run_once():
    clients = load_clients()
    if not clients:
        print("[INFO] No clients configured. Exiting cleanly.")
        return

    print(
        f"[INFO] Alerts run at {datetime.utcnow().isoformat()}Z for {len(clients)} client(s)."
    )
    kpi_batch = pull_kpis_for_all_clients(clients)

    all_findings = []
    for c in clients:
        try:
            findings = run_fatigue_rules(kpi_batch.get(c["ad_account_id"], []),
                                         c)
            if findings:
                send_alerts_to_notion_and_slack(findings, c)
                all_findings.extend(findings)
        except Exception as e:
            print(f"[ERROR] Client {c.get('name')} failed: {e}")
            traceback.print_exc()

    print(f"[INFO] Alerts complete. Total findings: {len(all_findings)}")


if __name__ == "__main__":
    try:
        # Ensure required envs are present
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
