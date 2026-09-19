"""
Unit/integration tests for CrisisSim Lambda function.
Tests API Gateway event routing and handler execution in memory mode.
"""
import json
import os
import pytest

# Force memory mode for local testing
os.environ["PERSISTENCE_MODE"] = "memory"

from lambda_function import lambda_handler
from seed_data import get_default_scenario
import persistence.memory_store as store

@pytest.fixture(autouse=True)
def setup_store():
    store.reset_store()
    scenario = get_default_scenario()
    store.seed_scenario(scenario)

def test_lambda_health():
    event = {
        "httpMethod": "GET",
        "path": "/api/v1/health"
    }
    res = lambda_handler(event, None)
    assert res["statusCode"] == 200
    body = json.loads(res["body"])
    assert body["status"] == "ok"

def test_lambda_list_scenarios():
    event = {
        "httpMethod": "GET",
        "path": "/api/v1/scenarios"
    }
    res = lambda_handler(event, None)
    assert res["statusCode"] == 200
    body = json.loads(res["body"])
    assert len(body["scenarios"]) == 1
    assert body["scenarios"][0]["scenario_id"] == "flood-scenario-001"

def test_lambda_get_scenario():
    event = {
        "httpMethod": "GET",
        "path": "/api/v1/scenarios/flood-scenario-001"
    }
    res = lambda_handler(event, None)
    assert res["statusCode"] == 200
    body = json.loads(res["body"])
    assert body["scenario_id"] == "flood-scenario-001"
    assert len(body["zones"]) == 5

def test_lambda_create_incident():
    event = {
        "httpMethod": "POST",
        "path": "/api/v1/incidents",
        "body": json.dumps({
            "hazard_type": "fire",
            "location_name": "Bhopal",
            "latitude": 23.25,
            "longitude": 77.41,
            "severity": "high",
            "description": "Smoke",
        }),
    }
    res = lambda_handler(event, None)
    assert res["statusCode"] == 201
    body = json.loads(res["body"])
    assert body["incident_id"].startswith("INC-")
    assert body["status"] == "reported"


def test_lambda_simulate():
    sc = store.get_scenario("flood-scenario-001")
    params = [
        {
            "zone_id": z.zone_id,
            "flood_severity": z.flood_severity,
            "affected_population": z.affected_population,
            "medical_urgency": z.medical_urgency,
            "road_accessibility": z.road_accessibility,
            "rescue_teams": z.rescue_teams,
            "ambulances": z.ambulances,
            "demand_units": z.demand_units,
        }
        for z in sc.zones
    ]
    event = {
        "httpMethod": "POST",
        "path": "/api/v1/simulate",
        "body": json.dumps({
            "scenario_id": "flood-scenario-001",
            "params": params
        })
    }
    res = lambda_handler(event, None)
    assert res["statusCode"] == 200
    body = json.loads(res["body"])
    assert body["recommended_strategy"] == "combined"

def test_lambda_cors_options():
    event = {
        "httpMethod": "OPTIONS",
        "path": "/api/v1/simulate"
    }
    res = lambda_handler(event, None)
    assert res["statusCode"] == 200
    assert res["headers"]["Access-Control-Allow-Origin"] == "*"
