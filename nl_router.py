"""
nl_router.py — natural-language front door for BusinessIntelligence.ai.

IMPORTANT BOUNDARY (per challenge requirement 14):
The LLM is NEVER used to calculate KPI values, anomaly scores, contribution
values, or confidence numbers. It only (a) helps interpret free-text intent
into a structured {kpi, region} query, and (b) optionally rewords an
already-computed, deterministic result into prose. If no API key is
available, both steps fall back to fully deterministic logic and the
prototype still works end-to-end.
"""
import re
import time

import engine

KPI_ALIASES = {
    "gross margin": "Gross Margin", "margin": "Gross Margin", "gm": "Gross Margin",
    "revenue": "Revenue", "sales": "Revenue",
    "volume": "Volume", "units": "Volume",
    "inventory": "Inventory", "stock": "Inventory",
    "discount": "Discount Rate", "discounting": "Discount Rate", "discount rate": "Discount Rate",
}
REGION_ALIASES = {"west": "West", "north": "North", "south": "South", "east": "East"}


def parse_query(text: str, default_region: str):
    """Deterministic keyword parser. No LLM required for this step."""
    t = (text or "").lower()
    kpi = "Gross Margin"
    for k, v in KPI_ALIASES.items():
        if k in t:
            kpi = v
            break
    region = default_region
    for k, v in REGION_ALIASES.items():
        if re.search(rf"\b{k}\b", t):
            region = v
            break
    return {"kpi": kpi, "region": region}


def deterministic_narrative(kpi: str, region: str, persona: str, drivers: list, top_driver: dict,
                             status: str, confidence: float) -> str:
    lead = drivers[0]["Driver"] if drivers else "no clear driver"
    if persona == "Commercial Manager":
        return (f"For {region}, {kpi} movement is most associated with **{lead}** "
                f"({status.lower()}, confidence {confidence:.0f}%). "
                f"This is a decision aid based on deterministic scoring — not proof of causation.")
    signals = ", ".join(f"{r['Driver']}={r['Support score']:.0f}" for r in drivers[:3])
    return (f"Query resolved to KPI='{kpi}', region='{region}'. Ranked support scores: {signals}. "
            f"Leading hypothesis '{lead}' has causal status **{status}** at confidence {confidence:.0f}%. "
            f"Scores are deterministic (magnitude + correlation + temporal alignment + evidence count).")


def llm_narrative(api_key: str, kpi: str, region: str, persona: str, drivers: list, status: str,
                   confidence: float, deterministic_fallback: str):
    """Optional real LLM call. The prompt hands the model ALREADY-COMPUTED numbers
    and asks only for wording — it is not permitted to invent figures."""
    try:
        import anthropic
    except ImportError:
        return deterministic_fallback, {"llm_used": False, "tokens": 0, "reason": "anthropic package not installed"}

    if not api_key:
        return deterministic_fallback, {"llm_used": False, "tokens": 0, "reason": "no API key provided"}

    facts = "\n".join(
        f"- {r['Driver']}: support score {r['Support score']:.1f}/100, "
        f"signal {r['Signal']:+.1f}%, correlation {r['Correlation with GM']:+.2f}, "
        f"{r['Evidence records']} evidence record(s)"
        for r in drivers[:4]
    )
    prompt = (
        f"You are the narrative layer of an enterprise BI tool. Do NOT invent, adjust, or estimate any "
        f"numbers — only restate the facts below in plain, {persona}-appropriate business language, in 3-4 "
        f"sentences. Never claim proven causation; use 'evidence supports' framing.\n\n"
        f"KPI: {kpi}\nRegion: {region}\nCausal status: {status}\nConfidence: {confidence:.0f}%\n"
        f"Driver signals (already computed, do not alter):\n{facts}\n"
    )
    try:
        client = anthropic.Anthropic(api_key=api_key)
        t0 = time.perf_counter()
        resp = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=220,
            messages=[{"role": "user", "content": prompt}],
        )
        latency_ms = (time.perf_counter() - t0) * 1000
        text = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text").strip()
        usage = getattr(resp, "usage", None)
        tokens = (getattr(usage, "input_tokens", 0) or 0) + (getattr(usage, "output_tokens", 0) or 0)
        # Rough Sonnet-class blended estimate; illustrative only, not a billing figure.
        est_cost = tokens / 1_000_000 * 6.0
        return text or deterministic_fallback, {
            "llm_used": True, "tokens": tokens, "latency_ms": latency_ms, "est_cost": est_cost,
        }
    except Exception as e:  # noqa: BLE001 — any API/network failure falls back safely
        return deterministic_fallback, {"llm_used": False, "tokens": 0, "reason": f"LLM call failed: {e}"}


def route(query_text: str, sales, ops, events, persona: str, default_region: str, api_key: str = ""):
    """Full NL pipeline: parse -> deterministic analytics -> (optional) LLM wording."""
    t0 = time.perf_counter()
    parsed = parse_query(query_text, default_region)
    region = parsed["region"]
    drivers = engine.driver_analysis(sales, ops, events, region)
    top = drivers[0]
    ev = engine.evidence(events, region, top["Driver"])
    confidence = engine.confidence_for(top, len(ev))
    status = engine.causal_status(confidence, len(ev), top["Temporal alignment"], top["Correlation with GM"])
    deterministic_text = deterministic_narrative(parsed["kpi"], region, persona, drivers, top, status, confidence)

    telemetry = {"llm_used": False, "tokens": 0, "est_cost": 0.0}
    narrative = deterministic_text
    if api_key:
        narrative, llm_meta = llm_narrative(api_key, parsed["kpi"], region, persona, drivers, status,
                                             confidence, deterministic_text)
        telemetry.update(llm_meta)

    telemetry["analytical_latency_ms"] = (time.perf_counter() - t0) * 1000
    return {
        "parsed": parsed, "region": region, "drivers": drivers, "top_driver": top,
        "status": status, "confidence": confidence, "narrative": narrative, "telemetry": telemetry,
    }
