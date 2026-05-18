from pathlib import Path
from datetime import datetime
import pandas as pd

#hanged path
from src.PLA_api import PlaActivityClient


DATA_DIR = Path("data")
CSV_PATH = DATA_DIR / "kpi1_data.csv"


def update_pla_history() -> None:
    DATA_DIR.mkdir(exist_ok=True)

    client = PlaActivityClient()
    observation = client.fetch_latest_observation()

    today = datetime.utcnow().date().isoformat()

    new_row = {
        "date": today,
        "pla_aircraft": observation.pla_aircraft,
        "median_line_crossings": observation.median_line_crossings,
        "plan_ships": observation.plan_ships,
        "official_ships": observation.official_ships,
        "total_aircraft_and_ships": (
            observation.pla_aircraft
            + observation.plan_ships
            + observation.official_ships
        ),
    }

    if CSV_PATH.exists():
        df = pd.read_csv(CSV_PATH)
    else:
        df = pd.DataFrame()

    if not df.empty and today in df["date"].astype(str).values:
        df.loc[df["date"].astype(str) == today, new_row.keys()] = new_row.values()
    else:
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    df = df.sort_values("date")
    df.to_csv(CSV_PATH, index=False)

    print(f"Saved PLA data for {today}")
    print(new_row)


if __name__ == "__main__":
    update_pla_history()