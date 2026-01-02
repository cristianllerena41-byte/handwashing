# app.py
# Semmelweis Clinic 1 vs Clinic 2 — Yearly Dashboard (reads CSV from GitHub)

import re
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Semmelweis Clinics Dashboard", layout="wide")

st.title("Semmelweis Clinic 1 vs Clinic 2 — Mortality Dashboard (Yearly)")
st.write(
    "This dashboard compares yearly maternal deaths and death rates between Clinic 1 and Clinic 2. "
    "Data is loaded automatically from GitHub."
)

# -------------------------
# GitHub CSV URL (file must exist in your repo root)
# -------------------------
GITHUB_CSV_URL = (
    "https://raw.githubusercontent.com/"
    "cristianllerena41-byte/handwashing/main/"
    "semmelweis_yearly.csv"
)

@st.cache_data
def load_data_from_github(url: str) -> pd.DataFrame:
    df = pd.read_csv(url)

    # Expected CSV headers (must match exactly)
    rename_map = {
        "Year": "year_label",
        "Births in Clinic 1": "births_clinic1",
        "Deaths in Clinic 1": "deaths_clinic1",
        "Births in Clinic 2": "births_clinic2",
        "Deaths in Clinic 2": "deaths_clinic2",
    }

    missing = [c for c in rename_map.keys() if c not in df.columns]
    if missing:
        raise ValueError(
            "Missing columns in CSV: "
            + ", ".join(missing)
            + ". Make sure your CSV headers match exactly."
        )

    df = df.rename(columns=rename_map)

    # Extract numeric year for sorting/filtering (handles '1847 (Before ...)' etc.)
    def extract_year(x):
        m = re.search(r"\d{4}", str(x))
        return int(m.group(0)) if m else None

    df["year"] = df["year_label"].apply(extract_year)
    df = df.dropna(subset=["year"]).sort_values("year")

    # Ensure numeric births/deaths
    num_cols = ["births_clinic1", "deaths_clinic1", "births_clinic2", "deaths_clinic2"]
    for c in num_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=num_cols)

    # Compute death rates
    df["death_rate_c1"] = df["deaths_clinic1"] / df["births_clinic1"]
    df["death_rate_c2"] = df["deaths_clinic2"] / df["births_clinic2"]

    return df

# -------------------------
# Load data
# -------------------------
try:
    df = load_data_from_github(GITHUB_CSV_URL)
except Exception as e:
    st.error(
        "Could not load the CSV from GitHub.\n\n"
        "Checklist:\n"
        "• You uploaded `semmelweis_yearly.csv` to the repo root\n"
        "• The filename matches exactly\n"
        "• The CSV headers match exactly\n\n"
        f"Details: {e}"
    )
    st.stop()

# -------------------------
# Sidebar filter
# -------------------------
st.sidebar.header("Filters")
min_year = int(df["year"].min())
max_year = int(df["year"].max())

start_year, end_year = st.sidebar.slider(
    "Year range",
    min_value=min_year,
    max_value=max_year,
    value=(min_year, max_year),
)

filtered = df[(df["year"] >= start_year) & (df["year"] <= end_year)].copy()

# -------------------------
# KPIs
# -------------------------
def safe_rate(deaths, births):
    return (deaths / births) if births and births != 0 else 0.0

births_c1 = float(filtered["births_clinic1"].sum())
deaths_c1 = float(filtered["deaths_clinic1"].sum())
rate_c1 = safe_rate(deaths_c1, births_c1)

births_c2 = float(filtered["births_clinic2"].sum())
deaths_c2 = float(filtered["deaths_clinic2"].sum())
rate_c2 = safe_rate(deaths_c2, births_c2)

st.subheader("Overall Summary")

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Clinic 1 — Total Births", f"{int(births_c1):,}")
c2.metric("Clinic 1 — Total Deaths", f"{int(deaths_c1):,}")
c3.metric("Clinic 1 — Death Rate", f"{rate_c1*100:.2f}%")
c4.metric("Clinic 2 — Total Births", f"{int(births_c2):,}")
c5.metric("Clinic 2 — Total Deaths", f"{int(deaths_c2):,}")
c6.metric("Clinic 2 — Death Rate", f"{rate_c2*100:.2f}%")

st.divider()

# -------------------------
# Charts
# -------------------------
left, right = st.columns(2)

# Line chart: death rates
rate_df = filtered[["year", "year_label", "death_rate_c1", "death_rate_c2"]].melt(
    id_vars=["year", "year_label"],
    var_name="clinic",
    value_name="death_rate",
)
rate_df["clinic"] = rate_df["clinic"].map(
    {"death_rate_c1": "Clinic 1", "death_rate_c2": "Clinic 2"}
)

fig_line = px.line(
    rate_df.sort_values("year"),
    x="year_label",
    y="death_rate",
    color="clinic",
    markers=True,
    labels={"year_label": "Year", "death_rate": "Death Rate", "clinic": "Clinic"},
    title="Yearly Death Rates (Deaths / Births)",
)
fig_line.update_yaxes(tickformat=".1%")
left.plotly_chart(fig_line, use_container_width=True)

# Bar chart: deaths
deaths_df = filtered[["year", "year_label", "deaths_clinic1", "deaths_clinic2"]].melt(
    id_vars=["year", "year_label"],
    var_name="clinic",
    value_name="deaths",
)
deaths_df["clinic"] = deaths_df["clinic"].map(
    {"deaths_clinic1": "Clinic 1", "deaths_clinic2": "Clinic 2"}
)

fig_bar = px.bar(
    deaths_df.sort_values("year"),
    x="year_label",
    y="deaths",
    color="clinic",
    barmode="group",
    labels={"year_label": "Year", "deaths": "Deaths", "clinic": "Clinic"},
    title="Yearly Death Counts",
)
right.plotly_chart(fig_bar, use_container_width=True)

with st.expander("Show data table"):
    st.dataframe(filtered, use_container_width=True)

st.caption("Make sure your CSV headers match exactly: Year, Births in Clinic 1, Deaths in Clinic 1, Births in Clinic 2, Deaths in Clinic 2.")
