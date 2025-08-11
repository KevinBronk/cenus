import os, json, requests

FB_TOKEN      = os.getenv("FB_TOKEN")
FB_APP_ID     = os.getenv("FB_APP_ID")
FB_APP_SECRET = os.getenv("FB_APP_SECRET")
AD_ACCOUNT_ID = os.getenv("AD_ACCOUNT_ID")
NOTION_TOKEN  = os.getenv("NOTION_TOKEN")
SLACK_URL     = os.getenv("SLACK_WEBHOOK_URL")

def ok(label):   print(f"✅ {label}")
def fail(label, msg): 
    print(f"❌ {label} -> {msg}")
    raise SystemExit(1)

# ----- META checks -----
def test_meta():
    base = "https://graph.facebook.com/v20.0"

    # 0) Sanity: required vars
    for k,v in [("FB_TOKEN",FB_TOKEN),("FB_APP_ID",FB_APP_ID),("FB_APP_SECRET",FB_APP_SECRET)]:
        if not v: fail("Meta secrets", f"{k} missing")

    # 1) Debug the token (validity, scopes)
    try:
        debug = requests.get(
            f"{base}/debug_token",
            params={
                "input_token": FB_TOKEN,
                "access_token": f"{FB_APP_ID}|{FB_APP_SECRET}",
            },
            timeout=30,
        ).json()
        data = debug.get("data", {})
        if not data.get("is_valid"):
            fail("Meta token", f"Invalid token: {json.dumps(debug)[:300]}")
        scopes = set(data.get("scopes", []))
        if "ads_read" not in scopes:
            fail("Meta token", f"ads_read not present in scopes: {sorted(scopes)}")
        ok("Meta token valid (includes ads_read)")
    except Exception as e:
        fail("Meta token debug", str(e))

    # 2) /me and /me/adaccounts
    try:
        me = requests.get(f"{base}/me", params={"access_token": FB_TOKEN, "fields":"id,name"}, timeout=30).json()
        if "id" in me:
            ok(f"Meta /me -> {me['name']} ({me['id']})")
        else:
            fail("Meta /me", json.dumps(me)[:300])
    except Exception as e:
        fail("Meta /me", str(e))

    try:
        accts = requests.get(f"{base}/me/adaccounts", params={"access_token": FB_TOKEN, "fields":"name,account_id"}, timeout=30).json()
        ok(f"Meta /me/adaccounts -> found {len(accts.get('data',[]))} account(s)")
    except Exception as e:
        fail("Meta adaccounts", str(e))

    # 3) Touch your account (if provided)
    if AD_ACCOUNT_ID:
        try:
            acct = requests.get(
                f"{base}/act_{AD_ACCOUNT_ID}",
                params={"access_token": FB_TOKEN, "fields":"id,account_id,name,account_status"},
                timeout=30
            ).json()
            if "id" in acct:
                ok(f"Meta act_{AD_ACCOUNT_ID} reachable ({acct.get('name','no-name')})")
            else:
                fail("Meta act_{AD_ACCOUNT_ID}", json.dumps(acct)[:300])
        except Exception as e:
            fail("Meta act lookup", str(e))

# ----- NOTION check -----
def test_notion():
    if not NOTION_TOKEN:
        print("↪️  Skipping Notion (NOTION_TOKEN missing)")
        return
    try:
        r = requests.get(
            "https://api.notion.com/v1/users/me",
            headers={
                "Authorization": f"Bearer {NOTION_TOKEN}",
                "Notion-Version": "2022-06-28",
            },
            timeout=30,
        )
        if r.status_code == 200:
            me = r.json()
            ok(f"Notion /users/me -> {me.get('name') or me.get('id')}")
        else:
            fail("Notion /users/me", f"{r.status_code} {r.text[:200]}")
    except Exception as e:
        fail("Notion", str(e))

# ----- SLACK check -----
def test_slack():
    if not SLACK_URL:
        print("↪️  Skipping Slack (SLACK_WEBHOOK_URL missing)")
        return
    try:
        r = requests.post(SLACK_URL, json={"text":"✅ Cenus test: secrets wired up and working."}, timeout=20)
        if r.status_code == 200:
            ok("Slack webhook sent")
        else:
            fail("Slack webhook", f"{r.status_code} {r.text[:200]}")
    except Exception as e:
        fail("Slack", str(e))

if __name__ == "__main__":
    test_meta()
    test_notion()
    test_slack()
    print("\n🎉 All checks passed.")
