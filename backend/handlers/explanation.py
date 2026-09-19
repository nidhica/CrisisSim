"""
Explanation handler — thin wrapper over bedrock/explainer.
POST /explain

Fetches simulation result from store, calls explainer.
Bedrock never makes decisions or calculates metrics.
"""
from __future__ import annotations
from bedrock.explainer import generate_explanation


def handle_explain(result_id: str, store) -> dict:
    """
    Load simulation result by result_id, generate explanation.

    Raises:
        ValueError: if result_id not found.
    """
    result = store.get_result_by_id(result_id)
    if result is None:
        raise ValueError(f"Simulation result not found: {result_id}")

    # Bedrock receives the complete structured result — never partial data
    return generate_explanation(result)
