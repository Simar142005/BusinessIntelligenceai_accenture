from pathlib import Path
import time
import re
import pandas as pd
import streamlit as st

import engine
import nl_router

BASE = Path(__file__).parent
custom_df = None
uploaded_files = []
api_key = None
st.set_page_config(page_title="BusinessIntelligence.ai", page_icon="◈", layout="wide", initial_sidebar_state="expanded")

sales, ops, events, semantic = engine.load_data(BASE)
KPI_LIST = engine.KPI_LIST
REGIONS = engine.REGIONS

st.markdown("""<style>
:root{
    --ink:#111827;
    --muted:#64748b;
    --line:#e7e8f0;
    --purple:#5b52d8;
    --red:#dc4b4b;
    --green:#0f9d72;
    --amber:#c77800;
}

.stApp{
    background:#f7f8fc;
    color:var(--ink);
}

.block-container{
    max-width:1540px;
    padding:1.3rem 2.1rem 3rem;
}

/* ================================
   SIDEBAR
   ================================ */

[data-testid="stSidebar"]{
    background:#f4f6fb !important;
    border-right:1px solid #e2e6ef !important;
}

/* Sidebar normal text
   NOTE: do not force every span/div to white.
   Streamlit's file uploader uses light cards internally,
   so a global span/div rule makes uploaded filenames invisible.
*/
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] .stMarkdown,
[data-testid="stSidebar"] .stCaption{
    color:#111827 !important;
}

/* Sidebar headings */
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3{
    color:#111827 !important;
}

/* ================================
   STREAMLIT SELECTBOX
   ================================ */

[data-testid="stSidebar"] [data-baseweb="select"] > div{
    background:#ffffff !important;
    border:1px solid #d9deea !important;
    border-radius:10px !important;
    min-height:46px !important;
}

/* Selected value inside selectbox */
[data-testid="stSidebar"] [data-baseweb="select"] [data-testid="stMarkdownContainer"],
[data-testid="stSidebar"] [data-baseweb="select"] span{
    color:#111827 !important;
}

/* Selectbox arrow */
[data-testid="stSidebar"] [data-baseweb="select"] svg{
    fill:#64748b !important;
    color:#64748b !important;
}

/* ================================
   SELECTBOX DROPDOWN MENU
   ================================ */

[data-baseweb="popover"]{
    z-index:999999 !important;
}

[data-baseweb="popover"] [role="option"]{
    background:#ffffff !important;
    color:#111827 !important;
}

[data-baseweb="popover"] [role="option"] *{
    color:#111827 !important;
}

[data-baseweb="popover"] [role="option"]:hover{
    background:#f1f5f9 !important;
}

/* Selected option */
[data-baseweb="popover"] [aria-selected="true"]{
    background:#eef2ff !important;
    color:#111827 !important;
}

/* ================================
   SIDEBAR INPUT
   ================================ */

[data-testid="stSidebar"] input{
    background:#ffffff !important;
    color:#111827 !important;
    border:1px solid #d9deea !important;
    border-radius:10px !important;
}

[data-testid="stSidebar"] input::placeholder{
    color:#94a3b8 !important;
}

/* ================================
   SIDEBAR CHECKBOX
   ================================ */

[data-testid="stSidebar"] [data-testid="stCheckbox"] label{
    color:#f8fafc !important;
}

[data-testid="stSidebar"] [data-testid="stCheckbox"] p{
    color:#f8fafc !important;
}


/* ================================
   SIDEBAR VISIBILITY FIX
   ================================ */

/* Keep sidebar background dark, but make all user-facing labels readable. */
[data-testid="stSidebar"] .stMarkdown,
[data-testid="stSidebar"] .stCaption,
[data-testid="stSidebar"] .stFileUploader,
[data-testid="stSidebar"] .stSelectbox,
[data-testid="stSidebar"] .stRadio,
[data-testid="stSidebar"] .stCheckbox,
[data-testid="stSidebar"] .stExpander {
    color:#f8fafc !important;
}

/* Radio buttons: visible option text + accessible circles. */
[data-testid="stSidebar"] [role="radiogroup"] label,
[data-testid="stSidebar"] [role="radiogroup"] label p,
[data-testid="stSidebar"] [role="radiogroup"] label span,
[data-testid="stSidebar"] [role="radiogroup"] [data-testid="stMarkdownContainer"] {
    color:#111827 !important;
    opacity:1 !important;
}

/* Radio circle borders/fill. */
[data-testid="stSidebar"] [role="radiogroup"] div[role="radio"] {
    border-color:#64748b !important;
    opacity:1 !important;
}

[data-testid="stSidebar"] [role="radiogroup"] div[role="radio"][aria-checked="true"] {
    border-color:#a78bfa !important;
    background:#7c3aed !important;
}

/* File uploader text, drag/drop area and buttons. */
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
    background:#ffffff !important;
    border:1px dashed #94a3b8 !important;
}

[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] * {
    color:#111827 !important;
    opacity:1 !important;
}

[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button {
    background:#ffffff !important;
    color:#111827 !important;
    border:1px solid #d9deea !important;
}

/* Uploaded-file card: keep filename + size dark on its white card. */
[data-testid="stSidebar"] [data-testid="stFileUploaderFile"] {
    background:#ffffff !important;
    color:#111827 !important;
    border:1px solid #d9deea !important;
}

[data-testid="stSidebar"] [data-testid="stFileUploaderFile"] *,
[data-testid="stSidebar"] [data-testid="stFileUploaderFileName"],
[data-testid="stSidebar"] [data-testid="stFileUploaderFileName"] * {
    color:#111827 !important;
    opacity:1 !important;
}

/* Fallback for newer Streamlit uploader markup. */
[data-testid="stSidebar"] [data-testid="stFileUploader"] [role="listitem"],
[data-testid="stSidebar"] [data-testid="stFileUploader"] [role="listitem"] * {
    color:#111827 !important;
}


/* Caption/help text should remain readable instead of inheriting unwanted white text. */
[data-testid="stSidebar"] small,
[data-testid="stSidebar"] .stCaption {
    color:#475569 !important;
}

/* Expander header/body. */
[data-testid="stSidebar"] details summary,
[data-testid="stSidebar"] details summary * {
    color:#f8fafc !important;
}

/* Number/date/text inputs in sidebar. */
[data-testid="stSidebar"] input,
[data-testid="stSidebar"] textarea {
    color:#111827 !important;
    background:#ffffff !important;
}

/* Sidebar alert boxes. */
[data-testid="stSidebar"] [data-testid="stAlert"] * {
    color:#f8fafc !important;
}


/* FINAL UPLOADER VISIBILITY FIX */
[data-testid="stSidebar"] [data-testid="stFileUploader"] section {
    background:#232746 !important;
    border:1px dashed #64748b !important;
}

[data-testid="stSidebar"] [data-testid="stFileUploader"] section * {
    opacity:1 !important;
}

[data-testid="stSidebar"] [data-testid="stFileUploader"] ul,
[data-testid="stSidebar"] [data-testid="stFileUploader"] ol {
    background:transparent !important;
}

[data-testid="stSidebar"] [data-testid="stFileUploader"] li {
    background:#ffffff !important;
    border:1px solid #d9deea !important;
    border-radius:10px !important;
}

[data-testid="stSidebar"] [data-testid="stFileUploader"] li * {
    color:#111827 !important;
    opacity:1 !important;
}

/* ================================
   MAIN UI
   ================================ */

.hero{
    padding:1.5rem 1.7rem;
    border:1px solid #e4e5f1;
    border-radius:22px;
    background:linear-gradient(120deg,#fff,#f4f2ff 55%,#eef8ff);
    box-shadow:0 10px 35px #0f172a0d;
    margin-bottom:1rem
}

.hero h1{
    margin:0;
    font-size:2.1rem;
    font-weight:900;
    letter-spacing:-.04em
}

.hero p{
    color:#64748b;
    margin:.4rem 0 0
}

.chip{
    display:inline-block;
    background:#ebe9ff;
    color:#4c42bd;
    border-radius:999px;
    padding:.3rem .6rem;
    font-size:.7rem;
    font-weight:900;
    margin-bottom:.55rem
}

.section{
    font-size:1.15rem;
    font-weight:900;
    margin:1.25rem 0 .35rem
}

.sub{
    color:#64748b;
    font-size:.8rem;
    margin-bottom:.7rem
}

.card{
    background:#fff;
    border:1px solid var(--line);
    border-radius:16px;
    padding:1rem;
    box-shadow:0 5px 18px #0f172a08
}

.kpi{
    background:#fff;
    border:1px solid var(--line);
    border-radius:17px;
    padding:1rem;
    min-height:120px;
    box-shadow:0 6px 20px #0f172a09
}

.kpi .label{
    font-size:.68rem;
    text-transform:uppercase;
    letter-spacing:.1em;
    color:#64748b;
    font-weight:900
}

.kpi .value{
    font-size:1.75rem;
    font-weight:900;
    margin-top:.35rem
}

.kpi .delta{
    font-size:.77rem;
    font-weight:800;
    margin-top:.25rem
}

.bad{color:var(--red)}
.good{color:var(--green)}
.warn{color:var(--amber)}

.driver{
    background:#fff;
    border:1px solid var(--line);
    border-radius:14px;
    padding:.85rem 1rem;
    margin:.4rem 0
}

.driver b{
    font-size:.9rem
}

.tiny{
    font-size:.72rem;
    color:#64748b
}

.score{
    float:right;
    color:var(--purple);
    font-weight:900
}

.evidence{
    background:#fff;
    border:1px solid var(--line);
    border-left:4px solid var(--purple);
    border-radius:12px;
    padding:.8rem;
    margin:.5rem 0
}

.trace{
    background:#faf9ff;
    border:1px solid #e7e4ff;
    border-radius:14px;
    padding:.9rem
}

.trace-row{
    padding:.42rem 0;
    border-bottom:1px solid #eceaf7;
    font-size:.78rem
}

.trace-row:last-child{
    border:0
}

.badge{
    display:inline-block;
    border-radius:999px;
    padding:.25rem .55rem;
    background:#ece9ff;
    color:#4c42bd;
    font-size:.68rem;
    font-weight:900
}

.footer{
    text-align:center;
    color:#7c8497;
    font-size:.7rem;
    margin-top:1.5rem
}
</style>""", unsafe_allow_html=True)


def pretty(value):
    """Convert internal names to readable labels without affecting calculations."""
    if value is None:
        return "—"
    return str(value).replace("_", " ").strip().title()


def fmt_kpi_value(x, kpi):
    if kpi == "Gross Margin": return f"{x.gm_pct:.1f}%"
    if kpi == "Revenue": return f"{x.revenue/1000:.1f}K"
    if kpi == "Volume": return f"{x.volume:,.0f}"
    if kpi == "Inventory": return f"{x.inventory_units:,.0f}"
    return f"{x.avg_discount_rate*100:.1f}%"


def fmt_delta(x, kpi):
    meta=engine.KPI_META[kpi]; d=float(x[meta['delta_col']])
    return f"{d:+.1f} {meta['unit']} vs baseline"


def driver_status(row, conf, ev_count, contradictory=False):
    return engine.causal_status(conf, ev_count, row['Temporal alignment'], row['Correlation with KPI'], contradictory)


st.sidebar.markdown("## BusinessIntelligence.ai")
st.sidebar.caption("KPI intelligence → evidence → action")

# ============================================================
# DATA MODE
# ============================================================
st.sidebar.markdown("### 📂 Data Source")

data_mode = st.sidebar.radio(
    "Choose data source",
    ["Demo Dataset", "Upload Dataset"],
    index=0,
    key="data_source_mode",
    horizontal=False,
)

# ============================================================
# CUSTOM DATASET UPLOAD
# ============================================================

if data_mode == "Upload Dataset":

    uploaded_files = st.sidebar.file_uploader(
        "Upload CSV / Excel / JSON files",
        type=["csv", "xlsx", "xls", "json"],
        accept_multiple_files=True,
        help="Upload one or more CSV/Excel datasets."
    )

    if uploaded_files:
        st.sidebar.success(f"✓ {len(uploaded_files)} file(s) uploaded")
        st.sidebar.markdown("**Uploaded files**")

        for file in uploaded_files:
            st.sidebar.markdown(
                f"📄 **{file.name}**",
                unsafe_allow_html=False,
            )

        with st.sidebar.expander("🔗 Combine multiple files", expanded=len(uploaded_files) > 1):
            combine_files = st.checkbox(
                "Combine uploaded datasets",
                value=len(uploaded_files) > 1,
                key="combine_uploaded_files",
            )
            st.caption(
                "When enabled, the first file is the base table and additional "
                "files are joined using a shared business key."
            )

# ============================================================
# EXISTING DEMO CONTROLS
# ============================================================

persona = st.sidebar.selectbox(
    "Persona",
    ["Commercial Manager", "Data Analyst"]
)

if data_mode == "Demo Dataset":
    st.session_state["join_messages"] = []
    region = st.sidebar.selectbox("Region", REGIONS, index=0)
    kpi_focus = st.sidebar.selectbox("Primary KPI", KPI_LIST, index=0)
    selected_category = "All"

else:
    region = "All"
    selected_category = "All"

    if uploaded_files:
        try:
            loaded_frames = {}

            for file in uploaded_files:
                name = file.name.lower()
                if name.endswith(".csv"):
                    loaded_frames[file.name] = pd.read_csv(file)
                elif name.endswith(".json"):
                    loaded_frames[file.name] = pd.read_json(file)
                else:
                    loaded_frames[file.name] = pd.read_excel(file)

            base_name = list(loaded_frames.keys())[0]
            custom_df = loaded_frames[base_name].copy()

            combine_enabled = (
                len(uploaded_files) > 1
                and st.session_state.get("combine_uploaded_files", False)
            )

            join_messages = []

            if combine_enabled:
                priority_keys = [
                    "transaction_id", "order_id", "customer_id",
                    "product_id", "employee_id", "store_id", "account_id"
                ]

                for other_name, other_df in list(loaded_frames.items())[1:]:
                    left_lookup = {
                        str(c).strip().lower(): c for c in custom_df.columns
                    }
                    right_lookup = {
                        str(c).strip().lower(): c for c in other_df.columns
                    }
                    common = sorted(set(left_lookup) & set(right_lookup))

                    if not common:
                        join_messages.append(
                            f"⚠ {other_name}: no shared column found; file not joined."
                        )
                        continue

                    preferred = next(
                        (k for k in priority_keys if k in common),
                        None
                    )

                    if preferred is None:
                        semantic_keys = [
                            k for k in common
                            if any(
                                token in k
                                for token in [
                                    "customer", "product", "order",
                                    "transaction", "account", "store",
                                    "region", "date"
                                ]
                            )
                        ]
                        preferred = semantic_keys[0] if semantic_keys else common[0]

                    left_key = left_lookup[preferred]
                    right_key = right_lookup[preferred]

                    custom_df[left_key] = custom_df[left_key].astype(str).str.strip()
                    other_df[right_key] = other_df[right_key].astype(str).str.strip()

                    matched_keys = set(other_df[right_key].dropna())
                    match_count = int(custom_df[left_key].isin(matched_keys).sum())

                    custom_df = custom_df.merge(
                        other_df,
                        left_on=left_key,
                        right_on=right_key,
                        how="left",
                        suffixes=("", f"_{Path(other_name).stem}")
                    )

                    join_messages.append(
                        f"✓ {other_name}: joined on **{left_key}** "
                        f"with {match_count:,} matching base rows."
                    )

            st.session_state["custom_df"] = custom_df
            st.session_state["join_messages"] = join_messages

            numeric_columns = custom_df.select_dtypes(
                include="number"
            ).columns.tolist()

            categorical_columns = custom_df.select_dtypes(
                include=["object", "category", "bool"]
            ).columns.tolist()

            st.sidebar.markdown("### 📊 Dataset")
            st.sidebar.caption(
                f"{len(custom_df):,} rows × {len(custom_df.columns):,} columns"
            )

            if st.session_state.get("join_messages"):
                with st.sidebar.expander("🔗 Combination result", expanded=True):
                    for msg in st.session_state["join_messages"]:
                        st.markdown(msg, unsafe_allow_html=True)

            if numeric_columns:
                kpi_focus = st.sidebar.selectbox(
                    "Primary KPI",
                    numeric_columns,
                    index=0,
                )
            else:
                kpi_focus = None
                st.sidebar.error("No numeric columns found.")

            if categorical_columns:
                selected_category = st.sidebar.selectbox(
                    "Group / Category",
                    ["All"] + categorical_columns,
                    index=0,
                )

            with st.sidebar.expander("🔎 Dataset Profile", expanded=True):
                st.write(f"**Rows:** {len(custom_df):,}")
                st.write(f"**Columns:** {len(custom_df.columns):,}")
                st.write(f"**Numeric fields:** {len(numeric_columns)}")
                st.write(f"**Categorical fields:** {len(categorical_columns)}")
                st.write(
                    f"**Missing values:** {int(custom_df.isna().sum().sum()):,}"
                )
                st.write("**Columns:**")
                for col in custom_df.columns:
                    st.caption(f"• {col}")

        except Exception as e:
            st.sidebar.error(f"Could not read dataset: {e}")
            kpi_focus = None
    else:
        st.sidebar.info("Upload a CSV or Excel file to begin.")
        kpi_focus = None

# ============================================================
# COMMON CONTROLS
# ============================================================

time_range = st.sidebar.selectbox(
    "Chart window",
    [
        "Last 30 days",
        "Last 60 days",
        "Last 90 days"
    ],
    index=2
)

scenario = st.sidebar.selectbox(
    "Demo scenario",
    [
        "Material KPI movement & investigation",
        "Low-confidence / competing hypotheses",
        "Sparse-history / new KPI"
    ]
)

show_details = st.sidebar.checkbox(
    "Show analytical details",
    value=persona == "Data Analyst"
)


# ============================================================
# GENERIC UPLOADED-DATA ANALYSIS
# ============================================================
if data_mode == "Upload Dataset":
    if custom_df is None:
        st.markdown(
            '<div class="hero"><div class="chip">◈ CUSTOM DATA MODE</div>'
            '<h1>BusinessIntelligence.ai</h1>'
            '<p>Upload a CSV or Excel dataset to begin KPI investigation.</p></div>',
            unsafe_allow_html=True,
        )
        st.stop()

    st.markdown(
        '<div class="hero"><div class="chip">◈ CUSTOM DATA MODE · DATASET INDEPENDENT</div>'
        '<h1>BusinessIntelligence.ai</h1>'
        '<p>Detect what changed → quantify the signal → identify where it moved → decide what next.</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    if kpi_focus is None:
        st.error("This dataset has no usable numeric KPI column.")
        st.stop()

    df = custom_df.copy()

    # Clean column names only for display/selection; values are unchanged.
    df.columns = [
        str(c).strip() if str(c).strip() else f"Column_{i+1}"
        for i, c in enumerate(df.columns)
    ]

    kpi = pd.to_numeric(df[kpi_focus], errors="coerce")
    valid = kpi.notna()

    if valid.sum() < 2:
        st.error(f"'{kpi_focus}' does not contain enough numeric observations.")
        st.stop()

    # Detect a date/time column for a time-aware baseline when possible.
    date_col = None
    date_candidates = []

    for col in df.columns:
        if col == kpi_focus:
            continue
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            date_candidates.append(col)
            continue

        non_null = df[col].dropna()
        if len(non_null) >= 3:
            parsed = pd.to_datetime(non_null, errors="coerce")
            if parsed.notna().mean() >= 0.8:
                date_candidates.append(col)

    if date_candidates:
        date_col = date_candidates[0]
        df["_BI_Date"] = pd.to_datetime(df[date_col], errors="coerce")
        df = df.dropna(subset=["_BI_Date"])
        df["_BI_KPI"] = pd.to_numeric(df[kpi_focus], errors="coerce")
        df = df.dropna(subset=["_BI_KPI"]).sort_values("_BI_Date")
    else:
        df["_BI_Date"] = range(len(df))
        df["_BI_KPI"] = pd.to_numeric(df[kpi_focus], errors="coerce")
        df = df.dropna(subset=["_BI_KPI"])

    if len(df) < 2:
        st.error("Not enough valid KPI observations after cleaning.")
        st.stop()

    # Use a 28-observation rolling baseline. If history is shorter, use
    # the first half of observations as the comparison baseline.
    n = len(df)
    recent_n = max(1, min(28, n // 3 if n >= 6 else 1))
    baseline_n = max(1, n - recent_n)

    baseline = float(df["_BI_KPI"].iloc[:baseline_n].mean())
    actual = float(df["_BI_KPI"].iloc[-recent_n:].mean())
    delta = actual - baseline
    relative = delta / (abs(baseline) + 1e-9) * 100

    baseline_std = float(df["_BI_KPI"].iloc[:baseline_n].std(ddof=0))
    z_score = delta / (baseline_std + 1e-9)

    # A transparent materiality rule: relative movement >= 5% OR |z| >= 2.
    material = abs(relative) >= 5 or abs(z_score) >= 2

    st.markdown(
        '<div class="section">Custom dataset signal</div>'
        '<div class="sub">All KPI values below are calculated directly from the uploaded data; no LLM is used for numerical calculations. Trend charts automatically aggregate high-volume transaction data to a readable time grain.</div>',
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rows analyzed", f"{len(df):,}")
    c2.metric("Actual", f"{actual:,.2f}")
    c3.metric("Baseline", f"{baseline:,.2f}")
    c4.metric("Movement", f"{relative:+.2f}%")

    direction = "increased" if delta > 0 else ("decreased" if delta < 0 else "was stable")
    severity = "material" if material else "non-material"

    executive_html = (
        '<div class="card" style="margin-top:.8rem;">'
        '<div class="tiny"><b>EXECUTIVE SUMMARY</b></div>'
        f'<div style="font-size:1.05rem;font-weight:800;margin-top:.35rem;">'
        f'{pretty(kpi_focus)} {direction} by {relative:+.2f}% versus the calculated baseline.'
        '</div>'
        f'<div class="tiny" style="margin-top:.35rem;">'
        f'{len(df):,} valid observations · {severity} movement screen · '
        f'baseline = {baseline:,.2f} · recent = {actual:,.2f}. '
        'Quantitative claims are calculated directly from the uploaded dataset.'
        '</div>'
        '</div>'
    )
    st.markdown(executive_html, unsafe_allow_html=True)

    if material:
        st.warning(
            f"Material movement detected for **{kpi_focus}**: "
            f"{relative:+.2f}% versus the calculated baseline."
        )
    else:
        st.success(
            f"No material movement detected for **{kpi_focus}** under the "
            f"5% / |z|≥2 screening rule."
        )

    # ------------------------------------------------------------
    # TREND CHART — AUTOMATICALLY AGGREGATED
    # ------------------------------------------------------------
    st.markdown(
        f'<div class="section">{pretty(kpi_focus)}: actual trend</div>',
        unsafe_allow_html=True,
    )

    chart_df = df[["_BI_Date", "_BI_KPI"]].copy()
    chart_df = chart_df.rename(columns={"_BI_KPI": "Actual"})

    if date_col:
        # Avoid plotting thousands of transaction-level observations.
        # Pick a readable time grain automatically.
        unique_dates = chart_df["_BI_Date"].dt.normalize().nunique()
        span_days = max(
            1,
            int(
                (
                    chart_df["_BI_Date"].max() - chart_df["_BI_Date"].min()
                ).days
            ),
        )

        if unique_dates <= 120:
            freq = "D"
            grain_label = "daily"
        elif unique_dates <= 520:
            freq = "W"
            grain_label = "weekly"
        else:
            freq = "MS"
            grain_label = "monthly"

        chart_df["_Period"] = chart_df["_BI_Date"].dt.to_period(freq).dt.start_time
        chart_df = (
            chart_df.groupby("_Period", as_index=True)["Actual"]
            .mean()
            .to_frame()
            .sort_index()
        )

        st.caption(
            f"Showing {grain_label} average {pretty(kpi_focus).lower()} "
            f"to keep the trend readable ({len(chart_df):,} time points from "
            f"{len(df):,} records)."
        )
    else:
        # For datasets without dates, bin observations into at most 200
        # points instead of drawing thousands of transaction-level lines.
        max_points = 200
        bin_size = max(1, int(len(chart_df) / max_points))
        chart_df["Observation"] = range(1, len(chart_df) + 1)
        chart_df["Bin"] = ((chart_df["Observation"] - 1) // bin_size) + 1

        chart_df = (
            chart_df.groupby("Bin", as_index=True)["Actual"]
            .mean()
            .to_frame()
        )
        chart_df.index.name = "Observation group"

        st.caption(
            f"No date column detected. Showing {len(chart_df):,} averaged "
            f"observation groups from {len(df):,} records."
        )

    st.line_chart(
        chart_df[["Actual"]],
        height=320,
        use_container_width=True,
    )

    # ------------------------------------------------------------
    # WHERE DID THE KPI MOVE?
    # ------------------------------------------------------------
    st.markdown(
        '<div class="section">📍 Where did the KPI move?</div>'
        '<div class="sub">Compare each categorical segment between the same baseline and recent windows used for the headline KPI. This is a movement diagnostic, not a causal claim.</div>',
        unsafe_allow_html=True,
    )

    # Build useful grouping candidates. Some real-world datasets encode
    # dimensions such as Region/Product/Category as numeric codes, so do not
    # restrict grouping to object columns only.
    excluded_group_cols = {kpi_focus, "_BI_Date", "_BI_KPI", "_Period"}
    group_candidates = []
    group_type_labels = {}

    # Prevent IDs and near-unique transaction keys from being suggested as
    # business dimensions. They create thousands of tiny groups and do not
    # provide a useful executive explanation.
    id_tokens = {
        "id", "code", "key", "uuid", "guid", "number", "no", "num"
    }

    for col in df.columns:
        if col in excluded_group_cols:
            continue

        series = df[col]
        non_null = series.dropna()
        nunique = int(series.nunique(dropna=True))
        unique_ratio = nunique / max(len(non_null), 1)

        normalized = re.sub(r"[^a-z0-9]+", "_", str(col).strip().lower())
        name_tokens = set(normalized.split("_"))

        looks_like_id = (
            bool(name_tokens.intersection(id_tokens))
            and unique_ratio >= 0.50
        )

        near_unique = unique_ratio >= 0.90

        is_categorical = (
            pd.api.types.is_object_dtype(series)
            or pd.api.types.is_categorical_dtype(series)
            or pd.api.types.is_bool_dtype(series)
        )

        is_small_numeric_dimension = (
            pd.api.types.is_numeric_dtype(series)
            and 2 <= nunique <= 200
        )

        # Text columns are useful even when they have many unique values only
        # when they do not look like identifiers.
        useful_text_dimension = is_categorical and not looks_like_id and not near_unique

        if useful_text_dimension or is_small_numeric_dimension:
            group_candidates.append(col)
            group_type_labels[col] = (
                "categorical" if is_categorical
                else f"numeric code · {nunique:,} unique"
            )

    if group_candidates:
        # Prefer the user's sidebar selection when it is a valid group field.
        default_group = (
            selected_category
            if selected_category in group_candidates
            else group_candidates[0]
        )

        group_col = st.selectbox(
            "Analyze movement by",
            group_candidates,
            index=group_candidates.index(default_group),
            key="custom_group_dimension",
            format_func=lambda c: f"{c}  ({group_type_labels[c]})",
        )

        st.caption(
            "Identifier-like fields such as Customer_ID are filtered out automatically "
            "when they are nearly unique. This keeps the analysis focused on business dimensions."
        )

        work = df[[group_col, "_BI_KPI"]].copy()
        work[group_col] = work[group_col].fillna("Missing").astype(str)

        # Keep exactly the same baseline/recent split as the headline KPI.
        work["_Window"] = "Baseline"
        work.loc[work.index.isin(df.tail(recent_n).index), "_Window"] = "Recent"

        baseline_groups = (
            work[work["_Window"] == "Baseline"]
            .groupby(group_col, dropna=False)["_BI_KPI"]
            .agg(["count", "mean"])
            .rename(columns={"count": "Baseline records", "mean": "Baseline"})
        )

        recent_groups = (
            work[work["_Window"] == "Recent"]
            .groupby(group_col, dropna=False)["_BI_KPI"]
            .agg(["count", "mean"])
            .rename(columns={"count": "Recent records", "mean": "Recent"})
        )

        movement = baseline_groups.join(recent_groups, how="outer").fillna(0)

        # Require at least one observation in both windows where possible.
        movement = movement[
            (movement["Baseline records"] > 0)
            & (movement["Recent records"] > 0)
        ].copy()

        if not movement.empty:
            movement["Absolute change"] = movement["Recent"] - movement["Baseline"]
            movement["Movement %"] = (
                movement["Absolute change"]
                / (movement["Baseline"].abs() + 1e-9)
                * 100
            )

            # A transparent ranking signal:
            # magnitude of group movement weighted by its share of recent records.
            total_recent = max(float(movement["Recent records"].sum()), 1.0)
            movement["Movement score"] = (
                movement["Movement %"].abs()
                * movement["Recent records"]
                / total_recent
            )

            movement = movement.sort_values(
                "Movement score",
                ascending=False,
            )

            top_n = min(10, len(movement))
            display = movement.head(top_n).reset_index()
            display = display.rename(columns={group_col: "Segment"})

            st.dataframe(
                display[
                    [
                        "Segment",
                        "Baseline records",
                        "Recent records",
                        "Baseline",
                        "Recent",
                        "Absolute change",
                        "Movement %",
                        "Movement score",
                    ]
                ].round(2),
                use_container_width=True,
                hide_index=True,
            )

            chart = (
                display.set_index("Segment")["Movement %"]
                .sort_values()
            )

            st.caption(
                f"Top {top_n} segments ranked by absolute movement weighted by recent record share. "
                "A positive value means the segment KPI is higher in the recent window."
            )

            st.bar_chart(chart, height=300)

            top = display.iloc[0]
            st.info(
                f"**Largest movement signal:** {top['Segment']} · "
                f"{float(top['Movement %']):+.2f}% versus its segment baseline. "
                "This identifies where the KPI moved most; it does not by itself prove why it moved."
            )
        else:
            st.info(
                f"Not enough observations in both windows to rank segments by **{group_col}**."
            )
    else:
        st.info(
            "No usable grouping field was detected. Add a field such as Region, "
            "Product, Category, Department, or Customer Segment. Text/categorical "
            "fields and numeric-coded dimensions with up to 200 distinct values are supported."
        )

    # Calculation trace.
    st.markdown(
        '<div class="section">🔍 Calculation & Evidence Trace</div>',
        unsafe_allow_html=True,
    )

    trace_steps = [
        ("1. Dataset", f"{len(custom_df):,} rows × {len(custom_df.columns):,} columns"),
        ("2. KPI", f"{kpi_focus} · {len(df):,} valid observations"),
        ("3. Baseline", f"Mean of first {baseline_n:,} observations = {baseline:,.2f}"),
        ("4. Actual", f"Mean of latest {recent_n:,} observations = {actual:,.2f}"),
        ("5. Absolute movement", f"Actual − Baseline = {delta:+,.2f}"),
        ("6. Relative movement", f"(Actual − Baseline) / |Baseline| × 100 = {relative:+.2f}%"),
        ("7. Statistical signal", f"Z-score = {z_score:+.2f}"),
        ("8. Materiality", f"Material = {'YES' if material else 'NO'}"),
    ]

    for title, description in trace_steps:
        st.markdown(
            f'<div class="trace-row"><b>{title}</b><br>'
            f'<span class="tiny">{description}</span></div>',
            unsafe_allow_html=True,
        )

    st.caption(
        "Quantitative values are calculated by the deterministic Python layer. "
        "The optional LLM is not the source of numerical truth."
    )

    # Generic categorical driver view.
    categorical_cols = [
        c for c in df.columns
        if c not in {kpi_focus, "_BI_Date", "_BI_KPI"}
        and (
            pd.api.types.is_object_dtype(df[c])
            or pd.api.types.is_categorical_dtype(df[c])
            or pd.api.types.is_bool_dtype(df[c])
        )
    ]

    if categorical_cols:
        st.markdown(
            '<div class="section">Where did the KPI move?</div>'
            '<div class="sub">Groups are ranked by their KPI mean relative to the overall dataset mean.</div>',
            unsafe_allow_html=True,
        )

        group_col = selected_category if selected_category != "All" else categorical_cols[0]
        grouped = (
            df.groupby(group_col, dropna=False)["_BI_KPI"]
            .agg(["count", "mean"])
            .reset_index()
        )
        grouped["Gap vs overall"] = grouped["mean"] - float(df["_BI_KPI"].mean())
        grouped["Gap %"] = (
            grouped["Gap vs overall"]
            / (abs(float(df["_BI_KPI"].mean())) + 1e-9)
            * 100
        )
        grouped = grouped.sort_values(
            "Gap %",
            key=lambda s: s.abs(),
            ascending=False,
        )

        st.dataframe(
            grouped.round(2),
            use_container_width=True,
            hide_index=True,
        )

        st.bar_chart(
            grouped.set_index(group_col)["mean"].head(10),
            height=280,
        )

    st.info(
        "Next engine step: connect this generic dataset to the full "
        "evidence/driver-ranking engine. Multi-file joining will follow after that."
    )

    st.stop()

# Header
last_updated = max(sales.date.max(), ops.date.max()).strftime("%Y-%m-%d")
st.markdown(f'<div class="hero"><div class="chip">◈ PROBLEM TRACK 3 · AI-POWERED KPI INVESTIGATION</div><h1>BusinessIntelligence.ai</h1><p>Detect what changed → rank why → show evidence → quantify confidence → decide what next.</p><div class="tiny">Synthetic prototype data · latest data date: <b>{last_updated}</b></div></div>', unsafe_allow_html=True)

# Natural language investigation
st.markdown('<div class="section">Ask BusinessIntelligence.ai</div><div class="sub">Try: “Why did Revenue fall in West?” or “Investigate Inventory in North.”</div>', unsafe_allow_html=True)
q1,q2=st.columns([5,1])
with q1: query=st.text_input("Business question", placeholder="Why did Revenue fall in West?", label_visibility="collapsed")
with q2: go=st.button("Investigate", type="primary", use_container_width=True)
if go and query.strip():
    st.session_state["nl_result"] = nl_router.route(query, sales, ops, events, persona, region, api_key, BASE)

nl_result=st.session_state.get("nl_result")
if nl_result:
    r=nl_result
    st.info(f"**Parsed:** KPI = {r['parsed']['kpi']} · Region = {r['region']} · **{r['status']}** · Confidence {r['confidence']:.0f}%\n\n{r['narrative']}")
    tel=r['telemetry']; st.caption(f"LLM used: {'yes' if tel.get('llm_used') else 'no'} · analytical latency {tel.get('analytical_latency_ms',0):.0f} ms · tokens {tel.get('tokens',0)} · est. cost ${tel.get('est_cost',0):.4f}")

with st.expander("Confidence & causal-status glossary"):
    for k,v in engine.CAUSAL_STATUS_GLOSSARY.items(): st.markdown(f"**{k}** — {v}")

RANGE_DAYS={"Last 30 days":30,"Last 60 days":60,"Last 90 days":90}[time_range]

if scenario == "Material KPI movement & investigation":
    d_full=engine.region_daily(sales,ops,region); d=d_full.tail(RANGE_DAYS); x=d_full.iloc[-1]
    mat=engine.materiality(d_full); details=engine.materiality_details(d_full,kpi_focus)

    st.markdown('<div class="section">Executive signal</div><div class="sub">Five governed KPIs; materiality combines the semantic threshold with a statistical/business-impact check.</div>', unsafe_allow_html=True)
    cols=st.columns(5)
    for c,k in zip(cols,KPI_LIST):
        val=fmt_kpi_value(x,k); delta=fmt_delta(x,k); m=engine.materiality_details(d_full,k)
        cls='bad' if m['delta']<0 else ('warn' if k=='Discount Rate' and m['delta']>0 else 'good')
        border='2px solid #5b52d8' if k==kpi_focus else '1px solid #e7e8f0'
        c.markdown(f'<div class="kpi" style="border:{border}"><div class="label">{k}</div><div class="value">{val}</div><div class="delta {cls}">{delta}</div><div class="tiny">Material: {"YES" if mat[k] else "No"} · z={m["z_score"]:.1f}</div></div>',unsafe_allow_html=True)

    significant=[k for k,v in mat.items() if v]
    if significant: st.warning(f"Material movement detected: {', '.join(significant)}")
    else: st.success("No governed material KPI movement detected under current thresholds.")

    st.markdown(f'<div class="section">{kpi_focus}: actual vs 28-day baseline</div><div class="sub">The LLM does not calculate this chart; it is produced from deterministic data.</div>', unsafe_allow_html=True)
    meta=engine.KPI_META[kpi_focus]
    chart=d.set_index('date')[[meta['value_col'],meta['baseline_col']]].rename(columns={meta['value_col']:'Actual',meta['baseline_col']:'Baseline'})
    st.line_chart(chart,height=300)

    b1,b2,b3=st.columns(3)
    b1.metric("Movement", f"{details['delta']:+.1f} {meta['unit']}")
    b2.metric("Statistical signal", f"z={details['z_score']:.1f}")
    b3.metric("Business impact", f"{details['business_impact']:,.0f}")

    st.markdown('<div class="section">Investigation workspace</div><div class="sub">Multi-signal driver ranking uses observed movement, KPI relationship, timing and evidence. Support score is not a causal probability.</div>', unsafe_allow_html=True)
    t0=time.perf_counter(); drivers=engine.driver_analysis(sales,ops,events,region,kpi_focus,BASE,query or kpi_focus); driver_latency=(time.perf_counter()-t0)*1000
    left,right=st.columns([1.05,1.55])
    with left:
        for i,dr in enumerate(drivers,1):
            ev=engine.evidence(events,region,dr['Driver'],BASE,query or kpi_focus); conf=engine.confidence_for(dr,len(ev),BASE)
            status=driver_status(dr,conf,len(ev),len(drivers)>1 and drivers[0]['Support score']-drivers[1]['Support score']<7 and i<=2)
            badge='good' if conf>=65 else ('warn' if conf>=45 else 'bad')
            st.markdown(f'<div class="driver"><span class="score">{dr["Support score"]:.0f}/100</span><b>{i:02d} · {dr["Driver"]}</b><div class="tiny">Signal {dr["Signal"]:+.1f}% · KPI relationship {dr["Correlation with KPI"]:+.2f} · timing {dr["Temporal alignment"]:.0f}/100 · evidence {len(ev)} · confidence {conf:.0f}%</div><div class="tiny">Status: <span class="{badge}">{status}</span></div></div>',unsafe_allow_html=True)
        selected=st.selectbox("Inspect driver",[r['Driver'] for r in drivers])
    row=next(r for r in drivers if r['Driver']==selected); ev=engine.evidence(events,region,selected,BASE,query or kpi_focus); conf=engine.confidence_for(row,len(ev),BASE); status=driver_status(row,conf,len(ev))
    with right:
        st.markdown(f"### {selected}"); st.progress(conf/100,text=f"Confidence {conf:.0f}% · {status}")
        m1,m2,m3=st.columns(3); m1.metric("Driver signal",f"{row['Signal']:+.1f}%");m2.metric("KPI relationship",f"{row['Correlation with KPI']:+.2f}");m3.metric("Evidence",str(len(ev)))
        st.write(f"**Why it ranks:** contribution {row['Contribution %']:.0f}% of ranked support, with temporal alignment {row['Temporal alignment']:.0f}/100.")
        with st.expander("Confidence & score explanation", expanded=False):
            st.markdown(f"- **Confidence:** {conf:.0f}% based on the engine confidence function and retrieved evidence.")
            st.markdown(f"- **Support score:** {row['Support score']:.0f}/100 is a ranking signal, not a causal probability.")
            st.markdown(f"- **KPI relationship:** correlation = {row['Correlation with KPI']:+.2f}; correlation does not prove causation.")
            st.markdown(f"- **Evidence records:** {len(ev)}")
            st.markdown(f"- **Temporal alignment:** {row['Temporal alignment']:.0f}/100")
        if status == "Conflicting evidence — abstain": st.warning("The engine is intentionally abstaining because competing hypotheses are too close.")

    st.markdown('<div class="section">🔍 Calculation & Evidence Trace</div>', unsafe_allow_html=True)

    actual_value = float(x[meta['value_col']])
    baseline_value = float(x[meta['baseline_col']])
    xdelta = float(x[meta['delta_col']])
    relative_movement = xdelta / (abs(baseline_value) + 1e-9) * 100

    trace_steps = [
       ("1. KPI observation", f"{kpi_focus} actual value = {fmt_kpi_value(x, kpi_focus)}"),
        ("2. Baseline", f"28-day baseline = {baseline_value:,.2f}"),
        ("3. Absolute movement", f"Actual − Baseline = {actual_value:,.2f} − {baseline_value:,.2f} = {xdelta:+,.2f}"),
        ("4. Relative movement", f"(Actual − Baseline) / Baseline × 100 = {relative_movement:+.2f}%"),
        ("5. Statistical signal", f"Z-score = {details['z_score']:+.2f}"),
        ("6. Materiality", f"Business impact = {details['business_impact']:,.0f} · Material = {'YES' if mat[kpi_focus] else 'NO'}"),
        ("7. Driver movement", f"{selected} changed {row['Signal']:+.1f}% versus its comparison window"),
        ("8. KPI relationship", f"Correlation = {row['Correlation with KPI']:+.2f} (correlation is not proof of causation)"),
        ("9. Temporal alignment", f"{row['Temporal alignment']:.0f}/100"),
        ("10. Evidence", f"{len(ev)} relevant evidence record(s) retrieved"),
        ("11. Confidence / decision", f"{conf:.0f}% · Status: {status}"),
    ]

    for title, description in trace_steps:
        trace_html = f'<div class="trace-row"><b>{title}</b><br><span class="tiny">{description}</span></div>'
        st.markdown(trace_html, unsafe_allow_html=True)

    st.caption("Quantitative values are calculated by the deterministic analytics engine. The optional LLM is not the source of numerical truth.")

    st.markdown('<div class="section">Driver comparison</div><div class="sub">This shows why the top hypothesis beats the alternatives instead of presenting a single unexplained answer.</div>',unsafe_allow_html=True)
    st.bar_chart(pd.DataFrame({'Support score':[r['Support score'] for r in drivers]},index=[r['Driver'] for r in drivers]))

    st.markdown('<div class="section">Evidence ledger</div>',unsafe_allow_html=True)
    ec1, ec2 = st.columns(2)
    ec1.metric("Evidence records", len(ev))
    ec2.metric("Source types", ev['type'].nunique() if (not ev.empty and 'type' in ev.columns) else 0)
    if ev.empty: st.warning("No independent evidence was retrieved. The engine should not over-claim.")
    else:
        for _,e in ev.iterrows():
            dt=pd.Timestamp(e['date']).strftime('%Y-%m-%d'); st.markdown(f'<div class="evidence"><b>{e.get("source","Source")}</b> · {dt} · {e.get("type","evidence")}<div style="margin:.3rem 0">{e.get("text","")}</div><span class="tiny">Retrieval score: {e.get("retrieval_score",0):.0f}/100 · lineage: {e.get("source","source")}</span></div>',unsafe_allow_html=True)

    st.markdown('<div class="section">Product / segment impact</div>',unsafe_allow_html=True)
    impact=engine.product_impact(sales,region,kpi_focus).reset_index().rename(columns={'product':'Product'})
    st.dataframe(impact.round(2),use_container_width=True,hide_index=True)

    st.markdown('<div class="section">Source reconciliation</div><div class="sub">The engine compares overlapping finance/operations metrics and can reduce trust when sources conflict.</div>',unsafe_allow_html=True)
    recon=engine.reconcile_sources(sales,ops,region); st.dataframe(recon.round(2),use_container_width=True,hide_index=True)
    if (recon['Status']=='Conflict').any(): st.warning("Source conflict detected. Confidence should be treated cautiously until the source mismatch is resolved.")

    st.markdown('<div class="section">Recommended next action</div>',unsafe_allow_html=True)
    lever,action,impact_text,owner=engine.action_for(selected); ac=st.columns(5)
    vals=[f"{selected}\n\n{lever}",action,impact_text,owner,f"{conf:.0f}%"]
    for c,lab,val in zip(ac,['Driver / lever','Action','Expected impact','Owner','Confidence'],vals): c.markdown(f'<div class="card"><div class="tiny"><b>{lab}</b></div><div style="margin-top:.4rem">{val}</div></div>',unsafe_allow_html=True)
    st.info("**Monitoring plan:** monitor the selected KPI and driver for 7 days; reopen if the movement persists, reverses, or new evidence arrives.")

    st.markdown('<div class="section">Human decision & learning</div>',unsafe_allow_html=True)
    decision=st.radio("Decision",['Approve','Reject','Unresolved'],horizontal=True,key='decision_main')
    v1,v2,v3=st.columns([1,1,3])
    if v1.button('👍 Correct',key='correct_main'): st.session_state['vote']='Correct'
    if v2.button('👎 Incorrect',key='incorrect_main'): st.session_state['vote']='Incorrect'
    feedback=st.text_input("Feedback",placeholder="What was correct, missing or misleading?",key='feedback_main')
    if st.button("Save decision + feedback",type='primary',key='save_feedback'):
        engine.log_feedback(BASE,{'timestamp':pd.Timestamp.now().isoformat(),'persona':persona,'region':region,'scenario':scenario,'kpi':kpi_focus,'driver':selected,'decision':decision,'vote':st.session_state.get('vote',''),'feedback':feedback})
        st.success("Saved. Future confidence for this driver can use the historical reliability signal.")
    hist=engine.feedback_history(BASE)
    if len(hist):
        votes=hist.get('vote',pd.Series(dtype=str)).fillna(''); rated=votes.isin(['Correct','Incorrect']); acc=(votes=='Correct').sum()/max(rated.sum(),1)
        st.caption(f"Feedback calibration: {acc*100:.0f}% correct among rated decisions ({rated.sum()} rated).")

elif scenario == "Low-confidence / competing hypotheses":
    st.markdown('<div class="section">Abstention & ambiguity</div><div class="sub">Computed from live KPI-specific driver scores; no fixed top-driver claim is inserted.</div>',unsafe_allow_html=True)
    amb_region,amb_rows=engine.find_ambiguous_region(sales,ops,events,REGIONS,kpi_focus,BASE)
    top,second=amb_rows[0],amb_rows[1]; gap=top['Support score']-second['Support score']
    st.warning(f"For **{amb_region} / {kpi_focus}**, the top two hypotheses are only {gap:.1f} points apart. The system prefers abstention over false certainty.")
    table=[]
    for r in amb_rows:
        ev=engine.evidence(events,amb_region,r['Driver'],BASE,kpi_focus); c=engine.confidence_for(r,len(ev),BASE)
        table.append({'Hypothesis':r['Driver'],'Support':r['Support score'],'Evidence':len(ev),'Confidence':c,'Status':engine.causal_status(c,len(ev),r['Temporal alignment'],r['Correlation with KPI'],True)})
    st.dataframe(pd.DataFrame(table).round(1),use_container_width=True,hide_index=True)
    st.info("Next diagnostic step: request additional independent evidence, validate source conflicts and/or run a controlled comparison before taking a corrective action.")

else:
    st.markdown('<div class="section">Sparse-history safety</div>',unsafe_allow_html=True)
    st.warning("Simulated new-KPI scenario: the bundled dataset has full history, so this screen demonstrates how the engine behaves with only 21 days available.")
    peer=engine.sparse_peer_analysis(sales,region,kpi_focus,21,28)
    c1,c2,c3,c4=st.columns(4);c1.metric('History available','21 days');c2.metric('Required','28+ days');c3.metric('Peer median',f"{peer['peer_median']:.2f}");c4.metric('Confidence',f"{peer['confidence']:.0f}%")
    st.markdown("### Peer comparison fallback")
    st.write(f"Simulated new KPI value for **{region}** = **{peer['own_value']:.2f}**; peer-region median = **{peer['peer_median']:.2f}**; gap = **{peer['peer_gap_pct']:+.1f}%**.")
    st.info("Decision status: monitor / request more history. The engine does not fabricate a seasonal baseline when history is sparse.")

# Governance and health
st.markdown('<div class="section">Governance & semantic contract</div>',unsafe_allow_html=True)
g1,g2,g3,g4=st.columns(4);g1.metric('Problem track','3');g2.metric('Persona',persona);g3.metric('Access scope','Aggregated' if persona=='Commercial Manager' else 'Detailed');g4.metric('Audit trail','Enabled')
with st.expander('View KPI semantic contract'):
    st.json(semantic['kpis'][kpi_focus])

st.markdown('<div class="section">Data-source health & lineage</div>',unsafe_allow_html=True)
st.dataframe(engine.source_health(BASE,semantic),use_container_width=True,hide_index=True)
docs=engine.load_documents(BASE)
st.caption(f"Unstructured document sources loaded: {len(docs)}")
if docs and show_details:
    st.dataframe(pd.DataFrame([{'File':d['file'],'Modified':d['modified'],'Characters':len(d['text'])} for d in docs]),use_container_width=True,hide_index=True)

st.markdown('<div class="section">Runtime telemetry</div>',unsafe_allow_html=True)
hist=engine.feedback_history(BASE); tel=nl_result['telemetry'] if nl_result else {}
t1,t2,t3,t4,t5=st.columns(5);t1.metric('Analytical latency',f"{driver_latency:.0f} ms" if 'driver_latency' in locals() else 'n/a');t2.metric('LLM calls','1' if tel.get('llm_used') else '0');t3.metric('Token usage',str(tel.get('tokens',0)));t4.metric('Est. LLM cost',f"${tel.get('est_cost',0):.4f}");t5.metric('Feedback records',str(len(hist)))
st.caption("Boundary: deterministic analytics produce quantitative truth; document retrieval supplies evidence; the optional LLM only parses intent and/or rewrites already-computed facts.")
st.info("🔒 Trust & computation: KPI values, baselines, movements, materiality and driver analytics are produced by the deterministic Python analytics layer. The optional LLM is used only for intent/narrative tasks.")
st.markdown('<div class="footer">BusinessIntelligence.ai · Evidence-grounded KPI intelligence · Prototype data is synthetic</div>',unsafe_allow_html=True)
