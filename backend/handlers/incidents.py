"""
Incident handlers — citizen reports and authority status updates.
No simulation engine imports.
"""
from __future__ import annotations

from datetime import datetime, timezone

VALID_HAZARDS = frozenset(
    {"flood", "fire", "earthquake", "cyclone", "industrial_accident"}
)
VALID_SEVERITIES = frozenset({"low", "moderate", "high", "critical"})
VALID_STATUSES = frozenset(
    {
        "reported",
        "acknowledged",
        "assessing",
        "response_dispatched",
        "resolved",
    }
)

NEXT_STATUS = {
    "reported": "acknowledged",
    "acknowledged": "assessing",
    "assessing": "response_dispatched",
    "response_dispatched": "resolved",
}


def _validate_create_payload(data: dict) -> dict:
    if not isinstance(data, dict):
        raise ValueError("Request body must be a JSON object.")

    required = (
        "hazard_type",
        "location_name",
        "latitude",
        "longitude",
        "severity",
        "description",
    )
    missing = [field for field in required if field not in data or data[field] in (None, "")]
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")

    hazard_type = str(data["hazard_type"]).strip()
    if hazard_type not in VALID_HAZARDS:
        raise ValueError(f"Invalid hazard_type: {hazard_type}")

    severity = str(data["severity"]).strip().lower()
    if severity not in VALID_SEVERITIES:
        raise ValueError(f"Invalid severity: {severity}")

    location_name = str(data["location_name"]).strip()
    if not location_name:
        raise ValueError("location_name must not be empty.")

    description = str(data["description"]).strip()
    if not description:
        raise ValueError("description must not be empty.")

    try:
        latitude = float(data["latitude"])
        longitude = float(data["longitude"])
    except (TypeError, ValueError):
        raise ValueError("latitude and longitude must be valid numbers.")

    if not (-90 <= latitude <= 90):
        raise ValueError("latitude must be between -90 and 90.")
    if not (-180 <= longitude <= 180):
        raise ValueError("longitude must be between -180 and 180.")

    payload = {
        "hazard_type": hazard_type,
        "location_name": location_name,
        "latitude": latitude,
        "longitude": longitude,
        "severity": severity,
        "description": description,
        "status": "reported",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    if data.get("evidence_url"):
        payload["evidence_url"] = str(data["evidence_url"])
    return payload


def handle_create_incident(data: dict, store) -> dict:
    payload = _validate_create_payload(data)
    return store.create_incident(payload)


def handle_list_incidents(store) -> dict:
    incidents = store.list_incidents()
    return {"incidents": incidents}


def handle_get_incident(incident_id: str, store) -> dict | None:
    return store.get_incident(incident_id)


def handle_update_incident(incident_id: str, data: dict, store) -> dict:
    if not isinstance(data, dict):
        raise ValueError("Request body must be a JSON object.")
    new_status = data.get("status")
    if not new_status:
        raise ValueError("status is required.")
    new_status = str(new_status).strip().lower()
    if new_status not in VALID_STATUSES:
        raise ValueError(f"Invalid status: {new_status}")

    existing = store.get_incident(incident_id)
    if existing is None:
        raise LookupError(f"Incident not found: {incident_id}")

    current = existing["status"]
    allowed_next = NEXT_STATUS.get(current)
    if allowed_next != new_status:
        raise ValueError(
            f"Invalid status transition from '{current}' to '{new_status}'. "
            f"Expected next status: '{allowed_next}'."
            if allowed_next
            else f"Incident is already '{current}' and cannot be updated further."
        )

    return store.update_incident(incident_id, new_status)
