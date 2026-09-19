"""
Shared fixtures and Hypothesis strategies for CrisisSim engine tests.
"""
import dataclasses
import pytest
from hypothesis import strategies as st

from engine.models import (
    ZoneParams, Shelter, Hospital, Scenario, SimulationState, Zone,
)


# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------

def zone_params_strategy(zone_id: str = "z1"):
    """Generate valid ZoneParams with demand_units >= 1."""
    return st.builds(
        ZoneParams,
        zone_id=st.just(zone_id),
        flood_severity=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        affected_population=st.integers(min_value=0, max_value=100_000),
        medical_urgency=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        road_accessibility=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        rescue_teams=st.integers(min_value=0, max_value=20),
        ambulances=st.integers(min_value=0, max_value=20),
        demand_units=st.integers(min_value=1, max_value=20),
    )


def shelter_strategy(shelter_id: str = "s1"):
    return st.builds(
        Shelter,
        shelter_id=st.just(shelter_id),
        name=st.just("Test Shelter"),
        coordinates=st.just([51.5, -0.1]),
        capacity=st.integers(min_value=1, max_value=1000),
        current_occupancy=st.integers(min_value=0, max_value=1200),
    )


def hospital_strategy(hospital_id: str = "h1"):
    return st.builds(
        Hospital,
        hospital_id=st.just(hospital_id),
        name=st.just("Test Hospital"),
        coordinates=st.just([51.5, -0.1]),
        capacity=st.integers(min_value=1, max_value=500),
        surge_capacity=st.integers(min_value=0, max_value=200),
        current_occupancy=st.integers(min_value=0, max_value=700),
    )


# ---------------------------------------------------------------------------
# Concrete fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def base_zone():
    return ZoneParams(
        zone_id="zone-1",
        flood_severity=0.8,
        affected_population=10_000,
        medical_urgency=0.7,
        road_accessibility=0.4,
        rescue_teams=2,
        ambulances=3,
        demand_units=8,
    )


@pytest.fixture
def base_shelter():
    return Shelter(
        shelter_id="shelter-1",
        name="Community Center",
        coordinates=[51.508, -0.087],
        capacity=500,
        current_occupancy=420,
    )


@pytest.fixture
def overcrowded_shelter():
    return Shelter(
        shelter_id="shelter-2",
        name="Overflow Shelter",
        coordinates=[51.508, -0.087],
        capacity=300,
        current_occupancy=400,
    )


@pytest.fixture
def base_hospital():
    return Hospital(
        hospital_id="hospital-1",
        name="North General",
        coordinates=[51.512, -0.082],
        capacity=200,
        surge_capacity=50,
        current_occupancy=180,
    )


@pytest.fixture
def overwhelmed_hospital():
    """Hospital where occupancy exceeds effective_capacity."""
    return Hospital(
        hospital_id="hospital-2",
        name="South Medical",
        coordinates=[51.512, -0.082],
        capacity=100,
        surge_capacity=20,
        current_occupancy=150,  # > 120 effective capacity
    )


@pytest.fixture
def two_zone_scenario():
    """A minimal Scenario with two zones, one shelter, one hospital."""
    zone1 = Zone(
        zone_id="zone-1", name="High Risk Zone",
        coordinates=[[51.5, -0.09], [51.51, -0.09], [51.51, -0.08], [51.5, -0.08]],
        centroid=[51.505, -0.085],
        flood_severity=0.9, affected_population=12_000,
        medical_urgency=0.8, road_accessibility=0.2,
        rescue_teams=1, ambulances=1, demand_units=8,
    )
    zone2 = Zone(
        zone_id="zone-2", name="Low Risk Zone",
        coordinates=[[51.5, -0.10], [51.51, -0.10], [51.51, -0.09], [51.5, -0.09]],
        centroid=[51.505, -0.095],
        flood_severity=0.2, affected_population=2_000,
        medical_urgency=0.1, road_accessibility=0.9,
        rescue_teams=5, ambulances=4, demand_units=4,
    )
    shelter = Shelter(
        shelter_id="shelter-1", name="Main Shelter",
        coordinates=[51.508, -0.087], capacity=500, current_occupancy=420,
    )
    hospital = Hospital(
        hospital_id="hospital-1", name="City Hospital",
        coordinates=[51.512, -0.082], capacity=200, surge_capacity=50,
        current_occupancy=180,
    )
    return Scenario(
        scenario_id="flood-scenario-001",
        name="River Delta Flood",
        description="Test scenario with two zones",
        severity="high",
        created_at="2026-09-10T00:00:00Z",
        zones=[zone1, zone2],
        shelters=[shelter],
        hospitals=[hospital],
        population_max=15_000,
    )


@pytest.fixture
def two_zone_params(two_zone_scenario):
    """ZoneParams derived from two_zone_scenario zones."""
    return [
        ZoneParams(
            zone_id=z.zone_id,
            flood_severity=z.flood_severity,
            affected_population=z.affected_population,
            medical_urgency=z.medical_urgency,
            road_accessibility=z.road_accessibility,
            rescue_teams=z.rescue_teams,
            ambulances=z.ambulances,
            demand_units=z.demand_units,
        )
        for z in two_zone_scenario.zones
    ]
