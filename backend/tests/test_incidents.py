"""
Incident API tests — FastAPI + memory store.
"""
import re

import pytest
from fastapi.testclient import TestClient

import persistence.memory_store as store
from local_server import app
from seed_data import get_default_scenario

client = TestClient(app)

INCIDENT_ID_PATTERN = re.compile(r"^INC-\d{4}-\d{4}$")

VALID_BODY = {
    "hazard_type": "fire",
    "location_name": "Bhopal, Madhya Pradesh, India",
    "latitude": 23.2599,
    "longitude": 77.4126,
    "severity": "high",
    "description": "Heavy smoke reported near the market.",
}


@pytest.fixture(autouse=True)
def reset_and_seed():
    store.reset_store()
    store.seed_scenario(get_default_scenario())
    yield
    store.reset_store()


def test_post_valid_incident():
    resp = client.post("/api/v1/incidents", json=VALID_BODY)
    assert resp.status_code == 201
    data = resp.json()
    assert INCIDENT_ID_PATTERN.match(data["incident_id"])
    assert data["status"] == "reported"
    assert data["hazard_type"] == "fire"


def test_post_generates_sequential_ids():
    first = client.post("/api/v1/incidents", json=VALID_BODY).json()
    second = client.post(
        "/api/v1/incidents",
        json={**VALID_BODY, "description": "Second report"},
    ).json()
    assert first["incident_id"] != second["incident_id"]
    assert first["incident_id"].endswith("0001") or first["incident_id"][-4:] == "0001"


def test_list_incidents():
    client.post("/api/v1/incidents", json=VALID_BODY)
    resp = client.get("/api/v1/incidents")
    assert resp.status_code == 200
    incidents = resp.json()["incidents"]
    assert len(incidents) == 1


def test_get_incident():
    created = client.post("/api/v1/incidents", json=VALID_BODY).json()
    resp = client.get(f"/api/v1/incidents/{created['incident_id']}")
    assert resp.status_code == 200
    assert resp.json()["incident_id"] == created["incident_id"]


def test_get_incident_404():
    resp = client.get("/api/v1/incidents/INC-2099-9999")
    assert resp.status_code == 404


def test_status_transitions():
    created = client.post("/api/v1/incidents", json=VALID_BODY).json()
    incident_id = created["incident_id"]

    for current, nxt in [
        ("reported", "acknowledged"),
        ("acknowledged", "assessing"),
        ("assessing", "response_dispatched"),
        ("response_dispatched", "resolved"),
    ]:
        resp = client.patch(f"/api/v1/incidents/{incident_id}", json={"status": nxt})
        assert resp.status_code == 200
        assert resp.json()["status"] == nxt


def test_invalid_transition_rejected():
    created = client.post("/api/v1/incidents", json=VALID_BODY).json()
    incident_id = created["incident_id"]
    resp = client.patch(
        f"/api/v1/incidents/{incident_id}",
        json={"status": "resolved"},
    )
    assert resp.status_code == 400


def test_missing_required_field():
    body = {**VALID_BODY}
    del body["description"]
    resp = client.post("/api/v1/incidents", json=body)
    assert resp.status_code in (400, 422)


def test_invalid_hazard():
    resp = client.post("/api/v1/incidents", json={**VALID_BODY, "hazard_type": "volcano"})
    assert resp.status_code == 400


def test_invalid_severity():
    resp = client.post("/api/v1/incidents", json={**VALID_BODY, "severity": "extreme"})
    assert resp.status_code == 400


def test_patch_404():
    resp = client.patch("/api/v1/incidents/INC-2099-0001", json={"status": "acknowledged"})
    assert resp.status_code == 404
