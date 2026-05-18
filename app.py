from pathlib import Path

import pandas as pd
import streamlit as st

from main import (
    KPI_WEIGHTS,
    PlaDailyObservation,
    MarketSnapshot,
    calculate_kpi1_pla_air_naval_pressure,
    calculate_kpi7_market_stress,
    manual_kpi,
    calculate_tcri,
)


DATA_DIR = Path("data")

KPI_FILES = {
    "PLA_Air_Naval_Pressure": "kpi1_data.csv",
    "Exercise_Escalation": "kpi2_data.csv",
    "Maritime_Blockade_Shipping": "kpi3_data.csv",
    "China_Rhetoric_Legal": "kpi4_data.csv",
    "US_Allies_Signal": "kpi5_data.csv",
    "Cyber_Infrastructure": "kpi6_data.csv",
    "Market_Stress": "kpi7_data.csv",
    "Semiconductor_Supply_Chain": "kpi8_data.csv",
    "China_Domestic_Mobilization": "kpi9_data.csv",
}


def read_csv(filename: str) -> pd.DataFrame:
    path = DATA_DIR / filename
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def get_kpi1():
    df = read_csv("kpi1_data.csv")

    if df.empty:
        return manual_kpi("PLA_Air_Naval_Pressure", 0)

    observations = [
        PlaDailyObservation(
            pla_aircraft=row["pla_aircraft"],
            median_line_crossings=row["median_line_crossings"],
            plan_ships=row["plan_ships"],
            official_ships=row["official_ships"],
        )
        for _, row in df.iterrows()
    ]

    return calculate_kpi1_pla_air_naval_pressure(observations)


def get_kpi7():
    df = read_csv("kpi7_data.csv")

    if df.empty:
        return manual_kpi("Market_Stress", 0)

    latest = df.iloc[-1]

    snapshot = MarketSnapshot(
        tsm_5d_return=latest.get("tsm_5d_return", 0),
        soxx_vs_spy_5d=latest.get("soxx_vs_spy_5d", 0),
        twd_5d_return=latest.get("twd_5d_return", 0),
        vix_change_5d=latest.get("vix_change_5d", 0),
        taiwan_cds_change_score=latest.get("taiwan_cds_change_score", None),
    )

    return calculate_kpi7_market_stress(snapshot)


def get_manual_kpi(kpi_name: str, filename: str):
    df = read_csv(filename)

    if df.empty:
        return manual_kpi(kpi_name, 0)

    latest = df.iloc[-1]

    if "value" in df.columns:
        value = latest["value"]
    elif "score" in df.columns:
        value = latest["score"]
    else:
        value = 0

    return manual_kpi(kpi_name, value)


def build_dashboard_result():
    kpis = {
        "PLA_Air_Naval_Pressure": get_kpi1(),
        "Market_Stress": get_kpi7(),
    }

    for kpi_name, filename in KPI_FILES.items():
        if kpi_name in kpis:
            continue

        kpis[kpi_name] = get_manual_kpi(kpi_name, filename)

    return calculate_tcri(kpis)


st.set_page_config(
    page_title="Taiwan Risk Dashboard",
    layout="wide",
)

st.title("Taiwan Risk Dashboard")

result = build_dashboard_result()

col1, col2, col3 = st.columns(3)

col1.metric("Overall Score", result.score)
col2.metric("Risk Bucket", result.bucket.value)
col3.metric("Red Alert", "YES" if result.red_alert else "NO")

st.divider()

st.subheader("KPI values")

rows = []

for kpi in result.kpis.values():
    rows.append(
        {
            "KPI": kpi.name,
            "Value": kpi.value,
            "Weight": kpi.weight,
            "Contribution": kpi.contribution,
        }
    )

kpi_df = pd.DataFrame(rows)

st.dataframe(kpi_df, use_container_width=True)

st.bar_chart(kpi_df.set_index("KPI")["Value"])

st.divider()

st.subheader("CSV status")

for kpi_name, filename in KPI_FILES.items():
    path = DATA_DIR / filename
    st.write(f"`{filename}` — {'OK' if path.exists() else 'missing'}")