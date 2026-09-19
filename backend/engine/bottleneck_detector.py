"""
Bottleneck detection — deterministic, no AWS/HTTP/LLM dependencies.

Flood evaluates exactly four categories:
  1. Resource shortage   (per zone)
  2. Shelter capacity    (per shelter)
  3. Hospital capacity   (per hospital, uses effective_capacity = capacity + surge_capacity)
  4. Road access         (per zone, reported for highest-risk zones)

Non-flood hazards add registry-defined bottleneck types driven by specialist
coverage and hazard factors. Coefficients are prototype assumptions.

Returns list[Bottleneck] sorted by severity_score descending.
First item is the primary bottleneck.
"""
from __future__ import annotations
from .models import ZoneResult, Shelter, Hospital, Bottleneck, ZoneParams
from .hazards import get_hazard, clamp_factor, specialist_coverage

# Only report road-access bottlenecks for zones with risk_score >= this threshold
ROAD_ACCESS_MIN_RISK_SCORE: float = 30.0
SPECIALIST_SHORTAGE_THRESHOLD: float = 0.3
FACTOR_PRESSURE_THRESHOLD: float = 0.7


def _facility_bottlenecks(shelters: list[Shelter], hospitals: list[Hospital]) -> list[Bottleneck]:
    bottlenecks: list[Bottleneck] = []

    for shelter in shelters:
        if shelter.capacity > 0 and shelter.current_occupancy > shelter.capacity:
            severity = 1.0 - shelter.capacity / shelter.current_occupancy
            bottlenecks.append(
                Bottleneck(
                    type="shelter_capacity",
                    zone_id=None,
                    facility_id=shelter.shelter_id,
                    description=f"Shelter overcapacity: {shelter.name}",
                    severity_score=round(severity, 4),
                )
            )

    for hospital in hospitals:
        effective_capacity = hospital.capacity + hospital.surge_capacity
        if effective_capacity > 0 and hospital.current_occupancy > effective_capacity:
            severity = 1.0 - effective_capacity / hospital.current_occupancy
            bottlenecks.append(
                Bottleneck(
                    type="hospital_capacity",
                    zone_id=None,
                    facility_id=hospital.hospital_id,
                    description=f"Hospital capacity critical: {hospital.name}",
                    severity_score=round(severity, 4),
                )
            )

    return bottlenecks


def _flood_bottlenecks(
    zone_results: list[ZoneResult],
    shelters: list[Shelter],
    hospitals: list[Hospital],
) -> list[Bottleneck]:
    """Legacy flood bottleneck path — preserved for regression compatibility."""
    bottlenecks: list[Bottleneck] = []

    for zr in zone_results:
        shortage_ratio = zr.risk_components.resource_shortage_score / 0.10
        if shortage_ratio > 0.0:
            bottlenecks.append(
                Bottleneck(
                    type="resource_shortage",
                    zone_id=zr.zone_id,
                    facility_id=None,
                    description=f"Resource shortage in zone {zr.zone_id}",
                    severity_score=round(shortage_ratio, 4),
                )
            )

    bottlenecks.extend(_facility_bottlenecks(shelters, hospitals))

    for zr in zone_results:
        if zr.risk_score >= ROAD_ACCESS_MIN_RISK_SCORE:
            road_access_risk = zr.risk_components.road_accessibility_score / 0.15
            if road_access_risk > 0.0:
                bottlenecks.append(
                    Bottleneck(
                        type="road_access",
                        zone_id=zr.zone_id,
                        facility_id=None,
                        description=f"Road access impaired in zone {zr.zone_id}",
                        severity_score=round(road_access_risk, 4),
                    )
                )

    bottlenecks.sort(key=lambda b: b.severity_score, reverse=True)
    return bottlenecks


def _append_road_access(
    bottlenecks: list[Bottleneck],
    zone_results: list[ZoneResult],
    road_weight: float,
    bottleneck_type: str = "road_access",
) -> None:
    if road_weight <= 0:
        return
    for zr in zone_results:
        if zr.risk_score < ROAD_ACCESS_MIN_RISK_SCORE:
            continue
        road_access_risk = zr.risk_components.road_accessibility_score / road_weight
        if road_access_risk > 0.0:
            bottlenecks.append(
                Bottleneck(
                    type=bottleneck_type,
                    zone_id=zr.zone_id,
                    facility_id=None,
                    description=f"Road access impaired in zone {zr.zone_id}",
                    severity_score=round(min(road_access_risk, 1.0), 4),
                )
            )


def _hazard_bottlenecks(
    zone_results: list[ZoneResult],
    shelters: list[Shelter],
    hospitals: list[Hospital],
    hazard_type: str,
    zones: list[ZoneParams] | None,
) -> list[Bottleneck]:
    """Hazard-specific bottlenecks using registry types and specialist coverage."""
    hazard = get_hazard(hazard_type)
    bottlenecks: list[Bottleneck] = []
    params = {z.zone_id: z for z in zones or []}
    road_weight = hazard.risk_weights.get("road_accessibility", 0.15)

    # Facility constraints remain relevant (especially cyclone shelter capacity).
    if "shelter_capacity" in hazard.bottleneck_types or hazard_type == "cyclone":
        bottlenecks.extend(
            b for b in _facility_bottlenecks(shelters, hospitals) if b.type == "shelter_capacity"
        )
    else:
        # Still surface hospital overcrowding for medical-pressure hazards.
        bottlenecks.extend(
            b for b in _facility_bottlenecks(shelters, hospitals) if b.type == "hospital_capacity"
        )

    for zr in zone_results:
        zone = params.get(zr.zone_id)
        if zone is None:
            continue
        factors = {name: clamp_factor(zone.hazard_factors.get(name)) for name in hazard.factors}
        medical = clamp_factor(zone.medical_urgency)
        shortage = 1.0 - specialist_coverage(zone, hazard_type)

        if hazard_type == "fire":
            crews = max(0, int(zone.specialist_resources.get("fire_crews", 0)))
            if shortage >= SPECIALIST_SHORTAGE_THRESHOLD or crews == 0:
                bottlenecks.append(
                    Bottleneck(
                        "fire_crew_shortage",
                        zr.zone_id,
                        None,
                        f"Fire crew shortage in zone {zr.zone_id}",
                        round(max(shortage, 1.0 if crews == 0 else shortage), 4),
                    )
                )
            if factors.get("spread_potential", 0.0) >= FACTOR_PRESSURE_THRESHOLD:
                bottlenecks.append(
                    Bottleneck(
                        "uncontrolled_spread",
                        zr.zone_id,
                        None,
                        f"Uncontrolled fire spread risk in zone {zr.zone_id}",
                        round(factors["spread_potential"], 4),
                    )
                )
            smoke = factors.get("smoke_exposure", 0.0)
            if smoke >= 0.6 and medical >= 0.5:
                bottlenecks.append(
                    Bottleneck(
                        "smoke_medical_pressure",
                        zr.zone_id,
                        None,
                        f"Smoke exposure driving medical pressure in zone {zr.zone_id}",
                        round(min(1.0, 0.5 * smoke + 0.5 * medical), 4),
                    )
                )

        elif hazard_type == "earthquake":
            sar = max(0, int(zone.specialist_resources.get("search_and_rescue_teams", 0)))
            if shortage >= SPECIALIST_SHORTAGE_THRESHOLD or sar == 0:
                bottlenecks.append(
                    Bottleneck(
                        "search_and_rescue_shortage",
                        zr.zone_id,
                        None,
                        f"Search-and-rescue shortage in zone {zr.zone_id}",
                        round(max(shortage, 1.0 if sar == 0 else shortage), 4),
                    )
                )
            structural = factors.get("structural_damage", 0.0)
            if structural >= FACTOR_PRESSURE_THRESHOLD and shortage >= 0.2:
                bottlenecks.append(
                    Bottleneck(
                        "structural_rescue_backlog",
                        zr.zone_id,
                        None,
                        f"Structural rescue backlog in zone {zr.zone_id}",
                        round(min(1.0, 0.6 * structural + 0.4 * shortage), 4),
                    )
                )
            if medical >= 0.6:
                bottlenecks.append(
                    Bottleneck(
                        "medical_pressure",
                        zr.zone_id,
                        None,
                        f"Medical pressure in zone {zr.zone_id}",
                        round(medical, 4),
                    )
                )

        elif hazard_type == "cyclone":
            evacuation = max(0, int(zone.specialist_resources.get("evacuation_teams", 0)))
            utility = max(0, int(zone.specialist_resources.get("utility_crews", 0)))
            if zone.demand_units > 0:
                evac_shortage = 1.0 - min(evacuation / zone.demand_units, 1.0)
            else:
                evac_shortage = 0.0
            if evac_shortage >= SPECIALIST_SHORTAGE_THRESHOLD or evacuation == 0:
                bottlenecks.append(
                    Bottleneck(
                        "evacuation_capacity",
                        zr.zone_id,
                        None,
                        f"Evacuation capacity constrained in zone {zr.zone_id}",
                        round(max(evac_shortage, 1.0 if evacuation == 0 else evac_shortage), 4),
                    )
                )
            power = factors.get("power_outage_severity", 0.0)
            if utility == 0 or (power >= 0.6 and utility < max(1, zone.demand_units // 2)):
                util_severity = 1.0 if utility == 0 else min(1.0, 0.5 * power + 0.5 * (1.0 - min(utility / max(zone.demand_units, 1), 1.0)))
                bottlenecks.append(
                    Bottleneck(
                        "utility_restoration_shortage",
                        zr.zone_id,
                        None,
                        f"Utility restoration shortage in zone {zr.zone_id}",
                        round(util_severity, 4),
                    )
                )

        elif hazard_type == "industrial_accident":
            hazmat = max(0, int(zone.specialist_resources.get("hazmat_teams", 0)))
            containment = max(0, int(zone.specialist_resources.get("containment_units", 0)))
            if zone.demand_units > 0:
                hazmat_shortage = 1.0 - min(hazmat / zone.demand_units, 1.0)
                containment_shortage = 1.0 - min(containment / zone.demand_units, 1.0)
            else:
                hazmat_shortage = 0.0
                containment_shortage = 0.0
            if hazmat_shortage >= SPECIALIST_SHORTAGE_THRESHOLD or hazmat == 0:
                bottlenecks.append(
                    Bottleneck(
                        "hazmat_shortage",
                        zr.zone_id,
                        None,
                        f"Hazmat team shortage in zone {zr.zone_id}",
                        round(max(hazmat_shortage, 1.0 if hazmat == 0 else hazmat_shortage), 4),
                    )
                )
            if containment_shortage >= SPECIALIST_SHORTAGE_THRESHOLD or containment == 0:
                bottlenecks.append(
                    Bottleneck(
                        "containment_shortage",
                        zr.zone_id,
                        None,
                        f"Containment unit shortage in zone {zr.zone_id}",
                        round(
                            max(containment_shortage, 1.0 if containment == 0 else containment_shortage),
                            4,
                        ),
                    )
                )
            exposure = factors.get("exposure_level", 0.0)
            release = factors.get("toxic_release_severity", 0.0)
            if exposure >= 0.6 and medical >= 0.5:
                bottlenecks.append(
                    Bottleneck(
                        "toxic_medical_pressure",
                        zr.zone_id,
                        None,
                        f"Toxic exposure driving medical pressure in zone {zr.zone_id}",
                        round(min(1.0, 0.5 * exposure + 0.5 * medical), 4),
                    )
                )
            toxic = max(exposure, release, factors.get("containment_failure", 0.0))
            if toxic >= FACTOR_PRESSURE_THRESHOLD:
                bottlenecks.append(
                    Bottleneck(
                        "toxic_exposure",
                        zr.zone_id,
                        None,
                        f"Toxic exposure pressure in zone {zr.zone_id}",
                        round(toxic, 4),
                    )
                )

    road_type = "blocked_access" if hazard_type == "earthquake" else "road_access"
    if road_type in hazard.bottleneck_types or "road_access" in hazard.bottleneck_types:
        _append_road_access(bottlenecks, zone_results, road_weight, road_type)

    bottlenecks.sort(key=lambda b: b.severity_score, reverse=True)
    return bottlenecks


def detect_bottlenecks(
    zone_results: list[ZoneResult],
    shelters: list[Shelter],
    hospitals: list[Hospital],
    hazard_type: str = "flood",
    zones: list[ZoneParams] | None = None,
) -> list[Bottleneck]:
    """
    Detect and rank all bottlenecks across the current simulation state.
    Returns list sorted by severity_score descending (primary bottleneck first).
    """
    if hazard_type == "flood":
        return _flood_bottlenecks(zone_results, shelters, hospitals)
    return _hazard_bottlenecks(zone_results, shelters, hospitals, hazard_type, zones)
