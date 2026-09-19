"""
Risk scoring module — deterministic, no AWS/HTTP/LLM dependencies.

Legacy flood weights (must sum to exactly 1.0):
  affected_population : 0.25
  flood_severity      : 0.25
  medical_urgency     : 0.25
  road_accessibility  : 0.15  (inverted: high accessibility = low risk)
  resource_shortage   : 0.10  (inverted: high coverage = low shortage)

Non-flood hazards use registry weights in hazards.py. Coefficients are
prototype assumptions, not scientific emergency-management guidance.
"""
from __future__ import annotations
from .models import SimulationState, ZoneParams, ZoneResult, RiskComponents
from .hazards import get_hazard, clamp_factor, specialist_coverage

WEIGHTS: dict[str, float] = {
    "affected_population": 0.25,
    "flood_severity": 0.25,
    "medical_urgency": 0.25,
    "road_accessibility": 0.15,
    "resource_shortage": 0.10,
}

assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-10, "Risk weights must sum to exactly 1.0"


def _risk_level(score: float) -> str:
    """
    Deterministic severity mapping. Handles decimal values correctly.
    Boundaries are inclusive on the upper end:
      [0, 25]   → "low"
      (25, 50]  → "medium"
      (50, 75]  → "high"
      (75, 100] → "critical"
    """
    if score <= 25.0:
        return "low"
    elif score <= 50.0:
        return "medium"
    elif score <= 75.0:
        return "high"
    else:
        return "critical"


def calculate_risk_score(zone: ZoneParams, population_max: int) -> tuple[float, RiskComponents]:
    """
    Calculate the weighted risk score for a single flood zone.

    Returns (risk_score, RiskComponents).
    risk_score is clamped to [0, 100] and rounded to 2 decimal places.

    Normalization:
      - population : min(affected_population / population_max, 1.0)
      - flood      : flood_severity  (already 0–1)
      - medical    : medical_urgency (already 0–1)
      - road risk  : 1 - road_accessibility
      - resource shortage : 1 - clamp(resources / demand_units, 0, 1)

    population_max must be > 0. demand_units must be > 0.
    """
    # Guard against division by zero — treat degenerate inputs as worst-case
    pop_norm = min(zone.affected_population / population_max, 1.0) if population_max > 0 else 1.0
    road_risk = 1.0 - zone.road_accessibility

    if zone.demand_units > 0:
        resource_coverage = min((zone.rescue_teams + zone.ambulances) / zone.demand_units, 1.0)
    else:
        # Zero demand: any resources cover it fully → no shortage
        resource_coverage = 1.0
    resource_shortage = 1.0 - resource_coverage

    components = RiskComponents(
        affected_population_score=WEIGHTS["affected_population"] * pop_norm,
        flood_severity_score=WEIGHTS["flood_severity"] * zone.flood_severity,
        medical_urgency_score=WEIGHTS["medical_urgency"] * zone.medical_urgency,
        road_accessibility_score=WEIGHTS["road_accessibility"] * road_risk,
        resource_shortage_score=WEIGHTS["resource_shortage"] * resource_shortage,
    )

    raw = (
        components.affected_population_score
        + components.flood_severity_score
        + components.medical_urgency_score
        + components.road_accessibility_score
        + components.resource_shortage_score
    )

    score = round(min(max(raw * 100.0, 0.0), 100.0), 2)
    return score, components


def calculate_hazard_risk_score(
    zone: ZoneParams,
    population_max: int,
    hazard_type: str,
) -> tuple[float, RiskComponents]:
    """
    Calculate a hazard-aware risk score.

    Flood path preserves the legacy weighted formula exactly.
    Non-flood path uses registry factors and treats specialist coverage
    separately from common rescue/ambulance assets.
    """
    if hazard_type == "flood":
        return calculate_risk_score(zone, population_max)

    hazard = get_hazard(hazard_type)
    weights = hazard.risk_weights
    pop = min(zone.affected_population / population_max, 1.0) if population_max > 0 else 1.0
    road = 1.0 - clamp_factor(zone.road_accessibility)

    # Specialist shortage only — common assets do not fill specialist demand.
    resource_shortage = 1.0 - specialist_coverage(zone, hazard_type)

    specific = {
        name: weights[name] * clamp_factor(zone.hazard_factors.get(name))
        for name in hazard.factors
    }
    components = RiskComponents(
        affected_population_score=weights["affected_population"] * pop,
        flood_severity_score=0.0,
        medical_urgency_score=weights["medical_urgency"] * clamp_factor(zone.medical_urgency),
        road_accessibility_score=weights["road_accessibility"] * road,
        resource_shortage_score=weights["resource_shortage"] * resource_shortage,
        hazard_intensity_score=specific[hazard.factors[0]],
        hazard_specific_scores=specific,
    )
    raw = (
        components.affected_population_score
        + components.medical_urgency_score
        + components.road_accessibility_score
        + components.resource_shortage_score
        + sum(specific.values())
    )
    return round(min(max(raw * 100.0, 0.0), 100.0), 2), components


def calculate_zone_results(state: SimulationState, population_max: int) -> list[ZoneResult]:
    """
    Calculate ZoneResult for every zone in the SimulationState.
    Imports response_time here to avoid circular imports.
    """
    from .response_time import estimate_response_time

    results: list[ZoneResult] = []
    for zone in state.zones:
        score, components = calculate_hazard_risk_score(zone, population_max, state.hazard_type)
        rt = estimate_response_time(zone, state.hazard_type)
        results.append(
            ZoneResult(
                zone_id=zone.zone_id,
                risk_score=score,
                risk_level=_risk_level(score),
                response_time_minutes=rt,
                risk_components=components,
            )
        )
    return results
