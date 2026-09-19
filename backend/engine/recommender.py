"""
Intervention recommender — deterministic, no AWS/HTTP/LLM dependencies.

Recommendation weights (must sum to exactly 1.0):
  risk_reduction_pct             : 0.40
  bottleneck_resolution_score    : 0.30
  resource_efficiency            : 0.20  (inverse of resource_cost)
  response_time_improvement_mins : 0.10

Normalization: each metric is scaled to [0, 1] across all four strategies.
Tie-break: higher risk_reduction_pct wins.
The recommendation is NEVER decided by an LLM.
"""
from __future__ import annotations
import dataclasses
from .models import InterventionResult

RECOMMENDATION_WEIGHTS: dict[str, float] = {
    "risk_reduction_pct": 0.40,
    "bottleneck_resolution_score": 0.30,
    "resource_efficiency": 0.20,
    "response_time_improvement_minutes": 0.10,
}

assert (
    abs(sum(RECOMMENDATION_WEIGHTS.values()) - 1.0) < 1e-10
), "Recommendation weights must sum to exactly 1.0"


def _normalize(values: list[float]) -> list[float]:
    """
    Min-max normalize a list of values to [0, 1].
    If all values are identical, returns 1.0 for all (avoids division by zero).
    """
    min_v = min(values)
    max_v = max(values)
    rng = max_v - min_v
    if rng == 0.0:
        return [1.0] * len(values)
    return [(v - min_v) / rng for v in values]


def rank_and_recommend(interventions: list[InterventionResult]) -> str:
    """
    Compute composite scores for all interventions and return the strategy
    name of the best one.

    Also mutates each InterventionResult in-place to set its composite_score.

    Resource efficiency = inverse of resource_cost.
    Zero cost (baseline) gets maximum efficiency.
    """
    n = len(interventions)
    if n == 0:
        raise ValueError("No interventions to rank")
    if n == 1:
        return interventions[0].strategy

    # Extract raw metric vectors
    risk_reductions = [i.risk_reduction_pct for i in interventions]
    bn_resolutions = [i.bottleneck_resolution_score for i in interventions]
    rt_improvements = [i.response_time_improvement_minutes for i in interventions]

    # Resource efficiency: invert resource_cost so lower cost = higher efficiency
    # Add 1 to avoid division by zero; baseline cost=0 → efficiency = 1/(0+1) = 1.0
    raw_efficiencies = [1.0 / (i.resource_cost + 1) for i in interventions]

    # Normalize all four metrics
    norm_risk = _normalize(risk_reductions)
    norm_bn = _normalize(bn_resolutions)
    norm_rt = _normalize(rt_improvements)
    norm_eff = _normalize(raw_efficiencies)

    composite_scores: list[float] = []
    for idx in range(n):
        score = (
            RECOMMENDATION_WEIGHTS["risk_reduction_pct"] * norm_risk[idx]
            + RECOMMENDATION_WEIGHTS["bottleneck_resolution_score"] * norm_bn[idx]
            + RECOMMENDATION_WEIGHTS["resource_efficiency"] * norm_eff[idx]
            + RECOMMENDATION_WEIGHTS["response_time_improvement_minutes"] * norm_rt[idx]
        )
        composite_scores.append(round(score, 6))

    # Write composite scores back to the InterventionResult objects
    for idx, intervention in enumerate(interventions):
        interventions[idx] = dataclasses.replace(
            intervention, composite_score=composite_scores[idx]
        )

    # Select winner: highest composite score; tie-break by highest risk_reduction_pct
    best_idx = max(
        range(n),
        key=lambda i: (composite_scores[i], interventions[i].risk_reduction_pct),
    )
    return interventions[best_idx].strategy
