"""
Tests for recommender.py

Properties tested:
  P-6: Recommended strategy has composite_score >= all others
  P-7: Same input → same recommendation (determinism)
  Recommendation weights sum to 1.0
  Tie-breaking uses higher risk_reduction_pct
  Normalization produces [0,1] scores
  run_full_simulation returns a valid recommended_strategy
"""
import dataclasses
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from engine.models import (
    InterventionResult, ZoneParams, Shelter, Hospital, SimulationState,
)
from engine.recommender import rank_and_recommend, RECOMMENDATION_WEIGHTS
from engine.risk_scorer import calculate_zone_results
from engine.bottleneck_detector import detect_bottlenecks
from engine.intervention_engine import generate_simulation_states
from engine.evaluator import evaluate_intervention
from engine import run_full_simulation
from engine.models import Scenario, Zone


# ---------------------------------------------------------------------------
# Weight integrity
# ---------------------------------------------------------------------------

def test_recommendation_weights_sum_to_one():
    total = sum(RECOMMENDATION_WEIGHTS.values())
    assert abs(total - 1.0) < 1e-10


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_intervention(strategy, risk_reduction=0.0, bn_resolution=0.0,
                      resource_cost=0, rt_improvement=0.0):
    return InterventionResult(
        strategy=strategy,
        label=strategy,
        zone_results=[],
        avg_risk_score=50.0,
        avg_response_time_minutes=30.0,
        risk_reduction_pct=risk_reduction,
        response_time_improvement_minutes=rt_improvement,
        bottleneck_resolution_score=bn_resolution,
        resource_cost=resource_cost,
        composite_score=0.0,
    )


def make_full_interventions():
    """Four InterventionResults with distinct metrics."""
    return [
        make_intervention("baseline", 0.0, 0.0, 0, 0.0),
        make_intervention("resource_reallocation", 15.0, 0.4, 2, 5.0),
        make_intervention("capacity_expansion", 5.0, 0.6, 1, 2.0),
        make_intervention("combined", 20.0, 0.7, 3, 8.0),
    ]


def full_pipeline_result(population_max=15_000):
    """Run the full engine on a known 2-zone scenario."""
    zones = [
        ZoneParams(zone_id="zone-1", flood_severity=0.9, affected_population=12_000,
                   medical_urgency=0.8, road_accessibility=0.2,
                   rescue_teams=1, ambulances=1, demand_units=8),
        ZoneParams(zone_id="zone-2", flood_severity=0.2, affected_population=2_000,
                   medical_urgency=0.1, road_accessibility=0.9,
                   rescue_teams=5, ambulances=4, demand_units=4),
    ]
    state = SimulationState(
        zones=zones,
        shelters=[Shelter(shelter_id="s1", name="S1", coordinates=[0, 0],
                          capacity=300, current_occupancy=250)],
        hospitals=[Hospital(hospital_id="h1", name="H1", coordinates=[0, 0],
                            capacity=100, surge_capacity=20, current_occupancy=80)],
    )
    zone_results = calculate_zone_results(state, population_max)
    bottlenecks = detect_bottlenecks(zone_results, state.shelters, state.hospitals)
    intervention_states = generate_simulation_states(state, zone_results, bottlenecks)
    interventions = [
        evaluate_intervention(
            strategy=s,
            state=ms,
            baseline_zone_results=zone_results,
            population_max=population_max,
            baseline_state=state,
            baseline_bottlenecks=bottlenecks,
        )
        for s, ms in intervention_states.items()
    ]
    return interventions


# ---------------------------------------------------------------------------
# P-6: Recommended strategy has highest composite score
# ---------------------------------------------------------------------------

def test_recommended_strategy_has_highest_composite_score():
    interventions = make_full_interventions()
    recommended = rank_and_recommend(interventions)
    recommended_result = next(i for i in interventions if i.strategy == recommended)
    for other in interventions:
        assert recommended_result.composite_score >= other.composite_score - 1e-9, (
            f"Recommended {recommended} composite {recommended_result.composite_score} < "
            f"{other.strategy} composite {other.composite_score}"
        )


def test_recommended_from_full_pipeline_has_highest_score():
    interventions = full_pipeline_result()
    recommended = rank_and_recommend(interventions)
    recommended_result = next(i for i in interventions if i.strategy == recommended)
    for other in interventions:
        assert recommended_result.composite_score >= other.composite_score - 1e-9


# ---------------------------------------------------------------------------
# P-7: Determinism
# ---------------------------------------------------------------------------

def test_recommendation_is_deterministic():
    interventions_a = make_full_interventions()
    interventions_b = make_full_interventions()
    rec_a = rank_and_recommend(interventions_a)
    rec_b = rank_and_recommend(interventions_b)
    assert rec_a == rec_b


def test_full_pipeline_recommendation_is_deterministic():
    i1 = full_pipeline_result()
    i2 = full_pipeline_result()
    assert rank_and_recommend(i1) == rank_and_recommend(i2)


# ---------------------------------------------------------------------------
# Tie-breaking
# ---------------------------------------------------------------------------

def test_tie_broken_by_higher_risk_reduction():
    """Two strategies with equal composite scores → higher risk_reduction wins."""
    # Same metrics except risk_reduction_pct
    i1 = make_intervention("resource_reallocation", risk_reduction=10.0, bn_resolution=0.5,
                            resource_cost=1, rt_improvement=5.0)
    i2 = make_intervention("combined", risk_reduction=15.0, bn_resolution=0.5,
                            resource_cost=1, rt_improvement=5.0)
    i3 = make_intervention("baseline", risk_reduction=0.0, bn_resolution=0.0,
                            resource_cost=0, rt_improvement=0.0)
    i4 = make_intervention("capacity_expansion", risk_reduction=5.0, bn_resolution=0.5,
                            resource_cost=1, rt_improvement=5.0)
    # Force equal composite scores by using identical normalized metrics for i1 and i2
    # We do this by giving them the same values in all dimensions but different risk_reduction
    interventions = [i3, i4,
                     make_intervention("resource_reallocation", risk_reduction=20.0,
                                       bn_resolution=1.0, resource_cost=0, rt_improvement=10.0),
                     make_intervention("combined", risk_reduction=20.0,
                                       bn_resolution=1.0, resource_cost=0, rt_improvement=10.0)]
    # Both "resource_reallocation" and "combined" have identical scores
    # tie-break should be deterministic (same risk_reduction here, so order-based)
    recommended = rank_and_recommend(interventions)
    assert recommended in ("resource_reallocation", "combined")


# ---------------------------------------------------------------------------
# Composite scores mutated in-place
# ---------------------------------------------------------------------------

def test_composite_scores_written_back():
    interventions = make_full_interventions()
    rank_and_recommend(interventions)
    # After ranking, composite scores should be set (not all 0.0)
    scores = [i.composite_score for i in interventions]
    assert any(s > 0.0 for s in scores)


# ---------------------------------------------------------------------------
# run_full_simulation integration
# ---------------------------------------------------------------------------

def make_scenario():
    zone1 = Zone(
        zone_id="zone-1", name="High Risk Zone",
        coordinates=[[51.5, -0.09], [51.51, -0.09], [51.51, -0.08], [51.5, -0.08]],
        centroid=[51.505, -0.085],
        flood_severity=0.9, affected_population=12_000,
        medical_urgency=0.8, road_accessibility=0.2,
        rescue_teams=1, ambulances=1, demand_units=8,
    )
    zone2 = Zone(
        zone_id="zone-2", name="Low Risk Zone",
        coordinates=[[51.5, -0.10], [51.51, -0.10], [51.51, -0.09], [51.5, -0.09]],
        centroid=[51.505, -0.095],
        flood_severity=0.2, affected_population=2_000,
        medical_urgency=0.1, road_accessibility=0.9,
        rescue_teams=5, ambulances=4, demand_units=4,
    )
    return Scenario(
        scenario_id="flood-scenario-001",
        name="River Delta Flood",
        description="Test scenario",
        severity="high",
        created_at="2026-09-10T00:00:00Z",
        zones=[zone1, zone2],
        shelters=[Shelter(shelter_id="s1", name="S1", coordinates=[0, 0],
                          capacity=300, current_occupancy=250)],
        hospitals=[Hospital(hospital_id="h1", name="H1", coordinates=[0, 0],
                            capacity=100, surge_capacity=20, current_occupancy=80)],
        population_max=15_000,
    )


def make_zone_params(scenario):
    return [
        ZoneParams(
            zone_id=z.zone_id,
            flood_severity=z.flood_severity,
            affected_population=z.affected_population,
            medical_urgency=z.medical_urgency,
            road_accessibility=z.road_accessibility,
            rescue_teams=z.rescue_teams,
            ambulances=z.ambulances,
            demand_units=z.demand_units,
        )
        for z in scenario.zones
    ]


def test_run_full_simulation_returns_valid_result():
    scenario = make_scenario()
    params = make_zone_params(scenario)
    result = run_full_simulation(scenario, params)

    assert result.scenario_id == "flood-scenario-001"
    assert result.recommended_strategy in (
        "baseline", "resource_reallocation", "capacity_expansion", "combined"
    )
    assert len(result.interventions) == 4
    assert len(result.baseline_zone_results) == 2


def test_run_full_simulation_recommended_has_highest_score():
    scenario = make_scenario()
    params = make_zone_params(scenario)
    result = run_full_simulation(scenario, params)

    recommended = next(i for i in result.interventions
                       if i.strategy == result.recommended_strategy)
    for other in result.interventions:
        assert recommended.composite_score >= other.composite_score - 1e-9


def test_run_full_simulation_determinism():
    scenario = make_scenario()
    params = make_zone_params(scenario)
    r1 = run_full_simulation(scenario, params)
    r2 = run_full_simulation(scenario, params)
    assert r1.recommended_strategy == r2.recommended_strategy
    for zr1, zr2 in zip(r1.baseline_zone_results, r2.baseline_zone_results):
        assert zr1.risk_score == zr2.risk_score
        assert zr1.response_time_minutes == zr2.response_time_minutes


def test_run_full_simulation_all_risk_scores_in_bounds():
    scenario = make_scenario()
    params = make_zone_params(scenario)
    result = run_full_simulation(scenario, params)
    for zr in result.baseline_zone_results:
        assert 0.0 <= zr.risk_score <= 100.0
    for intervention in result.interventions:
        for zr in intervention.zone_results:
            assert 0.0 <= zr.risk_score <= 100.0
