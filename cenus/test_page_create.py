import os, requests
from dotenv import load_dotenv
load_dotenv(".env")

headers = {
  "Authorization": f"Bearer {os.getenv('NOTION_TOKEN')}",
  "Notion-Version": os.getenv("NOTION_VERSION", "2025-09-03"),
  "Content-Type": "application/json",
}
payload = {
  "parent": {"type": "data_source_id", "data_source_id": os.getenv("NOTION_SETTINGS_DS_ID")},
  "properties": {"client_name": {"title": [{"text": {"content": "Cenus AI Test Page"}}]}}
}
r = requests.post("https://api.notion.com/v1/pages", headers=headers, json=payload)
print(r.status_code)
print(r.text[:400])
