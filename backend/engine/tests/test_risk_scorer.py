"""
Tests for risk_scorer.py

Properties tested:
  P-1: Risk score always in [0, 100]
  P-2: Increasing flood severity never decreases risk
  P-3: Increasing medical urgency never decreases risk
  P-6: Risk level boundaries are exactly correct (including decimals)
  P-7: Determinism — same input → same output

Edge cases: zero demand, maximum population, zero resources,
            fully/inaccessible roads, population above normalization max.
"""
import dataclasses
import pytest
from hypothesis import given, assume, settings
from hypothesis import strategies as st

from engine.models import ZoneParams, SimulationState, Shelter, Hospital
from engine.risk_scorer import (
    calculate_risk_score,
    calculate_zone_results,
    _risk_level,
    WEIGHTS,
)
from .conftest import zone_params_strategy, shelter_strategy, hospital_strategy


# ---------------------------------------------------------------------------
# Weight integrity (P-3 from spec)
# ---------------------------------------------------------------------------

def test_weights_sum_to_one():
    total = sum(WEIGHTS.values())
    assert abs(total - 1.0) < 1e-10, f"Weights sum to {total}, expected 1.0"


# ---------------------------------------------------------------------------
# Risk level boundaries (P-6)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("score,expected_level", [
    (0.0, "low"),
    (12.5, "low"),
    (25.0, "low"),       # boundary inclusive
    (25.5, "medium"),    # just above
    (50.0, "medium"),    # boundary inclusive
    (50.5, "high"),      # just above
    (75.0, "high"),      # boundary inclusive
    (75.5, "critical"),  # just above
    (100.0, "critical"),
])
def test_risk_level_boundaries(score, expected_level):
    assert _risk_level(score) == expected_level


# ---------------------------------------------------------------------------
# P-1: Risk score bounds
# ---------------------------------------------------------------------------

@given(zone_params_strategy())
@settings(max_examples=500)
def test_risk_score_bounds(zone):
    score, _ = calculate_risk_score(zone, population_max=100_000)
    assert 0.0 <= score <= 100.0, f"Score {score} out of bounds"


def test_risk_score_zero_inputs():
    zone = ZoneParams(
        zone_id="z0", flood_severity=0.0, affected_population=0,
        medical_urgency=0.0, road_accessibility=1.0,
        rescue_teams=10, ambulances=10, demand_units=1,
    )
    score, _ = calculate_risk_score(zone, population_max=100_000)
    assert score == 0.0


def test_risk_score_max_inputs():
    zone = ZoneParams(
        zone_id="z_max", flood_severity=1.0, affected_population=100_000,
        medical_urgency=1.0, road_accessibility=0.0,
        rescue_teams=0, ambulances=0, demand_units=10,
    )
    score, _ = calculate_risk_score(zone, population_max=100_000)
    assert score == 100.0


def test_risk_score_population_above_max():
    """Population above population_max should be clamped to 1.0 contribution."""
    zone = ZoneParams(
        zone_id="z_over", flood_severity=0.0, affected_population=200_000,
        medical_urgency=0.0, road_accessibility=1.0,
        rescue_teams=10, ambulances=10, demand_units=1,
    )
    score, _ = calculate_risk_score(zone, population_max=100_000)
    assert 0.0 <= score <= 100.0


def test_risk_score_zero_demand_units():
    """Zero demand_units should not raise and should produce valid score."""
    zone = ZoneParams(
        zone_id="z0d", flood_severity=0.5, affected_population=5_000,
        medical_urgency=0.5, road_accessibility=0.5,
        rescue_teams=3, ambulances=2, demand_units=0,
    )
    # demand_units=0 → resource_coverage treated as 1.0 → no resource shortage
    score, components = calculate_risk_score(zone, population_max=100_000)
    assert 0.0 <= score <= 100.0
    assert components.resource_shortage_score == 0.0


# ---------------------------------------------------------------------------
# P-2: Flood severity monotonicity
# ---------------------------------------------------------------------------

@given(zone_params_strategy(), st.floats(min_value=0.0, max_value=1.0, allow_nan=False))
@settings(max_examples=500)
def test_flood_severity_monotonicity(zone, higher_severity):
    assume(higher_severity >= zone.flood_severity)
    zone_high = dataclasses.replace(zone, flood_severity=higher_severity)
    s1, _ = calculate_risk_score(zone, population_max=100_000)
    s2, _ = calculate_risk_score(zone_high, population_max=100_000)
    assert s2 >= s1 - 1e-9, (
        f"Risk decreased when flood_severity increased: {zone.flood_severity}→{higher_severity}, "
        f"{s1}→{s2}"
    )


# ---------------------------------------------------------------------------
# P-3: Medical urgency monotonicity
# ---------------------------------------------------------------------------

@given(zone_params_strategy(), st.floats(min_value=0.0, max_value=1.0, allow_nan=False))
@settings(max_examples=500)
def test_medical_urgency_monotonicity(zone, higher_urgency):
    assume(higher_urgency >= zone.medical_urgency)
    zone_high = dataclasses.replace(zone, medical_urgency=higher_urgency)
    s1, _ = calculate_risk_score(zone, population_max=100_000)
    s2, _ = calculate_risk_score(zone_high, population_max=100_000)
    assert s2 >= s1 - 1e-9


# ---------------------------------------------------------------------------
# P-7: Determinism
# ---------------------------------------------------------------------------

@given(zone_params_strategy())
def test_risk_score_determinism(zone):
    s1, c1 = calculate_risk_score(zone, population_max=100_000)
    s2, c2 = calculate_risk_score(zone, population_max=100_000)
    assert s1 == s2
    assert c1 == c2


# ---------------------------------------------------------------------------
# calculate_zone_results
# ---------------------------------------------------------------------------

def test_calculate_zone_results_returns_all_zones():
    zones = [
        ZoneParams(zone_id=f"z{i}", flood_severity=0.5, affected_population=5000,
                   medical_urgency=0.5, road_accessibility=0.5,
                   rescue_teams=3, ambulances=2, demand_units=5)
        for i in range(5)
    ]
    state = SimulationState(zones=zones, shelters=[], hospitals=[])
    results = calculate_zone_results(state, population_max=10_000)
    assert len(results) == 5
    zone_ids = {r.zone_id for r in results}
    assert zone_ids == {f"z{i}" for i in range(5)}


def test_calculate_zone_results_single_zone():
    zone = ZoneParams(
        zone_id="solo", flood_severity=0.6, affected_population=8000,
        medical_urgency=0.6, road_accessibility=0.3,
        rescue_teams=2, ambulances=2, demand_units=6,
    )
    state = SimulationState(zones=[zone], shelters=[], hospitals=[])
    results = calculate_zone_results(state, population_max=10_000)
    assert len(results) == 1
    assert 0.0 <= results[0].risk_score <= 100.0
    assert results[0].risk_level in ("low", "medium", "high", "critical")
    assert 5.0 <= results[0].response_time_minutes <= 120.0


def test_risk_components_sum_equals_raw_score():
    """Sum of weighted components * 100 must equal risk_score (within rounding)."""
    zone = ZoneParams(
        zone_id="z_comp", flood_severity=0.5, affected_population=5000,
        medical_urgency=0.5, road_accessibility=0.5,
        rescue_teams=2, ambulances=2, demand_units=8,
    )
    score, components = calculate_risk_score(zone, population_max=10_000)
    component_sum = (
        components.affected_population_score
        + components.flood_severity_score
        + components.medical_urgency_score
        + components.road_accessibility_score
        + components.resource_shortage_score
    )
    assert abs(component_sum * 100 - score) < 0.01


# ---------------------------------------------------------------------------
# Edge cases: road accessibility
# ---------------------------------------------------------------------------

def test_fully_accessible_roads_zero_road_contribution():
    zone = ZoneParams(
        zone_id="z_road", flood_severity=0.0, affected_population=0,
        medical_urgency=0.0, road_accessibility=1.0,
        rescue_teams=5, ambulances=5, demand_units=5,
    )
    score, components = calculate_risk_score(zone, population_max=100_000)
    assert components.road_accessibility_score == 0.0


def test_inaccessible_roads_max_road_contribution():
    zone = ZoneParams(
        zone_id="z_blocked", flood_severity=0.0, affected_population=0,
        medical_urgency=0.0, road_accessibility=0.0,
        rescue_teams=5, ambulances=5, demand_units=5,
    )
    _, components = calculate_risk_score(zone, population_max=100_000)
    assert abs(components.road_accessibility_score - 0.15) < 1e-9
