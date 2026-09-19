"""
Phase 2 integration tests — FastAPI endpoints via TestClient.

Tests:
  - GET /scenarios (list)
  - GET /scenarios/{id} (full scenario)
  - GET /scenarios/{id} 404
  - POST /simulate (full pipeline)
  - POST /simulate validation errors
  - GET /results/{id}/latest (after simulate)
  - GET /results/{id}/latest 404 (before simulate)
  - POST /explain (fallback, no AWS)
  - POST /explain 404

All tests use an isolated in-memory store reset between tests.
"""
import pytest
from fastapi.testclient import TestClient

import persistence.memory_store as store
from local_server import app
from seed_data import get_default_scenario


@pytest.fixture(autouse=True)
def reset_and_seed():
    """Reset store and reseed before each test."""
    store.reset_store()
    store.seed_scenario(get_default_scenario())
    yield
    store.reset_store()


client = TestClient(app)

SCENARIO_ID = "flood-scenario-001"


# ── Helper ────────────────────────────────────────────────────────────────────

def default_params():
    """Build ZoneParams matching the default scenario zones."""
    scenario = get_default_scenario()
    return [
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
        for z in scenario.zones
    ]


# ── GET /scenarios ────────────────────────────────────────────────────────────

def test_list_scenarios_returns_200():
    resp = client.get("/api/v1/scenarios")
    assert resp.status_code == 200


def test_list_scenarios_contains_seed():
    resp = client.get("/api/v1/scenarios")
    data = resp.json()
    assert "scenarios" in data
    assert len(data["scenarios"]) == 1
    assert data["scenarios"][0]["scenario_id"] == SCENARIO_ID


def test_list_scenarios_has_required_fields():
    resp = client.get("/api/v1/scenarios")
    s = resp.json()["scenarios"][0]
    assert "scenario_id" in s
    assert "name" in s
    assert "description" in s
    assert "severity" in s


# ── GET /scenarios/{id} ───────────────────────────────────────────────────────

def test_get_scenario_returns_full_data():
    resp = client.get(f"/api/v1/scenarios/{SCENARIO_ID}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["scenario_id"] == SCENARIO_ID
    assert "zones" in data
    assert "shelters" in data
    assert "hospitals" in data
    assert "population_max" in data


def test_get_scenario_has_five_zones():
    resp = client.get(f"/api/v1/scenarios/{SCENARIO_ID}")
    assert len(resp.json()["zones"]) == 5


def test_get_scenario_zone_has_demand_units():
    resp = client.get(f"/api/v1/scenarios/{SCENARIO_ID}")
    for zone in resp.json()["zones"]:
        assert "demand_units" in zone, f"Missing demand_units in zone {zone['zone_id']}"


def test_get_scenario_not_found():
    resp = client.get("/api/v1/scenarios/nonexistent-id")
    assert resp.status_code == 404


# ── POST /simulate ────────────────────────────────────────────────────────────

def test_simulate_returns_200():
    resp = client.post(
        "/api/v1/simulate",
        json={"scenario_id": SCENARIO_ID, "params": default_params()},
    )
    assert resp.status_code == 200


def test_simulate_returns_complete_result():
    resp = client.post(
        "/api/v1/simulate",
        json={"scenario_id": SCENARIO_ID, "params": default_params()},
    )
    data = resp.json()
    assert "result_id" in data
    assert "scenario_id" in data
    assert "run_at" in data
    assert "baseline_zone_results" in data
    assert "bottlenecks" in data
    assert "interventions" in data
    assert "recommended_strategy" in data
    assert "params_used" in data


def test_simulate_returns_four_interventions():
    resp = client.post(
        "/api/v1/simulate",
        json={"scenario_id": SCENARIO_ID, "params": default_params()},
    )
    interventions = resp.json()["interventions"]
    strategies = {iv["strategy"] for iv in interventions}
    assert strategies == {"baseline", "resource_reallocation", "capacity_expansion", "combined"}


def test_simulate_baseline_risk_reduction_is_zero():
    resp = client.post(
        "/api/v1/simulate",
        json={"scenario_id": SCENARIO_ID, "params": default_params()},
    )
    baseline = next(
        iv for iv in resp.json()["interventions"] if iv["strategy"] == "baseline"
    )
    assert baseline["risk_reduction_pct"] == 0.0


def test_simulate_recommended_strategy_valid():
    resp = client.post(
        "/api/v1/simulate",
        json={"scenario_id": SCENARIO_ID, "params": default_params()},
    )
    rec = resp.json()["recommended_strategy"]
    assert rec in {"baseline", "resource_reallocation", "capacity_expansion", "combined"}


def test_simulate_recommended_has_highest_composite_score():
    resp = client.post(
        "/api/v1/simulate",
        json={"scenario_id": SCENARIO_ID, "params": default_params()},
    )
    data = resp.json()
    rec = data["recommended_strategy"]
    rec_result = next(iv for iv in data["interventions"] if iv["strategy"] == rec)
    for iv in data["interventions"]:
        assert rec_result["composite_score"] >= iv["composite_score"] - 1e-9


def test_simulate_risk_scores_in_bounds():
    resp = client.post(
        "/api/v1/simulate",
        json={"scenario_id": SCENARIO_ID, "params": default_params()},
    )
    data = resp.json()
    for zr in data["baseline_zone_results"]:
        assert 0 <= zr["risk_score"] <= 100
    for iv in data["interventions"]:
        for zr in iv["zone_results"]:
            assert 0 <= zr["risk_score"] <= 100


def test_simulate_response_times_in_bounds():
    resp = client.post(
        "/api/v1/simulate",
        json={"scenario_id": SCENARIO_ID, "params": default_params()},
    )
    for zr in resp.json()["baseline_zone_results"]:
        assert 5 <= zr["response_time_minutes"] <= 120


def test_simulate_scenario_not_found():
    resp = client.post(
        "/api/v1/simulate",
        json={"scenario_id": "bad-id", "params": default_params()},
    )
    assert resp.status_code == 404


def test_simulate_missing_zone_params():
    """Providing params for only some zones should fail."""
    params = default_params()[:2]  # only 2 of 5 zones
    resp = client.post(
        "/api/v1/simulate",
        json={"scenario_id": SCENARIO_ID, "params": params},
    )
    assert resp.status_code in (404, 422)


def test_simulate_deterministic():
    """Running the same params twice should return identical scores."""
    payload = {"scenario_id": SCENARIO_ID, "params": default_params()}
    r1 = client.post("/api/v1/simulate", json=payload).json()
    r2 = client.post("/api/v1/simulate", json=payload).json()

    for zr1, zr2 in zip(r1["baseline_zone_results"], r2["baseline_zone_results"]):
        assert zr1["risk_score"] == zr2["risk_score"]
        assert zr1["response_time_minutes"] == zr2["response_time_minutes"]
    assert r1["recommended_strategy"] == r2["recommended_strategy"]


def test_simulate_persists_result():
    """After simulate, GET /results/latest should return matching result_id."""
    sim_resp = client.post(
        "/api/v1/simulate",
        json={"scenario_id": SCENARIO_ID, "params": default_params()},
    )
    result_id = sim_resp.json()["result_id"]

    latest_resp = client.get(f"/api/v1/results/{SCENARIO_ID}/latest")
    assert latest_resp.status_code == 200
    assert latest_resp.json()["result_id"] == result_id


# ── GET /results/{id}/latest ──────────────────────────────────────────────────

def test_get_latest_result_404_before_simulate():
    resp = client.get(f"/api/v1/results/{SCENARIO_ID}/latest")
    assert resp.status_code == 404


def test_get_latest_result_returns_most_recent():
    """Run two simulations; latest should be the second one."""
    # Run first simulation with default params
    r1 = client.post(
        "/api/v1/simulate",
        json={"scenario_id": SCENARIO_ID, "params": default_params()},
    ).json()

    # Run second simulation with modified params (slightly higher flood severity)
    params2 = default_params()
    params2[0]["flood_severity"] = 1.0  # modify first zone
    r2 = client.post(
        "/api/v1/simulate",
        json={"scenario_id": SCENARIO_ID, "params": params2},
    ).json()

    latest = client.get(f"/api/v1/results/{SCENARIO_ID}/latest").json()
    # Latest should be r2 (run_at is later)
    assert latest["result_id"] == r2["result_id"]


# ── POST /explain ─────────────────────────────────────────────────────────────

def test_explain_returns_fallback_without_aws():
    """Without AWS credentials, explanation should use deterministic fallback."""
    sim_resp = client.post(
        "/api/v1/simulate",
        json={"scenario_id": SCENARIO_ID, "params": default_params()},
    )
    result_id = sim_resp.json()["result_id"]

    exp_resp = client.post("/api/v1/explain", json={"result_id": result_id})
    assert exp_resp.status_code == 200
    data = exp_resp.json()
    assert "explanation" in data
    assert "strategy_explained" in data
    assert "generated_at" in data
    assert "fallback" in data
    assert isinstance(data["explanation"], str)
    assert len(data["explanation"]) > 50  # non-trivial explanation


def test_explain_strategy_matches_recommended():
    """The explained strategy must match the simulation's recommendation."""
    sim_resp = client.post(
        "/api/v1/simulate",
        json={"scenario_id": SCENARIO_ID, "params": default_params()},
    )
    sim_data = sim_resp.json()
    result_id = sim_data["result_id"]
    recommended = sim_data["recommended_strategy"]

    exp_resp = client.post("/api/v1/explain", json={"result_id": result_id})
    assert exp_resp.json()["strategy_explained"] == recommended


def test_explain_not_found():
    resp = client.post("/api/v1/explain", json={"result_id": "nonexistent-id"})
    assert resp.status_code == 404


def test_explain_fallback_references_recommendation():
    """Fallback explanation should mention the recommended strategy label."""
    sim_resp = client.post(
        "/api/v1/simulate",
        json={"scenario_id": SCENARIO_ID, "params": default_params()},
    )
    result_id = sim_resp.json()["result_id"]

    exp_resp = client.post("/api/v1/explain", json={"result_id": result_id})
    explanation = exp_resp.json()["explanation"]
    # Should mention something simulation-specific (not be empty boilerplate)
    assert any(
        phrase in explanation.lower()
        for phrase in ["bottleneck", "risk", "strategy", "intervention", "response"]
    )


# ── Health check ──────────────────────────────────────────────────────────────

def test_health_check():
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
    assert resp.json()["scenarios_loaded"] == 1


# ── Bedrock explainer unit tests (no HTTP) ────────────────────────────────────

def test_fallback_explanation_not_empty():
    from bedrock.explainer import _build_fallback_explanation
    from engine import run_full_simulation
    from engine.models import ZoneParams

    scenario = get_default_scenario()
    params = [
        ZoneParams(
            zone_id=z.zone_id, flood_severity=z.flood_severity,
            affected_population=z.affected_population,
            medical_urgency=z.medical_urgency, road_accessibility=z.road_accessibility,
            rescue_teams=z.rescue_teams, ambulances=z.ambulances,
            demand_units=z.demand_units,
        )
        for z in scenario.zones
    ]
    result = run_full_simulation(scenario, params)
    explanation = _build_fallback_explanation(result)
    assert len(explanation) > 100
    assert result.recommended_strategy in explanation.lower() or any(
        label.lower() in explanation.lower()
        for label in ["baseline", "reallocation", "expansion", "combined"]
    )


def test_fallback_explanation_contains_numbers():
    """Fallback must embed actual simulation numbers, not be generic."""
    from bedrock.explainer import _build_fallback_explanation
    from engine import run_full_simulation
    from engine.models import ZoneParams

    scenario = get_default_scenario()
    params = [
        ZoneParams(
            zone_id=z.zone_id, flood_severity=z.flood_severity,
            affected_population=z.affected_population,
            medical_urgency=z.medical_urgency, road_accessibility=z.road_accessibility,
            rescue_teams=z.rescue_teams, ambulances=z.ambulances,
            demand_units=z.demand_units,
        )
        for z in scenario.zones
    ]
    result = run_full_simulation(scenario, params)
    explanation = _build_fallback_explanation(result)
    # Should contain at least one number from the simulation
    import re
    numbers_found = re.findall(r"\d+\.\d+", explanation)
    assert len(numbers_found) > 0, "Fallback explanation contains no numeric values"
