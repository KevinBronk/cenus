import os, sys, json, argparse
from typing import List, Dict

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.notion import (
    create_kpi_db,
    ensure_db_schema,
    create_settings_db,
    ensure_settings_rows,
    create_alerts_db,   # ✅ make sure this line is there
)

CLIENTS_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "clients.json"))
PARENT_PAGE_ID = os.getenv("NOTION_PARENT_PAGE_ID")

DEFAULT_SETTINGS_TITLE = "Cenus Settings — {client}"
DEFAULT_KPI_TITLE = "{client} Ads DB"
DEFAULT_ALERTS_TITLE = "Cenus Alerts — {client}"   # <-- ADD THIS

def load_clients() -> List[Dict]:
    if not os.path.exists(CLIENTS_FILE): return []
    with open(CLIENTS_FILE, "r", encoding="utf-8") as f: return json.load(f)

def save_clients(clients: List[Dict]):
    with open(CLIENTS_FILE, "w", encoding="utf-8") as f: json.dump(clients, f, indent=2)

def upsert_client_entry(clients: List[Dict], entry: Dict) -> List[Dict]:
    out, found = [], False
    for c in clients:
        if c["client_name"].strip().lower() == entry["client_name"].strip().lower():
            out.append(entry); found = True
        else:
            out.append(c)
    if not found: out.append(entry)
    return out

def main():
    ap = argparse.ArgumentParser(
        description="Register/update a client. Auto-creates Notion KPI, Settings, and Alerts DBs if missing."
    )
    ap.add_argument("--client", required=True, help="Client name, e.g., 'RAH Clothing'")
    ap.add_argument("--ad_account_id", required=True, help="Meta ad account id, e.g., act_123...")
    ap.add_argument("--notion_db_id", help="Existing KPI DB id (optional)")
    ap.add_argument("--notion_settings_db_id", help="Existing Settings DB id (optional)")
    ap.add_argument("--notion_alerts_db_id", help="Existing Alerts DB id (optional)")   # <-- ADD
    ap.add_argument("--slack_webhook", help="Slack webhook (optional). If omitted, left blank.", default="")   # <-- ADD

    args = ap.parse_args()
    alerts_db_id = args.notion_alerts_db_id   # <-- ADD THIS

    clients = load_clients()
    notion_db_id = args.notion_db_id
    settings_db_id = args.notion_settings_db_id
    alerts_db_id = args.notion_alerts_db_id  # <-- NEW

    if not PARENT_PAGE_ID:
        raise SystemExit("NOTION_PARENT_PAGE_ID missing in Secrets.")

    # Create KPI DB if missing
    if not notion_db_id:
        notion_db_id = create_kpi_db(PARENT_PAGE_ID, DEFAULT_KPI_TITLE.format(client=args.client))
        added = ensure_db_schema(notion_db_id)
        print(f"[Notion] Created KPI DB: {notion_db_id} (added_props={added})")
    else:
        added = ensure_db_schema(notion_db_id)
        if added:
            print(f"[Notion] Ensured KPI DB schema: added {added}")

    # Create Settings DB if missing + seed defaults
    if not settings_db_id:
        settings_db_id = create_settings_db(PARENT_PAGE_ID, DEFAULT_SETTINGS_TITLE.format(client=args.client))
        ensure_settings_rows(settings_db_id)
        print(f"[Notion] Created Settings DB: {settings_db_id} and seeded defaults.")
    else:
        ensure_settings_rows(settings_db_id)
        print(f"[Notion] Ensured Settings defaults: {settings_db_id}")

    # Create Alerts DB if missing
    if not alerts_db_id:
        alerts_db_id = create_alerts_db(PARENT_PAGE_ID, DEFAULT_ALERTS_TITLE.format(client=args.client))
        print(f"[Notion] Created Alerts DB: {alerts_db_id}")
    else:
        print(f"[Notion] Using existing Alerts DB: {alerts_db_id}")


    entry = {
        "client_name": args.client,
        "ad_account_id": args.ad_account_id,
        "notion_db_id": notion_db_id,
        "notion_settings_db_id": settings_db_id,
        "notion_alerts_db_id": alerts_db_id,   # <-- ADD THIS
        "slack_webhook": args.slack_webhook or "",   # already present or add it

    }
    clients = upsert_client_entry(clients, entry)
    save_clients(clients)
    print("[Clients] Updated clients.json with:")
    print(json.dumps(entry, indent=2))

if __name__ == "__main__":
    main()
