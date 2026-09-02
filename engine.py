"""BusinessIntelligence.ai deterministic analytics engine.

All quantitative truth is computed with pandas/numpy. Optional document retrieval
only supplies evidence text; the LLM is never used to calculate KPI values.
"""
import json
import re
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

CAUSAL_STATUS_GLOSSARY = {
    "Observation": "Measured fact about what happened; no claim about why.",
    "Correlation": "Two series moved together. Correlation does not imply causation.",
    "Supported hypothesis": "Magnitude, timing and evidence are consistent with a driver, but this is not causal proof.",
    "Plausible contributor": "Some signals align, but evidence is not strong enough for a single explanation.",
    "Causal evidence": "Not claimed by this prototype because the data are observational.",
    "Insufficient evidence": "Too little independent evidence or history to support a driver.",
    "Conflicting evidence — abstain": "Competing drivers or sources conflict, so the system refuses to over-claim.",
}

KPI_LIST = ["Gross Margin", "Revenue", "Volume", "Inventory", "Discount Rate"]
REGIONS = ["West", "North", "South", "East"]

# Driver definitions are KPI-specific. This fixes the previous issue where every
# investigation was effectively a Gross Margin investigation.
KPI_DRIVERS = {
    "Gross Margin": ["Increased discounting", "Supplier disruption", "Volume change", "Inventory pressure", "Product mix"],
    "Revenue": ["Volume change", "Pricing / discounting", "Inventory availability", "Product mix", "Supplier disruption"],
    "Volume": ["Pricing / discounting", "Inventory availability", "Customer demand", "Supplier disruption", "Product mix"],
    "Inventory": ["Supplier disruption", "Demand / volume", "Replenishment pressure", "Product mix", "Delivery performance"],
    "Discount Rate": ["Promotion / pricing policy", "Customer demand", "Regional mix", "Competition / market event", "Product mix"],
}

DRIVER_KEYWORDS = {
    "Supplier disruption": ["supplier", "delay", "disruption", "delivery", "shipment", "vendor"],
    "Increased discounting": ["discount", "promotion", "markdown", "pricing", "offer"],
    "Pricing / discounting": ["discount", "promotion", "price", "pricing", "markdown", "offer"],
    "Inventory availability": ["inventory", "stock", "stockout", "stock-out", "availability", "warehouse"],
    "Inventory pressure": ["inventory", "stock", "stockout", "warehouse"],
    "Volume change": ["volume", "units", "demand", "sales", "orders"],
    "Customer demand": ["demand", "customer", "orders", "traffic", "feedback"],
    "Demand / volume": ["demand", "volume", "units", "orders"],
    "Replenishment pressure": ["replenishment", "restock", "inventory", "warehouse"],
    "Product mix": ["mix", "product", "category", "segment"],
    "Supplier disruption": ["supplier", "delay", "disruption", "delivery", "shipment", "vendor"],
    "Delivery performance": ["delivery", "delay", "shipment", "supplier"],
    "Promotion / pricing policy": ["promotion", "discount", "pricing", "campaign", "markdown"],
    "Regional mix": ["region", "west", "north", "south", "east", "mix"],
    "Competition / market event": ["competition", "competitor", "market", "news", "campaign"],
}

LEVER_MAP = {
    "Supplier disruption": ("Supplier allocation", "Review affected supplier allocation and activate a backup supplier where available.", "Protect supply continuity and margin.", "Regional Supply Manager"),
    "Increased discounting": ("Discount policy", "Review discount depth and restrict discounts on low-margin products.", "Reduce margin leakage.", "Regional Commercial Manager"),
    "Pricing / discounting": ("Pricing and promotion", "Review discount depth and price realization by product segment.", "Recover revenue quality and margin.", "Regional Commercial Manager"),
    "Volume change": ("Demand / channel plan", "Validate demand weakness by segment before changing the commercial plan.", "Avoid overreacting to noisy demand.", "Regional Commercial Manager"),
    "Inventory availability": ("Replenishment", "Prioritize replenishment for affected product segments and monitor stock-outs.", "Reduce lost sales.", "Regional Supply Manager"),
    "Inventory pressure": ("Replenishment", "Prioritize replenishment and rebalance stock across affected segments.", "Reduce lost sales and excess-stock risk.", "Regional Supply Manager"),
    "Customer demand": ("Demand generation", "Validate demand weakness using customer and channel signals before changing supply.", "Align inventory and commercial spend with demand.", "Regional Commercial Manager"),
    "Demand / volume": ("Demand plan", "Reforecast demand using recent volume and peer behavior.", "Reduce inventory mismatch.", "Demand Planning Lead"),
    "Replenishment pressure": ("Replenishment", "Review reorder points and supplier lead times for affected regions.", "Reduce stock imbalance.", "Regional Supply Manager"),
    "Product mix": ("Portfolio mix", "Inspect product-level contribution and shift focus toward healthier mix segments.", "Improve KPI quality through mix management.", "Commercial Manager"),
    "Delivery performance": ("Delivery operations", "Review delayed lanes and prioritize high-impact deliveries.", "Reduce service and stock disruption.", "Operations Manager"),
    "Promotion / pricing policy": ("Pricing policy", "Review promotion depth, duration and affected products.", "Improve price realization.", "Commercial Manager"),
    "Regional mix": ("Regional portfolio", "Compare regional mix and rebalance commercial focus.", "Reduce mix-driven volatility.", "Commercial Manager"),
    "Competition / market event": ("Market response", "Validate the external event and adjust the commercial response if material.", "Limit market-driven downside.", "Commercial Manager"),
}

LIMITATION_MAP = {
    "Supplier disruption": "Observational evidence only; no controlled supplier intervention is available.",
    "Increased discounting": "Discount and demand effects are not experimentally separated.",
    "Pricing / discounting": "Price realization and demand response can move together; causal isolation is unavailable.",
    "Volume change": "Volume can be an outcome of another root cause, so it is not automatically causal.",
    "Inventory availability": "Region-level inventory is less precise than SKU-level stock-out data.",
    "Inventory pressure": "Region-level inventory is less precise than SKU-level stock-out data.",
    "Customer demand": "Customer demand is partly inferred from observed business signals.",
    "Demand / volume": "Demand is observational and may be affected by price, supply or mix.",
    "Replenishment pressure": "Reorder policy and lead-time constraints are not fully observed.",
    "Product mix": "Mix effects are descriptive unless a controlled comparison is available.",
    "Delivery performance": "Delivery delay may itself be caused by upstream demand or supply conditions.",
    "Promotion / pricing policy": "External competitive response is not fully observed.",
    "Regional mix": "Regional mix is descriptive and does not establish a causal mechanism.",
    "Competition / market event": "External event attribution requires independent validation.",
}

KPI_META = {
    "Gross Margin": {"value_col": "gm_pct", "baseline_col": "gm_baseline", "delta_col": "gm_dev_pp", "unit": "pp", "threshold": 1.5},
    "Revenue": {"value_col": "revenue", "baseline_col": "rev_baseline", "delta_col": "rev_dev_pct", "unit": "%", "threshold": 3.0},
    "Volume": {"value_col": "volume", "baseline_col": "vol_baseline", "delta_col": "vol_dev_pct", "unit": "%", "threshold": 5.0},
    "Inventory": {"value_col": "inventory_units", "baseline_col": "inv_baseline", "delta_col": "inv_dev_pct", "unit": "%", "threshold": 5.0},
    "Discount Rate": {"value_col": "avg_discount_rate", "baseline_col": "disc_baseline", "delta_col": "disc_dev_pct", "unit": "%", "threshold": 5.0},
}


def load_data(base: Path):
    sales = pd.read_csv(base / "sales_finance.csv", parse_dates=["date"])
    ops = pd.read_csv(base / "operations.csv", parse_dates=["date"])
    events = pd.read_csv(base / "business_events.csv", parse_dates=["date"])
    semantic = json.loads((base / "semantic_contract.json").read_text(encoding="utf-8"))
    return sales, ops, events, semantic


def pct(a, b):
    if b == 0 or pd.isna(b):
        return 0.0
    return float((a / b - 1) * 100)


def safe_corr(a, b):
    a, b = pd.Series(a).astype(float), pd.Series(b).astype(float)
    m = a.notna() & b.notna()
    if m.sum() < 5 or a[m].std() == 0 or b[m].std() == 0:
        return 0.0
    return float(np.corrcoef(a[m], b[m])[0, 1])


def _rolling_median(s):
    return s.rolling(28, min_periods=14).median()


def region_daily(sales, ops, region):
    d = ops[ops.region == region].sort_values("date").copy()
    d["gm_pct"] = d["gross_margin"] * 100
    d["gm_baseline"] = _rolling_median(d["gm_pct"])
    d["gm_dev_pp"] = d["gm_pct"] - d["gm_baseline"]
    d["rev_baseline"] = _rolling_median(d["revenue"])
    d["rev_dev_pct"] = (d["revenue"] / d["rev_baseline"] - 1) * 100
    d["inv_baseline"] = _rolling_median(d["inventory_units"])
    d["inv_dev_pct"] = (d["inventory_units"] / d["inv_baseline"] - 1) * 100
    d["disc_baseline"] = _rolling_median(d["avg_discount_rate"])
    d["disc_dev_pct"] = (d["avg_discount_rate"] / d["disc_baseline"] - 1) * 100
    vol = sales[sales.region == region].groupby("date")["volume"].sum()
    d["volume"] = d["date"].map(vol)
    d["vol_baseline"] = _rolling_median(d["volume"])
    d["vol_dev_pct"] = (d["volume"] / d["vol_baseline"] - 1) * 100
    return d


def materiality(d):
    x = d.iloc[-1]
    return {k: bool(abs(float(x[v["delta_col"]])) >= v["threshold"]) for k, v in KPI_META.items()}


def materiality_details(d, kpi):
    x = d.iloc[-1]
    meta = KPI_META[kpi]
    delta = float(x[meta["delta_col"]]) if pd.notna(x[meta["delta_col"]]) else 0.0
    hist = d[meta["value_col"]].dropna().tail(60)
    z = 0.0
    if len(hist) >= 10 and hist.std() > 0:
        z = abs((float(x[meta["value_col"]]) - float(hist.mean())) / float(hist.std()))
    business_impact = None
    if kpi == "Revenue":
        business_impact = abs(float(x["revenue"]) - float(x["rev_baseline"])) if pd.notna(x["rev_baseline"]) else 0
    elif kpi == "Gross Margin":
        business_impact = abs(float(x["revenue"]) * (float(x["gm_pct"]) - float(x["gm_baseline"])) / 100) if pd.notna(x["gm_baseline"]) else 0
    elif kpi == "Volume":
        business_impact = abs(float(x["volume"]) - float(x["vol_baseline"])) if pd.notna(x["vol_baseline"]) else 0
    elif kpi == "Inventory":
        business_impact = abs(float(x["inventory_units"]) - float(x["inv_baseline"])) if pd.notna(x["inv_baseline"]) else 0
    else:
        business_impact = abs(delta)
    threshold_hit = abs(delta) >= meta["threshold"]
    significant = threshold_hit and (z >= 1.0 or abs(delta) >= meta["threshold"] * 1.5)
    return {"delta": delta, "z_score": round(z, 2), "business_impact": float(business_impact or 0), "material": bool(significant)}


def anomaly_window(d, kpi):
    if d.empty:
        return None, None
    meta = KPI_META[kpi]
    delta = d[meta["delta_col"]]
    threshold = meta["threshold"]
    mask = delta.abs() >= threshold
    if not bool(mask.iloc[-1]):
        return d.iloc[-1].date, d.iloc[-1].date
    dates = d.loc[mask, "date"]
    return dates.iloc[0], dates.iloc[-1]


def _daily_driver_frame(sales, ops, region):
    d = region_daily(sales, ops, region).copy()
    d["supplier_delay_days"] = d["avg_supplier_delay_days"]
    d["discount_rate"] = d["avg_discount_rate"]
    d["inventory_units"] = d["inventory_units"]
    d["volume"] = d["volume"]
    d["unit_price"] = sales[sales.region == region].groupby("date").apply(
        lambda x: np.average(x["unit_price"], weights=np.maximum(x["volume"], 0.001))
    ).reindex(d.date).values
    d["product_mix_index"] = sales[sales.region == region].groupby("date").apply(
        lambda x: float(x.groupby("product")["revenue"].sum().div(x["revenue"].sum()).pow(2).sum())
    ).reindex(d.date).values
    return d


def _target_series(d, kpi):
    return d[KPI_META[kpi]["value_col"]]


def _driver_series(d, driver):
    mapping = {
        "Supplier disruption": "supplier_delay_days", "Increased discounting": "discount_rate", "Pricing / discounting": "discount_rate",
        "Inventory availability": "inventory_units", "Inventory pressure": "inventory_units", "Volume change": "volume",
        "Customer demand": "volume", "Demand / volume": "volume", "Replenishment pressure": "inventory_units",
        "Product mix": "product_mix_index", "Delivery performance": "supplier_delay_days", "Promotion / pricing policy": "discount_rate",
        "Regional mix": "product_mix_index", "Competition / market event": None,
    }
    return mapping.get(driver)


def _driver_signal(d, driver):
    col = _driver_series(d, driver)
    if col is None:
        return 0.0
    s = d[col].dropna()
    if len(s) < 28:
        return 0.0
    return pct(s.tail(14).mean(), s.iloc[-42:-14].mean())


def _event_rows(events, region, driver):
    keys = DRIVER_KEYWORDS.get(driver, [driver.lower()])
    mask = events.region.eq(region)
    text = (events.get("event_type", "").fillna("") + " " + events.get("text", "").fillna("")).str.lower()
    kwmask = False
    for k in keys:
        kwmask = kwmask | text.str.contains(re.escape(k.lower()), regex=True)
    return events[mask & kwmask].sort_values("date", ascending=False).copy()


def load_documents(base: Path):
    """Load TXT/MD/PDF/DOCX files from data/documents or documents."""
    roots = [base / "data" / "documents", base / "documents"]
    files = []
    for root in roots:
        if root.exists():
            files.extend([p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in {".txt", ".md", ".pdf", ".docx"}])
    docs = []
    for p in sorted(set(files)):
        text = ""
        try:
            if p.suffix.lower() in {".txt", ".md"}:
                text = p.read_text(encoding="utf-8", errors="ignore")
            elif p.suffix.lower() == ".pdf":
                from pypdf import PdfReader
                text = "\n".join(page.extract_text() or "" for page in PdfReader(str(p)).pages)
            elif p.suffix.lower() == ".docx":
                from docx import Document
                text = "\n".join(par.text for par in Document(str(p)).paragraphs)
        except Exception:
            continue
        if text.strip():
            docs.append({"file": p.name, "path": str(p), "text": text.strip(), "modified": pd.Timestamp(p.stat().st_mtime, unit="s")})
    return docs


def retrieve_document_evidence(base: Path, region: str, driver: str, query: str = ""):
    docs = load_documents(base)
    if not docs:
        return []
    terms = set(DRIVER_KEYWORDS.get(driver, []) + [region.lower()] + [t for t in re.findall(r"[a-zA-Z]{4,}", query.lower())])
    results = []
    for doc in docs:
        low = doc["text"].lower()
        hits = sum(1 for t in terms if t in low)
        if hits == 0:
            continue
        # Return the most relevant paragraph/line rather than the whole file.
        lines = [x.strip() for x in doc["text"].splitlines() if x.strip()]
        best = max(lines, key=lambda line: sum(1 for t in terms if t in line.lower()), default=doc["text"][:500])
        results.append({"source": doc["file"], "text": best[:700], "date": doc["modified"], "retrieval_score": min(100, hits * 12.5), "type": "unstructured"})
    return sorted(results, key=lambda x: x["retrieval_score"], reverse=True)[:5]


def evidence(events, region, driver, base: Optional[Path] = None, query: str = ""):
    rows = []
    for _, r in _event_rows(events, region, driver).iterrows():
        rows.append({"source": r.get("source", "business_events.csv"), "text": r.get("text", ""), "date": r["date"],
                     "event_type": r.get("event_type", "Business event"), "retrieval_score": 60.0, "type": "structured-event"})
    if base is not None:
        rows.extend(retrieve_document_evidence(base, region, driver, query))
    if not rows:
        return pd.DataFrame(columns=["source", "text", "date", "event_type", "retrieval_score", "type"])
    return pd.DataFrame(rows).sort_values(["retrieval_score", "date"], ascending=[False, False]).reset_index(drop=True)


def first_change_date(series_df, col, threshold_pct=8):
    if series_df.empty or col not in series_df.columns:
        return None
    s = series_df.sort_values("date").copy()
    base = s[col].rolling(28, min_periods=14).median()
    dev = (s[col] / base.replace(0, np.nan) - 1).abs() * 100
    idx = np.where(dev >= threshold_pct)[0]
    return s.iloc[int(idx[0])].date if len(idx) else None


def driver_analysis(sales, ops, events, region, kpi="Gross Margin", base: Optional[Path] = None, query=""):
    if kpi not in KPI_DRIVERS:
        kpi = "Gross Margin"
    d = _daily_driver_frame(sales, ops, region)
    target = _target_series(d, kpi)
    anomaly_start, _ = anomaly_window(d, kpi)
    rows = []
    for driver in KPI_DRIVERS[kpi]:
        signal = _driver_signal(d, driver)
        driver_col = _driver_series(d, driver)
        corr = safe_corr(d[driver_col], target) if driver_col else 0.0
        ev = evidence(events, region, driver, base, query)
        magnitude = min(100.0, abs(signal) * 2.5)
        relationship = min(100.0, abs(corr) * 100)
        change_date = first_change_date(d, driver_col) if driver_col else None
        alignment = 0.0
        if change_date is not None and anomaly_start is not None:
            distance = abs((pd.Timestamp(change_date) - pd.Timestamp(anomaly_start)).days)
            alignment = max(0.0, 100.0 - distance * 15.0)
        evidence_score = min(100.0, len(ev) * 20.0)
        # Driver score is prioritization support, not a causal probability.
        score = 0.30 * magnitude + 0.25 * relationship + 0.20 * alignment + 0.25 * evidence_score
        rows.append({
            "Driver": driver, "Support score": round(score, 1), "Signal": round(signal, 2),
            "Correlation": round(corr, 4), "Correlation with KPI": round(corr, 4),
            "Evidence records": int(len(ev)), "Change date": change_date,
            "Temporal alignment": round(alignment, 1), "KPI": kpi,
        })
    rows.sort(key=lambda r: r["Support score"], reverse=True)
    total = sum(r["Support score"] for r in rows) or 1
    for r in rows:
        r["Contribution %"] = round(r["Support score"] / total * 100, 1)
    return rows


def product_impact(sales, region, kpi="Gross Margin"):
    maxd = sales.date.max()
    recent = sales[(sales.region == region) & (sales.date >= maxd - pd.Timedelta(days=13))]
    prior = sales[(sales.region == region) & (sales.date < maxd - pd.Timedelta(days=13)) & (sales.date >= maxd - pd.Timedelta(days=41))]
    r = recent.groupby("product").agg(revenue=("revenue", "sum"), gm=("gross_margin", "mean"), volume=("volume", "sum"), discount=("discount_rate", "mean"))
    p = prior.groupby("product").agg(revenue=("revenue", "sum"), gm=("gross_margin", "mean"), volume=("volume", "sum"), discount=("discount_rate", "mean"))
    out = r.join(p, lsuffix="_recent", rsuffix="_prior", how="inner")
    for col in ["revenue", "volume"]:
        out[f"{col}_change_pct"] = np.where(out[f"{col}_prior"] != 0, (out[f"{col}_recent"] / out[f"{col}_prior"] - 1) * 100, 0)
    out["gm_change_pp"] = (out.gm_recent - out.gm_prior) * 100
    out["discount_change_pp"] = (out.discount_recent - out.discount_prior) * 100
    out["impact_weight"] = out.revenue_recent / max(out.revenue_recent.sum(), 1) * 100
    sort_col = {"Revenue": "revenue_change_pct", "Volume": "volume_change_pct", "Inventory": "volume_change_pct", "Discount Rate": "discount_change_pp", "Gross Margin": "gm_change_pp"}.get(kpi, "gm_change_pp")
    return out.sort_values(sort_col)


def causal_status(conf, ev_count, temporal, corr, contradictory=False):
    """
    Conservative decision status.

    Important:
    - Correlation is treated as supporting evidence, NOT causation.
    - Strong correlation cannot compensate for zero temporal alignment.
    - A single evidence record is not enough for a strong hypothesis.
    """

    if contradictory:
        return "Conflicting evidence — abstain"

    # No independent evidence -> do not make a driver claim.
    if ev_count == 0:
        return "Insufficient evidence"

    # Very low confidence -> insufficient evidence.
    if conf < 45:
        return "Insufficient evidence"

    # Strong correlation without timing/evidence should remain cautious.
    if temporal < 20 and ev_count < 2:
        return "Insufficient evidence"

    # Weak temporal alignment means we should not call it supported.
    if temporal < 40:
        return "Plausible contributor"

    # One evidence record is still weak even if other signals look good.
    if ev_count < 2:
        return "Plausible contributor"

    # Reasonable confidence is required for a supported hypothesis.
    if conf < 70:
        return "Plausible contributor"

    # Strong hypothesis requires reasonable timing and evidence.
    if temporal >= 40 and ev_count >= 2 and conf >= 70:
        return "Supported hypothesis"

    return "Plausible contributor"


def feedback_history(base):
    p = base / "feedback_log.csv"
    if not p.exists():
        return pd.DataFrame(columns=["timestamp", "persona", "region", "scenario", "kpi", "driver", "decision", "vote", "feedback"])
    try:
        return pd.read_csv(p)
    except Exception:
        return pd.DataFrame()


def feedback_reliability(base, driver):
    hist = feedback_history(base)
    if hist.empty or "vote" not in hist.columns:
        return 0.5
    h = hist[(hist.driver == driver) & hist.vote.isin(["Correct", "Incorrect"])]
    if h.empty:
        return 0.5
    return float((h.vote == "Correct").mean())


def confidence_for(row, ev_count, base: Optional[Path] = None):
    """
    Conservative confidence calculation.

    Confidence combines:
    - driver support score
    - evidence quantity
    - temporal alignment
    - correlation strength

    Correlation alone cannot produce high confidence.
    """

    support = float(row.get("Support score", 0))
    temporal = float(row.get("Temporal alignment", 0))
    correlation = abs(float(row.get("Correlation with KPI", 0)))

    # Base support from deterministic driver ranking.
    conf = 25.0 + 0.40 * support

    # Evidence quantity.
    if ev_count == 0:
        evidence_factor = 0.55
    elif ev_count == 1:
        evidence_factor = 0.75
    elif ev_count == 2:
        evidence_factor = 0.90
    else:
        evidence_factor = 1.00

    conf *= evidence_factor

    # Temporal alignment is important because a driver should occur
    # around the KPI movement rather than merely correlate historically.
    temporal_factor = 0.55 + 0.45 * (temporal / 100.0)
    conf *= temporal_factor

    # Correlation provides supporting information but is deliberately
    # capped so that correlation cannot dominate the decision.
    correlation_factor = 0.80 + 0.20 * min(correlation, 1.0)
    conf *= correlation_factor

    # Strong correlation with poor timing should be penalized heavily.
    if correlation >= 0.80 and temporal < 20:
        conf *= 0.70

    # One evidence record cannot justify very high confidence.
    if ev_count < 2:
        conf = min(conf, 64.0)

    # No temporal alignment means we should remain conservative.
    if temporal == 0:
        conf = min(conf, 58.0)

    conf = float(np.clip(conf, 25, 90))

    # Optional historical human-feedback adjustment.
    if base is not None:
        rel = feedback_reliability(base, row["Driver"])

        if rel != 0.5:
            conf = float(
                np.clip(
                    conf * (0.92 + 0.16 * rel),
                    25,
                    90
                )
            )

    return round(conf, 1)


def action_for(driver):
    return LEVER_MAP.get(driver, ("Investigation", "Collect additional evidence before taking corrective action.", "Reduce decision risk.", "Business Owner"))


def limitation_for(driver):
    return LIMITATION_MAP.get(driver, "Additional independent evidence is required to establish causality.")


def log_feedback(base, payload):
    p = base / "feedback_log.csv"
    pd.DataFrame([payload]).to_csv(p, mode="a", header=not p.exists(), index=False)


def reconcile_sources(sales, ops, region):
    s = sales[sales.region == region].groupby("date").agg(revenue=("revenue", "sum"), cost=("cost", "sum"), gross_margin=("gross_margin", "mean"))
    o = ops[ops.region == region].set_index("date")[['revenue', 'cost', 'gross_margin']]
    m = s.join(o, lsuffix="_sales", rsuffix="_ops", how="inner")
    rows = []
    for metric in ["revenue", "cost", "gross_margin"]:
        a, b = m[f"{metric}_sales"], m[f"{metric}_ops"]
        diff = ((a - b).abs() / a.replace(0, np.nan) * 100).replace([np.inf, -np.inf], np.nan).fillna(0)
        avg = float(diff.mean()) if len(diff) else 0
        status = "Reconciled" if avg <= 1.5 else "Conflict"
        rows.append({"Metric": metric.replace("gross_margin", "gross margin").title(), "Sales source": float(a.iloc[-1]), "Operations source": float(b.iloc[-1]), "Avg difference %": round(avg, 2), "Status": status})
    return pd.DataFrame(rows)


def source_health(base, semantic):
    rows = []
    now = pd.Timestamp.now()
    files = {p.name: p for p in base.glob("*.csv")}
    for name, meta in semantic.get("sources", {}).items():
        p = files.get(name)
        age_min = None
        if p and p.exists():
            age_min = max(0, (now - pd.Timestamp(p.stat().st_mtime, unit="s")).total_seconds() / 60)
        status = "Healthy" if age_min is None or age_min <= 24 * 60 else "Aging"
        rows.append({"Source": name, "Type": meta.get("type", "structured"), "Grain": meta.get("grain", ""), "Refresh": meta.get("refresh", ""), "Observed file age": f"{age_min:.0f} min" if age_min is not None else "n/a", "Declared freshness": meta.get("freshness", ""), "Status": status})
    return pd.DataFrame(rows)


def sparse_peer_analysis(sales, region, kpi, days_available=21, days_required=28):
    meta = KPI_META[kpi]
    # Use last available observation as the simulated new KPI value and compare it with peer regions.
    if kpi == "Gross Margin":
        reg = sales.groupby("region")["gross_margin"].mean() * 100
    elif kpi == "Revenue":
        reg = sales.groupby("region")["revenue"].sum()
    elif kpi == "Volume":
        reg = sales.groupby("region")["volume"].sum()
    elif kpi == "Inventory":
        reg = sales.groupby("region")["inventory_units"].mean()
    else:
        reg = sales.groupby("region")["discount_rate"].mean() * 100
    own = float(reg.get(region, np.nan))
    peers = reg.drop(labels=[region], errors="ignore")
    peer_median = float(peers.median()) if len(peers) else np.nan
    gap = pct(own, peer_median) if peer_median not in [0, np.nan] else 0
    return {"days_available": days_available, "days_required": days_required, "peer_median": peer_median, "own_value": own, "peer_gap_pct": gap, "confidence": sparse_history_confidence(days_available, days_required)}


def sparse_history_confidence(days_available, days_required=28):
    if days_available >= days_required:
        return 80.0
    ratio = max(0, min(1, days_available / days_required))
    return round(25 + ratio * 40, 1)


def find_ambiguous_region(sales, ops, events, regions, kpi="Gross Margin", base: Optional[Path] = None):
    best = None
    for region in regions:
        rows = driver_analysis(sales, ops, events, region, kpi, base)
        top, second = rows[0]["Support score"], rows[1]["Support score"]
        gap = top - second
        key = gap + max(0, top - 50)
        if best is None or key < best[0]:
            best = (key, region, rows)
    return best[1], best[2]
