"""
Tests for response_time.py

Properties tested:
  P-4: Increasing resources never increases response time
  P-5: Increasing road accessibility never increases response time
  Additional: Higher medical urgency never decreases response time
              Result always in [5, 120]
              Zero demand_units handled safely
"""
import dataclasses
import pytest
from hypothesis import given, assume, settings
from hypothesis import strategies as st

from engine.models import ZoneParams
from engine.response_time import estimate_response_time, BASE_RESPONSE_MINUTES
from .conftest import zone_params_strategy


# ---------------------------------------------------------------------------
# Bounds
# ---------------------------------------------------------------------------

@given(zone_params_strategy())
@settings(max_examples=500)
def test_response_time_bounds(zone):
    rt = estimate_response_time(zone)
    assert 5.0 <= rt <= 120.0, f"Response time {rt} out of [5, 120]"


# ---------------------------------------------------------------------------
# P-4: More resources never increases response time
# ---------------------------------------------------------------------------

@given(zone_params_strategy(), st.integers(min_value=0, max_value=10))
@settings(max_examples=500)
def test_more_rescue_teams_never_increase_response_time(zone, extra):
    assume(extra >= 0)
    zone_more = dataclasses.replace(zone, rescue_teams=zone.rescue_teams + extra)
    t1 = estimate_response_time(zone)
    t2 = estimate_response_time(zone_more)
    assert t2 <= t1 + 1e-9, (
        f"Response time increased with more rescue teams: {t1}→{t2} (+{extra} teams)"
    )


@given(zone_params_strategy(), st.integers(min_value=0, max_value=10))
@settings(max_examples=500)
def test_more_ambulances_never_increase_response_time(zone, extra):
    assume(extra >= 0)
    zone_more = dataclasses.replace(zone, ambulances=zone.ambulances + extra)
    t1 = estimate_response_time(zone)
    t2 = estimate_response_time(zone_more)
    assert t2 <= t1 + 1e-9


# ---------------------------------------------------------------------------
# P-5: Better road accessibility never increases response time
# ---------------------------------------------------------------------------

@given(zone_params_strategy(), st.floats(min_value=0.0, max_value=1.0, allow_nan=False))
@settings(max_examples=500)
def test_better_roads_never_increase_response_time(zone, better_access):
    assume(better_access >= zone.road_accessibility)
    zone_better = dataclasses.replace(zone, road_accessibility=better_access)
    t1 = estimate_response_time(zone)
    t2 = estimate_response_time(zone_better)
    assert t2 <= t1 + 1e-9, (
        f"Response time increased with better roads: {t1}→{t2}"
    )


# ---------------------------------------------------------------------------
# Higher medical urgency never decreases response time
# ---------------------------------------------------------------------------

@given(zone_params_strategy(), st.floats(min_value=0.0, max_value=1.0, allow_nan=False))
@settings(max_examples=300)
def test_higher_urgency_never_decreases_response_time(zone, higher_urgency):
    assume(higher_urgency >= zone.medical_urgency)
    zone_urgent = dataclasses.replace(zone, medical_urgency=higher_urgency)
    t1 = estimate_response_time(zone)
    t2 = estimate_response_time(zone_urgent)
    assert t2 >= t1 - 1e-9


# ---------------------------------------------------------------------------
# Known values
# ---------------------------------------------------------------------------

def test_fully_accessible_max_resources_min_urgency():
    """Best case: full access, max resources, zero urgency → near BASE * 1 * 1 * 1 = 10."""
    zone = ZoneParams(
        zone_id="best", flood_severity=0.0, affected_population=0,
        medical_urgency=0.0, road_accessibility=1.0,
        rescue_teams=100, ambulances=100, demand_units=1,
    )
    rt = estimate_response_time(zone)
    # road_factor=1, resource_factor=1, demand_factor=1 → 10 → clamped to max(5, 10)=10
    assert rt == 10.0


def test_inaccessible_roads_no_resources_max_urgency():
    """Worst case: full blockage, zero resources, max urgency → clamped to 120."""
    zone = ZoneParams(
        zone_id="worst", flood_severity=0.0, affected_population=0,
        medical_urgency=1.0, road_accessibility=0.0,
        rescue_teams=0, ambulances=0, demand_units=5,
    )
    rt = estimate_response_time(zone)
    # road_factor=3, resource_factor=2, demand_factor=2 → 10*3*2*2=120 → clamped to 120
    assert rt == 120.0


def test_zero_demand_units_safe():
    """Zero demand_units should not raise; should treat resource_ratio as 1.0."""
    zone = ZoneParams(
        zone_id="z0d", flood_severity=0.5, affected_population=0,
        medical_urgency=0.5, road_accessibility=0.5,
        rescue_teams=0, ambulances=0, demand_units=0,
    )
    rt = estimate_response_time(zone)
    assert 5.0 <= rt <= 120.0


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------

@given(zone_params_strategy())
def test_response_time_determinism(zone):
    t1 = estimate_response_time(zone)
    t2 = estimate_response_time(zone)
    assert t1 == t2
