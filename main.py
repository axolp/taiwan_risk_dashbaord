from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Iterable, Mapping, Optional

from src.PLA_api import PlaActivityClient

class RiskBucket(str, Enum):
    NORMAL = "Normal"
    ELEVATED = "Elevated"
    SERIOUS = "Serious"
    HIGH = "High"
    EXTREME = "Extreme"


KPI_WEIGHTS: Dict[str, float] = {
    "PLA_Air_Naval_Pressure": 0.18,
    "Exercise_Escalation": 0.15,
    "Maritime_Blockade_Shipping": 0.14,
    "China_Rhetoric_Legal": 0.10,
    "US_Allies_Signal": 0.12,
    "Cyber_Infrastructure": 0.08,
    "Market_Stress": 0.10,
    "Semiconductor_Supply_Chain": 0.08,
    "China_Domestic_Mobilization": 0.05,
}


@dataclass(frozen=True)
class PlaDailyObservation:
    """One daily military observation around Taiwan.

    You can later map this directly from Taiwan MND data.
    Values should be raw daily counts.
    """

    pla_aircraft: float = 0.0
    median_line_crossings: float = 0.0
    plan_ships: float = 0.0
    official_ships: float = 0.0


@dataclass(frozen=True)
class MarketSnapshot:
    """Market data already calculated as 5-day changes.

    All return values should be expressed in percentage points.

    Examples:
        TSM -8% over 5d -> tsm_5d_return = -8.0
        SOXX underperformed SPY by 6 p.p. -> soxx_vs_spy_5d = -6.0
        TWD weakened by 2% -> twd_5d_return = -2.0
        VIX rose by 10 points -> vix_change_5d = 10.0
    """

    tsm_5d_return: float = 0.0
    soxx_vs_spy_5d: float = 0.0
    twd_5d_return: float = 0.0
    vix_change_5d: float = 0.0
    taiwan_cds_change_score: Optional[float] = None


@dataclass(frozen=True)
class KpiResult:
    name: str
    value: float
    weight: float
    contribution: float
    details: Dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class TcriResult:
    score: float
    bucket: RiskBucket
    kpis: Dict[str, KpiResult]
    red_alert: bool = False
    red_alert_reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class TriggerEvents:
    closed_zones_around_major_taiwan_ports: bool = False
    us_japan_evacuation_warning: bool = False
    china_inspects_or_detains_merchant_ships: bool = False
    exercises_without_end_date: bool = False
    simultaneous_twd_tsm_soxx_selloff: bool = False

    def red_alert_reasons(self) -> tuple[str, ...]:
        reasons: list[str] = []

        if self.closed_zones_around_major_taiwan_ports:
            reasons.append("Closed zones around major Taiwan ports")
        if self.us_japan_evacuation_warning:
            reasons.append("US/Japan evacuation warning")
        if self.china_inspects_or_detains_merchant_ships:
            reasons.append("China inspects or detains merchant ships")
        if self.exercises_without_end_date:
            reasons.append("Military exercises without end date")
        if self.simultaneous_twd_tsm_soxx_selloff:
            reasons.append("Simultaneous TWD, TSM and SOXX selloff")

        return tuple(reasons)


def clamp_0_100(value: float) -> float:
    return max(0.0, min(100.0, float(value)))


def avg(values: Iterable[float]) -> float:
    values = list(values)
    if not values:
        return 0.0
    return sum(values) / len(values)


def calculate_kpi1_pla_air_naval_pressure(
    observations: Iterable[PlaDailyObservation],
    *,
    window_days: int = 7,
) -> KpiResult:
    """Calculate KPI 1: PLA Air & Naval Pressure.

    Formula:
        min(100,
            0.8 * PLA_aircraft_7d_avg
          + 2.0 * median_line_crossings_7d_avg
          + 3.0 * PLAN_ships_7d_avg
          + 4.0 * official_ships_7d_avg
        )

    The function accepts any number of observations and uses the latest `window_days`.
    Keep input order oldest -> newest.
    """

    latest = list(observations)[-window_days:]

    pla_aircraft_7d_avg = avg(item.pla_aircraft for item in latest)
    median_line_crossings_7d_avg = avg(item.median_line_crossings for item in latest)
    plan_ships_7d_avg = avg(item.plan_ships for item in latest)
    official_ships_7d_avg = avg(item.official_ships for item in latest)

    raw_score = (
        0.8 * pla_aircraft_7d_avg
        + 2.0 * median_line_crossings_7d_avg
        + 3.0 * plan_ships_7d_avg
        + 4.0 * official_ships_7d_avg
    )
    value = clamp_0_100(raw_score)
    weight = KPI_WEIGHTS["PLA_Air_Naval_Pressure"]

    return KpiResult(
        name="PLA_Air_Naval_Pressure",
        value=round(value, 2),
        weight=weight,
        contribution=round(value * weight, 2),
        details={
            "pla_aircraft_7d_avg": round(pla_aircraft_7d_avg, 2),
            "median_line_crossings_7d_avg": round(median_line_crossings_7d_avg, 2),
            "plan_ships_7d_avg": round(plan_ships_7d_avg, 2),
            "official_ships_7d_avg": round(official_ships_7d_avg, 2),
            "raw_score": round(raw_score, 2),
        },
    )


def calculate_kpi7_market_stress(snapshot: MarketSnapshot) -> KpiResult:
    """Calculate KPI 7: Market Stress Signal.

    If CDS score is present, use full formula:
        min(100,
            2.0 * max(0, -TSM_5d_return)
          + 1.5 * max(0, -SOXX_vs_SPY_5d)
          + 2.0 * max(0, -TWD_5d_return)
          + 1.0 * VIX_change_5d
          + 1.5 * Taiwan_CDS_change_score
        )

    If CDS is absent, use simplified formula:
        min(100,
            2.5 * max(0, -TSM_5d_return)
          + 2.0 * max(0, -SOXX_vs_SPY_5d)
          + 2.0 * max(0, -TWD_5d_return)
          + 1.5 * VIX_change_5d
        )
    """

    tsm_stress = max(0.0, -snapshot.tsm_5d_return)
    soxx_spy_stress = max(0.0, -snapshot.soxx_vs_spy_5d)
    twd_stress = max(0.0, -snapshot.twd_5d_return)
    vix_stress = max(0.0, snapshot.vix_change_5d)

    if snapshot.taiwan_cds_change_score is None:
        formula_variant = "without_cds"
        raw_score = (
            2.5 * tsm_stress
            + 2.0 * soxx_spy_stress
            + 2.0 * twd_stress
            + 1.5 * vix_stress
        )
        cds_stress = 0.0
    else:
        formula_variant = "with_cds"
        cds_stress = max(0.0, snapshot.taiwan_cds_change_score)
        raw_score = (
            2.0 * tsm_stress
            + 1.5 * soxx_spy_stress
            + 2.0 * twd_stress
            + 1.0 * vix_stress
            + 1.5 * cds_stress
        )

    value = clamp_0_100(raw_score)
    weight = KPI_WEIGHTS["Market_Stress"]

    return KpiResult(
        name="Market_Stress",
        value=round(value, 2),
        weight=weight,
        contribution=round(value * weight, 2),
        details={
            "formula_variant": 1.0 if formula_variant == "with_cds" else 0.0,
            "tsm_stress": round(tsm_stress, 2),
            "soxx_spy_stress": round(soxx_spy_stress, 2),
            "twd_stress": round(twd_stress, 2),
            "vix_stress": round(vix_stress, 2),
            "cds_stress": round(cds_stress, 2),
            "raw_score": round(raw_score, 2),
        },
    )


def manual_kpi(name: str, value: float) -> KpiResult:
    """Temporary helper for KPI 2, 3, 4, 5, 6, 8, 9.

    Use this until you implement data loaders and dedicated calculators.
    """

    if name not in KPI_WEIGHTS:
        raise KeyError(f"Unknown KPI name: {name}")

    score = clamp_0_100(value)
    weight = KPI_WEIGHTS[name]

    return KpiResult(
        name=name,
        value=round(score, 2),
        weight=weight,
        contribution=round(score * weight, 2),
        details={"manual_value": round(score, 2)},
    )


def risk_bucket(score: float) -> RiskBucket:
    if score < 20:
        return RiskBucket.NORMAL
    if score < 40:
        return RiskBucket.ELEVATED
    if score < 60:
        return RiskBucket.SERIOUS
    if score < 80:
        return RiskBucket.HIGH
    return RiskBucket.EXTREME


def calculate_tcri(
    kpis: Mapping[str, KpiResult],
    *,
    trigger_events: Optional[TriggerEvents] = None,
) -> TcriResult:
    """Calculate weighted Taiwan Conflict Risk Index.

    Missing KPIs are treated as 0, so you can gradually implement more sources.
    """

    normalized_kpis: Dict[str, KpiResult] = {}

    for name, weight in KPI_WEIGHTS.items():
        if name in kpis:
            normalized_kpis[name] = kpis[name]
        else:
            normalized_kpis[name] = KpiResult(
                name=name,
                value=0.0,
                weight=weight,
                contribution=0.0,
                details={"missing": 1.0},
            )

    score = round(sum(item.contribution for item in normalized_kpis.values()), 1)

    reasons = trigger_events.red_alert_reasons() if trigger_events else ()

    return TcriResult(
        score=score,
        bucket=risk_bucket(score),
        kpis=normalized_kpis,
        red_alert=bool(reasons),
        red_alert_reasons=reasons,
    )


def build_current_index(
    pla_observations: Iterable[PlaDailyObservation],
    market_snapshot: MarketSnapshot,
    manual_scores: Optional[Mapping[str, float]] = None,
    trigger_events: Optional[TriggerEvents] = None,
) -> TcriResult:
    """Main orchestration function.

    This is the function you can call from your future ETL/data loading layer.
    """

    kpis: Dict[str, KpiResult] = {
        "PLA_Air_Naval_Pressure": calculate_kpi1_pla_air_naval_pressure(pla_observations),
        "Market_Stress": calculate_kpi7_market_stress(market_snapshot),
    }

    for name, value in (manual_scores or {}).items():
        kpis[name] = manual_kpi(name, value)

    return calculate_tcri(kpis, trigger_events=trigger_events)


if __name__ == "__main__":
    # Example only. Replace this later with your data loading layer.
    client = PlaActivityClient()

    latest_observation = client.fetch_latest_observation()
    
    pla_data = [
       latest_observation,
    ]


    market = MarketSnapshot(
        tsm_5d_return=-8.0,
        soxx_vs_spy_5d=-6.0,
        twd_5d_return=-2.0,
        vix_change_5d=10.0,
    )

    manual = {
        "Exercise_Escalation": 40,
        "Maritime_Blockade_Shipping": 25,
        "China_Rhetoric_Legal": 25,
        "US_Allies_Signal": 25,
        "Cyber_Infrastructure": 25,
        "Semiconductor_Supply_Chain": 25,
        "China_Domestic_Mobilization": 0,
    }

    result = build_current_index(
        pla_observations=pla_data,
        market_snapshot=market,
        manual_scores=manual,
        trigger_events=TriggerEvents(simultaneous_twd_tsm_soxx_selloff=True),
    )

    print(result)
