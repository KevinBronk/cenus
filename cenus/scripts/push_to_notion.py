import os, sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))  # add repo root to PYTHONPATH

# scripts/push_to_notion.py
import os, json, argparse
from typing import List, Dict
from src.notion import upsert_record  # ✅ only this import

CLIENTS_FILE = "clients.json"

def load_clients() -> List[Dict]:
    with open(CLIENTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def get_client(name: str, clients: List[Dict]):
    for c in clients:
        if c["client_name"].strip().lower() == name.strip().lower():
            return c
    return None

def main():
    ap = argparse.ArgumentParser(description="Push KPI JSONL into Notion with upsert")
    ap.add_argument("--client", required=True, help="Client name as in clients.json")
    ap.add_argument("--file", required=True, help="Path to JSONL file produced by Step 3 / mock")
    args = ap.parse_args()

    clients = load_clients()
    client = get_client(args.client, clients)
    if not client:
        raise SystemExit(f"No client named '{args.client}' in clients.json")

    db_id = client["notion_db_id"]

    count_create = 0
    count_update = 0

    with open(args.file, "r", encoding="utf-8") as f:
        for line in f:
            record = json.loads(line)
            action, _ = upsert_record(db_id, record)
            if action == "create":
                count_create += 1
            else:
                count_update += 1

    print(f"[Done] Notion upsert: created={count_create}, updated={count_update}")

if __name__ == "__main__":
    main()
