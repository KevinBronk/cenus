import os, json, requests
from dotenv import load_dotenv

# Load .env from project root
load_dotenv(".env")

def show(title, resp):
    print(f"\n--- {title} ---")
    if isinstance(resp, requests.Response):
        print("Status:", resp.status_code)
        try:
            print(json.dumps(resp.json(), indent=2)[:800])
        except Exception:
            print(resp.text[:800])
    else:
        print(resp)

NOTION_TOKEN   = os.getenv("NOTION_TOKEN") or ""
NOTION_VERSION = os.getenv("NOTION_VERSION") or "2025-09-03"
DB_ID          = os.getenv("NOTION_SETTINGS_DB_ID") or ""

print("Token starts with:", NOTION_TOKEN[:3], "…  len:", len(NOTION_TOKEN))
print("Version:", NOTION_VERSION)
print("DB_ID:", DB_ID)

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": NOTION_VERSION,
}

# 1) Basic auth check
r = requests.get("https://api.notion.com/v1/users/me", headers=HEADERS)
show("users/me", r)

# 2) Database fetch — on 2025-09-03 this returns data_sources if the DB is shared correctly
if DB_ID:
    r = requests.get(f"https://api.notion.com/v1/databases/{DB_ID}", headers=HEADERS)
    show("get database", r)
    if r.ok:
        j = r.json()
        ds = j.get("data_sources", [])
        print("\nData sources (if any):", json.dumps(ds, indent=2)[:800])
        if ds:
            data_source_id = ds[0]["id"]
            print("Using data_source_id:", data_source_id)
            payload = {
                "parent": {"type": "data_source_id", "data_source_id": data_source_id},
                "properties": {"client_name": {"title": [{"text": {"content": "API smoke page"}}]}},
            }
            pr = requests.post("https://api.notion.com/v1/pages", headers=HEADERS, json=payload)
            show("create page", pr)
else:
    print("\nNo DB_ID set. Set NOTION_SETTINGS_DB_ID in .env.")
