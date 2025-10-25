import os, json, argparse, datetime, random

def date_str(d): return d.strftime("%Y-%m-%d")

def gen_series(days=14, level="ad", entity_id="1234567890", name="Mock Ad A"):
    end = datetime.date.today() - datetime.timedelta(days=1)
    start = end - datetime.timedelta(days=days-1)
    out = []
    base_ctr = 1.2  # %
    base_roas = 2.2
    base_cpm = 10.0
    base_cpc = 0.80
    base_freq = 1.6
    base_impr = 4500
    base_spend = 35.0
    base_clicks = 55
    base_results = 2

    d = start
    day_idx = 0
    while d <= end:
        # introduce fatigue after day 9
        fatigue = day_idx >= 9
        mult = 0.6 if fatigue else 1.0
        ctr = round(base_ctr * mult * random.uniform(0.9, 1.1), 3)
        roas = round(base_roas * (0.7 if fatigue else 1.0) * random.uniform(0.9, 1.1), 2)
        cpm = round(base_cpm * (1.5 if fatigue else 1.0) * random.uniform(0.95, 1.1), 2)
        cpc = round(base_cpc * (1.3 if fatigue else 1.0) * random.uniform(0.9, 1.1), 2)
        freq = round(base_freq * (1.5 if fatigue else 1.0) * random.uniform(0.95, 1.1), 2)
        impr = int(base_impr * (1.0 if fatigue else 1.1) * random.uniform(0.9, 1.1))
        spend = round(base_spend * (1.0 if fatigue else 1.05) * random.uniform(0.9, 1.1), 2)
        clicks = int(base_clicks * (0.8 if fatigue else 1.1) * random.uniform(0.9, 1.1))
        results = max(0, int(base_results * (0.6 if fatigue else 1.2) * random.uniform(0.8, 1.2)))

        rec = {
            "timestamp": date_str(d),
            "level": level.capitalize(),
            "id": entity_id,
            "name": name,
            "status": "Active",
            "fatigue_flag": False,
            "reason": "",
            "actions": "",
            "kpis_ctr": ctr,
            "kpis_roas": roas,
            "kpis_cpm": cpm,
            "kpis_cpc": cpc,
            "kpis_cpa": round(spend / results, 2) if results else None,
            "kpis_frequency": freq,
            "kpis_impressions": impr,
            "kpis_spend": spend,
            "kpis_clicks": clicks,
            "kpis_results": results,
            "account_id": "act_mock",
            "campaign_id": "cmp_mock",
            "adset_id": "set_mock",
            "ad_id": entity_id,
            "date_start": date_str(d),
            "date_stop": date_str(d),
        }
        out.append(rec)
        d += datetime.timedelta(days=1)
        day_idx += 1
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--client_folder", required=True, help="e.g., data/Rah_Clothing")
    ap.add_argument("--level", default="ad", choices=["campaign","adset","ad"])
    args = ap.parse_args()

    os.makedirs(args.client_folder, exist_ok=True)
    records = gen_series(days=14, level=args.level, entity_id="1234567890", name="Mock Ad A")
    # Write JSONL like Step 3 does
    path = os.path.join(args.client_folder, f"{args.level}_MOCK.jsonl")
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    print(f"[Mock] Wrote {len(records)} rows to {path}")

if __name__ == "__main__":
    main()
