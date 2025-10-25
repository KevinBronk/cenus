import os
import requests
from typing import List, Dict, Any

# --- helper to call Graph API ---
def _get(url: str, params: dict) -> dict:
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    return resp.json()

# --- fetch insights ---
def fetch_insights_for_account(ad_account_id: str, level: str, since: str, until: str) -> List[Dict[str, Any]]:
    token = os.getenv("FB_ACCESS_TOKEN")  # read from .env

    fields = [
        "impressions", "spend", "clicks", "cpc", "cpm", "ctr", "frequency",
        "actions", "action_values", "reach", "results", "roas"
    ]
    params = {
        "access_token": token,
        "level": level,
        "time_increment": 1,
        "time_range": {"since": since, "until": until},
        "fields": ",".join(fields),
        "limit": 500,
    }

    url = f"https://graph.facebook.com/{os.getenv('META_API_VERSION','v18.0')}/{ad_account_id}/insights"
    out: List[Dict[str, Any]] = []

    while True:
        data = _get(url, params)
        out.extend(data.get("data", []))
        paging = data.get("paging", {})
        next_url = paging.get("next")
        if not next_url:
            break
        url = next_url
        params = {}  # token already baked into next_url

    return out

# --- transform to KPIs ---
def transform_rows_to_kpis(rows: List[Dict[str, Any]], level: str) -> List[Dict[str, Any]]:
    def _normalize_number(v):
        try:
            return float(v)
        except Exception:
            return 0.0

    out = []
    for r in rows:
        impressions = _normalize_number(r.get("impressions"))
        spend = _normalize_number(r.get("spend"))
        ctr = _normalize_number(r.get("ctr"))
        cpm = _normalize_number(r.get("cpm"))
        cpc = _normalize_number(r.get("cpc"))
        freq = _normalize_number(r.get("frequency"))
        clicks = _normalize_number(r.get("clicks"))

        out.append({
            "id": r.get(f"{level}_id"),
            "name": r.get(f"{level}_name"),
            "impressions": impressions,
            "spend": spend,
            "ctr": ctr,
            "cpm": cpm,
            "cpc": cpc,
            "frequency": freq,
            "clicks": clicks,
            "actions": r.get("actions", []),
            "results": r.get("results"),
            "roas": r.get("roas"),
        })
    return out
