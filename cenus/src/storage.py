# src/storage.py
import os, json, csv, datetime
from typing import List, Dict, Any

def _ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def ts_now_iso() -> str:
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

def save_jsonl(records: List[Dict[str, Any]], out_path: str):
    _ensure_dir(os.path.dirname(out_path))
    with open(out_path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

def save_csv(records: List[Dict[str, Any]], out_path: str):
    _ensure_dir(os.path.dirname(out_path))
    if not records:
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp"])
        return
    keys = sorted({k for r in records for k in r.keys()})
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for r in records:
            writer.writerow(r)
