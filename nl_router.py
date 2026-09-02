"""Natural-language router for BusinessIntelligence.ai.

Intent parsing is deterministic. The optional LLM only rewrites already-computed
facts and is never allowed to calculate quantitative truth.
"""
import re
import time
import engine

KPI_ALIASES = {
    "gross margin": "Gross Margin", "margin": "Gross Margin", "gm": "Gross Margin",
    "revenue": "Revenue", "sales": "Revenue", "turnover": "Revenue",
    "volume": "Volume", "units": "Volume", "unit sales": "Volume",
    "inventory": "Inventory", "stock": "Inventory",
    "discount rate": "Discount Rate", "discount": "Discount Rate", "discounting": "Discount Rate",
}
REGION_ALIASES = {"west": "West", "north": "North", "south": "South", "east": "East"}


def parse_query(text: str, default_region: str):
    t = (text or "").lower()
    kpi = "Gross Margin"
    # Longest aliases first so "discount rate" wins over "discount".
    for key in sorted(KPI_ALIASES, key=len, reverse=True):
        if re.search(rf"\b{re.escape(key)}\b", t):
            kpi = KPI_ALIASES[key]
            break
    region = default_region
    for key, value in REGION_ALIASES.items():
        if re.search(rf"\b{key}\b", t):
            region = value
            break
    return {"kpi": kpi, "region": region}


def deterministic_narrative(kpi, region, persona, drivers, top_driver, status, confidence):
    lead = top_driver["Driver"] if top_driver else "no clear driver"
    if status == "Conflicting evidence — abstain":
        return (f"For {region}, the {kpi} movement does not have one sufficiently dominant explanation. "
                f"The engine is abstaining rather than over-claiming causation. Confidence is {confidence:.0f}%. "
                f"Review the ranked alternatives and collect the missing evidence before acting.")
    if persona == "Commercial Manager":
        return (f"For {region}, {kpi} is most strongly associated with **{lead}** ({status.lower()}, confidence {confidence:.0f}%). "
                f"The ranking combines deterministic magnitude, KPI relationship, timing and evidence retrieval. "
                f"This is a decision aid, not proof of causality.")
    signals = ", ".join(f"{r['Driver']}={r['Support score']:.0f}" for r in drivers[:4])
    return (f"Query resolved to KPI='{kpi}', region='{region}'. Ranked support scores: {signals}. "
            f"Leading hypothesis '{lead}' has status **{status}** at confidence {confidence:.0f}%. "
            f"All quantitative values come from deterministic analytics; retrieved documents provide contextual evidence.")


def llm_narrative(api_key, kpi, region, persona, drivers, status, confidence, deterministic_fallback):
    if not api_key:
        return deterministic_fallback, {"llm_used": False, "tokens": 0, "est_cost": 0.0, "reason": "no API key provided"}
    try:
        import anthropic
    except ImportError:
        return deterministic_fallback, {"llm_used": False, "tokens": 0, "est_cost": 0.0, "reason": "anthropic package not installed"}
    facts = "\n".join(
        f"- {r['Driver']}: support={r['Support score']:.1f}/100, signal={r['Signal']:+.1f}%, "
        f"KPI correlation={r['Correlation with KPI']:+.2f}, evidence={r['Evidence records']}"
        for r in drivers[:5]
    )
    prompt = ("You are only the narrative layer of a BI tool. Do not calculate, invent, or change any number. "
              "Do not claim causation. Restate the supplied deterministic facts in 3-4 concise business sentences.\n\n"
              f"KPI={kpi}\nRegion={region}\nPersona={persona}\nStatus={status}\nConfidence={confidence:.0f}%\n{facts}")
    try:
        t0 = time.perf_counter()
        client = anthropic.Anthropic(api_key=api_key)
        resp = client.messages.create(model="claude-sonnet-4-6", max_tokens=220, messages=[{"role": "user", "content": prompt}])
        latency = (time.perf_counter() - t0) * 1000
        text = "".join(getattr(b, "text", "") for b in resp.content if getattr(b, "type", "") == "text").strip()
        usage = getattr(resp, "usage", None)
        tokens = (getattr(usage, "input_tokens", 0) or 0) + (getattr(usage, "output_tokens", 0) or 0)
        return text or deterministic_fallback, {"llm_used": True, "tokens": tokens, "latency_ms": latency, "est_cost": tokens / 1_000_000 * 6.0}
    except Exception as e:
        return deterministic_fallback, {"llm_used": False, "tokens": 0, "est_cost": 0.0, "reason": f"LLM call failed: {e}"}


def route(query_text, sales, ops, events, persona, default_region, api_key="", base=None):
    t0 = time.perf_counter()
    parsed = parse_query(query_text, default_region)
    kpi, region = parsed["kpi"], parsed["region"]
    drivers = engine.driver_analysis(sales, ops, events, region, kpi, base, query_text)
    top = drivers[0]
    ev = engine.evidence(events, region, top["Driver"], base, query_text)
    confidence = engine.confidence_for(top, len(ev), base)
    contradictory = len(drivers) > 1 and (drivers[0]["Support score"] - drivers[1]["Support score"] < 7) and len(ev) > 0
    status = engine.causal_status(confidence, len(ev), top["Temporal alignment"], top["Correlation with KPI"], contradictory)
    fallback = deterministic_narrative(kpi, region, persona, drivers, top, status, confidence)
    narrative, llm_meta = llm_narrative(api_key, kpi, region, persona, drivers, status, confidence, fallback)
    telemetry = {"llm_used": False, "tokens": 0, "est_cost": 0.0}
    telemetry.update(llm_meta)
    telemetry["analytical_latency_ms"] = (time.perf_counter() - t0) * 1000
    return {"parsed": parsed, "region": region, "drivers": drivers, "top_driver": top, "status": status, "confidence": confidence, "narrative": narrative, "telemetry": telemetry}
