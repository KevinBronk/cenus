import os, json, requests

url = os.getenv("SLACK_WEBHOOK_URL")
payload = {
    "text": ":zap: Cenus test — Slack webhook connected! (If you see this, we’re good.)"
}
r = requests.post(url, data=json.dumps(payload), headers={"Content-Type": "application/json"}, timeout=20)
print(r.status_code, r.text[:200])