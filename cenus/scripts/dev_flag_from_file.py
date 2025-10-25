import os, sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))  # add repo root to PYTHONPATH

import json, argparse
from typing import List, Dict
from src.fatigue import rolling_baseline, evaluate_rules
from src.notion import upsert_record, update_fatigue_fields

def load_jsonl(path: str) -> List[Dict]:
    out = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            out.append(json.loads(line))
    # ensure sorted by date
    out.sort(key=lambda r: r["timestamp"])
    return out

def main():
    ap = argparse.ArgumentParser(description="Flag fatigue using a local JSONL (no Meta fetch).")
    ap.add_argument("--client", required=True)
    ap.add_argument("--db", required=False, help="Notion DB id (if omitted, we read from clients.json)")
    ap.add_argument("--file", required=True, help="Path to JSONL from dev_make_fake_kpis.py")
    ap.add_argument("--baseline_days", type=int, default=7)
    args = ap.parse_args()

    # Get Notion DB id
    if not args.db:
        import json as _json
        clients = _json.load(open("clients.json","r",encoding="utf-8"))
        cli = next((c for c in clients if c["client_name"].lower()==args.client.lower()), None)
        if not cli: raise SystemExit(f"No client {args.client} in clients.json")
        db_id = cli["notion_db_id"]
    else:
        db_id = args.db

    rows = load_jsonl(args.file)
    if len(rows) < args.baseline_days + 1:
        raise SystemExit("Need at least baseline_days+1 rows")

    latest = rows[-1]
    baseline_rows = rows[-(args.baseline_days+1):-1]
    base = rolling_baseline(baseline_rows)

    # Default thresholds (you can later pull from settings DB)
    th = {"CTR_DOWN_PCT":25, "ROAS_DOWN_PCT":30, "CPM_UP_PCT":40, "FREQ_UP_PCT":35, "CPC_UP_PCT":30, "RESULTS_DOWN_PCT":30}

    fatigued, reasons, actions = evaluate_rules(latest, base, th)

    # Ensure the page exists; then write fatigue fields
    _, page_id = upsert_record(db_id, latest)
    if fatigued:
        reason_txt = " | ".join(reasons)[:1800]
        actions_txt = " • " + " • ".join(actions)
        update_fatigue_fields(page_id, True, reason_txt, actions_txt)
        print("[FLAGGED]", reason_txt)
    else:
        update_fatigue_fields(page_id, False, "", "")
        print("[OK] No fatigue per rules.")

if __name__ == "__main__":
    main()
