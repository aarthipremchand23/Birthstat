import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------
st.set_page_config(page_title="2025 U.S. Natality Dashboard", layout="wide")

# ---------------------------------------------------------
# Data Loading & Preparation
# ---------------------------------------------------------
@st.cache_data
def load_data():
    # Load dataset
    df = pd.read_csv("Week-3-Video-Lab-2-Provisional-Natality-2025-CDC.csv")
    # Sort chronologically
    df = df.sort_values(by=['state_of_residence', 'month_code'])
    return df

df_raw = load_data()

# ---------------------------------------------------------
# Sidebar Filters
# ---------------------------------------------------------
st.sidebar.header("Dashboard Filters")

# State Filter
states = df_raw['state_of_residence'].unique().tolist()
selected_states = st.sidebar.multiselect("Select State(s)", options=states, default=states)

# Month Filter
min_month, max_month = int(df_raw['month_code'].min()), int(df_raw['month_code'].max())
selected_months = st.sidebar.slider("Select Month Range", min_value=min_month, max_value=max_month, value=(min_month, max_month))

# Sex Filter
sexes = df_raw['sex_of_infant'].unique().tolist()
selected_sex = st.sidebar.multiselect("Select Sex of Infant", options=sexes, default=sexes)

# ---------------------------------------------------------
# Filter the Data
# ---------------------------------------------------------
df_filtered = df_raw[
    (df_raw['state_of_residence'].isin(selected_states)) &
    (df_raw['month_code'] >= selected_months[0]) &
    (df_raw['month_code'] <= selected_months[1]) &
    (df_raw['sex_of_infant'].isin(selected_sex))
]

# ---------------------------------------------------------
# Main Dashboard Body
# ---------------------------------------------------------
st.title("🏥 2025 U.S. Provisional Natality Dynamics")
st.markdown("Decision-support dashboard for Public Health Planning Office.")

if df_filtered.empty:
    st.warning("No data available for the selected filters. Please adjust your criteria.")
else:
    # --- KPIs ---
    total_births = df_filtered['births'].sum()
    avg_monthly = total_births / df_filtered['month_code'].nunique()
    top_state = df_filtered.groupby('state_of_residence')['births'].sum().idxmax()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Births", f"{total_births:,.0f}")
    col2.metric("Avg. Monthly Births", f"{avg_monthly:,.0f}")
    col3.metric("Highest Volume State", top_state)

    st.divider()

    # --- Visualizations ---
    colA, colB = st.columns(2)

    with colA:
        st.subheader("Monthly Birth Dynamics")
        # Aggregate by month
        monthly_trend = df_filtered.groupby(['month_code', 'month'])['births'].sum().reset_index().sort_values('month_code')
        fig_trend = px.line(monthly_trend, x='month', y='births', markers=True, 
                            title="Total Births by Month",
                            labels={'month': 'Month', 'births': 'Number of Births'})
        st.plotly_chart(fig_trend, use_container_width=True)

    with colB:
        st.subheader("Sex/Gender Distribution")
        # Aggregate by month and sex
        sex_trend = df_filtered.groupby(['month_code', 'month', 'sex_of_infant'])['births'].sum().reset_index().sort_values('month_code')
        fig_sex = px.bar(sex_trend, x='month', y='births', color='sex_of_infant', barmode='group',
                         title="Monthly Births by Sex",
                         labels={'month': 'Month', 'births': 'Number of Births', 'sex_of_infant': 'Sex'})
        st.plotly_chart(fig_sex, use_container_width=True)

    st.subheader("State Volume Comparisons")
    # Aggregate by state
    state_vol = df_filtered.groupby('state_of_residence')['births'].sum().reset_index().sort_values('births', ascending=False)
    # Take top 15 if there are too many for a clean chart
    fig_state = px.bar(state_vol.head(15), x='births', y='state_of_residence', orientation='h',
                       title="Top 15 States by Total Births (Filtered)",
                       labels={'state_of_residence': 'State', 'births': 'Number of Births'})
    fig_state.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_state, use_container_width=True)
    
    # --- Planning Signals Section ---
    st.divider()
    st.subheader("🚨 Early Planning Signals")
    st.info("**Hospital Capacity:** Expect peak maternity ward demand during July and August based on annual volume highs.")
    st.info("**Vaccination Planning:** The late-summer birth surge will drive a corresponding spike in 6-month vaccination demands precisely during the January/February respiratory illness season.")
