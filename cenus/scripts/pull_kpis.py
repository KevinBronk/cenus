# cenus/scripts/pull_kpis.py
import os, sys, json, argparse
from datetime import date, timedelta
from typing import List, Dict

# allow imports from src/ no matter where we run from
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.meta_client import fetch_insights_for_account, transform_rows_to_kpis
from src.storage import save_jsonl, save_csv, ts_now_iso

CLIENTS_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "clients.json"))

def load_clients() -> List[Dict]:
    if not os.path.exists(CLIENTS_FILE):
        raise SystemExit("clients.json not found. Run scripts/add_client.py first.")
    with open(CLIENTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def dstr(d: date) -> str:
    return d.strftime("%Y-%m-%d")

def pull_for_client(client: Dict, level: str, since: str, until: str):
    name = client["client_name"]
    account_id = client["ad_account_id"]
    print(f"[Pull] {name} {account_id} | level={level} | range {since}..{until}")

    raw_rows = fetch_insights_for_account(account_id, level=level, since=since, until=until)
    recs = transform_rows_to_kpis(raw_rows, level=level)

    # Output under ./data/<ClientName>/
    base_dir = os.path.join("data", name.replace(" ", "_"))
    os.makedirs(base_dir, exist_ok=True)
    jsonl_path = os.path.join(base_dir, f"{level}_{since}_{until}.jsonl")
    csv_path  = os.path.join(base_dir,  f"{level}_{since}_{until}.csv")

    save_jsonl(recs, jsonl_path)
    save_csv(recs, csv_path)
    print(f"[Saved] {len(recs)} records | JSONL: {jsonl_path} | CSV: {csv_path}")

def main():
    p = argparse.ArgumentParser(description="Pull KPIs from Meta for one/all clients.")
    p.add_argument("--client", help="Client name (defaults to all in clients.json)")
    p.add_argument("--level", default="all", help="campaign|adset|ad|all")
    p.add_argument("--since", help="YYYY-MM-DD (inclusive)")
    p.add_argument("--until", help="YYYY-MM-DD (inclusive)")
    args = p.parse_args()

    # default date range = yesterday
    if args.since and args.until:
        since, until = args.since, args.until
    else:
        y = date.today() - timedelta(days=1)
        since = until = dstr(y)

    levels = ["campaign", "adset", "ad"] if args.level == "all" else [args.level]

    clients = load_clients()
    if args.client:
        clients = [c for c in clients if c["client_name"].strip().lower() == args.client.strip().lower()]
        if not clients:
            raise SystemExit(f"No client named '{args.client}' found in clients.json")

    print(f"[Start] {ts_now_iso()} | range {since}..{until} | levels={levels} | clients={len(clients)}")
    for c in clients:
        for lvl in levels:
            pull_for_client(c, lvl, since, until)
    print(f"[Done] {ts_now_iso()}")

if __name__ == "__main__":
    main()
