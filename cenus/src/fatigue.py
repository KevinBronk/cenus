from typing import List, Dict, Tuple, Any
import statistics as stats


def _flt(x):
    try:
        return float(x) if x is not None else None
    except Exception:
        return None


def pct_change(curr: float, base: float) -> float:
    if base is None or base == 0 or curr is None:
        return 0.0
    return (curr - base) / base * 100.0


def build_series(rows: List[Dict[str, Any]], key: str) -> List[float]:
    vals = []
    for r in rows:
        v = _flt(r.get(key))
        if v is not None:
            vals.append(v)
    return vals


def rolling_baseline(last_7_rows: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Compute 7-day baseline (mean) for key KPIs.
    Input rows must be daily (one per date for the same entity).
    """
    keys = [
        "kpis_ctr", "kpis_roas", "kpis_cpm", "kpis_cpc", "kpis_frequency",
        "kpis_impressions", "kpis_spend", "kpis_clicks", "kpis_results"
    ]
    base = {}
    for k in keys:
        s = build_series(last_7_rows, k)
        base[k] = stats.fmean(s) if s else 0.0
    return base

def _to_float(v, default):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def evaluate_rules(latest: Dict[str, Any], base: Dict[str, float],
                   th: Dict[str, float]) -> Tuple[bool, List[str], List[str]]:
    """
    Returns (is_fatigued, reasons[], actions[])
    th keys:
      CTR_DOWN_PCT, ROAS_DOWN_PCT, CPM_UP_PCT, FREQ_UP_PCT, CPC_UP_PCT, RESULTS_DOWN_PCT
    """
    reasons = []
    actions = []

    # Extract values
    ctr = _flt(latest.get("kpis_ctr")) or 0.0
    roas = _flt(latest.get("kpis_roas")) or 0.0
    cpm = _flt(latest.get("kpis_cpm")) or 0.0
    cpc = _flt(latest.get("kpis_cpc")) or 0.0
    freq = _flt(latest.get("kpis_frequency")) or 0.0
    results = _flt(latest.get("kpis_results")) or 0.0

    # Baselines
    b_ctr = base.get("kpis_ctr", 0.0)
    b_roas = base.get("kpis_roas", 0.0)
    b_cpm = base.get("kpis_cpm", 0.0)
    b_cpc = base.get("kpis_cpc", 0.0)
    b_freq = base.get("kpis_frequency", 0.0)
    b_results = base.get("kpis_results", 0.0)

    # % deltas
    d_ctr = pct_change(ctr, b_ctr)
    d_roas = pct_change(roas, b_roas)
    d_cpm = pct_change(cpm, b_cpm)
    d_cpc = pct_change(cpc, b_cpc)
    d_freq = pct_change(freq, b_freq)
    d_results = pct_change(results, b_results)

    # Thresholds (defaults baked; can be overridden by Notion settings)
    FREQ_UP_PCT      = _to_float(th.get("FREQ_UP_PCT"), 35.0)
    CTR_DOWN_PCT     = _to_float(th.get("CTR_DOWN_PCT"), 25.0)
    ROAS_DOWN_PCT    = _to_float(th.get("ROAS_DOWN_PCT"), 30.0)
    CPM_UP_PCT       = _to_float(th.get("CPM_UP_PCT"), 40.0)
    RESULTS_DOWN_PCT = _to_float(th.get("RESULTS_DOWN_PCT"), 30.0)

    # --- Rules ---
    # A) Classic fatigue: Frequency up + CTR down
    rule_A = (d_freq >= FREQ_UP_PCT) and (d_ctr <= -CTR_DOWN_PCT)
    if rule_A:
        reasons.append(
            f"Frequency ↑ {d_freq:.0f}% vs 7d (from {b_freq:.2f} to {freq:.2f}) while CTR ↓ {abs(d_ctr):.0f}% (from {b_ctr:.2f}% to {ctr:.2f}%). → Audience saturation."
        )
        actions += [
            "Rotate new creative (fresh hook/thumbnail within first 3s).",
            "Broaden/exclude recent engagers to reset Frequency.",
            "Shift spend to best placements (Reels/Stories) for lower CPM."
        ]

    # B) Efficiency drop: ROAS down
    rule_B = (d_roas <= -ROAS_DOWN_PCT)
    if rule_B:
        reasons.append(
            f"ROAS ↓ {abs(d_roas):.0f}% vs 7d (from {b_roas:.2f} to {roas:.2f})."
        )
        actions += [
            "Swap to proven winner creative (highest ROAS past 14d).",
            "Test price/offer/urgency in headline or on landing page.",
            "Reduce spend cap or tighten audience until creative refresh."
        ]

    # C) Auction pressure: CPM up + CTR down
    rule_C = (d_cpm >= CPM_UP_PCT) and (d_ctr <= -CTR_DOWN_PCT)
    if rule_C:
        reasons.append(
            f"CPM ↑ {d_cpm:.0f}% vs 7d (from ${b_cpm:.2f} to ${cpm:.2f}) while CTR ↓ {abs(d_ctr):.0f}%. → Auction pressure/creative mismatch."
        )
        actions += [
            "Try square/vertical cut for mobile-first placements.",
            "Refine audience (exclude recent purchasers, add broad LAL).",
            "Test value-led hook addressing objections in first 3s."
        ]

    # D) Click cost up; results down
    rule_D = (d_cpc >= CPM_UP_PCT) and (d_results <= -RESULTS_DOWN_PCT)
    if rule_D:
        reasons.append(
            f"CPC ↑ {d_cpc:.0f}% and Results ↓ {abs(d_results):.0f}% vs 7d.")
        actions += [
            "Improve thumb/first frame to lift CTR.",
            "Move budget to higher-CTR placement (e.g., Reels).",
            "Add stronger CTA on-video and in primary text."
        ]

    fatigued = any([rule_A, rule_B, rule_C, rule_D])

    # If nothing tripped but CTR is sliding for 2+ days, you could add a softer early warning rule later.
    if not fatigued:
        actions = []
        reasons = []

    return fatigued, reasons, actions
