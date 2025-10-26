#!/usr/bin/env python3
# Daily pipeline: pull yesterday KPIs -> push to Notion -> fatigue+alerts

import os, subprocess, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
os.chdir(ROOT)


def sh(args):
    print("+", " ".join(args), flush=True)
    r = subprocess.run(args)
    if r.returncode != 0:
        sys.exit(r.returncode)


# Call the helper that glues everything together
sh(["python", "scripts/run_daily_pipeline.py"])
