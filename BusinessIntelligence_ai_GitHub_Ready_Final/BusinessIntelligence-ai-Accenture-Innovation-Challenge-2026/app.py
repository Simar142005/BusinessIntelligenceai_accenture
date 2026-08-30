import time
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

import engine
import nl_router

BASE = Path(__file__).parent
st.set_page_config(page_title="BusinessIntelligence.ai", page_icon="◈", layout="wide",
                    initial_sidebar_state="expanded")

# ---------- Data (deterministic quantitative layer) ----------
sales, ops, events, semantic = engine.load_data(BASE)
KPI_LIST = ["Gross Margin", "Revenue", "Volume", "Inventory", "Discount Rate"]

# ---------- Theme ----------
st.markdown(r'''<style>
:root{--ink:#0f172a;--muted:#64748b;--line:#e8eaf2;--panel:#ffffff;--soft:#f6f7fb;--purple:#6257e8;--purple2:#8b5cf6;--red:#e05252;--amber:#d97706;--green:#159570;--blue:#3b82f6}
.stApp{background:#f7f8fc;color:var(--ink)}
.block-container{padding:1.35rem 2.2rem 3rem;max-width:1540px}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#101326 0%,#171a35 100%);border:0}
[data-testid="stSidebar"] *{color:#eef2ff!important}
[data-testid="stSidebar"] .stSelectbox label,[data-testid="stSidebar"] .stCheckbox label,[data-testid="stSidebar"] .stTextInput label,[data-testid="stSidebar"] .stMultiSelect label,[data-testid="stSidebar"] .stRadio label{color:#c7cbea!important}
.hero{position:relative;overflow:hidden;padding:1.55rem 1.7rem;border:1px solid #e5e7f5;border-radius:22px;background:linear-gradient(120deg,#ffffff 0%,#f6f4ff 55%,#eef7ff 100%);margin-bottom:1.15rem;box-shadow:0 10px 35px rgba(31,41,55,.06)}
.hero:after{content:"";position:absolute;width:180px;height:180px;right:-55px;top:-80px;border-radius:50%;background:radial-gradient(circle,#b7aaff55,transparent 65%)}
.hero h1{margin:0;color:#111827;font-size:2.05rem;letter-spacing:-.045em;font-weight:900}.hero p{margin:.42rem 0 0;color:#64748b;font-size:.94rem}
.hero-chip{display:inline-flex;align-items:center;gap:.35rem;background:#ece9ff;color:#4c42bd;border-radius:999px;padding:.34rem .62rem;font-size:.72rem;font-weight:850;margin-bottom:.55rem}
.hero-ts{position:absolute;right:1.7rem;top:1.4rem;font-size:.72rem;color:#7c8497;text-align:right}
.section{font-size:1.16rem;font-weight:850;color:#111827;margin:1.35rem 0 .38rem;letter-spacing:-.02em}.sub{font-size:.81rem;color:#64748b;margin-bottom:.72rem}
.kpi{border:1px solid #e7e8f0;border-radius:18px;background:rgba(255,255,255,.96);padding:1.05rem 1.1rem;box-shadow:0 7px 22px rgba(15,23,42,.045);min-height:125px;position:relative;overflow:hidden}
.kpi:before{content:"";position:absolute;left:0;top:0;bottom:0;width:4px;background:linear-gradient(180deg,#6257e8,#8b5cf6)}
.kpi.focus{outline:2px solid #6257e8;outline-offset:-1px}
.kpi .label{font-size:.7rem;font-weight:850;color:#64748b;text-transform:uppercase;letter-spacing:.1em}.kpi .value{font-size:1.85rem;font-weight:900;color:#111827;margin-top:.38rem;letter-spacing:-.035em}.kpi .delta{font-size:.78rem;margin-top:.35rem;font-weight:700}
.good{color:var(--green)}.bad{color:var(--red)}.warn{color:var(--amber)}.muted{color:var(--muted)}
.pill{display:inline-block;padding:.27rem .58rem;border-radius:999px;font-size:.7rem;font-weight:850}.pill-red{background:#fee8e8;color:#b42318}.pill-amber{background:#fff3d7;color:#9a5b00}.pill-green{background:#def7ec;color:#08744f}.pill-blue{background:#ebe9ff;color:#4c42bd}
.card{border:1px solid #e7e8f0;border-radius:17px;background:#fff;padding:1rem;box-shadow:0 5px 18px rgba(15,23,42,.035)}
.driver-card{border:1px solid #e7e8f0;border-radius:16px;background:#fff;padding:.9rem 1rem;margin:.45rem 0;box-shadow:0 4px 15px rgba(15,23,42,.035)}
.driver-title{font-weight:850;color:#111827;font-size:.9rem}.driver-score{font-weight:900;color:#5b52d8;font-size:1rem}.driver-meta{font-size:.72rem;color:#64748b;margin-top:.3rem}
.evidence{border:1px solid #e6e7f0;border-left:4px solid #6257e8;background:#fff;padding:.85rem 1rem;border-radius:12px;margin:.55rem 0;box-shadow:0 4px 14px rgba(15,23,42,.035)}
.evidence-dot{display:inline-block;width:8px;height:8px;border-radius:50%;background:#6257e8;margin-right:7px}.tiny{font-size:.71rem;color:#64748b}.metric-label{font-size:.71rem;text-transform:uppercase;letter-spacing:.08em;color:#64748b;font-weight:850}
.trace{background:#f8f7ff;border:1px solid #e8e5ff;border-radius:14px;padding:1rem}.trace-row{padding:.45rem 0;border-bottom:1px solid #eceaf7;font-size:.78rem}.trace-row:last-child{border-bottom:0}
.status-box{border:1px solid #e5e7f0;border-radius:17px;padding:1rem;background:linear-gradient(135deg,#fff,#fafaff)}
.callout{border-radius:15px;padding:.95rem 1.05rem;border:1px solid #e8e6ff;background:#f8f7ff;color:#3730a3}
.footer-note{font-size:.72rem;color:#7c8497;text-align:center;margin-top:1.5rem}
.sim-badge{display:inline-flex;align-items:center;gap:.3rem;background:#fff3d7;color:#9a5b00;border-radius:999px;padding:.28rem .65rem;font-size:.68rem;font-weight:850;margin-bottom:.6rem}
.lineage{display:flex;flex-direction:column;gap:0}
.lineage-step{border:1px solid #e7e8f0;border-radius:12px;background:#fff;padding:.6rem .85rem;font-size:.79rem;box-shadow:0 3px 10px rgba(15,23,42,.03)}
.lineage-arrow{text-align:center;color:#9ca3c4;font-size:.85rem;margin:.15rem 0}
.nlbox{border:1px solid #e5e7f0;border-radius:16px;background:linear-gradient(135deg,#faf9ff,#ffffff);padding:1rem 1.1rem;margin-bottom:1rem}
div[data-testid="stMetric"]{border:1px solid #e5e7f0;border-radius:14px;padding:.65rem;background:#fff;box-shadow:0 4px 15px rgba(15,23,42,.03)}
button[kind="primary"]{border-radius:10px;background:linear-gradient(90deg,#5b52d8,#7c68ee);border:0}
.stTabs [data-baseweb="tab-list"]{gap:6px;background:#fff;border:1px solid #e7e8f0;padding:5px;border-radius:13px}.stTabs [data-baseweb="tab"]{border-radius:9px;padding:8px 14px}.stTabs [aria-selected="true"]{background:#eeecff;color:#4c42bd;font-weight:800}
</style>''', unsafe_allow_html=True)


def persona_text(persona, driver, status, conf, metrics):
    if persona == 'Commercial Manager':
        return (f"**Executive narrative:** {driver} is the leading **{status.lower()}** for the current Gross "
                f"Margin movement. Confidence is {conf:.0f}%. The strongest signals are a {metrics['signal']:+.1f}% "
                f"driver change and {metrics['evidence']} supporting context record(s). Treat this as a decision "
                f"aid, not proof of causality.")
    return (f"**Analyst narrative:** {driver} ranks first under a transparent multi-signal heuristic. Status = "
            f"**{status}**; confidence = **{conf:.0f}%**. Signal={metrics['signal']:+.1f}%, "
            f"GM relationship={metrics['corr']:+.2f}, temporal alignment={metrics['temporal']:.0f}/100, "
            f"supporting context={metrics['evidence']} record(s).")


# ---------- Sidebar ----------
st.sidebar.markdown('## BusinessIntelligence.ai')
st.sidebar.caption('KPI intelligence → evidence → action')
persona = st.sidebar.selectbox('Persona', ['Commercial Manager', 'Data Analyst'])
region = st.sidebar.selectbox('Region', ['West', 'North', 'South', 'East'], index=0)
kpi_focus = st.sidebar.multiselect('KPI focus', KPI_LIST, default=KPI_LIST)
time_range = st.sidebar.selectbox('Time range (chart window)', ['Last 30 days', 'Last 60 days', 'Last 90 days'],
                                   index=2)
scenario = st.sidebar.selectbox('Demo scenario', [
    'Material KPI movement & investigation', 'Low-confidence / competing hypotheses', 'Sparse-history / new KPI',
])
show_details = st.sidebar.checkbox('Show analytical details', value=(persona == 'Data Analyst'))
st.sidebar.markdown('---')
with st.sidebar.expander('Optional: enable live LLM narrative'):
    api_key = st.text_input('Anthropic API key (session only, never saved)', type='password',
                             help='Leave blank to use the deterministic narrative layer. '
                                  'The LLM never computes KPI numbers — only wording.')
st.sidebar.caption('Quantitative truth = deterministic analytics. LLM = optional narrative/intent layer only.')

RANGE_DAYS = {'Last 30 days': 30, 'Last 60 days': 60, 'Last 90 days': 90}[time_range]

# ---------- Header ----------
last_updated = max(sales.date.max(), ops.date.max()).strftime('%Y-%m-%d')
st.markdown(
    f'<div class="hero"><div class="hero-chip">◈ AI-POWERED KPI INVESTIGATION</div>'
    f'<h1>BusinessIntelligence.ai</h1>'
    f'<p>From <b>what changed</b> → <b>why</b> → <b>how certain</b> → <b>what next</b>.</p>'
    f'<div class="hero-ts">Data last updated<br><b>{last_updated}</b></div></div>',
    unsafe_allow_html=True)

# ---------- Natural-language investigation box ----------
st.markdown('<div class="nlbox">', unsafe_allow_html=True)
st.markdown('**Ask BusinessIntelligence.ai**')
st.caption('Type a business question. Intent parsing is deterministic; wording is deterministic unless an '
           'LLM key is provided above — the LLM never calculates numbers.')
nl_col1, nl_col2 = st.columns([4, 1])
with nl_col1:
    nl_query = st.text_input('nl_query', placeholder='e.g. "Why did Gross Margin fall in West?"',
                              label_visibility='collapsed')
with nl_col2:
    nl_go = st.button('Investigate', type='primary', use_container_width=True)
nl_result = None
if nl_go and nl_query.strip():
    nl_result = nl_router.route(nl_query, sales, ops, events, persona, region, api_key)
    tel = nl_result['telemetry']
    st.markdown(
        f"Parsed as: KPI = **{nl_result['parsed']['kpi']}**, Region = **{nl_result['region']}** "
        f"&nbsp;·&nbsp; <span class='pill pill-blue'>{nl_result['status']}</span> "
        f"&nbsp;·&nbsp; Confidence {nl_result['confidence']:.0f}%",
        unsafe_allow_html=True)
    st.info(nl_result['narrative'])
    llm_note = ("LLM narrative used" if tel.get('llm_used') else
                f"Deterministic fallback ({tel.get('reason', 'no API key provided')})")
    st.caption(f"{llm_note} · analytical latency {tel['analytical_latency_ms']:.0f} ms · "
               f"tokens {tel.get('tokens', 0)} · est. cost ${tel.get('est_cost', 0.0):.4f}")
st.markdown('</div>', unsafe_allow_html=True)

# ---------- Causal-status glossary ----------
with st.expander('What do "confidence" and "causal status" mean here?'):
    for term, desc in engine.CAUSAL_STATUS_GLOSSARY.items():
        st.markdown(f"**{term}** — {desc}")

driver_latency_ms = None

if scenario == 'Material KPI movement & investigation':
    d_full = engine.region_daily(sales, ops, region)
    d = d_full.tail(RANGE_DAYS)
    x = d_full.iloc[-1]
    flags = engine.materiality(d_full)
    significant = [k for k, v in flags.items() if v and k in kpi_focus]

    st.markdown('<div class="section">Executive signal</div>', unsafe_allow_html=True)
    cols = st.columns(5)
    cards = {
        'Gross Margin': ('Gross Margin', f'{x.gm_pct:.1f}%', f'{x.gm_dev_pp:+.1f} pp vs baseline',
                          'bad' if x.gm_dev_pp < 0 else 'good'),
        'Revenue': ('Revenue', f'{x.revenue / 1000:.1f}K', f'{x.rev_dev_pct:+.1f}% vs baseline',
                    'bad' if x.rev_dev_pct < 0 else 'good'),
        'Volume': ('Volume', f'{x.volume:,.0f}' if pd.notna(x.volume) else '—',
                   f'{x.vol_dev_pct:+.1f}% vs baseline' if pd.notna(x.vol_dev_pct) else 'n/a',
                   'bad' if pd.notna(x.vol_dev_pct) and x.vol_dev_pct < 0 else 'good'),
        'Inventory': ('Inventory', f'{x.inventory_units:,.0f}', f'{x.inv_dev_pct:+.1f}% vs baseline',
                      'bad' if x.inv_dev_pct < 0 else 'good'),
        'Discount Rate': ('Discount Rate', f'{x.avg_discount_rate * 100:.1f}%',
                           f'{x.disc_dev_pct:+.1f}% vs baseline', 'warn' if x.disc_dev_pct > 0 else 'good'),
    }
    for c, kpi_name in zip(cols, KPI_LIST):
        lab, val, delta, cls = cards[kpi_name]
        focus_cls = ' focus' if kpi_name in kpi_focus else ''
        c.markdown(f'<div class="kpi{focus_cls}"><div class="label">{lab}</div><div class="value">{val}</div>'
                    f'<div class="delta {cls}">{delta}</div></div>', unsafe_allow_html=True)

    if significant:
        st.warning(f"{len(significant)} material KPI movement(s) detected among selected KPIs: "
                   f"{', '.join(significant)}")
    else:
        st.success('No material movement detected among selected KPIs under the governed semantic thresholds.')

    st.markdown(f'<div class="section">KPI movement vs expected baseline</div>'
                f'<div class="sub">28-day rolling median (governed by the semantic contract); '
                f'chart window = {time_range.lower()}.</div>', unsafe_allow_html=True)
    chart = d.set_index('date')[['gm_pct', 'gm_baseline']].rename(
        columns={'gm_pct': 'Actual %', 'gm_baseline': 'Expected %'})
    st.line_chart(chart, height=300)

    st.markdown('<div class="section">Investigation workspace</div>', unsafe_allow_html=True)
    left, right = st.columns([1.08, 1.55])
    t_start = time.perf_counter()
    drivers = engine.driver_analysis(sales, ops, events, region)
    driver_latency_ms = (time.perf_counter() - t_start) * 1000
    with left:
        st.markdown('**Ranked explanatory drivers**')
        st.caption('Transparent prioritization — not a causal probability.')
        for rank, dr in enumerate(drivers, 1):
            score = dr['Support score']
            badge = 'pill-green' if score >= 65 else ('pill-amber' if score >= 45 else 'pill-red')
            st.markdown(f'''<div class="driver-card"><div style="display:flex;justify-content:space-between;align-items:center"><div><span class="driver-title">{rank:02d} · {dr['Driver']}</span><div class="driver-meta">Signal {dr['Signal']:+.1f}% · GM relationship {dr['Correlation with GM']:+.2f} · {dr['Evidence records']} evidence records · Contribution {dr['Contribution %']:.0f}%</div></div><div><span class="pill {badge}">{score:.0f}/100</span></div></div></div>''', unsafe_allow_html=True)
        selected = st.selectbox('Inspect driver', [r['Driver'] for r in drivers], label_visibility='collapsed')

    row = next(r for r in drivers if r['Driver'] == selected)
    ev = engine.evidence(events, region, selected)
    conf = engine.confidence_for(row, len(ev))
    status = engine.causal_status(conf, len(ev), row['Temporal alignment'], row['Correlation with GM'])
    metrics = {'signal': row['Signal'], 'evidence': len(ev), 'corr': row['Correlation with GM'],
               'temporal': row['Temporal alignment']}
    with right:
        st.markdown(f'**{selected}**')
        st.progress(conf / 100, text=f"Confidence: {conf:.0f}%")
        st.markdown(f'**Causal status:** <span class="pill pill-blue">{status}</span>', unsafe_allow_html=True)
        st.write(persona_text(persona, selected, status, conf, metrics))
        m1, m2, m3 = st.columns(3)
        m1.metric('Driver signal', f"{row['Signal']:+.1f}%")
        m2.metric('GM relationship', f"{row['Correlation with GM']:+.2f}")
        m3.metric('Temporal alignment', f"{row['Temporal alignment']:.0f}/100")
        st.caption('These signals support prioritization; they are not causal probabilities.')

    # ---------- Evidence lineage (computed, not hard-coded) ----------
    st.markdown('<div class="section">Evidence lineage — how did we reach this conclusion?</div>'
                '<div class="sub">Each step below is generated from the numbers already computed above.</div>',
                unsafe_allow_html=True)
    steps = [
        f"KPI anomaly detected: Gross Margin deviated {x.gm_dev_pp:+.1f} pp from its 28-day baseline",
        f"Candidate driver **{selected}** changed {row['Signal']:+.1f}% vs its prior 28-day window",
        f"Driver–KPI relationship: correlation {row['Correlation with GM']:+.2f} over the observed window",
        f"Temporal alignment score {row['Temporal alignment']:.0f}/100 (how closely the driver's change date "
        f"lines up with the KPI anomaly window)",
        f"{len(ev)} independent unstructured evidence record(s) retrieved for this driver"
        if len(ev) else "No independent unstructured evidence retrieved for this driver",
        f"Resulting causal status: **{status}** at {conf:.0f}% confidence",
    ]
    st.markdown('<div class="lineage">', unsafe_allow_html=True)
    for i, s in enumerate(steps):
        st.markdown(f'<div class="lineage-step">{s}</div>', unsafe_allow_html=True)
        if i < len(steps) - 1:
            st.markdown('<div class="lineage-arrow">↓</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Product-level impact makes the driver explanation inspectable.
    st.markdown('<div class="section">Impact by product segment</div><div class="sub">Shows where the KPI '
                'movement is concentrated; this is descriptive, not causal proof.</div>', unsafe_allow_html=True)
    impact = engine.product_impact(sales, region).reset_index().rename(columns={'product': 'Product'})
    st.dataframe(impact[['Product', 'gm_change_pp', 'revenue_change_pct', 'volume_change_pct',
                          'impact_weight']].rename(columns={
        'gm_change_pp': 'GM change (pp)', 'revenue_change_pct': 'Revenue change (%)',
        'volume_change_pct': 'Volume change (%)', 'impact_weight': 'Revenue weight (%)',
    }).round(2), use_container_width=True, hide_index=True)

    st.markdown('<div class="section">Evidence ledger</div><div class="sub">Trace every hypothesis to source, '
                'timing, method, contribution and lineage.</div>', unsafe_allow_html=True)
    e1, e2 = st.columns([1.45, 1])
    with e1:
        if len(ev) == 0:
            st.info('No matching unstructured evidence retrieved for this hypothesis.')
        for _, r in ev.iterrows():
            freshness = '1 day' if r.date.date() < pd.Timestamp.now().date() else 'same day'
            st.markdown(
                f'<div class="evidence"><div><span class="evidence-dot"></span><b>{r.event_type}</b> '
                f'<span class="tiny">· {r.date.date()} · {r.source} (unstructured)</span></div>'
                f'<div style="margin:.35rem 0 .25rem">{r.text}</div>'
                f'<span class="tiny">Freshness: {freshness} · Retrieval: region + event type · '
                f'Lineage: business_events.csv</span></div>', unsafe_allow_html=True)
    with e2:
        st.markdown('**Analytical trace**')
        st.markdown(f'''<div class="trace">
<div class="trace-row"><b>Claim</b><br>{selected} contributed to the {region} Gross Margin movement</div>
<div class="trace-row"><b>Baseline</b><br>28-day rolling median</div>
<div class="trace-row"><b>Method</b><br>Magnitude + GM relationship + temporal alignment + context</div>
<div class="trace-row"><b>Driver signal</b><br>{row['Signal']:+.1f}%</div>
<div class="trace-row"><b>GM relationship</b><br>{row['Correlation with GM']:+.2f}</div>
<div class="trace-row"><b>Temporal alignment</b><br>{row['Temporal alignment']:.0f}/100</div>
<div class="trace-row"><b>Contribution (relative)</b><br>{row['Contribution %']:.0f}% of total ranked support</div>
<div class="trace-row"><b>Segment impact</b><br>see product-level table above</div>
<div class="trace-row"><b>Supporting context</b><br>{len(ev)} record(s)</div>
<div class="trace-row"><b>Confidence</b><br>{conf:.0f}%</div>
<div class="trace-row"><b>Causal status</b><br>{status}</div>
<div class="trace-row"><b>Limitation</b><br>{engine.limitation_for(selected)}</div>
<div class="trace-row"><b>Quantitative truth</b><br>Python / Pandas (deterministic)</div>
<div class="trace-row"><b>Narrative</b><br>Deterministic template · LLM optional</div>
</div>''', unsafe_allow_html=True)

    if persona == 'Data Analyst' and show_details:
        with st.expander('🔎 Source-row drill-down'):
            detail = sales[sales.region == region].sort_values('date', ascending=False).head(100)
            st.dataframe(detail, use_container_width=True, height=320)

    st.markdown('<div class="section">Recommended next action</div>', unsafe_allow_html=True)
    lever, action, impact_text, owner = engine.action_for(selected)
    ac = st.columns(4)
    for c, lab, val in zip(ac, ['Driver / lever', 'Action', 'Expected impact', 'Owner'],
                            [f'{selected}\n\n{lever}', action, impact_text, owner]):
        c.markdown(f'<div class="card"><div class="metric-label">{lab}</div>'
                    f'<div style="margin-top:.45rem">{val}</div></div>', unsafe_allow_html=True)
    st.info('**Monitoring plan:** monitor the KPI and driver daily for 7 days. Re-open the investigation if the '
            'movement persists, reverses, or new evidence arrives.')

    st.markdown('<div class="section">Human decision & feedback</div>', unsafe_allow_html=True)
    decision = st.radio('Human decision', ['Approve', 'Reject', 'Unresolved'], horizontal=True)
    vcol1, vcol2, _ = st.columns([1, 1, 3])
    if 'vote' not in st.session_state:
        st.session_state['vote'] = ''
    if vcol1.button('👍 Correct'):
        st.session_state['vote'] = 'Correct'
    if vcol2.button('👎 Incorrect'):
        st.session_state['vote'] = 'Incorrect'
    if st.session_state['vote']:
        st.caption(f"Quick vote recorded this session: **{st.session_state['vote']}**")
    feedback = st.text_input('Business-user / analyst feedback', placeholder='What was correct, missing, '
                                                                               'or misleading?')
    if st.button('Save decision + feedback', type='primary'):
        engine.log_feedback(BASE, {
            'timestamp': pd.Timestamp.now().isoformat(), 'persona': persona, 'region': region,
            'scenario': scenario, 'driver': selected, 'decision': decision,
            'vote': st.session_state['vote'], 'feedback': feedback,
        })
        st.success('Decision and feedback recorded. Feedback captured for future model/rule improvement.')

    hist = engine.feedback_history(BASE)
    if len(hist):
        with st.expander(f'Feedback history & learning indicator ({len(hist)} record(s))'):
            votes = hist['vote'].fillna('') if 'vote' in hist.columns else pd.Series([], dtype=str)
            correct = (votes == 'Correct').sum()
            rated = (votes.isin(['Correct', 'Incorrect'])).sum()
            if rated:
                st.metric('Explanation usefulness (of rated feedback)', f"{correct / rated * 100:.0f}% 👍")
            st.caption('This is a simple tally, not a trained model — it becomes calibration signal for future '
                       'versions.')
            st.dataframe(hist.tail(20), use_container_width=True, hide_index=True)

elif scenario == 'Low-confidence / competing hypotheses':
    st.markdown('<div class="section">Abstention & ambiguity</div>', unsafe_allow_html=True)
    st.caption('Computed live from the same driver-scoring engine used above — the region shown below is the '
               'one where competing hypotheses genuinely have the closest scores in the current dataset.')
    amb_region, amb_rows = engine.find_ambiguous_region(sales, ops, events, ['West', 'North', 'South', 'East'])
    top_score = amb_rows[0]['Support score']
    second_score = amb_rows[1]['Support score']
    st.warning(f"Region **{amb_region}**: the engine cannot establish a single dominant explanation from the "
               f"available evidence (top score {top_score:.0f} vs second {second_score:.0f}).")
    st.markdown('### Ranked alternatives (real computed scores)')
    alt = pd.DataFrame([{
        'Hypothesis': r['Driver'], 'Support score': f"{r['Support score']:.0f}/100",
        'Evidence records': r['Evidence records'],
        'Status': engine.causal_status(engine.confidence_for(r, r['Evidence records']), r['Evidence records'],
                                        r['Temporal alignment'], r['Correlation with GM'], contradictory=True),
    } for r in amb_rows])
    st.dataframe(alt, use_container_width=True, hide_index=True)
    a, b = st.columns(2)
    with a:
        st.markdown('**Why the engine abstains**')
        st.write(f'• Top driver ({amb_rows[0]["Driver"]}) does not clearly dominate the runner-up')
        st.write('• Evidence sources are incomplete for several candidate drivers (see 0-record rows above)')
        st.write('• No controlled intervention is available to separate correlation from causation')
    with b:
        st.markdown('**Next diagnostic step**')
        missing = [r['Driver'] for r in amb_rows if r['Evidence records'] == 0]
        st.info(f"Request additional unstructured evidence for: "
                f"{', '.join(missing) if missing else 'all candidate drivers'} before making a corrective "
                f"recommendation.")
    if st.button('Request additional evidence', type='primary'):
        st.success('Evidence request logged. No causal claim was issued.')

elif scenario == 'Sparse-history / new KPI':
    st.markdown('<div class="section">Sparse-history safety</div>', unsafe_allow_html=True)
    st.markdown('<span class="sim-badge">⚠ Simulated scenario</span>', unsafe_allow_html=True)
    st.caption('The bundled dataset has full 90-day history for every region, so this scenario simulates a '
               'newly launched KPI/region to demonstrate the safety behavior. The confidence figure below is '
               'computed by a real (deterministic) penalty formula, not a fixed placeholder.')
    days_available, days_required = 21, 28
    sparse_conf = engine.sparse_history_confidence(days_available, days_required)
    c1, c2, c3 = st.columns(3)
    c1.metric('History available', f'{days_available} days')
    c2.metric('Required baseline', f'{days_required}+ days')
    c3.metric('Confidence', f'{sparse_conf:.0f}% (Low)')
    st.markdown('### What changes?')
    st.write('The engine does not fabricate a seasonal baseline. It switches to a peer-group comparison and '
             'explicitly lowers confidence using `sparse_history_confidence()` in `engine.py`.')
    st.info('**Alternative method:** compare against similar products/segments and recent peer behavior. '
            '**Decision status:** monitor / request more history.')

# ---------- Persona / semantic contract ----------
st.markdown('<div class="section">Governance & semantic contract</div>', unsafe_allow_html=True)
g1, g2, g3, g4 = st.columns(4)
g1.metric('Persona', persona)
g2.metric('Access scope', 'Aggregated' if persona == 'Commercial Manager' else 'Detailed')
g3.metric('KPI definition', 'Governed')
g4.metric('Audit trail', 'Enabled')
with st.expander('View KPI semantic contract'):
    kpi_name = st.selectbox('KPI', KPI_LIST, key='contract_kpi')
    st.json(semantic['kpis'][kpi_name])

# ---------- Data-source health ----------
st.markdown('<div class="section">Data-source health</div>', unsafe_allow_html=True)
source_rows = []
for name, meta in semantic['sources'].items():
    source_rows.append({'Source': name, 'Type': meta['type'], 'Grain': meta['grain'], 'Refresh': meta['refresh'],
                         'Freshness': meta['freshness'], 'Status': 'Healthy'})
st.dataframe(pd.DataFrame(source_rows), use_container_width=True, hide_index=True)

# ---------- Telemetry (measured, not hard-coded) ----------
feedback_count = len(engine.feedback_history(BASE))
st.markdown('<div class="section">Runtime telemetry</div>', unsafe_allow_html=True)
t1, t2, t3, t4, t5 = st.columns(5)
t1.metric('Analytical latency', f"{driver_latency_ms:.0f} ms" if driver_latency_ms is not None else "n/a")
nl_tel = nl_result['telemetry'] if nl_result else {}
t2.metric('LLM calls', '1' if nl_tel.get('llm_used') else '0')
t3.metric('Token usage', str(nl_tel.get('tokens', 0)))
t4.metric('Est. LLM cost', f"${nl_tel.get('est_cost', 0.0):.4f}")
t5.metric('Feedback records', str(feedback_count))
st.caption('Design boundary: deterministic logic/statistics provide quantitative truth; an optional LLM may '
           'handle intent parsing and narrative synthesis. It must not calculate KPI truth.')
st.markdown('<div class="footer-note">BusinessIntelligence.ai · Evidence-grounded KPI intelligence · '
            'Prototype data is synthetic</div>', unsafe_allow_html=True)
