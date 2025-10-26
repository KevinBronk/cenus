# scripts/run_daily_pipeline.py
import os, json, datetime, subprocess, sys

CLIENTS_FILE = "clients.json"


def sh(args):
    print("+", " ".join(args), flush=True)
    r = subprocess.run(args, stdout=sys.stdout, stderr=sys.stderr)
    if r.returncode != 0:
        raise SystemExit(r.returncode)


def main():
    if not os.path.exists(CLIENTS_FILE):
        raise SystemExit(
            "clients.json not found. Run scripts/add_client.py first.")
    with open(CLIENTS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # supports {"clients":[...]} or bare list [...]
    if isinstance(data, dict) and "clients" in data:
        clients = data["clients"]
    elif isinstance(data, list):
        clients = data
    else:
        clients = []

    # Default: yesterday
    y = (datetime.date.today() -
         datetime.timedelta(days=1)).strftime("%Y-%m-%d")

    for c in clients:
        name = c["client_name"]
        print(f"\n=== Daily pipeline for: {name} ===")

        # 1) Pull KPIs (campaign/adset/ad) for yesterday
        sh([
            "python", "scripts/pull_kpis.py", "--client", name, "--level",
            "all", "--since", y, "--until", y
        ])

        # 2) Push each level’s JSONL to Notion (exists in data/<Client_Name>/)
        client_dir = os.path.join("data", name.replace(" ", "_"))
        for level in ["campaign", "adset", "ad"]:
            jsonl = os.path.join(client_dir, f"{level}_{y}_{y}.jsonl")
            if os.path.exists(jsonl):
                sh([
                    "python", "scripts/push_to_notion.py", "--client", name,
                    "--file", jsonl
                ])
            else:
                print(f"   (skip: {jsonl} not found)")

        # 3) Run fatigue + alerts across the last 14 days (7-day baseline)
        sh([
            "python", "scripts/run_fatigue_and_alerts.py", "--client", name,
            "--level", "ad", "--days", "14", "--baseline_days", "7"
        ])

    print("\n[Daily pipeline complete]")


if __name__ == "__main__":
    main()
