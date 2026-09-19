"""
CrisisSim local FastAPI server — for development only.
Uses in-memory store instead of DynamoDB. No AWS credentials required.

Run with:
  uvicorn local_server:app --reload --port 8000

All routes call handler functions that call the simulation engine.
No simulation logic lives in this file.
"""
from __future__ import annotations
import dataclasses
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import persistence.memory_store as store
from seed_data import get_all_scenarios
from handlers.scenarios import handle_list_scenarios, handle_get_scenario
from handlers.simulation import handle_run_simulation, handle_get_latest_result
from handlers.explanation import handle_explain
from handlers.incidents import (
    handle_create_incident,
    handle_get_incident,
    handle_list_incidents,
    handle_update_incident,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Seed the in-memory store on startup."""
    for scenario in get_all_scenarios():
        store.seed_scenario(scenario)
        logger.info(f"Seeded scenario: {scenario.scenario_id} ({len(scenario.zones)} zones)")
    yield


app = FastAPI(
    title="CrisisSim API",
    description="Multi-hazard emergency simulation and decision-support platform (local dev)",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _to_json(obj) -> dict:
    """Convert a dataclass to a JSON-serialisable dict."""
    return dataclasses.asdict(obj)


# ── Request models ────────────────────────────────────────────────────────────

class ZoneParamsInput(BaseModel):
    zone_id: str
    flood_severity: float
    affected_population: int
    medical_urgency: float
    road_accessibility: float
    rescue_teams: int
    ambulances: int
    demand_units: int
    hazard_factors: dict[str, float] = {}
    specialist_resources: dict[str, int] = {}


class SimulateRequest(BaseModel):
    scenario_id: str
    params: list[ZoneParamsInput]


class ExplainRequest(BaseModel):
    result_id: str


class CreateIncidentRequest(BaseModel):
    hazard_type: str
    location_name: str
    latitude: float
    longitude: float
    severity: str
    description: str
    evidence_url: str | None = None


class UpdateIncidentRequest(BaseModel):
    status: str


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/api/v1/scenarios")
def list_scenarios():
    """GET /api/v1/scenarios — list all available scenarios."""
    return handle_list_scenarios(store)


@app.get("/api/v1/scenarios/{scenario_id}")
def get_scenario(scenario_id: str):
    """GET /api/v1/scenarios/{scenario_id} — full scenario with zones, shelters, hospitals."""
    scenario = handle_get_scenario(scenario_id, store)
    if scenario is None:
        raise HTTPException(status_code=404, detail=f"Scenario not found: {scenario_id}")
    return _to_json(scenario)


@app.post("/api/v1/simulate")
def run_simulation(request: SimulateRequest):
    """
    POST /api/v1/simulate — run simulation with What-If parameters.
    Persists and returns the full SimulationResult.
    """
    try:
        result = handle_run_simulation(
            scenario_id=request.scenario_id,
            raw_params=[p.model_dump() for p in request.params],
            store=store,
        )
        return _to_json(result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception("Simulation error")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/results/{scenario_id}/latest")
def get_latest_result(scenario_id: str):
    """GET /api/v1/results/{scenario_id}/latest — most recent simulation result."""
    result = handle_get_latest_result(scenario_id, store)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"No simulation results found for scenario: {scenario_id}",
        )
    return _to_json(result)


@app.post("/api/v1/explain")
def explain(request: ExplainRequest):
    """
    POST /api/v1/explain — generate plain-language explanation of the recommendation.
    Bedrock never makes decisions; it only explains the deterministic result.
    """
    try:
        return handle_explain(request.result_id, store)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception("Explanation error")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/health")
def health():
    """Health check."""
    return {"status": "ok", "scenarios_loaded": len(store.list_scenarios())}


@app.post("/api/v1/incidents", status_code=201)
def create_incident(request: CreateIncidentRequest):
    """POST /api/v1/incidents — create a citizen incident report."""
    try:
        return handle_create_incident(request.model_dump(exclude_none=True), store)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/incidents")
def list_incidents():
    """GET /api/v1/incidents — list incident reports (newest first)."""
    return handle_list_incidents(store)


@app.get("/api/v1/incidents/{incident_id}")
def get_incident(incident_id: str):
    """GET /api/v1/incidents/{incident_id} — single incident."""
    incident = handle_get_incident(incident_id, store)
    if incident is None:
        raise HTTPException(status_code=404, detail=f"Incident not found: {incident_id}")
    return incident


@app.patch("/api/v1/incidents/{incident_id}")
def update_incident(incident_id: str, request: UpdateIncidentRequest):
    """PATCH /api/v1/incidents/{incident_id} — advance incident status."""
    try:
        return handle_update_incident(incident_id, request.model_dump(), store)
    except LookupError:
        raise HTTPException(status_code=404, detail=f"Incident not found: {incident_id}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
