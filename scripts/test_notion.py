import sys
import requests
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.config import NOTION_TOKEN

BASE = "https://api.notion.com/v1"
HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}

if __name__ == "__main__":
    try:
        r = requests.get(f"{BASE}/users/me", headers=HEADERS, timeout=20)
        r.raise_for_status()
        j = r.json()
        name = j.get("name") or j.get("bot", {}).get(
            "owner", {}).get("workspace_name") or "Unknown"
        print(f"[Notion OK] Connected as: {name}")
        sys.exit(0)
    except requests.HTTPError as e:
        print("[Notion ERROR]", e.response.status_code, e.response.text[:300])
        sys.exit(1)
    except Exception as e:
        print("[Notion ERROR]", str(e))
        sys.exit(1)
