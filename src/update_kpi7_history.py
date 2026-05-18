from pathlib import Path
from datetime import datetime
import pandas as pd

from main import calculate_kpi7_market_stress
from src.market_api import MarketStressClient

DATA_DIR = Path("data")
CSV_PATH = DATA_DIR / "kpi7_data.csv"


def update_kpi7_history() -> None:
    DATA_DIR.mkdir(exist_ok=True)

    client = MarketStressClient()
    snapshot = client.fetch_latest_snapshot()
    result = calculate_kpi7_market_stress(snapshot)

    today = datetime.utcnow().date().isoformat()

    new_row = {
        "date": today,
        "kpi_name": result.name,
        "kpi_value": result.value,
        "weight": result.weight,
        "contribution": result.contribution,
        "tsm_5d_return": snapshot.tsm_5d_return,
        "soxx_vs_spy_5d": snapshot.soxx_vs_spy_5d,
        "twd_5d_return": snapshot.twd_5d_return,
        "vix_change_5d": snapshot.vix_change_5d,
        "taiwan_cds_change_score": snapshot.taiwan_cds_change_score,
        **result.details,
    }

    if CSV_PATH.exists():
        df = pd.read_csv(CSV_PATH)
    else:
        df = pd.DataFrame()

    if not df.empty and today in df["date"].astype(str).values:
        df.loc[df["date"].astype(str) == today, list(new_row.keys())] = list(new_row.values())
    else:
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    df = df.sort_values("date")
    df.to_csv(CSV_PATH, index=False)

    print(f"Saved KPI7 data for {today}")
    print(new_row)


if __name__ == "__main__":
    update_kpi7_history()