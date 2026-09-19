"""Deterministic multi-hazard configuration registry.

Coefficients are transparent hackathon-prototype assumptions, not scientific
emergency-management guidance.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Literal

from .models import ZoneParams

HazardType = Literal["flood", "fire", "earthquake", "cyclone", "industrial_accident"]


@dataclass(frozen=True)
class HazardDefinition:
    type: HazardType
    display_name: str
    factors: tuple[str, ...]
    risk_weights: dict[str, float]
    response_modifier: float
    specialist_resources: tuple[str, ...]
    bottleneck_types: tuple[str, ...]


HAZARDS: dict[str, HazardDefinition] = {
    "flood": HazardDefinition(
        "flood",
        "Flood",
        ("flood_severity", "water_velocity", "drainage_failure"),
        {},
        0.0,
        (),
        ("resource_shortage", "shelter_capacity", "hospital_capacity", "road_access"),
    ),
    "fire": HazardDefinition(
        "fire",
        "Fire",
        ("fire_intensity", "smoke_exposure", "spread_potential"),
        {
            "affected_population": 0.20,
            "medical_urgency": 0.15,
            "road_accessibility": 0.10,
            "resource_shortage": 0.10,
            "fire_intensity": 0.20,
            "smoke_exposure": 0.13,
            "spread_potential": 0.12,
        },
        0.35,
        ("fire_crews",),
        ("fire_crew_shortage", "uncontrolled_spread", "smoke_medical_pressure", "road_access"),
    ),
    "earthquake": HazardDefinition(
        "earthquake",
        "Earthquake",
        ("structural_damage", "trapped_person_likelihood", "aftershock_risk"),
        {
            "affected_population": 0.18,
            "medical_urgency": 0.16,
            "road_accessibility": 0.14,
            "resource_shortage": 0.12,
            "structural_damage": 0.20,
            "trapped_person_likelihood": 0.12,
            "aftershock_risk": 0.08,
        },
        0.40,
        ("search_and_rescue_teams",),
        (
            "search_and_rescue_shortage",
            "blocked_access",
            "structural_rescue_backlog",
            "medical_pressure",
        ),
    ),
    "cyclone": HazardDefinition(
        "cyclone",
        "Cyclone / Severe Storm",
        ("wind_severity", "storm_surge_exposure", "power_outage_severity"),
        {
            "affected_population": 0.18,
            "medical_urgency": 0.12,
            "road_accessibility": 0.14,
            "resource_shortage": 0.12,
            "wind_severity": 0.18,
            "storm_surge_exposure": 0.16,
            "power_outage_severity": 0.10,
        },
        0.30,
        ("evacuation_teams", "utility_crews"),
        (
            "evacuation_capacity",
            "road_access",
            "utility_restoration_shortage",
            "shelter_capacity",
        ),
    ),
    "industrial_accident": HazardDefinition(
        "industrial_accident",
        "Industrial Accident",
        ("toxic_release_severity", "exposure_level", "containment_failure"),
        {
            "affected_population": 0.16,
            "medical_urgency": 0.16,
            "road_accessibility": 0.08,
            "resource_shortage": 0.12,
            "toxic_release_severity": 0.20,
            "exposure_level": 0.16,
            "containment_failure": 0.12,
        },
        0.45,
        ("hazmat_teams", "containment_units"),
        (
            "hazmat_shortage",
            "containment_shortage",
            "toxic_medical_pressure",
            "toxic_exposure",
        ),
    ),
}

for definition in HAZARDS.values():
    if definition.risk_weights:
        assert abs(sum(definition.risk_weights.values()) - 1.0) < 1e-10


def get_hazard(hazard_type: str | None) -> HazardDefinition:
    return HAZARDS.get(hazard_type or "flood", HAZARDS["flood"])


def clamp_factor(value: float | int | None) -> float:
    return max(0.0, min(float(value or 0.0), 1.0))


def specialist_total(zone: ZoneParams, hazard_type: str) -> int:
    """Sum of hazard-appropriate specialist units only (never mixes hazard types)."""
    hazard = get_hazard(hazard_type)
    return sum(
        max(0, int(zone.specialist_resources.get(key, 0)))
        for key in hazard.specialist_resources
    )


def specialist_coverage(zone: ZoneParams, hazard_type: str) -> float:
    """
    Deterministic specialist coverage against zone demand_units.

    Assumption (prototype, not scientific):
      each specialist unit covers one demand unit of hazard-specific need.
      Common rescue teams / ambulances do NOT substitute for specialists
      (fire crews ≠ ambulances, hazmat ≠ SAR, utility crews ≠ medical).
    """
    hazard = get_hazard(hazard_type)
    if not hazard.specialist_resources:
        return 1.0
    if zone.demand_units <= 0:
        return 1.0
    return min(specialist_total(zone, hazard_type) / zone.demand_units, 1.0)


def common_resource_coverage(zone: ZoneParams) -> float:
    """Coverage from shared rescue teams + ambulances only."""
    if zone.demand_units <= 0:
        return 1.0
    return min(
        (max(0, zone.rescue_teams) + max(0, zone.ambulances)) / zone.demand_units,
        1.0,
    )
