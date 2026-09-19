"""
Scenario handlers — thin wrappers over the persistence store.
GET /scenarios and GET /scenarios/{scenario_id}

No simulation logic here. No AWS, HTTP client, or Bedrock imports.
"""
from __future__ import annotations
from engine.models import Scenario


def handle_list_scenarios(store) -> dict:
    """
    Returns a summary list of all available scenarios.
    """
    scenarios = store.list_scenarios()
    return {
        "scenarios": [
            {
                "scenario_id": s.scenario_id,
                "name": s.name,
                "description": s.description,
                "severity": s.severity,
                "hazard_type": getattr(s, "hazard_type", "flood"),
            }
            for s in scenarios
        ]
    }


def handle_get_scenario(scenario_id: str, store) -> Scenario | None:
    """
    Returns the full Scenario object or None if not found.
    """
    return store.get_scenario(scenario_id)
