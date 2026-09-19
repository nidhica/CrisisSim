"""
Tests for evaluator.py

Properties tested:
  P-8: Intervention projected result = running engine on the modified state
  Baseline has risk_reduction_pct = 0 and rt_improvement = 0
  All metrics in valid ranges
"""
import pytest

from engine.models import ZoneParams, Shelter, Hospital, SimulationState
from engine.risk_scorer import calculate_zone_results
from engine.bottleneck_detector import detect_bottlenecks
from engine.intervention_engine import generate_simulation_states
from engine.evaluator import evaluate_intervention


def make_two_zone_state():
    return SimulationState(
        zones=[
            ZoneParams(zone_id="zone-1", flood_severity=0.9, affected_population=12_000,
                       medical_urgency=0.8, road_accessibility=0.2,
                       rescue_teams=1, ambulances=1, demand_units=8),
            ZoneParams(zone_id="zone-2", flood_severity=0.2, affected_population=2_000,
                       medical_urgency=0.1, road_accessibility=0.9,
                       rescue_teams=5, ambulances=4, demand_units=4),
        ],
        shelters=[Shelter(shelter_id="s1", name="S1", coordinates=[0, 0],
                          capacity=300, current_occupancy=250)],
        hospitals=[Hospital(hospital_id="h1", name="H1", coordinates=[0, 0],
                            capacity=100, surge_capacity=20, current_occupancy=80)],
    )


@pytest.fixture
def evaluated_interventions():
    state = make_two_zone_state()
    population_max = 15_000
    zone_results = calculate_zone_results(state, population_max)
    bottlenecks = detect_bottlenecks(zone_results, state.shelters, state.hospitals)
    intervention_states = generate_simulation_states(state, zone_results, bottlenecks)

    results = {}
    for strategy, mod_state in intervention_states.items():
        result = evaluate_intervention(
            strategy=strategy,
            state=mod_state,
            baseline_zone_results=zone_results,
            population_max=population_max,
            baseline_state=state,
            baseline_bottlenecks=bottlenecks,
        )
        results[strategy] = result
    return results, state, population_max, zone_results, bottlenecks


# ---------------------------------------------------------------------------
# Baseline metrics
# ---------------------------------------------------------------------------

def test_baseline_risk_reduction_is_zero(evaluated_interventions):
    results, _, _, _, _ = evaluated_interventions
    baseline = results["baseline"]
    assert baseline.risk_reduction_pct == 0.0


def test_baseline_response_time_improvement_is_zero(evaluated_interventions):
    results, _, _, _, _ = evaluated_interventions
    baseline = results["baseline"]
    assert baseline.response_time_improvement_minutes == 0.0


def test_baseline_resource_cost_is_zero(evaluated_interventions):
    results, _, _, _, _ = evaluated_interventions
    baseline = results["baseline"]
    assert baseline.resource_cost == 0


# ---------------------------------------------------------------------------
# P-8: Before/After accuracy
# ---------------------------------------------------------------------------

def test_intervention_projected_result_equals_engine_run(evaluated_interventions):
    """
    The avg_risk_score in InterventionResult must equal directly running
    calculate_zone_results on the same modified state.
    """
    results, baseline_state, population_max, baseline_zone_results, bottlenecks = evaluated_interventions
    intervention_states = generate_simulation_states(
        baseline_state,
        baseline_zone_results,
        bottlenecks,
    )
    for strategy, mod_state in intervention_states.items():
        direct_results = calculate_zone_results(mod_state, population_max)
        direct_avg = sum(zr.risk_score for zr in direct_results) / len(direct_results)
        stored_avg = results[strategy].avg_risk_score
        assert abs(direct_avg - stored_avg) < 1e-4, (
            f"Strategy {strategy}: direct avg {direct_avg} != stored {stored_avg}"
        )


def test_zone_results_count_matches_state_zones(evaluated_interventions):
    results, state, _, _, _ = evaluated_interventions
    for strategy, result in results.items():
        assert len(result.zone_results) == len(state.zones), (
            f"Strategy {strategy}: zone count mismatch"
        )


# ---------------------------------------------------------------------------
# Metric ranges
# ---------------------------------------------------------------------------

def test_risk_reduction_pct_non_negative(evaluated_interventions):
    results, _, _, _, _ = evaluated_interventions
    for strategy, result in results.items():
        assert result.risk_reduction_pct >= 0.0, (
            f"Strategy {strategy} has negative risk_reduction_pct"
        )


def test_response_time_improvement_non_negative(evaluated_interventions):
    results, _, _, _, _ = evaluated_interventions
    for strategy, result in results.items():
        assert result.response_time_improvement_minutes >= 0.0


def test_bottleneck_resolution_in_0_1(evaluated_interventions):
    results, _, _, _, _ = evaluated_interventions
    for strategy, result in results.items():
        assert 0.0 <= result.bottleneck_resolution_score <= 1.0


def test_avg_risk_score_in_bounds(evaluated_interventions):
    results, _, _, _, _ = evaluated_interventions
    for strategy, result in results.items():
        assert 0.0 <= result.avg_risk_score <= 100.0


def test_avg_response_time_in_bounds(evaluated_interventions):
    results, _, _, _, _ = evaluated_interventions
    for strategy, result in results.items():
        assert 5.0 <= result.avg_response_time_minutes <= 120.0


# ---------------------------------------------------------------------------
# Strategy labels
# ---------------------------------------------------------------------------

def test_all_four_strategies_evaluated(evaluated_interventions):
    results, _, _, _, _ = evaluated_interventions
    assert set(results.keys()) == {"baseline", "resource_reallocation", "capacity_expansion", "combined"}


def test_strategy_labels_correct(evaluated_interventions):
    results, _, _, _, _ = evaluated_interventions
    assert results["baseline"].label == "Baseline / No Intervention"
    assert results["resource_reallocation"].label == "Resource Reallocation"
    assert results["capacity_expansion"].label == "Capacity Expansion"
    assert results["combined"].label == "Combined Intervention"
