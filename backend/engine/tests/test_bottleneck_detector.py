"""
Tests for bottleneck_detector.py

Properties tested:
  P-5: Primary bottleneck = worst constraint by severity
  Shelter within capacity → no bottleneck generated
  Hospital within effective_capacity → no bottleneck generated
  Bottlenecks sorted descending by severity_score
  effective_capacity = capacity + surge_capacity
"""
import dataclasses
import pytest

from engine.models import ZoneResult, RiskComponents, Shelter, Hospital, Bottleneck
from engine.bottleneck_detector import detect_bottlenecks


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_zone_result(zone_id="z1", risk_score=60.0, road_accessibility_raw=0.5,
                     resource_shortage_raw=0.5):
    """
    Build a ZoneResult with controlled component values.
    road_accessibility_score = 0.15 * (1 - road_accessibility_raw)
    resource_shortage_score  = 0.10 * resource_shortage_raw
    """
    return ZoneResult(
        zone_id=zone_id,
        risk_score=risk_score,
        risk_level="high",
        response_time_minutes=30.0,
        risk_components=RiskComponents(
            affected_population_score=0.0,
            flood_severity_score=0.0,
            medical_urgency_score=0.0,
            road_accessibility_score=0.15 * (1.0 - road_accessibility_raw),
            resource_shortage_score=0.10 * resource_shortage_raw,
        ),
    )


# ---------------------------------------------------------------------------
# Resource shortage
# ---------------------------------------------------------------------------

def test_resource_shortage_detected_for_high_risk_zone():
    zr = make_zone_result(risk_score=60.0, resource_shortage_raw=0.8)
    bottlenecks = detect_bottlenecks([zr], [], [])
    resource_bn = [b for b in bottlenecks if b.type == "resource_shortage"]
    assert len(resource_bn) >= 1
    assert resource_bn[0].zone_id == "z1"


def test_no_resource_shortage_when_fully_covered():
    zr = make_zone_result(risk_score=60.0, resource_shortage_raw=0.0)
    bottlenecks = detect_bottlenecks([zr], [], [])
    resource_bn = [b for b in bottlenecks if b.type == "resource_shortage"]
    assert len(resource_bn) == 0


# ---------------------------------------------------------------------------
# Shelter capacity
# ---------------------------------------------------------------------------

def test_shelter_within_capacity_no_bottleneck():
    shelter = Shelter(
        shelter_id="s1", name="S1", coordinates=[0, 0],
        capacity=500, current_occupancy=400,
    )
    bottlenecks = detect_bottlenecks([], [shelter], [])
    shelter_bn = [b for b in bottlenecks if b.type == "shelter_capacity"]
    assert len(shelter_bn) == 0


def test_shelter_at_capacity_no_bottleneck():
    shelter = Shelter(
        shelter_id="s1", name="S1", coordinates=[0, 0],
        capacity=500, current_occupancy=500,
    )
    bottlenecks = detect_bottlenecks([], [shelter], [])
    shelter_bn = [b for b in bottlenecks if b.type == "shelter_capacity"]
    assert len(shelter_bn) == 0


def test_shelter_over_capacity_creates_bottleneck():
    shelter = Shelter(
        shelter_id="s1", name="S1", coordinates=[0, 0],
        capacity=300, current_occupancy=400,
    )
    bottlenecks = detect_bottlenecks([], [shelter], [])
    shelter_bn = [b for b in bottlenecks if b.type == "shelter_capacity"]
    assert len(shelter_bn) == 1
    # severity = 1 - 300/400 = 0.25
    assert abs(shelter_bn[0].severity_score - 0.25) < 1e-4


# ---------------------------------------------------------------------------
# Hospital capacity
# ---------------------------------------------------------------------------

def test_hospital_within_effective_capacity_no_bottleneck():
    hosp = Hospital(
        hospital_id="h1", name="H1", coordinates=[0, 0],
        capacity=200, surge_capacity=50, current_occupancy=230,
    )
    # effective_capacity = 250, occupancy = 230 → within → no bottleneck
    bottlenecks = detect_bottlenecks([], [], [hosp])
    hosp_bn = [b for b in bottlenecks if b.type == "hospital_capacity"]
    assert len(hosp_bn) == 0


def test_hospital_at_effective_capacity_no_bottleneck():
    hosp = Hospital(
        hospital_id="h1", name="H1", coordinates=[0, 0],
        capacity=200, surge_capacity=50, current_occupancy=250,
    )
    # effective_capacity = 250, occupancy = 250 → exactly at → no bottleneck
    bottlenecks = detect_bottlenecks([], [], [hosp])
    hosp_bn = [b for b in bottlenecks if b.type == "hospital_capacity"]
    assert len(hosp_bn) == 0


def test_hospital_above_effective_capacity_creates_bottleneck():
    hosp = Hospital(
        hospital_id="h1", name="H1", coordinates=[0, 0],
        capacity=100, surge_capacity=20, current_occupancy=150,
    )
    # effective_capacity = 120, occupancy = 150 → over
    bottlenecks = detect_bottlenecks([], [], [hosp])
    hosp_bn = [b for b in bottlenecks if b.type == "hospital_capacity"]
    assert len(hosp_bn) == 1
    expected_severity = 1.0 - 120 / 150
    assert abs(hosp_bn[0].severity_score - expected_severity) < 1e-4


def test_hospital_with_zero_surge_capacity():
    """Surge capacity of 0 means effective = base capacity only."""
    hosp = Hospital(
        hospital_id="h1", name="H1", coordinates=[0, 0],
        capacity=100, surge_capacity=0, current_occupancy=120,
    )
    bottlenecks = detect_bottlenecks([], [], [hosp])
    hosp_bn = [b for b in bottlenecks if b.type == "hospital_capacity"]
    assert len(hosp_bn) == 1  # 120 > 100 effective
    expected_severity = 1.0 - 100 / 120
    assert abs(hosp_bn[0].severity_score - expected_severity) < 1e-4


# ---------------------------------------------------------------------------
# Sorting (P-5 — primary bottleneck = worst constraint)
# ---------------------------------------------------------------------------

def test_bottlenecks_sorted_descending():
    shelter_low = Shelter(
        shelter_id="s_low", name="Low", coordinates=[0, 0],
        capacity=300, current_occupancy=310,   # low severity
    )
    shelter_high = Shelter(
        shelter_id="s_high", name="High", coordinates=[0, 0],
        capacity=100, current_occupancy=500,   # high severity
    )
    bottlenecks = detect_bottlenecks([], [shelter_low, shelter_high], [])
    scores = [b.severity_score for b in bottlenecks]
    assert scores == sorted(scores, reverse=True)


def test_primary_bottleneck_is_worst_constraint():
    """
    Combine shelter overcapacity and hospital overcapacity.
    The one with higher severity_score must be first.
    """
    shelter = Shelter(
        shelter_id="s1", name="S1", coordinates=[0, 0],
        capacity=100, current_occupancy=200,   # severity = 0.5
    )
    hospital = Hospital(
        hospital_id="h1", name="H1", coordinates=[0, 0],
        capacity=100, surge_capacity=0, current_occupancy=1000,  # severity = 0.9
    )
    bottlenecks = detect_bottlenecks([], [shelter], [hospital])
    assert len(bottlenecks) >= 2
    assert bottlenecks[0].severity_score >= bottlenecks[1].severity_score
    assert bottlenecks[0].facility_id == "h1"


# ---------------------------------------------------------------------------
# Empty inputs
# ---------------------------------------------------------------------------

def test_no_bottlenecks_with_healthy_state():
    zr = make_zone_result(risk_score=10.0, road_accessibility_raw=0.9, resource_shortage_raw=0.0)
    shelter = Shelter(
        shelter_id="s1", name="S1", coordinates=[0, 0],
        capacity=500, current_occupancy=100,
    )
    hospital = Hospital(
        hospital_id="h1", name="H1", coordinates=[0, 0],
        capacity=200, surge_capacity=50, current_occupancy=50,
    )
    bottlenecks = detect_bottlenecks([zr], [shelter], [hospital])
    # Low risk zone (10.0) won't trigger road_access; no shortages or overcrowding
    capacity_types = {b.type for b in bottlenecks}
    assert "shelter_capacity" not in capacity_types
    assert "hospital_capacity" not in capacity_types
