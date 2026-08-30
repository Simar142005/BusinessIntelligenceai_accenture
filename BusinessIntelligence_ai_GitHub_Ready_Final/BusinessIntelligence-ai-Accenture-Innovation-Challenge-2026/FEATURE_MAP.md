# BusinessIntelligence.ai — Feature Map

Maps prototype features to the official Accenture Innovation Challenge 2026 Round 2 requirements
(Problem Track 3, "Minimum Prototype Expectations") and to the Round 2 objective list.

| Challenge requirement | Where it's demonstrated |
|---|---|
| 3–5 connected KPIs across 2–3 sources with different grains/cadences | `semantic_contract.json` + `engine.py::region_daily` — 5 KPIs (Gross Margin, Revenue, Volume, Inventory, Discount Rate) across `sales_finance.csv` (product-day, hourly refresh), `operations.csv` (region-day, 30-min refresh), `business_events.csv` (event grain, daily/as-entered) |
| Lightweight KPI/semantic contract (definitions, calculations, drivers, thresholds, lineage, access) | `semantic_contract.json`, rendered live in the "Governance & semantic contract" section of `app.py` |
| Detect and prioritise material KPI movements | `engine.py::materiality`, `region_daily`, `anomaly_window` — governed thresholds, not arbitrary flags |
| Identify and rank explanatory drivers using appropriate analytical methods | `engine.py::driver_analysis` — magnitude, correlation with GM, temporal alignment, supporting-evidence count, relative contribution % |
| At least two personas with different narratives/actions | Commercial Manager vs Data Analyst — different `persona_text()` output and gated source-row drill-down |
| One multi-factor KPI movement with known/simulated drivers | Default "Material KPI movement & investigation" scenario, region = West |
| One low-confidence scenario that requests clarification or abstains | "Low-confidence / competing hypotheses" — **computed live** from `engine.find_ambiguous_region`, not a fixed table |
| One sparse-history / newly launched KPI scenario | "Sparse-history / new KPI" — clearly labelled **Simulated scenario**, confidence from `engine.sparse_history_confidence` (real formula) |
| One role-based security/entitlement scenario | Commercial Manager (aggregated) vs Data Analyst (+ source-row drill-down), enforced in `app.py` and declared in `semantic_contract.json::security` |
| Evidence showing source freshness, analytical method, contribution, confidence, lineage | Evidence ledger + "Analytical trace" panel in `app.py`, per-hypothesis, including an explicit **Limitation** field |
| Clear breakdown of LLM vs non-LLM processing | `nl_router.py` docstring + boundary caption in the UI + "LLM never computes KPI truth" note repeated in-app |
| Runtime telemetry: latency, model calls, token usage, estimated cost | "Runtime telemetry" section — **measured** with `time.perf_counter()`, not hard-coded |
| Recommend practical actions (driver → lever → action → impact → owner → confidence → monitoring) | "Recommended next action" cards + monitoring-plan callout in `app.py`, sourced from `engine.action_for` |
| Mechanism to learn from analyst/business-user feedback | Approve/Reject/Unresolved + 👍/👎 vote + free text → `feedback_log.csv` via `engine.log_feedback`; feedback-history panel with a usefulness-rate indicator |
| Operate within realistic cost/latency/security constraints, and demonstrably work without an API key | Deterministic-first design; LLM key is optional, session-only, and every call path has a tested fallback |

## Core investigation engine (engine.py)
- Governed KPI baselines (28-day rolling median) and materiality thresholds for all 5 KPIs.
- Multi-factor driver scoring using only observable signals: magnitude, GM correlation, temporal alignment,
  supporting unstructured evidence count, and a normalized relative contribution %.
- Product-level impact / concentration analysis.
- Ranked hypotheses — explicitly labelled support scores, never causal probabilities.

## Evidence & trust
- Evidence ledger: claim, source, source type, date, freshness, lineage.
- Analytical trace: method, signal, correlation, temporal alignment, contribution %, segment impact,
  confidence, causal status, and an explicit limitation sentence per driver.
- Evidence lineage flow: a generated (not hard-coded) "how did we reach this conclusion" trace.
- Causal-status glossary distinguishing observation / correlation / supported hypothesis / plausible
  contributor / causal evidence / insufficient evidence / conflicting evidence—abstain.

## Decision support
- Recommended action: driver → lever → action → expected impact → owner.
- Monitoring plan.
- Human Approve / Reject / Unresolved workflow plus a quick usefulness vote.
- Feedback capture and a simple, honestly-labelled usefulness-rate indicator (not claimed to be ML).

## Safety scenarios
- Low-confidence / competing hypotheses: computed live from real driver scores; abstains when no driver
  clearly dominates; names the specific missing evidence needed next.
- Sparse-history KPI: clearly labelled simulated scenario; no fabricated seasonal baseline; lower confidence
  via a real formula; peer-comparison guidance.

## Enterprise readiness
- Commercial Manager vs Data Analyst views with genuinely different depth, not just a title change.
- Role-based aggregation vs. detailed source-row access.
- Semantic KPI contract, rendered live.
- Data-source health table.
- Measured runtime telemetry: latency, LLM calls, tokens, estimated cost, feedback count.

## LLM boundary
Quantitative KPI calculations and driver signals are 100% deterministic (`engine.py`). `nl_router.py` adds an
optional LLM step purely for wording an already-computed result, with the prompt explicitly instructing the
model not to alter any number, and a tested fallback path when no key is provided or the call fails.

## Known limitations (stated explicitly, not hidden)
- All data is synthetic; regional dynamics are illustrative, not real enterprise data.
- The "low-confidence" scenario picks the most ambiguous *region* in the existing dataset rather than
  simulating a bespoke ambiguous case — this keeps the demo honest but means which region it lands on can
  change if the underlying data changes.
- The sparse-history scenario is explicitly simulated (labelled in-app) because the bundled dataset has full
  history for every region.
- The LLM narrative path (when enabled) depends on network access to the Anthropic API; it is optional and
  the prototype's core investigation flow does not require it.
