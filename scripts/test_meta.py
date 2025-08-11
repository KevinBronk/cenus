import sys
import requests
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.config import FB_ACCESS_TOKEN, META_API_VERSION, mask

BASE = f"https://graph.facebook.com/{META_API_VERSION}"


def get_me():
    r = requests.get(f"{BASE}/me",
                     params={
                         "access_token": FB_ACCESS_TOKEN,
                         "fields": "id,name"
                     })
    r.raise_for_status()
    return r.json()


def list_ad_accounts():
    r = requests.get(f"{BASE}/me/adaccounts",
                     params={
                         "access_token": FB_ACCESS_TOKEN,
                         "fields": "account_id,name,account_status"
                     })
    r.raise_for_status()
    return r.json()


if __name__ == "__main__":
    try:
        me = get_me()
        print(f"[Meta OK] User: {me.get('name')} (id: {me.get('id')})")
        accts = list_ad_accounts().get("data", [])
        if not accts:
            print(
                "[Meta WARN] No ad accounts returned. Ensure the token user has ad accounts and 'ads_read'."
            )
        else:
            print("[Meta OK] Found ad accounts:")
            for a in accts[:5]:
                print(
                    f" - act_{a['account_id']} | {a.get('name')} | status={a.get('account_status')}"
                )
        print(f"[Token (masked)] {mask(FB_ACCESS_TOKEN)}")
        sys.exit(0)
    except requests.HTTPError as e:
        print("[Meta ERROR]", e.response.status_code, e.response.text[:300])
        sys.exit(1)
    except Exception as e:
        print("[Meta ERROR]", str(e))
        sys.exit(1)
