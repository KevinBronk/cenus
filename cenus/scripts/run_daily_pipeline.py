# scripts/run_daily_pipeline.py
import os, json, datetime, subprocess, sys
from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parents[1]  # repo root (…/cenus)
def abspath(*parts):
    return str(REPO_ROOT.joinpath(*parts))


# Resolve absolute paths so it works from any CWD (GitHub Actions, Replit, local)
SCRIPT_DIR = Path(__file__).resolve().parent  # .../scripts
ROOT = SCRIPT_DIR.parent  # repo root
SCRIPTS = ROOT / "scripts"
DATA_DIR = ROOT / "data"
CLIENTS_FILE = ROOT / "clients.json"


def sh(args):
    # Ensure everything is str (Path -> str) and use the same Python interpreter
    cmd = [sys.executable] + [str(a) for a in args] if isinstance(
        args, list) and str(args[0]).endswith(".py") else [
            str(a) for a in args
        ]
    print("+", " ".join(cmd))
    r = subprocess.run(cmd, stdout=sys.stdout, stderr=sys.stderr)
    if r.returncode != 0:
        raise SystemExit(r.returncode)


def main():
    if not CLIENTS_FILE.exists():
        raise SystemExit(
            "clients.json not found at repo root. Run scripts/add_client.py first."
        )
    clients = json.load(open(CLIENTS_FILE, "r", encoding="utf-8"))

    # Default: yesterday (ISO date)
    y = (datetime.date.today() -
         datetime.timedelta(days=1)).strftime("%Y-%m-%d")

    for c in clients:
        name = c["client_name"]
        print(f"\n=== Daily pipeline for: {name} ===")

        # 1) Pull KPIs (campaign/adset/ad) for yesterday
        sh(["python", abspath("scripts", "pull_kpis.py"),
            "--client", name, "--level", "all", "--since", y, "--until", y])
        ])

        # 2) Push each level’s JSONL to Notion (exists in data/<Client_Name>/)
        client_dir = DATA_DIR / name.replace(" ", "_")
        for level in ["campaign", "adset", "ad"]:
            jsonl = client_dir / f"{level}_{y}_{y}.jsonl"
            if os.path.exists(jsonl):
                sh(["python", abspath("scripts", "push_to_notion.py"),
                    "--client", name, "--file", jsonl])
                ])
            else:
                print(f"   (skip: {jsonl} not found)")

        # 3) Run fatigue + alerts across the last 14 days (7-day baseline)
        sh([
            "python", abspath("scripts", "run_fatigue_and_alerts.py"),
            "--client", name, "--level", "ad", "--days", "14", "--baseline_days", "7",
        ])

    print("\n[Daily pipeline complete]")


if __name__ == "__main__":
    main()
