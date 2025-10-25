# scripts/doctor.py
import os, json, sys, argparse, requests
from pathlib import Path

NOTION_API = "https://api.notion.com/v1"
GRAPH_API = "https://graph.facebook.com"


def clean_token(t: str) -> str:
    return (t or "").strip().strip('"').strip("'")


def load_clients(path="clients.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_client(clients, name=None):
    if name:
        for c in clients:
            if c["client_name"].strip().lower() == name.strip().lower():
                return c
        print(f"[!] No client named '{name}' in clients.json")
        sys.exit(1)
    return clients[0]


def env_head():
    nt = os.getenv("NOTION_TOKEN", "")
    fb = clean_token(os.getenv("FB_ACCESS_TOKEN", ""))
    ver = os.getenv("META_API_VERSION", "")

    def safe(x):
        return (x[:6] + "..." + x[-4:]) if x and len(x) > 12 else x

    print("\n[ENV]")
    print("  NOTION_TOKEN:", "present" if nt else "MISSING", safe(nt))
    print("  FB_ACCESS_TOKEN:", "present" if fb else "MISSING", safe(fb))
    print("  META_API_VERSION:", ver or "MISSING")
    if nt and not nt.startswith("secret_"):
        print(
            "  [WARN] NOTION_TOKEN usually starts with 'secret_'. Double-check it’s the Internal Integration Secret."
        )
    return nt, fb, ver


def notion_headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }


def notion_ping_db(token, db_id, label):
    try:
        r = requests.post(f"{NOTION_API}/databases/{db_id}/query",
                          headers=notion_headers(token),
                          json={"page_size": 1},
                          timeout=30)
        code = r.status_code
        print(f"\n[NOTION] {label} query -> HTTP {code}")
        try:
            j = r.json()
            print("  resp:", (j.get("message") or j)
                  if isinstance(j, dict) else str(j)[:300])
        except Exception:
            print("  raw:", r.text[:300])
        return code, r.text
    except Exception as e:
        print(f"  [ERR] {e}")
        return -1, str(e)


def graph_get(url, params):
    try:
        r = requests.get(url, params=params, timeout=30)
        code = r.status_code
        try:
            j = r.json()
        except Exception:
            j = {"_raw": r.text}
        return code, j
    except Exception as e:
        return -1, {"_err": str(e)}


def meta_ping_account(fb_token, ver, act_id):
    print(f"\n[META] act_{act_id} basic check")
    code, j = graph_get(f"{GRAPH_API}/v{ver}/act_{act_id}", {
        "fields": "name,account_status,disable_reason",
        "access_token": fb_token
    })
    print(f"  account lookup -> HTTP {code}")
    print(
        "  resp:", j if code != 200 else {
            "name": j.get("name"),
            "account_status": j.get("account_status")
        })
    return code, j


def meta_ping_insights(fb_token, ver, act_id):
    print(
        f"\n[META] act_{act_id} minimal insights (yesterday, level=ad, limit=1)"
    )
    code, j = graph_get(
        f"{GRAPH_API}/v{ver}/act_{act_id}/insights", {
            "level": "ad",
            "date_preset": "yesterday",
            "limit": 1,
            "access_token": fb_token
        })
    print(f"  insights -> HTTP {code}")
    print("  resp:",
          j if code != 200 else {"data_len": len(j.get("data", []))})
    return code, j


def print_next_steps(notion_kpi_code, notion_settings_code, meta_acct_code,
                     meta_ins_code):
    print("\n=== NEXT ACTIONS ===")

    # Notion KPI DB
    if notion_kpi_code == 403:
        print(
            "- NOTION KPI DB 403: In Notion open your KPI database → ••• (three dots) → Connections → Add connections → select your integration."
        )
        print(
            "  Also click Share → Invite → select the same integration. Then re-run this doctor."
        )
    elif notion_kpi_code not in (200, 0) and notion_kpi_code != -1:
        print(
            f"- NOTION KPI DB returned HTTP {notion_kpi_code}. Check DB ID and integration access."
        )

    act_id = c.get("ad_account_id", "")

    # Notion Settings DB
    if notion_settings_code == 403:
        print(
            "- NOTION Settings DB 403: Open the Settings DB → ••• → Connections → Add connections → select your integration."
        )
        print(
            "  Also Share → Invite → add the integration. Then re-run this doctor."
        )
    elif notion_settings_code not in (200, 0) and notion_settings_code != -1:
        print(
            f"- NOTION Settings DB returned HTTP {notion_settings_code}. Verify the DB ID (32 chars) and access."
        )

    # Meta account
    if meta_acct_code == 403:
        print(
            "- META 403 on account lookup: Give the token’s user access to the ad account."
        )
        print(
            "  Click path: Business Settings → Accounts → Ad Accounts → Add People → select YOUR user → grant Admin or Advertiser."
        )
        print(
            "  Also ensure the token includes 'ads_read' (and 'ads_management' if you’ll write)."
        )
    elif meta_acct_code not in (200, 0) and meta_acct_code != -1:
        print(
            f"- META account lookup HTTP {meta_acct_code}. Check token validity and account ID (act_...)"
        )

    # Meta insights
    if meta_ins_code == 403:
        print(
            "- META 403 on insights: Token missing scope or the user lacks access."
        )
        print(
            "  Fix: Ensure the token user is in the business and has access to the ad account (Admin/Advertiser)."
        )
        print(
            "  If still failing, regenerate a long-lived user token with 'ads_read' and update FB_ACCESS_TOKEN."
        )
    elif meta_ins_code not in (200, 0) and meta_ins_code != -1:
        print(
            f"- META insights HTTP {meta_ins_code}. If 400 (#100/#200) read the error message; often a scope/access issue."
        )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--client",
                    default=None,
                    help="Client name in clients.json (default: first)")
    args = ap.parse_args()

    nt, fb, ver = env_head()
    if not nt or not fb or not ver:
        print(
            "\n[STOP] One or more required env vars are missing. Set NOTION_TOKEN, FB_ACCESS_TOKEN, META_API_VERSION."
        )
        sys.exit(1)

    clients = load_clients()
    c = get_client(clients, args.client)
    kpi_db = c.get("notion_db_id", "")
    set_db = c.get("notion_settings_db_id", "")
    act_id = c.get("ad_account_id", "").replace("act_", "")

    if not kpi_db or not set_db or not act_id:
        print(
            "[STOP] clients.json missing notion_db_id / notion_settings_db_id / ad_account_id."
        )
        sys.exit(1)

    nk_code, _ = notion_ping_db(nt, kpi_db, "KPI DB")
    ns_code, _ = notion_ping_db(nt, set_db, "Settings DB")
    ma_code, _ = meta_ping_account(fb, ver, act_id)
    mi_code, _ = meta_ping_insights(fb, ver, act_id)
    
def print_next_steps(notion_kpi_code, notion_settings_code, meta_acct_code, meta_ins_code, client):
    print("\n=== NEXT ACTIONS ===")
    print(f"Client: {client.get('client_name')} | Ad Account: {client.get('ad_account_id')}")

    if notion_kpi_code == 403:
        print("- NOTION KPI DB 403: Check DB ID and integration access.")
    if notion_settings_code == 403:
        print("- NOTION Settings DB 403: Check DB ID and integration access.")
    if meta_acct_code not in (200, 0, -1):
        print(f"- META account lookup returned {meta_acct_code}")
    if meta_ins_code not in (200, 0, -1):
        print(f"- META insights returned {meta_ins_code}")


if __name__ == "__main__":
    main()
