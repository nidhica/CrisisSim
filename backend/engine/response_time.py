"""
Response time estimation — deterministic, no AWS/HTTP/LLM dependencies.

Flood formula (unchanged):
  BASE = 10 minutes
  road_factor     = 1 + 2 * (1 - road_accessibility)   → range [1.0, 3.0]
  resource_ratio  = clamp((rescue_teams + ambulances) / demand_units, 0, 1)
  resource_factor = 1 + (1 - resource_ratio)            → range [1.0, 2.0]
  demand_factor   = 1 + medical_urgency                 → range [1.0, 2.0]
  response_time   = BASE * road_factor * resource_factor * demand_factor

Non-flood hazards keep the common-resource logistics term, then apply:
  1) hazard-condition friction from registry response_modifier × avg factor
  2) specialist coverage friction (specialists ≠ ambulances / rescue teams)

Result clamped to [5, 120] minutes, rounded to 2 decimal places.

Coefficients are prototype assumptions, not scientific guidance.
"""
from __future__ import annotations
from .models import ZoneParams
from .hazards import get_hazard, clamp_factor, specialist_coverage

BASE_RESPONSE_MINUTES: float = 10.0
MIN_RESPONSE_MINUTES: float = 5.0
MAX_RESPONSE_MINUTES: float = 120.0

# Prototype assumption: specialist shortage adds up to +50% logistics friction.
SPECIALIST_RESPONSE_WEIGHT: float = 0.5


def estimate_response_time(zone: ZoneParams, hazard_type: str = "flood") -> float:
    """
    Estimate response time in minutes for a zone.
    Handles zero demand_units safely — zero demand means resources are
    more than sufficient, so resource_ratio is treated as 1.0 (no shortage).
    """
    road_factor = 1.0 + 2.0 * (1.0 - zone.road_accessibility)

    if zone.demand_units > 0:
        resource_ratio = min((zone.rescue_teams + zone.ambulances) / zone.demand_units, 1.0)
    else:
        resource_ratio = 1.0  # no demand → fully covered

    resource_factor = 1.0 + (1.0 - resource_ratio)
    demand_factor = 1.0 + zone.medical_urgency

    raw = BASE_RESPONSE_MINUTES * road_factor * resource_factor * demand_factor

    if hazard_type != "flood":
        hazard = get_hazard(hazard_type)
        # Hazard conditions add deterministic logistics friction; flood path is untouched.
        avg_factor = (
            sum(clamp_factor(zone.hazard_factors.get(name)) for name in hazard.factors)
            / len(hazard.factors)
        )
        raw *= 1.0 + hazard.response_modifier * avg_factor
        # Specialist shortage worsens response independently of common assets.
        coverage = specialist_coverage(zone, hazard_type)
        raw *= 1.0 + SPECIALIST_RESPONSE_WEIGHT * (1.0 - coverage)

    return round(min(max(raw, MIN_RESPONSE_MINUTES), MAX_RESPONSE_MINUTES), 2)
