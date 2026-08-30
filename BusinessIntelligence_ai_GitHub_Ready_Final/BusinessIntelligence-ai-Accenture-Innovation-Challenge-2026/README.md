# BusinessIntelligence.ai

### Accenture Innovation Challenge 2026 · Round 2 · Problem Track 3

**BusinessIntelligence.ai** is an AI-assisted business intelligence prototype that turns KPI movement into an understandable, evidence-backed decision workflow.

> **Detect → Explain → Trust → Act**

## What the prototype does

Business users often know that a KPI changed, but still need to understand **why**, **how confident the explanation is**, and **what to do next**.

This prototype provides:

- KPI monitoring and material-movement detection
- Driver ranking and investigation
- Evidence and source visibility
- Confidence and uncertainty handling
- Natural-language investigation
- Practical action recommendations
- Persona-oriented views
- CSV/XLSX data upload
- Governance and lineage information
- Low-confidence / abstention scenarios
- Sparse-history safety handling
- Human feedback support
- Deterministic analytics with an optional LLM narrative layer

## Key KPIs

The prototype demonstrates business intelligence using:

- Gross Margin
- Revenue
- Volume
- Inventory
- Discount Rate

## Data sources

The prototype can combine information from:

1. **Sales / Finance**
2. **Operations**
3. **Business Events**

The included sample data is for demonstration. Replace it with your own data through the upload workflow.

## How it works

```text
Business Data
     │
     ▼
Validation & Data Mapping
     │
     ▼
KPI Calculation
     │
     ▼
Material Movement Detection
     │
     ▼
Driver Ranking
     │
     ├── Evidence
     ├── Confidence
     └── Lineage
     │
     ▼
Recommended Action
     │
     ▼
Human Review & Feedback
```

### AI boundary

The quantitative KPI calculations and analytical signals are handled by the application's analytics layer.

If an LLM is enabled, it is used for supported language/narrative tasks rather than being treated as the source of quantitative KPI truth.

## Run locally

### 1. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd BusinessIntelligence-ai-Accenture-Innovation-Challenge-2026
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Start the application

```bash
streamlit run app.py
```

The application will open at the Streamlit local address shown in the terminal.

## Run on Google Colab

Upload the repository/project ZIP to Colab and run:

```python
!pip install -q -r requirements.txt
!streamlit run app.py --server.port 8501 --server.address 0.0.0.0 > /content/streamlit.log 2>&1 &
```

If a public preview is needed, expose port `8501` with a tunnel such as Cloudflare Tunnel.

## Data upload

The application supports business data upload through the UI.

Recommended source roles:

### Sales / Finance

Typical fields include:

```text
date
region
product
volume
unit_price
discount_rate
inventory_units
supplier_delay_days
revenue
cost
gross_margin
```

### Operations

Typical fields include:

```text
date
region
avg_supplier_delay_days
inventory_units
avg_discount_rate
revenue
cost
gross_margin
```

### Business Events

Typical fields include:

```text
date
region
event_type
text
source
```

The exact fields supported by the current implementation are defined by the application's existing validation/mapping logic.

## Demo flow

For a short competition demonstration:

1. Open the application.
2. Launch the demo or upload business data.
3. Show the KPI overview.
4. Select an important KPI movement.
5. Show the ranked drivers.
6. Open the supporting evidence and confidence.
7. Show the recommended action.
8. Ask a natural-language question such as:
   **"Why did Gross Margin fall in West?"**
9. Demonstrate the low-confidence / competing-hypotheses scenario.
10. Finish with the Governance / Trust view.

## Project structure

```text
app.py                  # Streamlit user interface
engine.py               # Analytics / KPI intelligence
nl_router.py            # Natural-language routing
semantic_contract.json  # KPI and governance definitions
requirements.txt        # Python dependencies
```

## Safety and limitations

- Included business data is illustrative/demo data.
- Driver scores should be interpreted as prioritisation signals, not proof of causation.
- Observational evidence does not automatically establish causal relationships.
- The application can lower confidence or abstain when evidence is insufficient.
- Production deployment would require enterprise authentication, secure secrets, access enforcement, source integrations and operational monitoring.

## Challenge alignment

The prototype is designed around the Round 2 goals of:

- Detecting and prioritising material KPI movements
- Reconciling heterogeneous business data
- Ranking explanatory drivers
- Communicating uncertainty
- Providing evidence and lineage
- Supporting different business personas
- Recommending practical actions
- Capturing human feedback
- Keeping quantitative truth separate from optional AI narrative generation

## Team

**Accenture Innovation Challenge 2026 — Round 2 Prototype**


## Additional project notes

# BusinessIntelligence.ai — Round 2 Prototype

A prototype for the Accenture Innovation Challenge 2026, Problem Track 3: **BusinessIntelligence.ai**.

## Core demo
**KPI anomaly → ranked drivers → evidence lineage → confidence/causal status → recommended action → human decision → feedback loop**

## Main scenario
Synthetic retail data for a **Regional Commercial Manager** investigating Gross Margin movement across four regions (West, North, South, East).

## Project structure
```
app.py          # Streamlit UI + orchestration only
engine.py       # deterministic quantitative-truth layer (anomaly, drivers, evidence, confidence)
nl_router.py    # natural-language query parsing + optional LLM narrative, with deterministic fallback
sales_finance.csv, operations.csv, business_events.csv   # structured + unstructured data sources
semantic_contract.json   # governed KPI definitions, thresholds, lineage, access rules
feedback_log.csv         # created at runtime by the human-in-the-loop workflow
```
Analytics and UI are deliberately separated (`engine.py` vs `app.py`) so the quantitative logic can be
tested and audited independently of the interface.

## Included features
- **5 connected, governed KPIs**: Gross Margin, Revenue, Volume, Inventory, Discount Rate.
- **3 heterogeneous sources**: sales/finance (structured, product grain), operations (structured, region grain),
  business-event notes (unstructured).
- 28-day rolling KPI baselines with explicit materiality thresholds from the semantic contract.
- Multi-factor, transparent driver scoring (magnitude, GM correlation, temporal alignment, supporting
  unstructured evidence, relative contribution %) — explicitly labelled as support scores, not causal
  probabilities.
- **Evidence ledger** with claim, source, source type, date, freshness, method, contribution, temporal
  alignment, segment impact, confidence, causal status and an explicit **limitation** per hypothesis.
- **Evidence lineage** — a step-by-step "how did we reach this conclusion" trace, generated from the same
  numbers shown elsewhere on the page (not hard-coded copy).
- **Causal-status glossary** distinguishing observation / correlation / supported hypothesis / causal
  evidence / uncertainty / insufficient evidence.
- Product-level impact analysis.
- **Natural-language investigation box** ("Ask BusinessIntelligence.ai") — deterministic keyword/KPI/region
  parsing routes into the same analytical engine; wording is deterministic by default, or optionally
  generated by a live Anthropic API call (session-only key) that narrates already-computed numbers and
  never calculates KPI truth itself. Falls back to the deterministic path automatically if no key is
  supplied or the call fails.
- **Low-confidence / competing-hypotheses scenario** — computed live: the app finds the region where the
  top two drivers are genuinely closest in score and abstains from naming a single cause, using real
  numbers (not a fixed demo table).
- **Sparse-history / new-KPI scenario** — clearly labelled "Simulated scenario" (the bundled dataset has
  full history for every region) and uses a real deterministic confidence-penalty formula rather than a
  placeholder number.
- Commercial Manager and Data Analyst personas with genuinely different narrative depth and detail access.
- Role-based aggregation vs. detailed source-row view.
- KPI-focus, region, persona, time-range and scenario selectors, plus a "last updated" timestamp.
- Semantic contract viewer and data-source health table.
- Human **Approve / Reject / Unresolved** decision, a quick 👍/👎 usefulness vote, free-text feedback, and
  a feedback-history panel with a simple usefulness-rate learning indicator.
- **Measured runtime telemetry**: analytical latency is timed with `time.perf_counter()` around the actual
  driver-analysis call (not hard-coded), plus LLM call count / token usage / estimated cost when the
  optional LLM path is used.

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Run in Google Colab
Upload the ZIP, extract it, `cd` into the folder, install requirements, then run:
```bash
streamlit run app.py --server.port 8501 > /content/streamlit.log 2>&1 &
```
Expose port 8501 with a temporary tunnel if needed. See `BusinessIntelligence_ai_Colab_Starter.ipynb`.

## Optional: live LLM narrative
In the sidebar, expand **"Optional: enable live LLM narrative"** and paste an Anthropic API key
(session-only — it is never written to disk). Install the optional dependency first:
```bash
pip install anthropic
```
Without a key, or if the package isn't installed, the app automatically uses its deterministic narrative
templates and still demonstrates the full investigation flow.

## Important design principle
The prototype deliberately separates quantitative truth from narrative generation. `engine.py` computes all
KPI movement, driver scores, confidence, and causal status deterministically with pandas/numpy. `nl_router.py`
may optionally call an LLM, but only to reword already-computed facts — it is never allowed to invent or
adjust a number, and the code path is designed to fail safely back to deterministic wording.

All data is synthetic and created for demonstration.
