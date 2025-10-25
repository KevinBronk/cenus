# src/notion.py
import os, time, requests

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
if not NOTION_TOKEN:
    raise RuntimeError("NOTION_TOKEN missing. Add it in Replit > Secrets.")

BASE = "https://api.notion.com/v1"
HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}

RATE_SLEEP = 0.35  # ~3 req/sec

def _req(method: str, path: str, **kwargs):
    url = f"{BASE}{path}"
    for _ in range(3):
        r = requests.request(method, url, headers=HEADERS, timeout=40, **kwargs)
        if r.status_code == 429:
            time.sleep(1.0); continue
        if r.status_code >= 500:
            time.sleep(0.8); continue
        if r.ok:
            return r.json()
        # bubble up useful error text
        raise RuntimeError(f"Notion API error {r.status_code}: {r.text}")
    raise RuntimeError("Notion API failed after retries")

# ---------- schema helpers ----------
def get_database(db_id: str):
    return _req("GET", f"/databases/{db_id}")

def ensure_db_schema(db_id: str):
    """
    Add any missing properties used by record_to_props().
    Safe to call every run.
    """
    db = get_database(db_id)
    existing = set(db.get("properties", {}).keys())

    required = {
        "timestamp": {"date": {}},
        "level": {"select": {"options": [{"name": "Campaign"}, {"name": "Adset"}, {"name": "Ad"}]}},
        "id": {"rich_text": {}},
        "name": {"title": {}},
        "status": {"select": {"options": [{"name": "Active"}, {"name": "Paused"}, {"name": "Deleted"}]}},
        "fatigue_flag": {"checkbox": {}},
        "reason": {"rich_text": {}},
        "actions": {"rich_text": {}},
        "kpis_ctr": {"number": {}},
        "kpis_roas": {"number": {}},
        "kpis_cpm": {"number": {}},
        "kpis_cpc": {"number": {}},
        "kpis_cpa": {"number": {}},
        "kpis_frequency": {"number": {}},
        "kpis_impressions": {"number": {}},
        "kpis_spend": {"number": {}},
        "kpis_clicks": {"number": {}},
        "kpis_results": {"number": {}},
    }

    missing = {k: v for k, v in required.items() if k not in existing}
    if missing:
        _req("PATCH", f"/databases/{db_id}", json={"properties": missing})
        time.sleep(RATE_SLEEP)
    return list(missing.keys())

# ---------- mapping + upsert ----------
def record_to_props(record: dict) -> dict:
    def num(x): return None if x is None else float(x)
    return {
        "timestamp": {"date": {"start": record["timestamp"]}},
        "level": {"select": {"name": record.get("level") or "Ad"}},
        "id": {"rich_text": [{"text": {"content": record.get("id") or ""}}]},
        "name": {"title": [{"text": {"content": record.get("name") or ""}}]},
        "status": {"select": {"name": record.get("status") or "Active"}},
        "fatigue_flag": {"checkbox": bool(record.get("fatigue_flag", False))},
        "reason": {"rich_text": [{"text": {"content": record.get("reason") or ""}}]},
        "actions": {"rich_text": [{"text": {"content": record.get("actions") or ""}}]},
        "kpis_ctr": {"number": num(record.get("kpis_ctr"))},
        "kpis_roas": {"number": num(record.get("kpis_roas"))},
        "kpis_cpm": {"number": num(record.get("kpis_cpm"))},
        "kpis_cpc": {"number": num(record.get("kpis_cpc"))},
        "kpis_cpa": {"number": num(record.get("kpis_cpa"))},
        "kpis_frequency": {"number": num(record.get("kpis_frequency"))},
        "kpis_impressions": {"number": num(record.get("kpis_impressions"))},
        "kpis_spend": {"number": num(record.get("kpis_spend"))},
        "kpis_clicks": {"number": num(record.get("kpis_clicks"))},
        "kpis_results": {"number": num(record.get("kpis_results"))},
    }

def query_existing(db_id: str, ts: str, level: str, ent_id: str):
    payload = {
        "filter": {
            "and": [
                {"property": "timestamp", "date": {"equals": ts}},
                {"property": "level", "select": {"equals": level}},
                {"property": "id", "rich_text": {"equals": ent_id}},
            ]
        },
        "page_size": 1,
    }
    j = _req("POST", f"/databases/{db_id}/query", json=payload)
    results = j.get("results", [])
    return results[0]["id"] if results else None

def create_page(db_id: str, props: dict):
    j = _req("POST", "/pages", json={"parent": {"database_id": db_id}, "properties": props})
    time.sleep(RATE_SLEEP)
    return j.get("id")

def update_page(page_id: str, props: dict):
    j = _req("PATCH", f"/pages/{page_id}", json={"properties": props})
    time.sleep(RATE_SLEEP)
    return j.get("id")

def upsert_record(db_id: str, record: dict):
    ts = record["timestamp"]
    lvl = record.get("level") or "Ad"
    ent_id = record.get("id") or ""
    props = record_to_props(record)
    page_id = query_existing(db_id, ts, lvl, ent_id)
    if page_id:
        update_page(page_id, props); return ("update", page_id)
    else:
        new_id = create_page(db_id, props); return ("create", new_id)

def query_last_n(db_id: str, n: int = 5):
    payload = {"sorts": [{"property": "timestamp", "direction": "descending"}], "page_size": n}
    j = _req("POST", f"/databases/{db_id}/query", json=payload)
    return j.get("results", [])