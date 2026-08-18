import streamlit as st
import pandas as pd
import plotly.express as px
import os
import glob

# ---------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="U.S. Natality Dynamics Dashboard",
    page_icon="🏥",
    layout="wide"
)

# ---------------------------------------------------------
# Helper Functions for Robust Field Matching
# ---------------------------------------------------------
def _normalize_colname(name: str) -> str:
    """Normalize string by trimming, lowercasing, and replacing spaces with underscores."""
    return str(name).strip().lower().replace(" ", "_")

def _canonical_key(name: str) -> str:
    """Remove non-alphanumerics to support flexible schema matching."""
    s = _normalize_colname(name)
    return "".join(ch for ch in s if ch.isalnum())

def _match_logical_fields(columns_norm):
    """
    Dynamically maps logical required fields to actual dataframe column names
    using exact matches, canonical keys, and standard aliases.
    """
    logical_required = [
        "state_of_residence",
        "month",
        "month_code",
        "year_code",
        "sex_of_infant",
        "births",
    ]

    cols_set = set(columns_norm)
    cols_canon_map = {c: _canonical_key(c) for c in columns_norm}
    canon_to_cols = {}
    for c, ck in cols_canon_map.items():
        canon_to_cols.setdefault(ck, []).append(c)

    alias_candidates = {
        "state_of_residence": ["state_of_residence", "state", "state_residence", "residence_state", "jurisdiction"],
        "month": ["month", "month_of_birth", "birth_month", "reporting_month"],
        "month_code": ["month_code", "monthcode", "month_cd", "month_cd_code", "monthnumber", "month_num", "monthnumbercode"],
        "year_code": ["year_code", "yearcode", "year_cd", "year", "reporting_year"],
        "sex_of_infant": ["sex_of_infant", "sex", "infant_sex", "gender", "infant_gender", "sex_of_child"],
        "births": ["births", "birth", "birth_count", "count", "number_of_births", "num_births", "total_births"],
    }

    matched = {}
    for logical in logical_required:
        # 1. Exact normalized match
        if logical in cols_set:
            matched[logical] = logical
            continue

        # 2. Canonical match
        target_canon = _canonical_key(logical)
        if target_canon in canon_to_cols and len(canon_to_cols[target_canon]) >= 1:
            candidates = sorted(canon_to_cols[target_canon], key=lambda x: (len(x), x))
            matched[logical] = candidates[0]
            continue

        # 3. Alias dictionary matching
        found = None
        for alias in alias_candidates.get(logical, []):
            alias_norm = _normalize_colname(alias)
            if alias_norm in cols_set:
                found = alias_norm
                break
            alias_canon = _canonical_key(alias_norm)
            if alias_canon in canon_to_cols:
                candidates = sorted(canon_to_cols[alias_canon], key=lambda x: (len(x), x))
                found = candidates[0]
                break
        if found is not None:
            matched[logical] = found

    return matched

# ---------------------------------------------------------
# Data Ingestion & Preprocessing
# ---------------------------------------------------------
@st.cache_data(show_spinner=False)
def process_data(file_source):
    """Loads, cleans, validates, and standardizes any CDC Natality CSV dataset."""
    try:
        df = pd.read_csv(file_source)
    except Exception as e:
        return None, f"Failed to read CSV file: {str(e)}"

    # Normalize column names
    df = df.copy()
    df.columns = [_normalize_colname(c) for c in df.columns]

    # Validate logical schema
    field_map = _match_logical_fields(list(df.columns))
    required_fields = ["state_of_residence", "month", "sex_of_infant", "births"]
    
    missing_fields = [f for f in required_fields if f not in field_map]
    if missing_fields:
        return None, f"Missing required columns in dataset: {', '.join(missing_fields)}"

    # Rename matched columns
    rename_dict = {field_map[k]: k for k in field_map if k in required_fields or k in ["month_code", "year_code"]}
    df = df.rename(columns=rename_dict)

    # Clean births column
    df["births"] = pd.to_numeric(df["births"], errors="coerce")
    df = df.dropna(subset=["births"])

    # If month_code is missing, synthesize from month name
    if "month_code" not in df.columns:
        month_order = ["january", "february", "march", "april", "may", "june", 
                       "july", "august", "september", "october", "november", "december"]
        month_map = {m: i + 1 for i, m in enumerate(month_order)}
        df["month_code"] = df["month"].astype(str).str.strip().str.lower().map(month_map).fillna(0).astype(int)

    # Coerce text columns
    for col in ["state_of_residence", "month", "sex_of_infant"]:
        df[col] = df[col].astype(str).str.strip()

    # Sort chronologically and by state
    df = df.sort_values(by=["state_of_residence", "month_code"])
    return df, None

# ---------------------------------------------------------
# Auto-Detect Local Dataset (No UI)
# ---------------------------------------------------------
csv_files = glob.glob("*.csv")

if not csv_files:
    st.error("⚠️ No CSV files found in the application directory. Please ensure the dataset is placed in the same folder as this script.")
    st.stop()

# Automatically load the first CSV found
file_to_load = csv_files[0]
df_raw, error_msg = process_data(file_to_load)

if error_msg:
    st.error(error_msg)
    st.stop()

# ---------------------------------------------------------
# Sidebar: Dynamic Filters with "All" Option
# ---------------------------------------------------------
st.sidebar.header("🔍 Filters")

def _build_options(series: pd.Series):
    vals = sorted([v for v in series.dropna().unique().tolist() if str(v).strip() != ""])
    return ["All"] + vals

month_options = _build_options(df_raw["month"])
state_options = _build_options(df_raw["state_of_residence"])
sex_options = _build_options(df_raw["sex_of_infant"])

selected_months = st.sidebar.multiselect("Month(s)", options=month_options, default=["All"])
selected_states = st.sidebar.multiselect("State(s)", options=state_options, default=["All"])
selected_sex = st.sidebar.multiselect("Sex of Infant", options=sex_options, default=["All"])

# Apply Filters
df_filtered = df_raw.copy()

if "All" not in selected_months:
    df_filtered = df_filtered[df_filtered["month"].isin(selected_months)]

if "All" not in selected_states:
    df_filtered = df_filtered[df_filtered["state_of_residence"].isin(selected_states)]

if "All" not in selected_sex:
    df_filtered = df_filtered[df_filtered["sex_of_infant"].isin(selected_sex)]

# ---------------------------------------------------------
# Dashboard Main Layout
# ---------------------------------------------------------
st.title("🏥 Provisional Natality Dynamics Dashboard")
st.markdown("Decision-support interface for public health capacity, seasonality analysis, and operational planning.")

if df_filtered.empty:
    st.warning("⚠️ No data matches the selected filters. Please expand your filter selections.")
    st.stop()

# --- Key Performance Indicators (KPIs) ---
total_births = df_filtered["births"].sum()
unique_months = max(1, df_filtered["month"].nunique())
avg_monthly = total_births / unique_months

state_totals = df_filtered.groupby("state_of_residence")["births"].sum()
top_state = state_totals.idxmax() if not state_totals.empty else "N/A"
top_state_val = state_totals.max() if not state_totals.empty else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Births (Filtered)", f"{int(total_births):,}")
col2.metric("Avg. Monthly Births", f"{int(avg_monthly):,}")
col3.metric("Leading State", f"{top_state}")
col4.metric("Leading State Volume", f"{int(top_state_val):,}")

st.divider()

# --- Visualizations ---
colA, colB = st.columns(2)

with colA:
    st.subheader("📈 Monthly Birth Trajectory")
    monthly_trend = (
        df_filtered.groupby(["month_code", "month"], as_index=False)["births"]
        .sum()
        .sort_values("month_code")
    )
    fig_trend = px.line(
        monthly_trend,
        x="month",
        y="births",
        markers=True,
        title="Total Births Across Selected Months",
        labels={"month": "Month", "births": "Birth Count"}
    )
    fig_trend.update_layout(plot_bgcolor="white", paper_bgcolor="white", margin=dict(l=20, r=20, t=50, b=30))
    st.plotly_chart(fig_trend, use_container_width=True)

with colB:
    st.subheader("⚖️ Sex / Gender Distribution")
    sex_trend = (
        df_filtered.groupby(["month_code", "month", "sex_of_infant"], as_index=False)["births"]
        .sum()
        .sort_values("month_code")
    )
    fig_sex = px.bar(
        sex_trend,
        x="month",
        y="births",
        color="sex_of_infant",
        barmode="group",
        title="Monthly Births by Sex",
        labels={"month": "Month", "births": "Birth Count", "sex_of_infant": "Sex"}
    )
    fig_sex.update_layout(plot_bgcolor="white", paper_bgcolor="white", margin=dict(l=20, r=20, t=50, b=30))
    st.plotly_chart(fig_sex, use_container_width=True)

st.subheader("🗺️ Birth Volume by State")
state_vol = (
    df_filtered.groupby("state_of_residence", as_index=False)["births"]
    .sum()
    .sort_values("births", ascending=False)
)
# Top 15 states or all if filtered list is short
display_states = state_vol.head(15) if len(state_vol) > 15 else state_vol
fig_state = px.bar(
    display_states,
    x="births",
    y="state_of_residence",
    orientation="h",
    title="State Volume Comparison (Top Jurisdictions)",
    labels={"state_of_residence": "State", "births": "Total Births"}
)
fig_state.update_layout(
    yaxis={"categoryorder": "total ascending"},
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin=dict(l=20, r=20, t=50, b=30)
)
st.plotly_chart(fig_state, use_container_width=True)

# --- Planning Signals Section ---
st.divider()
st.subheader("🚨 Descriptive Public Health Planning Signals")
c1, c2 = st.columns(2)
with c1:
    st.info(
        "**Hospital Bed & Staffing Allocation:** Mid-to-late summer months (July–August) consistently exhibit elevated birth volumes nationally. Ensure perinatal staffing levels and ward capacities are prepared during Q3."
    )
with c2:
    st.info(
        "**Pediatric Vaccine Milestone Alignment:** Summer birth cohorts achieve their 6-month immunization schedules during the winter respiratory season (January–February), necessitating proactive clinic vaccine inventory management."
    )

# --- Filtered Data Table Display ---
st.divider()
st.subheader("📋 Filtered Records Data Table")
display_cols = [c for c in ["state_of_residence", "month", "month_code", "year_code", "sex_of_infant", "births"] if c in df_filtered.columns]
df_table = df_filtered[display_cols].copy()

st.dataframe(df_table.reset_index(drop=True), use_container_width=True)
