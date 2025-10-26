#!/usr/bin/env python3
# Run fatigue+alerts for all clients (14d window, 7d baseline) from repo root.

import os, json, subprocess, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
os.chdir(ROOT)


def sh(args):
    print("+", " ".join(args), flush=True)
    r = subprocess.run(args)
    if r.returncode != 0:
        sys.exit(r.returncode)


# If you want to no-op when no clients.json:
if not os.path.exists("clients.json"):
    print("[WARN] clients.json not found. Exiting cleanly.")
    sys.exit(0)

# 1-liner: your helper already loops clients / or handles config
sh([
    "python", "scripts/run_fatigue_and_alerts.py", "--level", "ad", "--days",
    "14", "--baseline_days", "7"
])
