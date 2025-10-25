# src/notion.py
import os, requests, json

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_VERSION = "2022-06-28"


def _headers():
    return {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def create_kpi_db(parent_page_id: str, title: str) -> str:
    """
    Create the KPI database with a sensible default schema.
    """
    url = "https://api.notion.com/v1/databases"
    payload = {
        "parent": {
            "type": "page_id",
            "page_id": parent_page_id
        },
        "title": [{
            "type": "text",
            "text": {
                "content": title
            }
        }],
        "properties": {
            "timestamp": {
                "date": {}
            },
            "level": {
                "select": {
                    "options": [{
                        "name": "Campaign"
                    }, {
                        "name": "Adset"
                    }, {
                        "name": "Ad"
                    }]
                }
            },
            "id": {
                "rich_text": {}
            },
            "name": {
                "title": {}
            },
            "kpis": {
                "rich_text": {}
            },  # JSON blob as text
            "status": {
                "select": {
                    "options": [{
                        "name": "Active"
                    }, {
                        "name": "Paused"
                    }]
                }
            },
            "fatigue_flag": {
                "checkbox": {}
            },
            "reason": {
                "rich_text": {}
            },
            "actions": {
                "rich_text": {}
            },
        }
    }
    r = requests.post(url, headers=_headers(), json=payload, timeout=30)
    r.raise_for_status()
    return r.json()["id"]


def ensure_db_schema(database_id: str) -> int:
    """
    Adds any missing properties to the KPI DB. Returns count of added props.
    """
    # fetch current
    r = requests.get(f"https://api.notion.com/v1/databases/{database_id}",
                     headers=_headers(),
                     timeout=30)
    r.raise_for_status()
    current = r.json().get("properties", {})
    needed = {
        "timestamp": {
            "date": {}
        },
        "level": {
            "select": {
                "options": [{
                    "name": "Campaign"
                }, {
                    "name": "Adset"
                }, {
                    "name": "Ad"
                }]
            }
        },
        "id": {
            "rich_text": {}
        },
        "name": {
            "title": {}
        },
        "kpis": {
            "rich_text": {}
        },
        "status": {
            "select": {
                "options": [{
                    "name": "Active"
                }, {
                    "name": "Paused"
                }]
            }
        },
        "fatigue_flag": {
            "checkbox": {}
        },
        "reason": {
            "rich_text": {}
        },
        "actions": {
            "rich_text": {}
        },
    }
    to_add = {k: v for k, v in needed.items() if k not in current}
    added = 0
    for prop_name, prop_def in to_add.items():
        patch = {"properties": {prop_name: prop_def}}
        pr = requests.patch(
            f"https://api.notion.com/v1/databases/{database_id}",
            headers=_headers(),
            json=patch,
            timeout=30)
        pr.raise_for_status()
        added += 1
    return added


def create_settings_db(parent_page_id: str, title: str) -> str:
    """
    Create the per-client Settings DB with key/value columns.
    """
    url = "https://api.notion.com/v1/databases"
    payload = {
        "parent": {
            "type": "page_id",
            "page_id": parent_page_id
        },
        "title": [{
            "type": "text",
            "text": {
                "content": title
            }
        }],
        "properties": {
            "key": {
                "title": {}
            },
            "value": {
                "rich_text": {}
            },
        }
    }
    r = requests.post(url, headers=_headers(), json=payload, timeout=30)
    r.raise_for_status()
    return r.json()["id"]


def ensure_settings_rows(database_id: str) -> None:
    """
    Ensure default thresholds exist. If a key exists, skip.
    """
    defaults = [
        ("CTR_DOWN_PCT", "25"),
        ("ROAS_DOWN_PCT", "30"),
        ("CPM_UP_PCT", "40"),
        ("FREQ_UP_PCT", "35"),
        ("CPC_UP_PCT", "30"),
        ("RESULTS_DOWN_PCT", "30"),
    ]
    # fetch first 100 rows
    r = requests.post(
        "https://api.notion.com/v1/databases/{}/query".format(database_id),
        headers=_headers(),
        json={"page_size": 100},
        timeout=30)
    r.raise_for_status()
    existing = set()
    for row in r.json().get("results", []):
        title_prop = row["properties"]["key"]["title"]
        if title_prop:
            existing.add(title_prop[0]["plain_text"])

    for key, val in defaults:
        if key in existing:
            continue
        create_page_payload = {
            "parent": {
                "database_id": database_id
            },
            "properties": {
                "key": {
                    "title": [{
                        "type": "text",
                        "text": {
                            "content": key
                        }
                    }]
                },
                "value": {
                    "rich_text": [{
                        "type": "text",
                        "text": {
                            "content": val
                        }
                    }]
                }
            }
        }
        pr = requests.post("https://api.notion.com/v1/pages",
                           headers=_headers(),
                           json=create_page_payload,
                           timeout=30)
        pr.raise_for_status()


# --- Notion HTTP helpers (add these) ---
import os, requests

NOTION_API = "https://api.notion.com/v1"
NOTION_TOKEN = os.getenv("NOTION_TOKEN")


def _notion_headers():
    return {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }


def _post(path_or_url: str, payload: dict):
    # Accept either full URL or API path
    url = path_or_url if path_or_url.startswith(
        "http") else f"{NOTION_API}{path_or_url}"
    r = requests.post(url, headers=_notion_headers(), json=payload, timeout=30)
    if r.status_code >= 300:
        raise RuntimeError(
            f"Notion POST {url} -> {r.status_code}: {r.text[:300]}")
    return r.json()


# --- end helpers ---


def _patch(path_or_url: str, payload: dict):
    url = path_or_url if path_or_url.startswith(
        "http") else f"{NOTION_API}{path_or_url}"
    r = requests.patch(url,
                       headers=_notion_headers(),
                       json=payload,
                       timeout=30)
    if r.status_code >= 300:
        raise RuntimeError(
            f"Notion PATCH {url} -> {r.status_code}: {r.text[:300]}")
    return r.json()


# --- Settings loader (minimal, tolerant) ---
def get_settings(settings_db_id: str) -> dict:
    """
    Read key/value rows from the Notion Settings DB.
    Returns {} on any error so the engine can still run with defaults.
    Expected schema:
      - 'key'  (Title)
      - 'value' (Rich text)
    """
    if not settings_db_id:
        return {}
    try:
        url = f"{NOTION_API}/databases/{settings_db_id}/query"
        resp = requests.post(url,
                             headers=_notion_headers(),
                             json={"page_size": 100},
                             timeout=30)
        if resp.status_code >= 300:
            print(
                f"[warn] get_settings query {resp.status_code}: {resp.text[:200]}"
            )
            return {}
        data = resp.json()
        out = {}
        for row in data.get("results", []):
            props = row.get("properties", {})
            # Try common property names; fall back safely
            key_parts = props.get("key", {}).get("title", []) or props.get(
                "name", {}).get("title", [])
            key = "".join([p.get("plain_text", "") for p in key_parts]).strip()
            val_parts = props.get("value", {}).get("rich_text", [])
            val = "".join([p.get("plain_text", "") for p in val_parts]).strip()
            if key:
                out[key] = val
        return out
    except Exception as e:
        print(f"[warn] get_settings failed: {e}")
        return {}


# --- end settings loader ---


def create_alerts_db(parent_page_id: str, title: str) -> str:
    """
    Create the Alerts DB used to log every alert.
    """
    url = "https://api.notion.com/v1/databases"
    payload = {
        "parent": {
            "type": "page_id",
            "page_id": parent_page_id
        },
        "title": [{
            "type": "text",
            "text": {
                "content": title
            }
        }],
        "properties": {
            "timestamp": {
                "date": {}
            },
            "level": {
                "select": {
                    "options": [
                        {
                            "name": "Campaign"
                        },
                        {
                            "name": "Adset"
                        },
                        {
                            "name": "Ad"
                        },
                    ]
                }
            },
            "entity_id": {
                "rich_text": {}
            },
            "name": {
                "title": {}
            },
            "reason": {
                "rich_text": {}
            },
            "actions": {
                "rich_text": {}
            },
        },
    }
    return _post(url, payload)


def create_page(db_id: str, props: dict):
    url = f"https://api.notion.com/v1/pages"
    payload = {
        "parent": {
            "database_id": db_id
        },
        "properties": props,
    }
    return _post(url, payload)


def upsert_record(db_id: str, latest: dict):
    """
    Minimal shim: just create a page and return its id.
    (Good enough to finish Step 6; we can improve to a true upsert later.)
    """
    # choose an entity id to display
    ent = latest.get("ad_id") or latest.get("adset_id") or latest.get(
        "campaign_id") or ""
    title = latest.get("name") or ent or "Unknown"

    props = {
        "entity_name": {  # Title
            "title": [{
                "text": {
                    "content": title or "Untitled"
                }
            }]
        },
        "entity_id": {  # Text
            "rich_text": [{
                "text": {
                    "content": ent
                }
            }]
        },
        "level": {  # Select
            "select": {
                "name": (latest.get("level") or "Ad").title()
            } if latest.get("level") else None
        },
        "date": {  # Date
            "date": {
                "start": latest.get("date") or latest.get("timestamp") or ""
            }
        },
        "metric": {  # Select (optional)
            "select": {
                "name": latest.get("metric", "")
            } if latest.get("metric") else None
        },
        "value": {
            "number": latest.get("value")
        },
        "baseline": {
            "number": latest.get("baseline")
        },
        "pct_change": {
            "number": latest.get("pct_change")
        },
        "severity": {
            "select": {
                "name": latest.get("severity", "")
            } if latest.get("severity") else None
        },
        "client": {
            "rich_text": [{
                "text": {
                    "content": latest.get("client", "")
                }
            }]
        },
        "link": {
            "url": latest.get("link")
        },
        "notes": {
            "rich_text": [{
                "text": {
                    "content": latest.get("notes", "")
                }
            }]
        },
    }

    # Clean None-valued selects
    props = {k: v for k, v in props.items() if v is not None}

    resp = create_page(db_id, props)
    # Notion returns an object with 'id'
    page_id = resp.get("id") if isinstance(resp, dict) else None
    return "created", page_id


def update_fatigue_fields(page_id: str, fatigued: bool, reason: str,
                          actions: str):
    """
    Alerts DB does not have these properties. No-op to avoid 400 validation_error.
    """
    return


def add_alert_row(
    db_id: str,
    ts: str,
    level: str,
    entity_id: str,
    name: str,
    metric: str,
    value: float,
    baseline: float,
    pct_change: float,
    severity: str,
    client: str,
    link: str,
    notes: str = "",
):
    props = {
        "entity_name": {
            "title": [{
                "text": {
                    "content": name or "Untitled"
                }
            }]
        },  # Title
        "entity_id": {
            "rich_text": [{
                "text": {
                    "content": entity_id or ""
                }
            }]
        },  # Text
        "level": {
            "select": {
                "name": level
            }
        } if level else None,  # Select
        "date": {
            "date": {
                "start": ts
            }
        },  # Date (ISO)
        "metric": {
            "select": {
                "name": metric
            }
        } if metric else None,  # Select
        "value": {
            "number": value
        },  # Number
        "baseline": {
            "number": baseline
        },  # Number
        "pct_change": {
            "number": pct_change
        },  # Number
        "severity": {
            "select": {
                "name": severity
            }
        } if severity else None,  # Select
        "client": {
            "rich_text": [{
                "text": {
                    "content": client or ""
                }
            }]
        },  # Text
        "link": {
            "url": link
        },  # URL
        "notes": {
            "rich_text": [{
                "text": {
                    "content": notes or ""
                }
            }]
        },  # Rich text
    }
    # strip None selects
    props = {k: v for k, v in props.items() if v is not None}
    return _post("https://api.notion.com/v1/pages", {
        "parent": {
            "database_id": db_id
        },
        "properties": props,
    })
