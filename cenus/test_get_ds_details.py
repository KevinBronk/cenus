# test_get_ds_details.py
import os, json, requests
from dotenv import load_dotenv
load_dotenv(".env")

HEADERS = {
    "Authorization": f"Bearer {os.getenv('NOTION_TOKEN')}",
    "Notion-Version": os.getenv("NOTION_VERSION", "2025-09-03"),
}

# paste the data_source_id for **Cenus Global Settings** from your output
DS_ID = "28bab3b3047980c58546000bf10ee9ab"

url = f"https://api.notion.com/v1/data_sources/{DS_ID}"
r = requests.get(url, headers=HEADERS)
print("Status:", r.status_code)
j = r.json()
print(json.dumps(j, indent=2)[:2000])  # trim just to keep it readable

# Try to print the classic database_id if present
try:
    db_id = j.get("sources", [{}])[0].get("database_id")
    print("\nResolved database_id:", db_id)
except Exception:
    pass
