from dataclasses import dataclass
from datetime import date
import yfinance as yf


@dataclass(frozen=True)
class MarketSnapshot:
    tsm_5d_return: float
    soxx_vs_spy_5d: float
    twd_5d_return: float
    vix_change_5d: float
    taiwan_cds_change_score: float | None = None


class MarketStressClient:
    def fetch_latest_snapshot(self) -> MarketSnapshot:
        tickers = ["TSM", "SOXX", "SPY", "TWD=X", "^VIX"]

        df = yf.download(
            tickers,
            period="15d",
            interval="1d",
            auto_adjust=True,
            progress=False,
            threads=False,
        )

        close = df["Close"].dropna(how="all")

        if len(close) < 6:
            raise RuntimeError("Za mało danych rynkowych do obliczenia zmiany 5d.")

        latest = close.iloc[-1]
        prev = close.iloc[-6]

        tsm_5d_return = ((latest["TSM"] / prev["TSM"]) - 1.0) * 100.0
        soxx_5d_return = ((latest["SOXX"] / prev["SOXX"]) - 1.0) * 100.0
        spy_5d_return = ((latest["SPY"] / prev["SPY"]) - 1.0) * 100.0

        # Yahoo TWD=X = USD/TWD. Gdy USD/TWD rośnie, TWD słabnie.
        usd_twd_5d_return = ((latest["TWD=X"] / prev["TWD=X"]) - 1.0) * 100.0
        twd_5d_return = -usd_twd_5d_return

        # VIX jako zmiana w punktach, nie procentach.
        vix_change_5d = latest["^VIX"] - prev["^VIX"]

        return MarketSnapshot(
            tsm_5d_return=round(float(tsm_5d_return), 4),
            soxx_vs_spy_5d=round(float(soxx_5d_return - spy_5d_return), 4),
            twd_5d_return=round(float(twd_5d_return), 4),
            vix_change_5d=round(float(vix_change_5d), 4),
            taiwan_cds_change_score=None,
        )