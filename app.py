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

def build_kpi1_detail_table(kpi1_df: pd.DataFrame) -> None:
    if kpi1_df.empty:
        st.warning("No KPI1 data available.")
        return

    latest = kpi1_df.iloc[-1]

    total = (
        int(latest.get("pla_aircraft", 0))
        + int(latest.get("plan_ships", 0))
        + int(latest.get("official_ships", 0))
    )

    detail_df = pd.DataFrame(
        [
            {"Metric": "Date", "Value": latest.get("date", "N/A")},
            {"Metric": "PLA aircraft", "Value": int(latest.get("pla_aircraft", 0))},
            {"Metric": "Median line crossings", "Value": int(latest.get("median_line_crossings", 0))},
            {"Metric": "PLAN ships", "Value": int(latest.get("plan_ships", 0))},
            {"Metric": "Official ships", "Value": int(latest.get("official_ships", 0))},
            {"Metric": "Aircraft + ships", "Value": total},
        ]
    )

    st.subheader("Latest KPI1 details")
    st.dataframe(detail_df, use_container_width=True, hide_index=True)


st.set_page_config(
    page_title="Taiwan Risk Dashboard",
    layout="wide",
)

st.markdown(
    """
    <style>
        .stApp {
            background: linear-gradient(180deg, #0b1120 0%, #111827 45%, #020617 100%);
            color: #e5e7eb;
        }

        h1, h2, h3 {
            color: #f8fafc;
            letter-spacing: 0.02em;
        }

        h1 {
            font-size: 2.3rem !important;
            border-bottom: 1px solid #334155;
            padding-bottom: 0.6rem;
        }

        section[data-testid="stSidebar"] {
            background-color: #020617;
            border-right: 1px solid #1e293b;
        }

        div[data-testid="stMetric"] {
            background: #0f172a;
            border: 1px solid #334155;
            border-radius: 14px;
            padding: 18px;
            box-shadow: 0 0 18px rgba(15, 23, 42, 0.8);
        }

        div[data-testid="stMetricLabel"] {
            color: #94a3b8;
            font-size: 0.9rem;
        }

        div[data-testid="stMetricValue"] {
            color: #f8fafc;
            font-size: 1.8rem;
        }

        div[data-testid="stDataFrame"] {
            border: 1px solid #334155;
            border-radius: 12px;
            overflow: hidden;
        }

        .strategy-card {
            background: #0f172a;
            border: 1px solid #334155;
            border-left: 5px solid #dc2626;
            border-radius: 14px;
            padding: 18px 22px;
            margin: 18px 0;
        }

        .strategy-card-title {
            font-size: 1.05rem;
            font-weight: 700;
            color: #f8fafc;
            margin-bottom: 6px;
        }

        .strategy-card-text {
            color: #cbd5e1;
            font-size: 0.95rem;
            line-height: 1.5;
        }

        .small-muted {
            color: #94a3b8;
            font-size: 0.85rem;
        }

        hr {
            border-color: #334155;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Taiwan Risk Dashboard")

st.markdown(
    """
    <div class="strategy-card">
        <div class="strategy-card-title">Taiwan Conflict Risk Index</div>
        <div class="strategy-card-text">
            Dashboard monitoruje napięcie Chiny–Tajwan przez zestaw KPI:
            presję PLA, stres rynkowy oraz ręczne sygnały strategiczne.
            Celem nie jest przewidywanie wojny, tylko wczesne wykrywanie eskalacji.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

result = build_dashboard_result()



col1, col2, col3 = st.columns(3)

col1.metric("Overall Score", f"{result.score} / 100")
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
kpi1_df = read_csv("kpi1_data.csv")
build_kpi1_detail_table(kpi1_df)
st.divider()

st.subheader("CSV status")

for kpi_name, filename in KPI_FILES.items():
    path = DATA_DIR / filename
    st.write(f"`{filename}` — {'OK' if path.exists() else 'missing'}")