import json, requests

def _post_json(url: str, payload: dict, timeout: int = 15):
    r = requests.post(
        url,
        data=json.dumps(payload),
        headers={"Content-Type": "application/json"},
        timeout=timeout
    )
    if r.status_code >= 300:
        raise RuntimeError(f"Slack webhook error {r.status_code}: {r.text}")

def format_slack_block(client_name: str, level: str, name: str, ts: str, reasons: str, fixes: str, kpis: dict):
    fields = []
    if kpis.get("roas") is not None: fields.append(f"*ROAS*: {kpis['roas']}")
    if kpis.get("cpm")  is not None: fields.append(f"*CPM*: ${kpis['cpm']}")
    if kpis.get("ctr")  is not None: fields.append(f"*CTR*: {kpis['ctr']}%")
    if kpis.get("spend")is not None: fields.append(f"*Spend*: ${kpis['spend']}")
    if kpis.get("res")  is not None: fields.append(f"*Results*: {kpis['res']}")

    text_kpis = " • ".join(fields) if fields else ""
    blocks = [
        {"type":"section","text":{"type":"mrkdwn","text":f":rotating_light: *Creative Fatigue Detected — {client_name}*\n*Level:* {level}\n*Name:* {name}\n*Date:* {ts}"}},
        {"type":"section","text":{"type":"mrkdwn","text":f"*Why:*\n{reasons}"}},
        {"type":"section","text":{"type":"mrkdwn","text":f"*Quick fixes:*\n{fixes}"}},
    ]
    if text_kpis:
        blocks.append({"type":"context","elements":[{"type":"mrkdwn","text":text_kpis}]})
    return {"blocks": blocks}

def send_slack_alert(webhook_url: str, client_name: str, level: str, name: str, ts: str, reasons: str, actions_list: list, kpis: dict):
    fixes_bullets = "\n".join([f"• {a}" for a in actions_list]) if actions_list else "• Review creative & audience"
    payload = format_slack_block(client_name, level, name, ts, reasons, fixes_bullets, kpis)
    _post_json(webhook_url, payload)
