"""
In-memory persistence store for local development.
Mimics the DynamoDB access patterns used in Phase 4:
  - scenarios keyed by scenario_id
  - results keyed by (scenario_id, run_at) — latest = most recent run_at

No AWS dependencies. Thread-safe for single-process dev server use.
"""
from __future__ import annotations
import dataclasses
import json
from datetime import datetime, timezone
from typing import Any

from engine.models import (
    Scenario, Zone, Shelter, Hospital,
    SimulationResult, SimulationState, ZoneParams,
    ZoneResult, RiskComponents, Bottleneck, InterventionResult,
)

# ── In-memory stores ──────────────────────────────────────────────────────────
_scenarios: dict[str, Scenario] = {}
_results: dict[str, list[SimulationResult]] = {}   # scenario_id → [results] sorted by run_at
_incidents: dict[str, dict[str, Any]] = {}
_incident_sequence_year: int | None = None
_incident_sequence_value: int = 0


# ── Serialisation helpers ─────────────────────────────────────────────────────

def _dataclass_to_dict(obj: Any) -> Any:
    """Recursively convert dataclasses to plain dicts for JSON serialisation."""
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return {k: _dataclass_to_dict(v) for k, v in dataclasses.asdict(obj).items()}
    if isinstance(obj, list):
        return [_dataclass_to_dict(i) for i in obj]
    return obj


def scenario_to_dict(scenario: Scenario) -> dict:
    return _dataclass_to_dict(scenario)


def result_to_dict(result: SimulationResult) -> dict:
    return _dataclass_to_dict(result)


def scenario_from_dict(d: dict) -> Scenario:
    return Scenario(
        scenario_id=d["scenario_id"],
        name=d["name"],
        description=d["description"],
        severity=d["severity"],
        created_at=d["created_at"],
        population_max=d["population_max"],
        zones=[
            Zone(
                zone_id=z["zone_id"], name=z["name"],
                coordinates=z["coordinates"], centroid=z["centroid"],
                flood_severity=z["flood_severity"],
                affected_population=z["affected_population"],
                medical_urgency=z["medical_urgency"],
                road_accessibility=z["road_accessibility"],
                rescue_teams=z["rescue_teams"], ambulances=z["ambulances"],
                demand_units=z["demand_units"],
                hazard_factors=z.get("hazard_factors", {}),
                specialist_resources=z.get("specialist_resources", {}),
            )
            for z in d["zones"]
        ],
        shelters=[
            Shelter(
                shelter_id=s["shelter_id"], name=s["name"],
                coordinates=s["coordinates"], capacity=s["capacity"],
                current_occupancy=s["current_occupancy"],
            )
            for s in d["shelters"]
        ],
        hospitals=[
            Hospital(
                hospital_id=h["hospital_id"], name=h["name"],
                coordinates=h["coordinates"], capacity=h["capacity"],
                surge_capacity=h["surge_capacity"],
                current_occupancy=h["current_occupancy"],
            )
            for h in d["hospitals"]
        ],
        hazard_type=d.get("hazard_type", "flood"),
    )


def result_from_dict(d: dict) -> SimulationResult:
    def make_risk_components(rc: dict) -> RiskComponents:
        return RiskComponents(
            affected_population_score=rc["affected_population_score"],
            flood_severity_score=rc["flood_severity_score"],
            medical_urgency_score=rc["medical_urgency_score"],
            road_accessibility_score=rc["road_accessibility_score"],
            resource_shortage_score=rc["resource_shortage_score"],
            hazard_intensity_score=rc.get("hazard_intensity_score", 0.0),
            hazard_specific_scores=rc.get("hazard_specific_scores", {}),
        )

    def make_zone_result(zr: dict) -> ZoneResult:
        return ZoneResult(
            zone_id=zr["zone_id"],
            risk_score=zr["risk_score"],
            risk_level=zr["risk_level"],
            response_time_minutes=zr["response_time_minutes"],
            risk_components=make_risk_components(zr["risk_components"]),
        )

    def make_bottleneck(b: dict) -> Bottleneck:
        return Bottleneck(
            type=b["type"], zone_id=b["zone_id"], facility_id=b["facility_id"],
            description=b["description"], severity_score=b["severity_score"],
        )

    def make_intervention(iv: dict) -> InterventionResult:
        return InterventionResult(
            strategy=iv["strategy"], label=iv["label"],
            zone_results=[make_zone_result(zr) for zr in iv["zone_results"]],
            avg_risk_score=iv["avg_risk_score"],
            avg_response_time_minutes=iv["avg_response_time_minutes"],
            risk_reduction_pct=iv["risk_reduction_pct"],
            response_time_improvement_minutes=iv["response_time_improvement_minutes"],
            bottleneck_resolution_score=iv["bottleneck_resolution_score"],
            resource_cost=iv["resource_cost"],
            composite_score=iv["composite_score"],
        )

    def make_zone_params(zp: dict) -> ZoneParams:
        return ZoneParams(
            zone_id=zp["zone_id"], flood_severity=zp["flood_severity"],
            affected_population=zp["affected_population"],
            medical_urgency=zp["medical_urgency"],
            road_accessibility=zp["road_accessibility"],
            rescue_teams=zp["rescue_teams"], ambulances=zp["ambulances"],
            demand_units=zp["demand_units"],
            hazard_factors=zp.get("hazard_factors", {}),
            specialist_resources=zp.get("specialist_resources", {}),
        )

    return SimulationResult(
        result_id=d["result_id"],
        scenario_id=d["scenario_id"],
        run_at=d["run_at"],
        params_used=[make_zone_params(zp) for zp in d["params_used"]],
        baseline_zone_results=[make_zone_result(zr) for zr in d["baseline_zone_results"]],
        bottlenecks=[make_bottleneck(b) for b in d["bottlenecks"]],
        interventions=[make_intervention(iv) for iv in d["interventions"]],
        recommended_strategy=d["recommended_strategy"],
        hazard_type=d.get("hazard_type", "flood"),
    )


# ── Public API ────────────────────────────────────────────────────────────────

def seed_scenario(scenario: Scenario) -> None:
    """Load a scenario into the in-memory store."""
    _scenarios[scenario.scenario_id] = scenario


def list_scenarios() -> list[Scenario]:
    return list(_scenarios.values())


def get_scenario(scenario_id: str) -> Scenario | None:
    return _scenarios.get(scenario_id)


def save_result(result: SimulationResult) -> None:
    """Persist a simulation result. Keeps all results per scenario, sorted by run_at."""
    bucket = _results.setdefault(result.scenario_id, [])
    bucket.append(result)
    bucket.sort(key=lambda r: r.run_at)


def get_latest_result(scenario_id: str) -> SimulationResult | None:
    """Return the most recently run result for a scenario, or None."""
    bucket = _results.get(scenario_id, [])
    return bucket[-1] if bucket else None


def get_result_by_id(result_id: str) -> SimulationResult | None:
    """Find a result by its result_id across all scenarios."""
    for bucket in _results.values():
        for r in bucket:
            if r.result_id == result_id:
                return r
    return None


def _format_incident_id(year: int, sequence: int) -> str:
    return f"INC-{year}-{sequence:04d}"


def _next_incident_id() -> str:
    global _incident_sequence_year, _incident_sequence_value
    year = datetime.now(timezone.utc).year
    if _incident_sequence_year != year:
        _incident_sequence_year = year
        _incident_sequence_value = 0
    _incident_sequence_value += 1
    return _format_incident_id(year, _incident_sequence_value)


def create_incident(payload: dict[str, Any]) -> dict[str, Any]:
    """Create a citizen incident report with server-generated ID."""
    incident_id = _next_incident_id()
    incident = {
        "incident_id": incident_id,
        "hazard_type": payload["hazard_type"],
        "location_name": payload["location_name"],
        "latitude": float(payload["latitude"]),
        "longitude": float(payload["longitude"]),
        "severity": payload["severity"],
        "description": payload["description"],
        "status": payload.get("status", "reported"),
        "created_at": payload.get("created_at") or datetime.now(timezone.utc).isoformat(),
    }
    if payload.get("evidence_url"):
        incident["evidence_url"] = payload["evidence_url"]
    _incidents[incident_id] = incident
    return dict(incident)


def list_incidents() -> list[dict[str, Any]]:
    items = list(_incidents.values())
    items.sort(key=lambda item: item.get("created_at", ""), reverse=True)
    return items


def get_incident(incident_id: str) -> dict[str, Any] | None:
    incident = _incidents.get(incident_id)
    return dict(incident) if incident else None


def update_incident(incident_id: str, status: str) -> dict[str, Any]:
    incident = _incidents.get(incident_id)
    if incident is None:
        raise KeyError(incident_id)
    updated = {**incident, "status": status}
    _incidents[incident_id] = updated
    return dict(updated)


def reset_store() -> None:
    """Clear all data — used in tests."""
    global _incident_sequence_year, _incident_sequence_value
    _scenarios.clear()
    _results.clear()
    _incidents.clear()
    _incident_sequence_year = None
    _incident_sequence_value = 0
