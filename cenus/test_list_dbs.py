# test_list_dbs.py
import os, json, requests
from dotenv import load_dotenv

load_dotenv(".env")

headers = {
    "Authorization": f"Bearer {os.getenv('NOTION_TOKEN')}",
    "Notion-Version": os.getenv("NOTION_VERSION", "2025-09-03"),
    "Content-Type": "application/json",
}

payload = {
    "filter": {"property": "object", "value": "data_source"},
    "page_size": 100,
}

resp = requests.post("https://api.notion.com/v1/search", headers=headers, json=payload)
print("Status:", resp.status_code)

j = resp.json()
for r in j.get("results", []):
    # title is optional; try to show something human-readable
    title = ""
    try:
        title = r["title"][0]["plain_text"]
    except Exception:
        pass

    ds_id = r.get("id", "").replace("-", "")
    source = r.get("source", {})
    db_id = source.get("database_id")  # the classic 32-char database id

    print(f"{title or '(untitled)'}  -> data_source_id={ds_id}  database_id={db_id}")
# If you want to see the whole response while debugging:
# print(json.dumps(j, indent=2))
