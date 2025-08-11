import os, json, requests

VERSION = "v20.0"
TOKEN   = os.getenv("FB_TOKEN")
ACT_ID  = os.getenv("AD_ACCOUNT_ID")  # numbers only

def fb_get(path, params=None):
    params = params or {}
    params["access_token"] = TOKEN
    url = f"https://graph.facebook.com/{VERSION}/{path}"
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    return r.json()

def main():
    # 1) Verify user and token
    me = fb_get("me", {"fields":"id,name"})
    print("ME:", me)

    # 2) List ad accounts the token can see (sanity check)
    accts = fb_get("me/adaccounts", {"fields":"name,account_id,account_status,timezone_name,currency"})
    print("AD ACCOUNTS:", json.dumps(accts, indent=2))

    # 3) Touch your ad account (returns 200 even if empty)
    acct = fb_get(f"act_{ACT_ID}", {"fields":"id,account_id,name,account_status,currency,timezone_name"})
    print("ACCOUNT:", acct)

    # 4) Optional: try campaigns (will be empty if none yet)
    camps = fb_get(f"act_{ACT_ID}/campaigns", {"limit":1, "fields":"id,name,status"})
    print("CAMPAIGNS (first 1):", camps)

if __name__ == "__main__":
    try:
        main()
    except requests.HTTPError as e:
        print("HTTPError:", e.response.status_code, e.response.text[:400])