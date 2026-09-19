"""
Multi-hazard regression and behavior tests.

Coefficients exercised here are prototype assumptions, not scientific guidance.
Existing flood tests remain the source of truth for legacy flood behavior.
"""
from __future__ import annotations
import dataclasses

import pytest

from engine import run_full_simulation
from engine.models import (
    ZoneParams, Shelter, Hospital, Scenario, Zone, SimulationState,
)
from engine.risk_scorer import calculate_hazard_risk_score, calculate_zone_results
from engine.response_time import estimate_response_time
from engine.bottleneck_detector import detect_bottlenecks
from engine.intervention_engine import (
    _deep_copy_state,
    generate_simulation_states,
    MAX_TRANSFER_UNITS,
)
from engine.hazards import HAZARDS, get_hazard
from handlers.simulation import handle_run_simulation
from seed_data import get_all_scenarios, get_default_scenario


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _base_zone(**overrides) -> ZoneParams:
    data = dict(
        zone_id="zone-1",
        flood_severity=0.5,
        affected_population=8_000,
        medical_urgency=0.6,
        road_accessibility=0.4,
        rescue_teams=2,
        ambulances=2,
        demand_units=8,
        hazard_factors={},
        specialist_resources={},
    )
    data.update(overrides)
    return ZoneParams(**data)


def _two_zone_hazard_state(
    hazard_type: str,
    high_factors: dict[str, float],
    low_factors: dict[str, float],
    high_specialists: dict[str, int],
    low_specialists: dict[str, int],
) -> SimulationState:
    return SimulationState(
        hazard_type=hazard_type,
        zones=[
            _base_zone(
                zone_id="zone-1",
                flood_severity=0.2,
                affected_population=10_000,
                medical_urgency=0.7,
                road_accessibility=0.3,
                rescue_teams=2,
                ambulances=1,
                demand_units=8,
                hazard_factors=high_factors,
                specialist_resources=high_specialists,
            ),
            _base_zone(
                zone_id="zone-2",
                flood_severity=0.1,
                affected_population=2_000,
                medical_urgency=0.2,
                road_accessibility=0.8,
                rescue_teams=4,
                ambulances=3,
                demand_units=4,
                hazard_factors=low_factors,
                specialist_resources=low_specialists,
            ),
        ],
        shelters=[Shelter("s1", "S1", [0, 0], 300, 250)],
        hospitals=[Hospital("h1", "H1", [0, 0], 100, 20, 80)],
    )


def _scenario_from_state(state: SimulationState, scenario_id: str = "test-hazard") -> Scenario:
    zones = []
    for z in state.zones:
        zones.append(
            Zone(
                zone_id=z.zone_id,
                name=z.zone_id,
                coordinates=[[0, 0], [0, 1], [1, 1], [1, 0]],
                centroid=[0.5, 0.5],
                flood_severity=z.flood_severity,
                affected_population=z.affected_population,
                medical_urgency=z.medical_urgency,
                road_accessibility=z.road_accessibility,
                rescue_teams=z.rescue_teams,
                ambulances=z.ambulances,
                demand_units=z.demand_units,
                hazard_factors=dict(z.hazard_factors),
                specialist_resources=dict(z.specialist_resources),
            )
        )
    return Scenario(
        scenario_id=scenario_id,
        name=f"{state.hazard_type} test",
        description="multi-hazard test scenario",
        severity="high",
        created_at="2026-09-17T00:00:00Z",
        zones=zones,
        shelters=list(state.shelters),
        hospitals=list(state.hospitals),
        population_max=15_000,
        hazard_type=state.hazard_type,
    )


class _MemoryStore:
    def __init__(self, scenario: Scenario):
        self._scenario = scenario
        self._results = []

    def get_scenario(self, scenario_id: str):
        return self._scenario if scenario_id == self._scenario.scenario_id else None

    def save_result(self, result):
        self._results.append(result)


# ---------------------------------------------------------------------------
# Deep copy / pipeline hazard_type preservation
# ---------------------------------------------------------------------------

def test_deep_copy_preserves_hazard_type():
    state = SimulationState(
        zones=[_base_zone()],
        shelters=[],
        hospitals=[],
        hazard_type="fire",
    )
    copied = _deep_copy_state(state)
    assert copied.hazard_type == "fire"
    assert copied.zones[0].specialist_resources is not state.zones[0].specialist_resources


def test_run_full_simulation_returns_hazard_type():
    state = _two_zone_hazard_state(
        "earthquake",
        {"structural_damage": 0.9, "trapped_person_likelihood": 0.8, "aftershock_risk": 0.5},
        {"structural_damage": 0.2, "trapped_person_likelihood": 0.1, "aftershock_risk": 0.1},
        {"search_and_rescue_teams": 1},
        {"search_and_rescue_teams": 5},
    )
    scenario = _scenario_from_state(state, "eq-sim")
    result = run_full_simulation(scenario, state.zones)
    assert result.hazard_type == "earthquake"
    assert all(iv.strategy for iv in result.interventions)


def test_api_simulation_preserves_hazard_type():
    state = _two_zone_hazard_state(
        "fire",
        {"fire_intensity": 0.9, "smoke_exposure": 0.8, "spread_potential": 0.7},
        {"fire_intensity": 0.2, "smoke_exposure": 0.1, "spread_potential": 0.1},
        {"fire_crews": 0},
        {"fire_crews": 4},
    )
    scenario = _scenario_from_state(state, "fire-api")
    store = _MemoryStore(scenario)
    raw = [
        {
            "zone_id": z.zone_id,
            "flood_severity": z.flood_severity,
            "affected_population": z.affected_population,
            "medical_urgency": z.medical_urgency,
            "road_accessibility": z.road_accessibility,
            "rescue_teams": z.rescue_teams,
            "ambulances": z.ambulances,
            "demand_units": z.demand_units,
            "hazard_factors": z.hazard_factors,
            "specialist_resources": z.specialist_resources,
        }
        for z in state.zones
    ]
    result = handle_run_simulation("fire-api", raw, store)
    assert result.hazard_type == "fire"
    assert any(b.type == "fire_crew_shortage" for b in result.bottlenecks)


def test_seeded_scenarios_cover_all_hazards():
    scenarios = get_all_scenarios()
    types = {s.hazard_type for s in scenarios}
    assert types == set(HAZARDS.keys())
    flood = get_default_scenario()
    assert flood.hazard_type == "flood"


# ---------------------------------------------------------------------------
# Flood legacy compatibility
# ---------------------------------------------------------------------------

def test_flood_legacy_risk_unchanged_by_specialist_fields():
    zone = _base_zone(flood_severity=0.8, specialist_resources={"fire_crews": 20})
    score_a, _ = calculate_hazard_risk_score(zone, 15_000, "flood")
    score_b, _ = calculate_hazard_risk_score(
        dataclasses.replace(zone, specialist_resources={}), 15_000, "flood"
    )
    assert score_a == score_b


# ---------------------------------------------------------------------------
# Fire
# ---------------------------------------------------------------------------

def test_fire_hazard_factors_affect_risk():
    low = _base_zone(
        hazard_factors={"fire_intensity": 0.1, "smoke_exposure": 0.1, "spread_potential": 0.1},
        specialist_resources={"fire_crews": 4},
    )
    high = dataclasses.replace(
        low,
        hazard_factors={"fire_intensity": 0.95, "smoke_exposure": 0.9, "spread_potential": 0.9},
    )
    low_score, _ = calculate_hazard_risk_score(low, 15_000, "fire")
    high_score, _ = calculate_hazard_risk_score(high, 15_000, "fire")
    assert high_score > low_score


def test_fire_crew_shortage_detected():
    zone = _base_zone(
        hazard_factors={"fire_intensity": 0.9, "smoke_exposure": 0.8, "spread_potential": 0.85},
        specialist_resources={"fire_crews": 0},
        medical_urgency=0.8,
    )
    state = SimulationState(zones=[zone], shelters=[], hospitals=[], hazard_type="fire")
    results = calculate_zone_results(state, 15_000)
    bottlenecks = detect_bottlenecks(results, [], [], "fire", state.zones)
    assert any(b.type == "fire_crew_shortage" for b in bottlenecks)
    assert any(b.type == "uncontrolled_spread" for b in bottlenecks)


def test_fire_crew_reallocation_moves_specialists_only():
    state = _two_zone_hazard_state(
        "fire",
        {"fire_intensity": 0.95, "smoke_exposure": 0.8, "spread_potential": 0.8},
        {"fire_intensity": 0.1, "smoke_exposure": 0.1, "spread_potential": 0.1},
        {"fire_crews": 1},
        {"fire_crews": 5},
    )
    results = calculate_zone_results(state, 15_000)
    states = generate_simulation_states(state, results, [], "fire")
    realloc = states["resource_reallocation"]
    assert realloc.hazard_type == "fire"
    high = next(z for z in realloc.zones if z.zone_id == "zone-1")
    low = next(z for z in realloc.zones if z.zone_id == "zone-2")
    assert high.specialist_resources["fire_crews"] > 1
    assert low.specialist_resources["fire_crews"] < 5
    # Common assets unchanged by fire reallocation
    assert high.rescue_teams == state.zones[0].rescue_teams
    assert high.ambulances == state.zones[0].ambulances
    total = sum(z.specialist_resources["fire_crews"] for z in realloc.zones)
    assert total == 6


def test_fire_response_time_reacts_to_conditions():
    mild = _base_zone(
        hazard_factors={"fire_intensity": 0.1, "smoke_exposure": 0.1, "spread_potential": 0.1},
        specialist_resources={"fire_crews": 6},
    )
    severe = dataclasses.replace(
        mild,
        hazard_factors={"fire_intensity": 0.95, "smoke_exposure": 0.9, "spread_potential": 0.9},
        specialist_resources={"fire_crews": 0},
    )
    assert estimate_response_time(severe, "fire") > estimate_response_time(mild, "fire")
    assert estimate_response_time(severe, "fire") > estimate_response_time(severe, "flood")


# ---------------------------------------------------------------------------
# Earthquake
# ---------------------------------------------------------------------------

def test_earthquake_hazard_factors_affect_risk():
    low = _base_zone(
        hazard_factors={
            "structural_damage": 0.1,
            "trapped_person_likelihood": 0.1,
            "aftershock_risk": 0.1,
        },
        specialist_resources={"search_and_rescue_teams": 4},
    )
    high = dataclasses.replace(
        low,
        hazard_factors={
            "structural_damage": 0.95,
            "trapped_person_likelihood": 0.9,
            "aftershock_risk": 0.8,
        },
    )
    assert calculate_hazard_risk_score(high, 15_000, "earthquake")[0] > calculate_hazard_risk_score(low, 15_000, "earthquake")[0]


def test_earthquake_sar_shortage_and_reallocation():
    state = _two_zone_hazard_state(
        "earthquake",
        {"structural_damage": 0.9, "trapped_person_likelihood": 0.8, "aftershock_risk": 0.6},
        {"structural_damage": 0.2, "trapped_person_likelihood": 0.1, "aftershock_risk": 0.1},
        {"search_and_rescue_teams": 0},
        {"search_and_rescue_teams": 4},
    )
    results = calculate_zone_results(state, 15_000)
    bottlenecks = detect_bottlenecks(results, state.shelters, state.hospitals, "earthquake", state.zones)
    assert any(b.type == "search_and_rescue_shortage" for b in bottlenecks)

    states = generate_simulation_states(state, results, bottlenecks, "earthquake")
    high = next(z for z in states["resource_reallocation"].zones if z.zone_id == "zone-1")
    assert high.specialist_resources["search_and_rescue_teams"] >= MAX_TRANSFER_UNITS


def test_earthquake_response_time_reacts_to_conditions():
    mild = _base_zone(
        hazard_factors={
            "structural_damage": 0.1,
            "trapped_person_likelihood": 0.1,
            "aftershock_risk": 0.1,
        },
        specialist_resources={"search_and_rescue_teams": 5},
    )
    severe = dataclasses.replace(
        mild,
        hazard_factors={
            "structural_damage": 0.95,
            "trapped_person_likelihood": 0.9,
            "aftershock_risk": 0.8,
        },
        specialist_resources={"search_and_rescue_teams": 0},
    )
    assert estimate_response_time(severe, "earthquake") > estimate_response_time(mild, "earthquake")


# ---------------------------------------------------------------------------
# Cyclone
# ---------------------------------------------------------------------------

def test_cyclone_hazard_factors_affect_risk():
    low = _base_zone(
        hazard_factors={
            "wind_severity": 0.1,
            "storm_surge_exposure": 0.1,
            "power_outage_severity": 0.1,
        },
        specialist_resources={"evacuation_teams": 3, "utility_crews": 2},
    )
    high = dataclasses.replace(
        low,
        hazard_factors={
            "wind_severity": 0.95,
            "storm_surge_exposure": 0.9,
            "power_outage_severity": 0.85,
        },
    )
    assert calculate_hazard_risk_score(high, 15_000, "cyclone")[0] > calculate_hazard_risk_score(low, 15_000, "cyclone")[0]


def test_cyclone_evacuation_utility_constraints_and_intervention():
    state = _two_zone_hazard_state(
        "cyclone",
        {"wind_severity": 0.9, "storm_surge_exposure": 0.8, "power_outage_severity": 0.85},
        {"wind_severity": 0.2, "storm_surge_exposure": 0.1, "power_outage_severity": 0.2},
        {"evacuation_teams": 0, "utility_crews": 0},
        {"evacuation_teams": 4, "utility_crews": 3},
    )
    overcrowded = Shelter("s1", "S1", [0, 0], 100, 180)
    state = dataclasses.replace(state, shelters=[overcrowded])
    results = calculate_zone_results(state, 15_000)
    bottlenecks = detect_bottlenecks(results, state.shelters, state.hospitals, "cyclone", state.zones)
    types = {b.type for b in bottlenecks}
    assert "evacuation_capacity" in types
    assert "utility_restoration_shortage" in types
    assert "shelter_capacity" in types

    states = generate_simulation_states(state, results, bottlenecks, "cyclone")
    high = next(z for z in states["resource_reallocation"].zones if z.zone_id == "zone-1")
    # Transfers evacuation first (registry order), up to MAX_TRANSFER_UNITS
    moved_evac = high.specialist_resources["evacuation_teams"]
    moved_util = high.specialist_resources["utility_crews"]
    assert moved_evac + moved_util >= 2
    assert high.ambulances == state.zones[0].ambulances  # not treated as interchangeable


# ---------------------------------------------------------------------------
# Industrial accident
# ---------------------------------------------------------------------------

def test_industrial_toxic_factors_affect_risk():
    low = _base_zone(
        hazard_factors={
            "toxic_release_severity": 0.1,
            "exposure_level": 0.1,
            "containment_failure": 0.1,
        },
        specialist_resources={"hazmat_teams": 3, "containment_units": 2},
    )
    high = dataclasses.replace(
        low,
        hazard_factors={
            "toxic_release_severity": 0.95,
            "exposure_level": 0.9,
            "containment_failure": 0.85,
        },
    )
    assert (
        calculate_hazard_risk_score(high, 15_000, "industrial_accident")[0]
        > calculate_hazard_risk_score(low, 15_000, "industrial_accident")[0]
    )


def test_industrial_hazmat_containment_shortage_and_intervention():
    state = _two_zone_hazard_state(
        "industrial_accident",
        {"toxic_release_severity": 0.9, "exposure_level": 0.85, "containment_failure": 0.8},
        {"toxic_release_severity": 0.2, "exposure_level": 0.1, "containment_failure": 0.1},
        {"hazmat_teams": 0, "containment_units": 0},
        {"hazmat_teams": 4, "containment_units": 3},
    )
    results = calculate_zone_results(state, 15_000)
    bottlenecks = detect_bottlenecks(
        results, state.shelters, state.hospitals, "industrial_accident", state.zones
    )
    types = {b.type for b in bottlenecks}
    assert "hazmat_shortage" in types
    assert "containment_shortage" in types
    assert "toxic_exposure" in types

    states = generate_simulation_states(state, results, bottlenecks, "industrial_accident")
    high = next(z for z in states["resource_reallocation"].zones if z.zone_id == "zone-1")
    assert high.specialist_resources["hazmat_teams"] >= 1
    # Fire crews must not appear / be invented during industrial reallocation
    assert "fire_crews" not in high.specialist_resources


def test_specialists_are_not_interchangeable_across_hazards():
    """Ambulances do not reduce specialist shortage for industrial accidents."""
    with_ambu = _base_zone(
        ambulances=20,
        rescue_teams=20,
        specialist_resources={"hazmat_teams": 0, "containment_units": 0},
        hazard_factors={
            "toxic_release_severity": 0.8,
            "exposure_level": 0.7,
            "containment_failure": 0.7,
        },
    )
    with_hazmat = dataclasses.replace(
        with_ambu,
        ambulances=0,
        rescue_teams=0,
        specialist_resources={"hazmat_teams": 8, "containment_units": 8},
    )
    score_ambu, comps_ambu = calculate_hazard_risk_score(with_ambu, 15_000, "industrial_accident")
    score_hazmat, comps_hazmat = calculate_hazard_risk_score(with_hazmat, 15_000, "industrial_accident")
    assert comps_ambu.resource_shortage_score > comps_hazmat.resource_shortage_score
    assert score_ambu > score_hazmat


def test_intervention_states_preserve_hazard_type_for_all_hazards():
    for hazard_type in ("fire", "earthquake", "cyclone", "industrial_accident"):
        hazard = get_hazard(hazard_type)
        factors = {name: 0.8 for name in hazard.factors}
        low_factors = {name: 0.1 for name in hazard.factors}
        high_spec = {key: 0 for key in hazard.specialist_resources}
        low_spec = {key: 4 for key in hazard.specialist_resources}
        state = _two_zone_hazard_state(hazard_type, factors, low_factors, high_spec, low_spec)
        results = calculate_zone_results(state, 15_000)
        states = generate_simulation_states(state, results, [], hazard_type)
        for strategy_state in states.values():
            assert strategy_state.hazard_type == hazard_type
