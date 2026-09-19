"""
Intervention engine — generates one SimulationState per strategy.
Deterministic, no AWS/HTTP/LLM dependencies.

Four strategies:
  baseline             — original state unchanged
  resource_reallocation — moves resources from lowest-risk to highest-risk zone
  capacity_expansion   — increases shelter (+20%) and hospital surge (+15%) capacity
  combined             — applies both resource_reallocation and capacity_expansion

Combined reuses the two helper functions — no duplicated logic.

Resource reallocation is hazard-aware:
  flood               → rescue teams / ambulances
  fire                → fire crews
  earthquake          → search-and-rescue teams
  cyclone             → evacuation teams / utility crews
  industrial_accident → hazmat teams / containment units

Specialist types are never transferred across unrelated categories.
"""
from __future__ import annotations
import dataclasses
from .models import SimulationState, ZoneParams, Shelter, Hospital, ZoneResult, Bottleneck
from .hazards import get_hazard

STRATEGY_LABELS: dict[str, str] = {
    "baseline": "Baseline / No Intervention",
    "resource_reallocation": "Resource Reallocation",
    "capacity_expansion": "Capacity Expansion",
    "combined": "Combined Intervention",
}

# Minimum resources a zone must always retain (flood / common assets)
MIN_RESCUE_TEAMS: int = 1
MIN_AMBULANCES: int = 1

# Maximum units that can be transferred to a single zone in one reallocation
MAX_TRANSFER_UNITS: int = 2


def _deep_copy_state(state: SimulationState) -> SimulationState:
    """Return a fully independent copy of a SimulationState, including hazard_type."""
    return SimulationState(
        zones=[
            dataclasses.replace(
                z,
                hazard_factors=dict(z.hazard_factors),
                specialist_resources=dict(z.specialist_resources),
            )
            for z in state.zones
        ],
        shelters=[dataclasses.replace(s) for s in state.shelters],
        hospitals=[dataclasses.replace(h) for h in state.hospitals],
        hazard_type=state.hazard_type,
    )


def _apply_specialist_reallocation(
    state: SimulationState,
    zone_results: list[ZoneResult],
    hazard_type: str,
) -> SimulationState:
    """
    Move up to MAX_TRANSFER_UNITS of hazard-appropriate specialist resources
    from the lowest-risk zone to the highest-risk zone.

    Only transfers resource keys listed for the active hazard. Types are never
    mixed across hazards (e.g. fire crews are never treated as hazmat teams).
    """
    new_state = _deep_copy_state(state)
    hazard = get_hazard(hazard_type)
    if not hazard.specialist_resources or len(zone_results) < 2:
        return new_state

    ranked = sorted(zone_results, key=lambda item: item.risk_score)
    source_id, destination_id = ranked[0].zone_id, ranked[-1].zone_id
    index = {z.zone_id: i for i, z in enumerate(new_state.zones)}
    source = new_state.zones[index[source_id]]
    destination = new_state.zones[index[destination_id]]

    source_resources = dict(source.specialist_resources)
    destination_resources = dict(destination.specialist_resources)
    remaining = MAX_TRANSFER_UNITS

    for resource in hazard.specialist_resources:
        if remaining <= 0:
            break
        available = max(0, int(source_resources.get(resource, 0)))
        moved = min(remaining, available)
        if moved <= 0:
            continue
        source_resources[resource] = available - moved
        destination_resources[resource] = int(destination_resources.get(resource, 0)) + moved
        remaining -= moved

    new_state.zones[index[source_id]] = dataclasses.replace(
        source, specialist_resources=source_resources
    )
    new_state.zones[index[destination_id]] = dataclasses.replace(
        destination, specialist_resources=destination_resources
    )
    return new_state


def _apply_resource_reallocation(
    state: SimulationState,
    zone_results: list[ZoneResult],
    hazard_type: str = "flood",
) -> SimulationState:
    """
    Move up to MAX_TRANSFER_UNITS resources from the lowest-risk zone
    (that has surplus) to the highest-risk zone.

    Flood rules:
    - Source zone must have > MIN_RESCUE_TEAMS rescue teams OR > MIN_AMBULANCES ambulances
    - Source zone never falls below MIN_RESCUE_TEAMS rescue teams or MIN_AMBULANCES ambulances
    - All resource counts remain non-negative
    - Process is deterministic (sort by risk_score)

    Non-flood rules:
    - Only reallocate that hazard's specialist_resources keys
    """
    if hazard_type != "flood":
        return _apply_specialist_reallocation(state, zone_results, hazard_type)

    new_state = _deep_copy_state(state)

    # Map zone_id → index in new_state.zones for mutation
    zone_index = {z.zone_id: i for i, z in enumerate(new_state.zones)}

    # Sort zone results by risk score ascending (lowest risk first = potential source)
    sorted_by_risk = sorted(zone_results, key=lambda zr: zr.risk_score)

    if len(sorted_by_risk) < 2:
        return new_state  # nothing to reallocate with only one zone

    highest_risk_id = sorted_by_risk[-1].zone_id
    dest_idx = zone_index[highest_risk_id]
    dest = new_state.zones[dest_idx]

    units_to_transfer = MAX_TRANSFER_UNITS
    units_transferred = 0

    # Iterate source zones from lowest risk upward
    for source_result in sorted_by_risk[:-1]:
        if units_transferred >= units_to_transfer:
            break
        if source_result.zone_id == highest_risk_id:
            continue

        src_idx = zone_index[source_result.zone_id]
        src = new_state.zones[src_idx]

        # Calculate surplus for each resource type
        rescue_surplus = src.rescue_teams - MIN_RESCUE_TEAMS
        ambulance_surplus = src.ambulances - MIN_AMBULANCES

        # Transfer rescue teams first
        if rescue_surplus > 0 and units_transferred < units_to_transfer:
            take = min(rescue_surplus, units_to_transfer - units_transferred)
            new_state.zones[src_idx] = dataclasses.replace(
                src, rescue_teams=src.rescue_teams - take
            )
            new_state.zones[dest_idx] = dataclasses.replace(
                dest, rescue_teams=dest.rescue_teams + take
            )
            # Re-read after modification for next iteration
            src = new_state.zones[src_idx]
            dest = new_state.zones[dest_idx]
            units_transferred += take

        # Transfer ambulances if still have budget
        if ambulance_surplus > 0 and units_transferred < units_to_transfer:
            take = min(ambulance_surplus, units_to_transfer - units_transferred)
            new_state.zones[src_idx] = dataclasses.replace(
                src, ambulances=src.ambulances - take
            )
            new_state.zones[dest_idx] = dataclasses.replace(
                dest, ambulances=dest.ambulances + take
            )
            src = new_state.zones[src_idx]
            dest = new_state.zones[dest_idx]
            units_transferred += take

    return new_state


def _apply_capacity_expansion(state: SimulationState) -> SimulationState:
    """
    Increase capacity for the most constrained facilities.
    Shelter capacity: +20%
    Hospital surge capacity: +15%

    Applied to ALL shelters and hospitals (all are subject to potential stress).
    Capacity values are rounded to nearest integer.
    """
    new_state = _deep_copy_state(state)

    new_shelters = []
    for s in new_state.shelters:
        expanded = max(1, round(s.capacity * 1.20))
        new_shelters.append(dataclasses.replace(s, capacity=expanded))
    new_state.shelters = new_shelters

    new_hospitals = []
    for h in new_state.hospitals:
        expanded_surge = max(0, round(h.surge_capacity * 1.15))
        new_hospitals.append(dataclasses.replace(h, surge_capacity=expanded_surge))
    new_state.hospitals = new_hospitals

    return new_state


def generate_simulation_states(
    baseline_state: SimulationState,
    zone_results: list[ZoneResult],
    bottlenecks: list[Bottleneck],  # retained for future use / extensibility
    hazard_type: str | None = None,
) -> dict[str, SimulationState]:
    """
    Generate one SimulationState per intervention strategy.

    Returns an ordered dict (insertion order = evaluation order):
      "baseline"              → original state
      "resource_reallocation" → zones modified
      "capacity_expansion"    → shelters/hospitals modified
      "combined"              → zones + shelters/hospitals modified
    """
    active_hazard = hazard_type or baseline_state.hazard_type or "flood"
    baseline = _deep_copy_state(baseline_state)
    resource_realloc = _apply_resource_reallocation(baseline_state, zone_results, active_hazard)
    capacity_exp = _apply_capacity_expansion(baseline_state)

    # Combined = apply both transformations to the baseline state
    # Use capacity expansion on top of the resource-reallocated state
    combined_base = _apply_resource_reallocation(baseline_state, zone_results, active_hazard)
    combined = _apply_capacity_expansion(combined_base)

    return {
        "baseline": baseline,
        "resource_reallocation": resource_realloc,
        "capacity_expansion": capacity_exp,
        "combined": combined,
    }
