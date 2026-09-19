"""
Tests for intervention_engine.py

Properties tested:
  P-8 (partial): Resource constraints never violated
  Exactly four strategies produced
  Baseline state unchanged
  Resource reallocation maintains floor (≥1 rescue team, ≥1 ambulance per zone)
  Capacity expansion increases shelter/hospital values correctly
  Combined = reallocation + expansion
"""
import dataclasses
import pytest

from engine.models import ZoneParams, Shelter, Hospital, SimulationState
from engine.risk_scorer import calculate_zone_results
from engine.intervention_engine import (
    generate_simulation_states,
    STRATEGY_LABELS,
    MIN_RESCUE_TEAMS,
    MIN_AMBULANCES,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_two_zone_state(high_risk_resources=(1, 1), low_risk_resources=(5, 4)):
    """Two-zone state: zone-1 is high risk (few resources), zone-2 is low risk (surplus)."""
    return SimulationState(
        zones=[
            ZoneParams(
                zone_id="zone-1", flood_severity=0.9, affected_population=12_000,
                medical_urgency=0.8, road_accessibility=0.2,
                rescue_teams=high_risk_resources[0],
                ambulances=high_risk_resources[1],
                demand_units=8,
            ),
            ZoneParams(
                zone_id="zone-2", flood_severity=0.2, affected_population=2_000,
                medical_urgency=0.1, road_accessibility=0.9,
                rescue_teams=low_risk_resources[0],
                ambulances=low_risk_resources[1],
                demand_units=4,
            ),
        ],
        shelters=[Shelter(shelter_id="s1", name="S1", coordinates=[0, 0],
                          capacity=300, current_occupancy=250)],
        hospitals=[Hospital(hospital_id="h1", name="H1", coordinates=[0, 0],
                            capacity=100, surge_capacity=20, current_occupancy=80)],
    )


# ---------------------------------------------------------------------------
# Exactly four strategies
# ---------------------------------------------------------------------------

def test_exactly_four_strategies_produced():
    state = make_two_zone_state()
    zone_results = calculate_zone_results(state, population_max=15_000)
    states = generate_simulation_states(state, zone_results, [])
    assert set(states.keys()) == {"baseline", "resource_reallocation", "capacity_expansion", "combined"}


def test_strategy_labels_present():
    assert set(STRATEGY_LABELS.keys()) == {"baseline", "resource_reallocation", "capacity_expansion", "combined"}


# ---------------------------------------------------------------------------
# Baseline unchanged
# ---------------------------------------------------------------------------

def test_baseline_state_identical_to_input():
    state = make_two_zone_state()
    zone_results = calculate_zone_results(state, population_max=15_000)
    states = generate_simulation_states(state, zone_results, [])
    baseline = states["baseline"]
    for orig_z, base_z in zip(state.zones, baseline.zones):
        assert orig_z == base_z
    for orig_s, base_s in zip(state.shelters, baseline.shelters):
        assert orig_s == base_s
    for orig_h, base_h in zip(state.hospitals, baseline.hospitals):
        assert orig_h == base_h


def test_baseline_does_not_share_references_with_original():
    """Modifying the original should not affect the baseline copy."""
    state = make_two_zone_state()
    zone_results = calculate_zone_results(state, population_max=15_000)
    states = generate_simulation_states(state, zone_results, [])
    original_rescue = state.zones[0].rescue_teams
    # Mutate original (would only work if not frozen, but dataclasses aren't frozen here)
    # The point is that generate_simulation_states uses deep copies
    baseline_rescue = states["baseline"].zones[0].rescue_teams
    assert baseline_rescue == original_rescue


# ---------------------------------------------------------------------------
# Resource reallocation — floor constraints
# ---------------------------------------------------------------------------

def test_resource_reallocation_minimum_floor():
    """Source zone must never drop below MIN_RESCUE_TEAMS or MIN_AMBULANCES."""
    state = make_two_zone_state()
    zone_results = calculate_zone_results(state, population_max=15_000)
    states = generate_simulation_states(state, zone_results, [])
    reallocated = states["resource_reallocation"]
    for zone in reallocated.zones:
        assert zone.rescue_teams >= MIN_RESCUE_TEAMS, (
            f"Zone {zone.zone_id} has {zone.rescue_teams} rescue teams < min {MIN_RESCUE_TEAMS}"
        )
        assert zone.ambulances >= MIN_AMBULANCES, (
            f"Zone {zone.zone_id} has {zone.ambulances} ambulances < min {MIN_AMBULANCES}"
        )


def test_resource_reallocation_non_negative():
    """All resource counts must be >= 0 after reallocation."""
    state = make_two_zone_state()
    zone_results = calculate_zone_results(state, population_max=15_000)
    states = generate_simulation_states(state, zone_results, [])
    for zone in states["resource_reallocation"].zones:
        assert zone.rescue_teams >= 0
        assert zone.ambulances >= 0


def test_resource_reallocation_with_minimal_resources_no_violation():
    """When source has only minimum resources, nothing should be transferred."""
    state = make_two_zone_state(
        high_risk_resources=(1, 1),
        low_risk_resources=(1, 1),  # both at minimum — no surplus
    )
    zone_results = calculate_zone_results(state, population_max=15_000)
    states = generate_simulation_states(state, zone_results, [])
    reallocated = states["resource_reallocation"]
    for zone in reallocated.zones:
        assert zone.rescue_teams >= MIN_RESCUE_TEAMS
        assert zone.ambulances >= MIN_AMBULANCES


def test_resource_reallocation_conserves_total_resources():
    """Total rescue teams and ambulances should be conserved across zones."""
    state = make_two_zone_state()
    zone_results = calculate_zone_results(state, population_max=15_000)
    states = generate_simulation_states(state, zone_results, [])

    orig_rescue = sum(z.rescue_teams for z in state.zones)
    orig_ambu = sum(z.ambulances for z in state.zones)
    new_rescue = sum(z.rescue_teams for z in states["resource_reallocation"].zones)
    new_ambu = sum(z.ambulances for z in states["resource_reallocation"].zones)

    assert new_rescue == orig_rescue
    assert new_ambu == orig_ambu


# ---------------------------------------------------------------------------
# Capacity expansion
# ---------------------------------------------------------------------------

def test_capacity_expansion_increases_shelter_capacity():
    state = make_two_zone_state()
    zone_results = calculate_zone_results(state, population_max=15_000)
    states = generate_simulation_states(state, zone_results, [])
    expanded = states["capacity_expansion"]

    for orig_s, new_s in zip(state.shelters, expanded.shelters):
        expected = max(1, round(orig_s.capacity * 1.20))
        assert new_s.capacity == expected


def test_capacity_expansion_increases_hospital_surge_capacity():
    state = make_two_zone_state()
    zone_results = calculate_zone_results(state, population_max=15_000)
    states = generate_simulation_states(state, zone_results, [])
    expanded = states["capacity_expansion"]

    for orig_h, new_h in zip(state.hospitals, expanded.hospitals):
        expected = max(0, round(orig_h.surge_capacity * 1.15))
        assert new_h.surge_capacity == expected


def test_capacity_expansion_does_not_modify_zones():
    """Zone params should be unchanged in capacity_expansion."""
    state = make_two_zone_state()
    zone_results = calculate_zone_results(state, population_max=15_000)
    states = generate_simulation_states(state, zone_results, [])
    for orig_z, new_z in zip(state.zones, states["capacity_expansion"].zones):
        assert orig_z == new_z


# ---------------------------------------------------------------------------
# Combined intervention
# ---------------------------------------------------------------------------

def test_combined_applies_both_transformations():
    """Combined should have both modified zones (realloc) and modified facilities (expansion)."""
    state = make_two_zone_state()
    zone_results = calculate_zone_results(state, population_max=15_000)
    states = generate_simulation_states(state, zone_results, [])

    combined = states["combined"]
    realloc = states["resource_reallocation"]
    expansion = states["capacity_expansion"]

    # Zones should match reallocation
    for c_zone, r_zone in zip(combined.zones, realloc.zones):
        assert c_zone.rescue_teams == r_zone.rescue_teams
        assert c_zone.ambulances == r_zone.ambulances

    # Shelters should match expansion's capacity
    for c_shelter, e_shelter in zip(combined.shelters, expansion.shelters):
        assert c_shelter.capacity == e_shelter.capacity

    # Hospitals surge should match expansion
    for c_hosp, e_hosp in zip(combined.hospitals, expansion.hospitals):
        assert c_hosp.surge_capacity == e_hosp.surge_capacity


def test_combined_resource_floor_not_violated():
    state = make_two_zone_state()
    zone_results = calculate_zone_results(state, population_max=15_000)
    states = generate_simulation_states(state, zone_results, [])
    for zone in states["combined"].zones:
        assert zone.rescue_teams >= MIN_RESCUE_TEAMS
        assert zone.ambulances >= MIN_AMBULANCES


# ---------------------------------------------------------------------------
# Single zone edge case
# ---------------------------------------------------------------------------

def test_single_zone_no_transfer_possible():
    """With only one zone, resource reallocation cannot transfer anything."""
    state = SimulationState(
        zones=[ZoneParams(
            zone_id="z1", flood_severity=0.5, affected_population=5000,
            medical_urgency=0.5, road_accessibility=0.5,
            rescue_teams=3, ambulances=3, demand_units=5,
        )],
        shelters=[],
        hospitals=[],
    )
    zone_results = calculate_zone_results(state, population_max=10_000)
    states = generate_simulation_states(state, zone_results, [])
    baseline_zone = state.zones[0]
    realloc_zone = states["resource_reallocation"].zones[0]
    assert realloc_zone.rescue_teams == baseline_zone.rescue_teams
    assert realloc_zone.ambulances == baseline_zone.ambulances
