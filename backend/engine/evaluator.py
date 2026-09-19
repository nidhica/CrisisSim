"""
Intervention evaluator — runs the same simulation pipeline on each strategy's
modified SimulationState. No hardcoded projected values.
Deterministic, no AWS/HTTP/LLM dependencies.

For each strategy computes:
  - zone results (risk scores + response times)
  - bottlenecks
  - average risk score
  - average response time
  - risk reduction % vs baseline
  - response time improvement vs baseline
  - bottleneck resolution score
  - resource cost (units moved/expanded relative to baseline)
  - composite score (set to 0.0 here; filled in by recommender)
"""
from __future__ import annotations
from .models import (
    SimulationState,
    ZoneResult,
    Bottleneck,
    InterventionResult,
)
from .risk_scorer import calculate_zone_results
from .bottleneck_detector import detect_bottlenecks
from .intervention_engine import STRATEGY_LABELS


def _avg(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _compute_resource_cost(
    baseline_state: SimulationState,
    modified_state: SimulationState,
) -> int:
    """
    Resource cost = total units moved (rescue/ambulance and specialist outbound
    transfers counted separately) + capacity expansion overhead (count of
    facilities with increased capacity).

    Specialist units are counted by resource key and are never treated as
    interchangeable with common assets.
    """
    cost = 0

    # Count resource units moved from zones (common + specialist, separately)
    baseline_zone_map = {z.zone_id: z for z in baseline_state.zones}
    for zone in modified_state.zones:
        orig = baseline_zone_map.get(zone.zone_id)
        if orig is None:
            continue
        rescue_delta = orig.rescue_teams - zone.rescue_teams
        ambulance_delta = orig.ambulances - zone.ambulances
        # Only count outgoing transfers (positive delta = resources left this zone)
        if rescue_delta > 0:
            cost += rescue_delta
        if ambulance_delta > 0:
            cost += ambulance_delta
        # Specialist transfers — keyed by resource type, never mixed across hazards
        all_keys = set(orig.specialist_resources) | set(zone.specialist_resources)
        for key in all_keys:
            specialist_delta = int(orig.specialist_resources.get(key, 0)) - int(
                zone.specialist_resources.get(key, 0)
            )
            if specialist_delta > 0:
                cost += specialist_delta

    # Count expanded facilities
    baseline_shelter_map = {s.shelter_id: s for s in baseline_state.shelters}
    for shelter in modified_state.shelters:
        orig = baseline_shelter_map.get(shelter.shelter_id)
        if orig and shelter.capacity > orig.capacity:
            cost += 1

    baseline_hospital_map = {h.hospital_id: h for h in baseline_state.hospitals}
    for hospital in modified_state.hospitals:
        orig = baseline_hospital_map.get(hospital.hospital_id)
        if orig and hospital.surge_capacity > orig.surge_capacity:
            cost += 1

    return cost


def _bottleneck_resolution_score(
    baseline_bottlenecks: list[Bottleneck],
    intervention_bottlenecks: list[Bottleneck],
) -> float:
    """
    Score in [0, 1] representing how much the intervention reduced bottleneck severity.
    Computed as 1 - (sum of intervention severities / sum of baseline severities).
    Returns 0.0 if baseline has no bottlenecks.
    """
    baseline_total = sum(b.severity_score for b in baseline_bottlenecks)
    if baseline_total == 0.0:
        return 0.0
    intervention_total = sum(b.severity_score for b in intervention_bottlenecks)
    resolution = 1.0 - (intervention_total / baseline_total)
    return round(max(0.0, min(resolution, 1.0)), 4)


def evaluate_intervention(
    strategy: str,
    state: SimulationState,
    baseline_zone_results: list[ZoneResult],
    population_max: int,
    baseline_state: SimulationState | None = None,
    baseline_bottlenecks: list[Bottleneck] | None = None,
    hazard_type: str = "flood",
) -> InterventionResult:
    """
    Evaluate a single intervention strategy by running the full simulation pipeline
    on its modified state.

    baseline_zone_results is used to compute improvement metrics.
    baseline_state and baseline_bottlenecks are used for resource cost and
    bottleneck resolution. If not provided, baseline metrics are derived from
    baseline_zone_results only (bottleneck resolution will be 0.0).
    """
    # Run the same pipeline used for baseline on the modified state
    zone_results = calculate_zone_results(state, population_max)
    bottlenecks = detect_bottlenecks(zone_results, state.shelters, state.hospitals, hazard_type, state.zones)

    avg_risk = round(_avg([zr.risk_score for zr in zone_results]), 4)
    avg_rt = round(_avg([zr.response_time_minutes for zr in zone_results]), 4)

    baseline_avg_risk = round(_avg([zr.risk_score for zr in baseline_zone_results]), 4)
    baseline_avg_rt = round(_avg([zr.response_time_minutes for zr in baseline_zone_results]), 4)

    risk_reduction_pct = round(
        max(0.0, (baseline_avg_risk - avg_risk) / baseline_avg_risk * 100.0)
        if baseline_avg_risk > 0.0 else 0.0,
        4,
    )
    rt_improvement = round(max(0.0, baseline_avg_rt - avg_rt), 4)

    # Bottleneck resolution score
    if baseline_bottlenecks is not None:
        bn_resolution = _bottleneck_resolution_score(baseline_bottlenecks, bottlenecks)
    else:
        bn_resolution = 0.0

    # Resource cost
    if baseline_state is not None:
        resource_cost = _compute_resource_cost(baseline_state, state)
    else:
        resource_cost = 0

    return InterventionResult(
        strategy=strategy,
        label=STRATEGY_LABELS.get(strategy, strategy),
        zone_results=zone_results,
        avg_risk_score=avg_risk,
        avg_response_time_minutes=avg_rt,
        risk_reduction_pct=risk_reduction_pct,
        response_time_improvement_minutes=rt_improvement,
        bottleneck_resolution_score=bn_resolution,
        resource_cost=resource_cost,
        composite_score=0.0,  # filled in by recommender
    )
