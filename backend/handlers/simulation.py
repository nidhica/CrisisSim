"""
Simulation handler — thin wrapper over run_full_simulation().
POST /simulate

Validates input, calls the engine, persists the result.
No simulation formulas here.
"""
from __future__ import annotations
from engine.models import ZoneParams, SimulationResult
from engine import run_full_simulation


def handle_run_simulation(
    scenario_id: str,
    raw_params: list[dict],
    store,
) -> SimulationResult:
    """
    Load scenario, build ZoneParams, run engine, persist and return result.

    Raises:
        ValueError: if scenario not found or params are invalid.
    """
    scenario = store.get_scenario(scenario_id)
    if scenario is None:
        raise ValueError(f"Scenario not found: {scenario_id}")

    # Validate that every scenario zone has a matching param entry
    param_zone_ids = {p["zone_id"] for p in raw_params}
    scenario_zone_ids = {z.zone_id for z in scenario.zones}
    missing = scenario_zone_ids - param_zone_ids
    if missing:
        raise ValueError(f"Missing params for zones: {missing}")

    # Build typed ZoneParams objects
    zone_params = [
        ZoneParams(
            zone_id=p["zone_id"],
            flood_severity=float(p["flood_severity"]),
            affected_population=int(p["affected_population"]),
            medical_urgency=float(p["medical_urgency"]),
            road_accessibility=float(p["road_accessibility"]),
            rescue_teams=int(p["rescue_teams"]),
            ambulances=int(p["ambulances"]),
            demand_units=int(p["demand_units"]),
            hazard_factors={k: max(0.0, min(float(v), 1.0)) for k, v in p.get("hazard_factors", {}).items()},
            specialist_resources={k: max(0, int(v)) for k, v in p.get("specialist_resources", {}).items()},
        )
        for p in raw_params
    ]

    # Run the deterministic simulation engine
    result = run_full_simulation(scenario, zone_params)

    # Persist
    store.save_result(result)

    return result


def handle_get_latest_result(scenario_id: str, store) -> SimulationResult | None:
    """
    Returns the most recent simulation result for a scenario, or None.
    """
    return store.get_latest_result(scenario_id)
