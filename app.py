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
ASSETS_DIR = Path("assets")

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

KPI_LABELS = {
    "PLA_Air_Naval_Pressure": "PLA Air / Naval Pressure",
    "Exercise_Escalation": "Exercise Escalation",
    "Maritime_Blockade_Shipping": "Maritime / Blockade",
    "China_Rhetoric_Legal": "China Rhetoric / Legal",
    "US_Allies_Signal": "US & Allies Signal",
    "Cyber_Infrastructure": "Cyber / Infrastructure",
    "Market_Stress": "Market Stress",
    "Semiconductor_Supply_Chain": "Semiconductor Chain",
    "China_Domestic_Mobilization": "China Mobilization",
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


def risk_color(score: float) -> str:
    if score >= 75:
        return "#ef4444"
    if score >= 50:
        return "#f97316"
    if score >= 30:
        return "#eab308"
    return "#22c55e"


def render_score_card(title, value, subtitle, color="#38bdf8"):
    st.markdown(
        f"""
        <div class="op-card">
            <div class="op-card-label">{title}</div>
            <div class="op-card-value" style="color:{color};">{value}</div>
            <div class="op-card-subtitle">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


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

    st.dataframe(detail_df, use_container_width=True, hide_index=True)


st.set_page_config(
    page_title="Taiwan Risk Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;500;700&display=swap');

        .stApp {
            background:
                radial-gradient(circle at top left, rgba(34, 197, 94, 0.08), transparent 28%),
                radial-gradient(circle at top right, rgba(239, 68, 68, 0.10), transparent 25%),
                linear-gradient(180deg, #050807 0%, #08110d 48%, #020403 100%);
            color: #d1d5db;
            font-family: 'Roboto Mono', monospace;
        }

        .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
        }

        h1, h2, h3 {
            font-family: 'Roboto Mono', monospace;
            color: #f8fafc;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }

        h1 {
            font-size: 2.1rem !important;
            border-bottom: 1px solid rgba(148, 163, 184, 0.35);
            padding-bottom: 0.7rem;
        }

        .top-classified {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border: 1px solid rgba(34, 197, 94, 0.35);
            background: rgba(2, 6, 23, 0.72);
            padding: 10px 14px;
            margin-bottom: 18px;
            color: #86efac;
            font-size: 0.82rem;
            letter-spacing: 0.12em;
        }

        .war-room-panel {
            border: 1px solid rgba(148, 163, 184, 0.30);
            background:
                linear-gradient(rgba(15, 23, 42, 0.88), rgba(15, 23, 42, 0.88)),
                repeating-linear-gradient(0deg, transparent, transparent 28px, rgba(34,197,94,0.06) 29px),
                repeating-linear-gradient(90deg, transparent, transparent 28px, rgba(34,197,94,0.06) 29px);
            border-radius: 2px;
            padding: 20px;
            box-shadow: 0 0 32px rgba(0,0,0,0.45);
        }

        .briefing-title {
            color: #f8fafc;
            font-size: 1.1rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 8px;
        }

        .briefing-text {
            color: #cbd5e1;
            font-size: 0.92rem;
            line-height: 1.65;
        }

        .op-card {
            background: rgba(2, 6, 23, 0.82);
            border: 1px solid rgba(148, 163, 184, 0.32);
            border-left: 4px solid #22c55e;
            padding: 18px;
            min-height: 132px;
            box-shadow: inset 0 0 18px rgba(34, 197, 94, 0.05);
        }

        .op-card-label {
            color: #94a3b8;
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.14em;
            margin-bottom: 12px;
        }

        .op-card-value {
            font-size: 2.05rem;
            font-weight: 700;
            line-height: 1.1;
        }

        .op-card-subtitle {
            color: #64748b;
            font-size: 0.78rem;
            margin-top: 12px;
        }

        .map-placeholder {
            height: 340px;
            border: 1px solid rgba(34, 197, 94, 0.35);
            background:
                linear-gradient(rgba(2, 6, 23, 0.65), rgba(2, 6, 23, 0.65)),
                repeating-linear-gradient(0deg, transparent, transparent 34px, rgba(34,197,94,0.12) 35px),
                repeating-linear-gradient(90deg, transparent, transparent 34px, rgba(34,197,94,0.12) 35px);
            display: flex;
            align-items: center;
            justify-content: center;
            color: #86efac;
            text-align: center;
            font-size: 0.9rem;
            letter-spacing: 0.14em;
            text-transform: uppercase;
        }

        .section-header {
            margin-top: 26px;
            margin-bottom: 10px;
            padding: 9px 12px;
            background: rgba(15, 23, 42, 0.9);
            border-left: 4px solid #22c55e;
            color: #f8fafc;
            font-weight: 700;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            font-size: 0.9rem;
        }

        div[data-testid="stDataFrame"] {
            border: 1px solid rgba(148, 163, 184, 0.32);
            border-radius: 2px;
            overflow: hidden;
        }

        .status-ok {
            color: #86efac;
        }

        .status-missing {
            color: #f87171;
        }

        hr {
            border-color: rgba(148, 163, 184, 0.22);
        }
    </style>
    """,
    unsafe_allow_html=True,
)


st.markdown(
    """
    <div class="top-classified">
        <div>STRATEGIC SITUATION ROOM</div>
        <div>TAIWAN STRAIT MONITORING CELL</div>
        <div>LIVE CSV FEED</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.title("Taiwan Conflict Risk Index")

result = build_dashboard_result()
score_color = risk_color(result.score)

left, right = st.columns([1.35, 1])

with left:
    st.markdown(
        """
        <div class="war-room-panel">
            <div class="briefing-title">Operational Briefing</div>
             <div class="briefing-text">
                Strategic monitoring panel tracking China–Taiwan escalation dynamics through
                a 9-indicator risk framework covering military activity, geopolitical signaling,
                cyber domain pressure, maritime disruption and financial market stress.
                <br><br>
                Current live implementation includes:
                <b>KPI-1 — PLA Air & Naval Pressure</b> and
                <b>KPI-7 — Market Stress Indicator</b>.
                Additional intelligence modules are scheduled for phased deployment.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")

    c1, c2, c3 = st.columns(3)
    with c1:
        render_score_card("Overall Risk Score", f"{result.score} / 100", "Synthetic TCRI reading", score_color)
    with c2:
        render_score_card("Risk Bucket", result.bucket.value, "Current classification", "#f8fafc")
    with c3:
        alert_value = "YES" if result.red_alert else "NO"
        alert_color = "#ef4444" if result.red_alert else "#22c55e"
        render_score_card("Red Alert", alert_value, "Escalation trigger", alert_color)

with right:
    map_path = ASSETS_DIR / "taiwan_map.png"

    if map_path.exists():
        st.image(str(map_path), use_container_width=True)
    else:
        st.markdown(
            """
            <div class="map-placeholder">
                MAP / SATELLITE IMAGE SLOT<br><br>
                Add file:<br>
                assets/taiwan_map.png
            </div>
            """,
            unsafe_allow_html=True,
        )


st.markdown('<div class="section-header">KPI Tactical Board</div>', unsafe_allow_html=True)

rows = []

for kpi in result.kpis.values():
    rows.append(
        {
            "KPI": KPI_LABELS.get(kpi.name, kpi.name),
            "Raw Name": kpi.name,
            "Value": round(kpi.value, 2),
            "Weight": kpi.weight,
            "Contribution": round(kpi.contribution, 2),
        }
    )

kpi_df = pd.DataFrame(rows)
kpi_df = kpi_df.sort_values("Contribution", ascending=False)

st.dataframe(
    kpi_df[["KPI", "Value", "Weight", "Contribution"]],
    use_container_width=True,
    hide_index=True,
)

st.bar_chart(kpi_df.set_index("KPI")["Value"])

st.markdown('<div class="section-header">PLA Air / Naval Pressure — Latest Observation</div>', unsafe_allow_html=True)
kpi1_df = read_csv("kpi1_data.csv")
build_kpi1_detail_table(kpi1_df)

st.markdown('<div class="section-header">Source Feed Integrity</div>', unsafe_allow_html=True)

status_rows = []

for kpi_name, filename in KPI_FILES.items():
    path = DATA_DIR / filename
    df = read_csv(filename)

    latest_date = "N/A"
    rows_count = 0

    if not df.empty:
        rows_count = len(df)
        if "date" in df.columns:
            latest_date = df.iloc[-1].get("date", "N/A")

    status_rows.append(
        {
            "Feed": filename,
            "KPI": KPI_LABELS.get(kpi_name, kpi_name),
            "Status": "OK" if path.exists() else "MISSING",
            "Rows": rows_count,
            "Latest date": latest_date,
        }
    )

status_df = pd.DataFrame(status_rows)

st.dataframe(
    status_df,
    use_container_width=True,
    hide_index=True,
)