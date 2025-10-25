import os
import sys
import requests
from datetime import datetime, timedelta
from src.config import FB_ACCESS_TOKEN, META_API_VERSION

BASE = f"https://graph.facebook.com/{META_API_VERSION}"

def _act_id(raw: str) -> str:
    raw = (raw or "").strip()
    if not raw:
        raise RuntimeError("Missing AD_ACCOUNT_ID")
    return raw if raw.startswith("act_") else f"act_{raw}"

def get_active_campaign_count(account: str) -> int:
    # Uses summary=true to avoid listing everything
    params = {
        "access_token": FB_ACCESS_TOKEN,
        "fields": "name,effective_status",
        "effective_status": ["ACTIVE"],
        "summary": "true",
        "limit": 1
    }
    r = requests.get(f"{BASE}/{account}/campaigns", params=params, timeout=30)
    r.raise_for_status()
    j = r.json()
    summary = j.get("summary", {})
    return int(summary.get("total_count") or 0)

def get_yesterday_spend(account: str) -> float:
    yesterday = datetime.utcnow().date() - timedelta(days=1)
    time_range = {"since": str(yesterday), "until": str(yesterday)}
    params = {
        "access_token": FB_ACCESS_TOKEN,
        "level": "account",
        "fields": "spend",
        "time_range": str(time_range).replace("'", '"'),  # JSON-ish
        "limit": 1
    }
    r = requests.get(f"{BASE}/{account}/insights", params=params, timeout=60)
    r.raise_for_status()
    data = r.json().get("data", [])
    if not data:
        return 0.0
    spend_str = data[0].get("spend") or "0"
    try:
        return float(spend_str)
    except ValueError:
        return 0.0

if __name__ == "__main__":
    try:
        raw_id = os.getenv("AD_ACCOUNT_ID", "")
        account = _act_id(raw_id)

        active_count = get_active_campaign_count(account)
        y_spend = get_yesterday_spend(account)

        print(f"[Meta Health] Active campaigns: {active_count} | Yesterday spend: {y_spend:.2f}")

        # Alert if there ARE active campaigns but spend was zero yesterday.
        if active_count > 0 and y_spend <= 0.0:
            print("[Meta ALERT] Active campaigns detected but spend was 0 yesterday.")
            sys.exit(1)

        # Otherwise success
        print("[Meta OK] No issues detected.")
        sys.exit(0)

    except requests.HTTPError as e:
        print("[Meta ERROR]", e.response.status_code, e.response.text[:400])
        sys.exit(1)
    except Exception as e:
        print("[Meta ERROR]", str(e))
        sys.exit(1)