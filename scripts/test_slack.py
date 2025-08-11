import sys
import json
import time
import requests
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.config import SLACK_WEBHOOK_URL

if __name__ == "__main__":
    payload = {"text": f":white_check_mark: Cenus test ping at {int(time.time())}"}
    try:
        r = requests.post(
            SLACK_WEBHOOK_URL,
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
            timeout=20,
        )
        if r.status_code != 200:
            print("[Slack ERROR]", r.status_code, r.text[:300])
            sys.exit(1)
        print("[Slack OK] Message posted to your webhook channel.")
        sys.exit(0)
    except Exception as e:
        print("[Slack ERROR]", str(e))
        sys.exit(1)