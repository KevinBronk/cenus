# scripts/read_notion.py
import os, sys, json, argparse
from typing import List, Dict

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.notion import query_last_n

CLIENTS_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "clients.json"))

def load_clients() -> List[Dict]:
    with open(CLIENTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def get_client(name: str, clients: List[Dict]):
    for c in clients:
        if c["client_name"].strip().lower() == name.strip().lower():
            return c
    return None

def main():
    ap = argparse.ArgumentParser(description="Read last N rows from a client's Notion DB")
    ap.add_argument("--client", required=True)
    ap.add_argument("--n", type=int, default=5)
    args = ap.parse_args()

    clients = load_clients()
    client = get_client(args.client, clients)
    if not client:
        raise SystemExit(f"No client named '{args.client}' in clients.json")

    db_id = client["notion_db_id"]
    results = query_last_n(db_id, args.n)

    out = []
    for p in results:
        props = p.get("properties", {})
        def val(name, kind):
            v = props.get(name, {})
            if kind == "title":
                arr = v.get("title", [])
                return (arr[0]["plain_text"] if arr else "")
            if kind == "select":
                s = v.get("select")
                return s["name"] if s else ""
            if kind == "date":
                d = v.get("date")
                return d["start"] if d else ""
            if kind == "number":
                return v.get("number")
            if kind == "rich_text":
                arr = v.get("rich_text", [])
                return (arr[0]["plain_text"] if arr else "")
            return ""
        out.append({
            "timestamp": val("timestamp", "date"),
            "level": val("level", "select"),
            "id": val("id", "rich_text"),
            "name": val("name", "title"),
            "ctr": val("kpis_ctr", "number"),
            "roas": val("kpis_roas", "number"),
            "spend": val("kpis_spend", "number"),
        })

    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()