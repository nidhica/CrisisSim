"""
DynamoDB persistence store for CrisisSim AWS production environment.

Tables:
  - crisissim-scenarios (PK: scenario_id)
  - crisissim-results (PK: scenario_id, SK: run_at)
"""
from __future__ import annotations
import json
import os
import logging
from decimal import Decimal
from typing import Any

import boto3
from boto3.dynamodb.conditions import Attr, Key

from engine.models import (
    Scenario, SimulationResult,
)
from persistence.memory_store import (
    _dataclass_to_dict, scenario_from_dict, result_from_dict,
)

logger = logging.getLogger(__name__)

REGION_NAME = os.environ.get("APP_AWS_REGION") or os.environ.get("AWS_REGION", "us-east-1")
SCENARIOS_TABLE = os.environ.get("DYNAMODB_SCENARIOS_TABLE", "crisissim-scenarios")
RESULTS_TABLE = os.environ.get("DYNAMODB_RESULTS_TABLE", "crisissim-results")


def _get_resource():
    return boto3.resource("dynamodb", region_name=REGION_NAME)


def _convert_floats_to_decimals(obj: Any) -> Any:
    """Helper to convert floats to Decimals for DynamoDB compatibility."""
    if isinstance(obj, float):
        return Decimal(str(obj))
    if isinstance(obj, dict):
        return {k: _convert_floats_to_decimals(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_convert_floats_to_decimals(i) for i in obj]
    return obj


def _convert_decimals_to_floats(obj: Any) -> Any:
    """Helper to convert Decimals to floats/ints when reading from DynamoDB."""
    if isinstance(obj, Decimal):
        if obj % 1 == 0:
            return int(obj)
        return float(obj)
    if isinstance(obj, dict):
        return {k: _convert_decimals_to_floats(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_convert_decimals_to_floats(i) for i in obj]
    return obj


def seed_scenario(scenario: Scenario) -> None:
    """Save/update a scenario in the DynamoDB crisissim-scenarios table."""
    dynamodb = _get_resource()
    table = dynamodb.Table(SCENARIOS_TABLE)
    d = _dataclass_to_dict(scenario)
    item = _convert_floats_to_decimals(d)
    table.put_item(Item=item)
    logger.info(f"Seeded scenario to DynamoDB: {scenario.scenario_id}")


def list_scenarios() -> list[Scenario]:
    """Scan crisissim-scenarios and return all scenarios as Scenario objects."""
    dynamodb = _get_resource()
    table = dynamodb.Table(SCENARIOS_TABLE)
    resp = table.scan()
    items = resp.get("Items", [])
    scenarios = []
    for item in items:
        clean_item = _convert_decimals_to_floats(item)
        scenarios.append(scenario_from_dict(clean_item))
    return scenarios


def get_scenario(scenario_id: str) -> Scenario | None:
    """Get a single scenario from DynamoDB by scenario_id."""
    dynamodb = _get_resource()
    table = dynamodb.Table(SCENARIOS_TABLE)
    resp = table.get_item(Key={"scenario_id": scenario_id})
    item = resp.get("Item")
    if not item:
        return None
    clean_item = _convert_decimals_to_floats(item)
    return scenario_from_dict(clean_item)


def save_result(result: SimulationResult) -> None:
    """Save a SimulationResult item to DynamoDB crisissim-results table."""
    dynamodb = _get_resource()
    table = dynamodb.Table(RESULTS_TABLE)
    d = _dataclass_to_dict(result)
    item = _convert_floats_to_decimals(d)
    table.put_item(Item=item)
    logger.info(f"Saved simulation result to DynamoDB: {result.result_id}")


def get_latest_result(scenario_id: str) -> SimulationResult | None:
    """Query crisissim-results table for the latest result (ScanIndexForward=False, Limit=1)."""
    dynamodb = _get_resource()
    table = dynamodb.Table(RESULTS_TABLE)
    resp = table.query(
        KeyConditionExpression=Key("scenario_id").eq(scenario_id),
        ScanIndexForward=False,
        Limit=1,
    )
    items = resp.get("Items", [])
    if not items:
        return None
    clean_item = _convert_decimals_to_floats(items[0])
    return result_from_dict(clean_item)


def get_result_by_id(result_id: str) -> SimulationResult | None:
    """Scan results table to locate a result by result_id."""
    dynamodb = _get_resource()
    table = dynamodb.Table(RESULTS_TABLE)

    scan_kwargs = {
        "FilterExpression": Attr("result_id").eq(result_id),
    }

    while True:
        resp = table.scan(**scan_kwargs)

        items = resp.get("Items", [])
        if items:
            clean_item = _convert_decimals_to_floats(items[0])
            return result_from_dict(clean_item)

        last_key = resp.get("LastEvaluatedKey")
        if not last_key:
            return None

        scan_kwargs["ExclusiveStartKey"] = last_key


def _incidents_not_deployed() -> None:
    raise RuntimeError(
        "Incidents API requires DynamoDB table crisissim-incidents (not deployed yet). "
        "Use local FastAPI with memory_store for Phase 2 development."
    )


def create_incident(payload: dict) -> dict:
    _incidents_not_deployed()


def list_incidents() -> list:
    _incidents_not_deployed()


def get_incident(incident_id: str) -> dict | None:
    _incidents_not_deployed()


def update_incident(incident_id: str, status: str) -> dict:
    _incidents_not_deployed()
