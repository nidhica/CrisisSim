"""
CrisisSim Simulation Engine — multi-hazard deterministic simulation.
Pure Python — no AWS, no HTTP, no external dependencies.

Supported hazards: flood, fire, earthquake, cyclone, industrial_accident.
Coefficients are prototype assumptions, not scientific guidance.
"""
from .models import (
    ZoneParams,
    Zone,
    Shelter,
    Hospital,
    Scenario,
    SimulationState,
    ZoneResult,
    Bottleneck,
    InterventionResult,
    SimulationResult,
)
from .risk_scorer import calculate_zone_results
from .response_time import estimate_response_time
from .bottleneck_detector import detect_bottlenecks
from .intervention_engine import generate_simulation_states
from .evaluator import evaluate_intervention
from .recommender import rank_and_recommend

import uuid
from datetime import datetime, timezone


def run_full_simulation(scenario: Scenario, zone_params: list[ZoneParams]) -> SimulationResult:
    """
    Orchestrates the full deterministic simulation pipeline.

    Pipeline:
      zone_params → SimulationState
      → baseline zone results
      → baseline bottlenecks
      → generate four intervention states
      → evaluate every intervention
      → rank and recommend
      → SimulationResult
    """
    # Build baseline state from scenario facilities + provided zone params
    import dataclasses
    baseline_state = SimulationState(
        zones=zone_params,
        shelters=[dataclasses.replace(s) for s in scenario.shelters],
        hospitals=[dataclasses.replace(h) for h in scenario.hospitals],
        hazard_type=scenario.hazard_type,
    )

    # Baseline calculations
    baseline_zone_results = calculate_zone_results(baseline_state, scenario.population_max)
    baseline_bottlenecks = detect_bottlenecks(
        baseline_zone_results, baseline_state.shelters, baseline_state.hospitals, scenario.hazard_type, baseline_state.zones
    )

    # Generate all four intervention states
    intervention_states = generate_simulation_states(
        baseline_state, baseline_zone_results, baseline_bottlenecks, scenario.hazard_type
    )

    # Evaluate each strategy using the same pipeline
    interventions: list[InterventionResult] = []
    for strategy, state in intervention_states.items():
        result = evaluate_intervention(
            strategy=strategy,
            state=state,
            baseline_zone_results=baseline_zone_results,
            population_max=scenario.population_max,
            baseline_state=baseline_state,
            baseline_bottlenecks=baseline_bottlenecks,
            hazard_type=scenario.hazard_type,
        )
        interventions.append(result)

    # Rank and recommend
    recommended_strategy = rank_and_recommend(interventions)

    return SimulationResult(
        result_id=str(uuid.uuid4()),
        scenario_id=scenario.scenario_id,
        run_at=datetime.now(timezone.utc).isoformat(),
        params_used=zone_params,
        baseline_zone_results=baseline_zone_results,
        bottlenecks=baseline_bottlenecks,
        interventions=interventions,
        recommended_strategy=recommended_strategy,
        hazard_type=scenario.hazard_type,
    )
