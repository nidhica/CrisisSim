"""
CrisisSim AWS Lambda handler.
Handles REST API Proxy events from API Gateway.
Routes to domain handlers and persistence layer (DynamoDB).
"""
from __future__ import annotations
import dataclasses
import json
import logging
import os
from typing import Any

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

# Select store module: DynamoDB in AWS Lambda, memory_store if explicitly forced for testing
if os.environ.get("PERSISTENCE_MODE") == "memory":
    import persistence.memory_store as store
else:
    import persistence.dynamodb as store

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("crisissim-lambda")

CORS_HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
    "Access-Control-Allow-Methods": "GET,POST,PATCH,OPTIONS",
}


def _response(status_code: int, body: Any) -> dict:
    if dataclasses.is_dataclass(body) and not isinstance(body, type):
        body = dataclasses.asdict(body)
    return {
        "statusCode": status_code,
        "headers": CORS_HEADERS,
        "body": json.dumps(body) if not isinstance(body, str) else body,
    }


def lambda_handler(event: dict, context: Any) -> dict:
    """
    Main Lambda entry point for API Gateway REST/HTTP API proxy integration.
    """
    logger.info(f"Event: {json.dumps(event)}")
    
    http_method = event.get("httpMethod") or event.get("requestContext", {}).get("http", {}).get("method", "GET")
    path = event.get("path") or event.get("rawPath", "")
    
    # Handle CORS OPTIONS preflight
    if http_method == "OPTIONS":
        return _response(200, {"status": "ok"})
    
    # Normalize path by removing trailing slash if any
    path = path.rstrip("/")

    try:
        # Route: GET /api/v1/health
        if path.endswith("/health") and http_method == "GET":
            return _response(200, {"status": "ok", "environment": "aws-lambda"})

        # Route: GET /api/v1/scenarios
        if path.endswith("/scenarios") and http_method == "GET":
            result = handle_list_scenarios(store)
            return _response(200, result)

        # Route: GET /api/v1/scenarios/{scenario_id}
        if "/scenarios/" in path and http_method == "GET":
            scenario_id = path.split("/scenarios/")[1]
            scenario = handle_get_scenario(scenario_id, store)
            if scenario is None:
                return _response(404, {"detail": f"Scenario not found: {scenario_id}"})
            return _response(200, scenario)

        # Route: POST /api/v1/simulate
        if path.endswith("/simulate") and http_method == "POST":
            raw_body = event.get("body", "{}")
            if event.get("isBase64Encoded"):
                import base64
                raw_body = base64.b64decode(raw_body).decode("utf-8")
            data = json.loads(raw_body or "{}")
            
            result = handle_run_simulation(
                scenario_id=data.get("scenario_id", ""),
                raw_params=data.get("params", []),
                store=store,
            )
            return _response(200, result)

        # Route: GET /api/v1/results/{scenario_id}/latest
        if "/results/" in path and path.endswith("/latest") and http_method == "GET":
            parts = path.split("/results/")[1].split("/latest")[0]
            scenario_id = parts
            result = handle_get_latest_result(scenario_id, store)
            if result is None:
                return _response(404, {"detail": f"No simulation results found for scenario: {scenario_id}"})
            return _response(200, result)

        # Route: POST /api/v1/incidents
        if path.endswith("/incidents") and http_method == "POST":
            raw_body = event.get("body", "{}")
            if event.get("isBase64Encoded"):
                import base64
                raw_body = base64.b64decode(raw_body).decode("utf-8")
            data = json.loads(raw_body or "{}")
            result = handle_create_incident(data, store)
            return _response(201, result)

        # Route: GET /api/v1/incidents
        if path.endswith("/incidents") and http_method == "GET":
            result = handle_list_incidents(store)
            return _response(200, result)

        # Route: GET/PATCH /api/v1/incidents/{incident_id}
        if "/incidents/" in path and "/scenarios/" not in path:
            incident_id = path.split("/incidents/")[1].split("/")[0]
            if http_method == "GET":
                incident = handle_get_incident(incident_id, store)
                if incident is None:
                    return _response(404, {"detail": f"Incident not found: {incident_id}"})
                return _response(200, incident)
            if http_method == "PATCH":
                raw_body = event.get("body", "{}")
                if event.get("isBase64Encoded"):
                    import base64
                    raw_body = base64.b64decode(raw_body).decode("utf-8")
                data = json.loads(raw_body or "{}")
                try:
                    result = handle_update_incident(incident_id, data, store)
                    return _response(200, result)
                except LookupError:
                    return _response(404, {"detail": f"Incident not found: {incident_id}"})

        # Route: POST /api/v1/explain
        if path.endswith("/explain") and http_method == "POST":
            raw_body = event.get("body", "{}")
            if event.get("isBase64Encoded"):
                import base64
                raw_body = base64.b64decode(raw_body).decode("utf-8")
            data = json.loads(raw_body or "{}")
            
            result = handle_explain(
                result_id=data.get("result_id", ""),
                store=store,
            )
            return _response(200, result)

        return _response(404, {"detail": f"Route not found: {http_method} {path}"})

    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        return _response(400, {"detail": str(e)})
    except Exception as e:
        logger.exception("Unexpected error in Lambda handler")
        return _response(500, {"detail": str(e)})
