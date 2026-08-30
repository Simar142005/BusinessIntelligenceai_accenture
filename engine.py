"""
engine.py — BusinessIntelligence.ai deterministic analytics layer.

Design principle (per challenge requirements): the LLM is never the source of
quantitative truth. Every number in this module is produced by pandas/numpy
arithmetic on the underlying CSVs. Narrative wording lives in nl_router.py and
app.py; this module only returns numbers, labels and structured records.
"""
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Glossary — the challenge explicitly requires the system to clearly
# distinguish these categories rather than blur them together.
# ---------------------------------------------------------------------------
CAUSAL_STATUS_GLOSSARY = {
    "Observation": "A measured fact about what happened (e.g. 'Gross Margin fell 2.5pp'). No claim about why.",
    "Correlation": "Two series moved together in time. Does not imply either caused the other.",
    "Supported hypothesis": "Magnitude, direction, timing and independent (unstructured) evidence are all "
                             "consistent with this driver. Still not proof of causation.",
    "Plausible contributor": "Some but not all signals line up. Reasonable to investigate further, not to act on alone.",
    "Causal evidence": "Would require a controlled comparison (e.g. an intervention or natural experiment). "
                        "This prototype only has observational data, so it never claims this status.",
    "Insufficient evidence": "Too few independent signals (or too little data) to support any specific driver.",
    "Conflicting evidence — abstain": "Multiple drivers have comparable support and/or evidence disagrees. "
                                       "The system explicitly declines to name a single cause.",
}

DRIVERS = ["Supplier disruption", "Increased discounting", "Inventory pressure", "Volume change"]

CHANGE_COL = {
    "Supplier disruption": "supplier_delay_days",
    "Increased discounting": "discount_rate",
    "Inventory pressure": "inventory_units",
    "Volume change": "volume",
}

EVENT_MAP = {
    "Supplier disruption": ["Supplier disruption", "Inventory risk", "Supplier update"],
    "Increased discounting": ["Promotion"],
    "Inventory pressure": ["Inventory risk", "Supplier disruption", "Customer feedback"],
    "Volume change": ["Customer feedback"],
}

LEVER_MAP = {
    "Supplier disruption": (
        "Supplier allocation",
        "Review affected supplier allocation and activate a backup supplier where available.",
        "Protect margin in affected products.",
        "Regional Supply Manager",
    ),
    "Increased discounting": (
        "Discount policy",
        "Review discount depth and restrict discounts on low-margin products.",
        "Reduce margin leakage.",
        "Regional Commercial Manager",
    ),
    "Inventory pressure": (
        "Replenishment",
        "Prioritize replenishment for affected product segments.",
        "Reduce lost sales and margin pressure.",
        "Regional Supply Manager",
    ),
    "Volume change": (
        "Demand / channel plan",
        "Validate demand weakness by segment before changing the commercial plan.",
        "Avoid overreacting to noisy demand.",
        "Regional Commercial Manager",
    ),
}

LIMITATION_MAP = {
    "Supplier disruption": "Observational evidence only; no controlled intervention (e.g. a supplier swap test) "
                            "is available to establish causal proof.",
    "Increased discounting": "Discount timing correlates with the margin move, but demand response to the "
                              "discount was not isolated from other concurrent changes.",
    "Inventory pressure": "Inventory deviation is measured at region grain; SKU-level stock-out data would "
                           "sharpen this further.",
    "Volume change": "Volume swings can be a symptom of the same root cause as other drivers rather than an "
                      "independent cause; treat with extra caution.",
}


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
def load_data(base: Path):
    sales = pd.read_csv(base / "sales_finance.csv", parse_dates=["date"])
    ops = pd.read_csv(base / "operations.csv", parse_dates=["date"])
    events = pd.read_csv(base / "business_events.csv", parse_dates=["date"])
    semantic = json.loads((base / "semantic_contract.json").read_text())
    return sales, ops, events, semantic


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def pct(a, b):
    return 0.0 if b == 0 or pd.isna(b) else (a / b - 1) * 100


def safe_corr(a, b):
    a = pd.Series(a).astype(float)
    b = pd.Series(b).astype(float)
    m = a.notna() & b.notna()
    if m.sum() < 5 or a[m].std() == 0 or b[m].std() == 0:
        return 0.0
    return float(np.corrcoef(a[m], b[m])[0, 1])


# ---------------------------------------------------------------------------
# KPI baseline / anomaly detection (now including Volume as a governed KPI)
# ---------------------------------------------------------------------------
def region_daily(sales: pd.DataFrame, ops: pd.DataFrame, region: str) -> pd.DataFrame:
    d = ops[ops.region == region].sort_values("date").copy()
    d["gm_pct"] = d["gross_margin"] * 100
    d["gm_baseline"] = d["gm_pct"].rolling(28, min_periods=14).median()
    d["gm_dev_pp"] = d["gm_pct"] - d["gm_baseline"]

    d["rev_baseline"] = d["revenue"].rolling(28, min_periods=14).median()
    d["rev_dev_pct"] = (d["revenue"] / d["rev_baseline"] - 1) * 100

    d["inv_baseline"] = d["inventory_units"].rolling(28, min_periods=14).median()
    d["inv_dev_pct"] = (d["inventory_units"] / d["inv_baseline"] - 1) * 100

    d["disc_baseline"] = d["avg_discount_rate"].rolling(28, min_periods=14).median()
    d["disc_dev_pct"] = (d["avg_discount_rate"] / d["disc_baseline"] - 1) * 100

    # Volume is grained at region-product-day in sales_finance.csv; aggregate to
    # region-day so it can sit alongside the other operations-grain KPIs.
    vol = sales[sales.region == region].groupby("date")["volume"].sum()
    d["volume"] = d["date"].map(vol)
    d["vol_baseline"] = d["volume"].rolling(28, min_periods=14).median()
    d["vol_dev_pct"] = (d["volume"] / d["vol_baseline"] - 1) * 100
    return d


def materiality(d: pd.DataFrame) -> dict:
    x = d.iloc[-1]
    return {
        "Gross Margin": abs(x.gm_dev_pp) >= 1.5,
        "Revenue": abs(x.rev_dev_pct) >= 3,
        "Volume": abs(x.vol_dev_pct) >= 5,
        "Inventory": abs(x.inv_dev_pct) >= 5,
        "Discount Rate": abs(x.disc_dev_pct) >= 5,
    }


def anomaly_window(d: pd.DataFrame):
    if d.empty:
        return None, None
    latest = d.iloc[-1]
    threshold = 1.5
    mask = d.gm_dev_pp <= -threshold
    if not bool(mask.iloc[-1]):
        return latest.date, latest.date
    dates = d.loc[mask, "date"]
    return dates.iloc[0], latest.date


def first_change_date(series_df: pd.DataFrame, col: str, threshold_pct: float = 8):
    """First recent date a driver deviates materially from its own 28d rolling median."""
    if series_df.empty or col not in series_df.columns:
        return None
    s = series_df.sort_values("date").copy()
    base = s[col].rolling(28, min_periods=14).median()
    dev = (s[col] / base.replace(0, np.nan) - 1).abs() * 100
    idx = np.where(dev >= threshold_pct)[0]
    return s.iloc[int(idx[0])].date if len(idx) else None


# ---------------------------------------------------------------------------
# Driver analysis — transparent multi-signal scoring (NOT a causal probability)
# ---------------------------------------------------------------------------
def driver_analysis(sales: pd.DataFrame, ops: pd.DataFrame, events: pd.DataFrame, region: str):
    maxd = sales.date.max()
    recent_start = maxd - pd.Timedelta(days=13)
    prior_start = maxd - pd.Timedelta(days=41)
    recent = sales[(sales.region == region) & (sales.date >= recent_start)].copy()
    prior = sales[(sales.region == region) & (sales.date < recent_start) & (sales.date >= prior_start)].copy()

    daily = ops[ops.region == region].sort_values("date").copy()
    daily["gm_pct"] = daily.gross_margin * 100
    d_full = region_daily(sales, ops, region)
    anomaly_start, _ = anomaly_window(d_full)

    changes = {
        "supplier_delay_days": pct(recent.supplier_delay_days.mean(), prior.supplier_delay_days.mean()),
        "discount_rate": pct(recent.discount_rate.mean(), prior.discount_rate.mean()),
        "inventory_units": pct(recent.inventory_units.mean(), prior.inventory_units.mean()),
        "volume": pct(recent.volume.mean(), prior.volume.mean()),
    }

    daily["delay"] = daily["avg_supplier_delay_days"]
    daily["discount"] = daily["avg_discount_rate"]
    daily["inventory"] = daily["inventory_units"]
    daily["volume"] = sales[sales.region == region].groupby("date")["volume"].sum().reindex(daily.date).values

    corr = {
        "Supplier disruption": safe_corr(daily.delay, daily.gm_pct),
        "Increased discounting": safe_corr(daily.discount, daily.gm_pct),
        "Inventory pressure": safe_corr(daily.inventory, daily.gm_pct),
        "Volume change": safe_corr(daily.volume, daily.gm_pct),
    }
    signal_map = {
        "Supplier disruption": changes["supplier_delay_days"],
        "Increased discounting": changes["discount_rate"],
        "Inventory pressure": changes["inventory_units"],
        "Volume change": changes["volume"],
    }

    rows = []
    for driver in DRIVERS:
        signal = signal_map[driver]
        magnitude = min(100, abs(signal) * 2.5)
        rel = min(100, abs(corr[driver]) * 100)
        ev = events[(events.region == region) & events.event_type.isin(EVENT_MAP[driver])]
        evidence_score = min(100, len(ev) * 25)
        col = CHANGE_COL[driver]
        renamed = daily.rename(columns={
            "avg_supplier_delay_days": "supplier_delay_days",
            "avg_discount_rate": "discount_rate",
        })
        change_date = first_change_date(renamed, col) if col in renamed.columns else None
        alignment = 0
        if change_date is not None and anomaly_start is not None:
            distance = abs((pd.Timestamp(change_date) - pd.Timestamp(anomaly_start)).days)
            alignment = max(0, 100 - distance * 15)
        score = 0.35 * magnitude + 0.25 * rel + 0.20 * alignment + 0.20 * evidence_score
        rows.append({
            "Driver": driver, "Support score": round(score, 1), "Signal": signal,
            "Correlation with GM": corr[driver], "Evidence records": len(ev),
            "Change date": change_date, "Temporal alignment": alignment,
        })

    rows = sorted(rows, key=lambda r: r["Support score"], reverse=True)
    total = sum(r["Support score"] for r in rows) or 1.0
    for r in rows:
        r["Contribution %"] = round(r["Support score"] / total * 100, 1)
    return rows


def evidence(events: pd.DataFrame, region: str, driver: str) -> pd.DataFrame:
    return events[(events.region == region) & events.event_type.isin(EVENT_MAP[driver])].sort_values(
        "date", ascending=False
    )


def product_impact(sales: pd.DataFrame, region: str) -> pd.DataFrame:
    maxd = sales.date.max()
    recent = sales[(sales.region == region) & (sales.date >= maxd - pd.Timedelta(days=13))]
    prior = sales[(sales.region == region) & (sales.date < maxd - pd.Timedelta(days=13)) &
                  (sales.date >= maxd - pd.Timedelta(days=41))]
    r = recent.groupby("product").agg(revenue=("revenue", "sum"), gm=("gross_margin", "mean"), volume=("volume", "sum"))
    p = prior.groupby("product").agg(revenue=("revenue", "sum"), gm=("gross_margin", "mean"), volume=("volume", "sum"))
    out = r.join(p, lsuffix="_recent", rsuffix="_prior", how="inner")
    out["gm_change_pp"] = (out.gm_recent - out.gm_prior) * 100
    out["revenue_change_pct"] = (out.revenue_recent / out.revenue_prior - 1) * 100
    out["volume_change_pct"] = (out.volume_recent / out.volume_prior - 1) * 100
    out["impact_weight"] = out.revenue_recent / out.revenue_recent.sum() * 100
    return out.sort_values("gm_change_pp")


def causal_status(conf: float, ev_count: int, temporal: float, corr: float, contradictory: bool = False) -> str:
    if contradictory:
        return "Conflicting evidence — abstain"
    if ev_count == 0 or conf < 45:
        return "Insufficient evidence"
    if conf < 65:
        return "Plausible contributor"
    if temporal < 40 and abs(corr) < 0.35:
        return "Plausible contributor"
    return "Supported hypothesis"


def confidence_for(row: dict, ev_count: int) -> float:
    return float(np.clip(30 + 0.55 * row["Support score"] + min(15, ev_count * 5), 25, 92))


def action_for(driver: str):
    return LEVER_MAP[driver]


def limitation_for(driver: str) -> str:
    return LIMITATION_MAP[driver]


def log_feedback(base: Path, payload: dict):
    p = base / "feedback_log.csv"
    row = pd.DataFrame([payload])
    if p.exists():
        row.to_csv(p, mode="a", header=False, index=False)
    else:
        row.to_csv(p, index=False)


def feedback_history(base: Path) -> pd.DataFrame:
    p = base / "feedback_log.csv"
    if not p.exists():
        return pd.DataFrame(columns=["timestamp", "persona", "region", "scenario", "driver", "decision",
                                      "vote", "feedback"])
    return pd.read_csv(p)


# ---------------------------------------------------------------------------
# Ambiguity scenario — computed from real driver scores, not hard-coded.
# A region is "ambiguous" if the top driver does not clearly dominate.
# ---------------------------------------------------------------------------
def find_ambiguous_region(sales, ops, events, regions):
    """Return the region whose top drivers are closest together (real, computed)."""
    best_region, best_gap, best_rows = None, None, None
    for region in regions:
        rows = driver_analysis(sales, ops, events, region)
        top = rows[0]["Support score"]
        second = rows[1]["Support score"] if len(rows) > 1 else 0
        gap = top - second
        # Prefer a region that is both low-confidence (low top score) and close-scored.
        rank_key = gap + max(0, top - 50)
        if best_gap is None or rank_key < best_gap:
            best_gap, best_region, best_rows = rank_key, region, rows
    return best_region, best_rows


def sparse_history_confidence(days_available: int, days_required: int = 28) -> float:
    """Deterministic confidence penalty for sparse history. Simulated scenario —
    the underlying dataset has full history for all regions, so this formula
    (not a fabricated number) is what would drive the UI if a genuinely new
    KPI/region with `days_available` observations existed."""
    if days_available >= days_required:
        return 80.0
    ratio = days_available / days_required
    return round(25 + ratio * 40, 1)  # floor 25, scales up toward 65 as history fills in
