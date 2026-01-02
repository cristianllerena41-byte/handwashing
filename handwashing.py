# app.py
# Streamlit dashboard: Semmelweis Clinic 1 vs Clinic 2
#
# Expected CSV columns:
#   month, births_clinic1, deaths_clinic1, births_clinic2, deaths_clinic2
#
# Run:
#   pip install streamlit pandas plotly
#   streamlit run app.py

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Semmelweis Clinics Dashboard", layout="wide")

st.title("Semmelweis Clinic 1 vs Clinic 2 — Mortality Dashboard")
st.write(
    "This dashboard compares monthly maternal deaths and death rates between Clinic 1 and Clinic 2. "
    "Use the date range to explore how outcomes differed across time."
)

# -------------------------
# Sidebar: data input
# -------------------------
st.sidebar.header("Data")

uploaded = st.sidebar.file_uploader("Upload CSV", type=["csv"])
csv_path = st.sidebar.text_input("...or enter a local CSV path", value="semmelweis_clinics_monthly.csv")

@st.cache_data
def load_data(file_obj=None, path=None):
    if file_obj is not None:
        df_local = pd.read_csv(file_obj)
    else:
        df_local = pd.read_csv(path)

    # Parse/sort dates
    df_local["month"] = pd.to_datetime(df_local["month"], errors="coerce")
    df_local = df_local.dropna(subset=["month"]).sort_values("month")

    # Ensure numeric
    num_cols = ["births_clinic1", "deaths_clinic1", "births_clinic2", "deaths_clinic2"]
    for c in num_cols:
        df_local[c] = pd.to_numeric(df_local[c], errors="coerce")
    df_local = df_local.dropna(subset=num_cols)

    # Compute death rates
    df_local["death_rate_c1"] = df_local["deaths_clinic1"] / df_local["births_clinic1"]
    df_local["death_rate_c2"] = df_local["deaths_clinic2"] / df_local["births_clinic2"]
    return df_local

try:
    df = load_data(uploaded, csv_path if uploaded is None else None)
except Exception as e:
    st.error(
        "Could not load the CSV. Make sure it exists and has columns:\n"
        "month, births_clinic1, deaths_clinic1, births_clinic2, deaths_clinic2"
    )
    st.stop()

# -------------------------
# Date range filter
# -------------------------
min_date = df["month"].min().date()
max_date = df["month"].max().date()

st.sidebar.header("Filters")
start_date, end_date = st.sidebar.date_input(
    "Date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

start_dt = pd.to_datetime(start_date)
end_dt = pd.to_datetime(end_date)

filtered = df[(df["month"] >= start_dt) & (df["month"] <= end_dt)].copy()

# -------------------------
# KPIs
# -------------------------
def safe_rate(deaths, births):
    return (deaths / births) if births and births != 0 else 0.0

births_c1 = int(filtered["births_clinic1"].sum())
deaths_c1 = int(filtered["deaths_clinic1"].sum())
rate_c1 = safe_rate(deaths_c1, births_c1)

births_c2 = int(filtered["births_clinic2"].sum())
deaths_c2 = int(filtered["deaths_clinic2"].sum())
rate_c2 = safe_rate(deaths_c2, births_c2)

st.subheader("Overall Summary")

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Clinic 1 — Total Births", f"{births_c1:,}")
c2.metric("Clinic 1 — Total Deaths", f"{deaths_c1:,}")
c3.metric("Clinic 1 — Death Rate", f"{rate_c1*100:.2f}%")
c4.metric("Clinic 2 — Total Births", f"{births_c2:,}")
c5.metric("Clinic 2 — Total Deaths", f"{deaths_c2:,}")
c6.metric("Clinic 2 — Death Rate", f"{rate_c2*100:.2f}%")

st.divider()

# -------------------------
# Charts
# -------------------------
left, right = st.columns(2)

# Line chart: death rates
rate_df = filtered[["month", "death_rate_c1", "death_rate_c2"]].melt(
    id_vars="month",
    var_name="clinic",
    value_name="death_rate"
)
rate_df["clinic"] = rate_df["clinic"].map({"death_rate_c1": "Clinic 1", "death_rate_c2": "Clinic 2"})

fig_line = px.line(
    rate_df,
    x="month",
    y="death_rate",
    color="clinic",
    markers=True,
    labels={"month": "Month", "death_rate": "Death Rate", "clinic": "Clinic"},
)
fig_line.update_yaxes(tickformat=".1%")
fig_line.update_layout(margin=dict(l=10, r=10, t=40, b=10), title="Monthly Death Rates (Deaths / Births)")

left.plotly_chart(fig_line, use_container_width=True)

# Bar chart: deaths
deaths_df = filtered[["month", "deaths_clinic1", "deaths_clinic2"]].melt(
    id_vars="month",
    var_name="clinic",
    value_name="deaths"
)
deaths_df["clinic"] = deaths_df["clinic"].map({"deaths_clinic1": "Clinic 1", "deaths_clinic2": "Clinic 2"})

fig_bar = px.bar(
    deaths_df,
    x="month",
    y="deaths",
    color="clinic",
    barmode="group",
    labels={"month": "Month", "deaths": "Deaths", "clinic": "Clinic"},
)
fig_bar.update_layout(margin=dict(l=10, r=10, t=40, b=10), title="Monthly Death Counts")

right.plotly_chart(fig_bar, use_container_width=True)

# -------------------------
# Optional: show data table
# -------------------------
with st.expander("Show filtered data"):
    st.dataframe(filtered, use_container_width=True)

st.caption("Tip: If you know the intervention date (e.g., handwashing), you can add a vertical line annotation to both charts.")
