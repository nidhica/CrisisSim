"""
Seed data for CrisisSim — deterministic multi-hazard demo scenarios.
Provides Scenario objects used by both:
  - local_server.py (in-memory store)
  - seed_data --target dynamodb (Phase 4)

No AWS dependencies required for local use.
"""
from __future__ import annotations
from engine.models import Zone, Shelter, Hospital, Scenario
import dataclasses


def get_default_scenario() -> Scenario:
    """
    Returns the single pre-loaded flood scenario used in the MVP.
    population_max is set to 15000, the ceiling for population normalization.
    """
    return Scenario(
        scenario_id="flood-scenario-001",
        name="River Delta Flood — Category 3",
        description=(
            "Severe flooding across 5 urban zones following dam overflow. "
            "Multiple zones at critical risk with resource shortages and road blockages."
        ),
        severity="high",
        created_at="2026-09-10T00:00:00Z",
        population_max=15_000,
        zones=[
            Zone(
                zone_id="zone-1",
                name="North Bank",
                coordinates=[
                    [51.510, -0.090],
                    [51.515, -0.090],
                    [51.515, -0.080],
                    [51.510, -0.080],
                ],
                centroid=[51.5125, -0.085],
                flood_severity=0.9,
                affected_population=12_000,
                medical_urgency=0.8,
                road_accessibility=0.2,
                rescue_teams=1,
                ambulances=1,
                demand_units=8,
            ),
            Zone(
                zone_id="zone-2",
                name="City Centre",
                coordinates=[
                    [51.505, -0.090],
                    [51.510, -0.090],
                    [51.510, -0.080],
                    [51.505, -0.080],
                ],
                centroid=[51.5075, -0.085],
                flood_severity=0.6,
                affected_population=8_000,
                medical_urgency=0.5,
                road_accessibility=0.5,
                rescue_teams=3,
                ambulances=2,
                demand_units=6,
            ),
            Zone(
                zone_id="zone-3",
                name="East Suburb",
                coordinates=[
                    [51.510, -0.080],
                    [51.515, -0.080],
                    [51.515, -0.070],
                    [51.510, -0.070],
                ],
                centroid=[51.5125, -0.075],
                flood_severity=0.4,
                affected_population=5_000,
                medical_urgency=0.3,
                road_accessibility=0.7,
                rescue_teams=3,
                ambulances=2,
                demand_units=5,
            ),
            Zone(
                zone_id="zone-4",
                name="West Industrial",
                coordinates=[
                    [51.505, -0.100],
                    [51.510, -0.100],
                    [51.510, -0.090],
                    [51.505, -0.090],
                ],
                centroid=[51.5075, -0.095],
                flood_severity=0.7,
                affected_population=4_000,
                medical_urgency=0.6,
                road_accessibility=0.3,
                rescue_teams=2,
                ambulances=2,
                demand_units=6,
            ),
            Zone(
                zone_id="zone-5",
                name="South Residential",
                coordinates=[
                    [51.500, -0.090],
                    [51.505, -0.090],
                    [51.505, -0.080],
                    [51.500, -0.080],
                ],
                centroid=[51.5025, -0.085],
                flood_severity=0.2,
                affected_population=2_000,
                medical_urgency=0.1,
                road_accessibility=0.9,
                rescue_teams=5,
                ambulances=4,
                demand_units=4,
            ),
        ],
        shelters=[
            Shelter(
                shelter_id="shelter-1",
                name="Community Centre Alpha",
                coordinates=[51.512, -0.087],
                capacity=500,
                current_occupancy=420,
            ),
            Shelter(
                shelter_id="shelter-2",
                name="Riverside Community Hall",
                coordinates=[51.508, -0.092],
                capacity=200,
                current_occupancy=230,  # over capacity — triggers bottleneck
            ),
            Shelter(
                shelter_id="shelter-3",
                name="East Suburb Sports Centre",
                coordinates=[51.513, -0.075],
                capacity=300,
                current_occupancy=180,
            ),
        ],
        hospitals=[
            Hospital(
                hospital_id="hospital-1",
                name="North General Hospital",
                coordinates=[51.516, -0.082],
                capacity=200,
                surge_capacity=50,
                current_occupancy=230,  # over effective capacity (250) — triggers bottleneck
            ),
            Hospital(
                hospital_id="hospital-2",
                name="City Medical Centre",
                coordinates=[51.506, -0.086],
                capacity=150,
                surge_capacity=30,
                current_occupancy=120,
            ),
        ],
    )


def get_all_scenarios() -> list[Scenario]:
    """Built-in deterministic prototype scenarios for each supported hazard.

    Each non-flood scenario uses the shared geography but distinct hazard factors,
    specialist deployment, and severity so live demos show different behavior.
    Coefficients are prototype assumptions, not scientific guidance.
    """
    flood = get_default_scenario()
    profiles = {
        "fire": (
            "City Centre Fire",
            "High fire intensity and smoke exposure with limited fire-crew coverage in the worst-hit zone.",
            "critical",
            {"fire_intensity": 0.92, "smoke_exposure": 0.80, "spread_potential": 0.88},
            {"fire_crews": 1},
        ),
        "earthquake": (
            "Metro Earthquake",
            "Structural collapse risk and trapped-person pressure with scarce search-and-rescue capacity.",
            "critical",
            {"structural_damage": 0.90, "trapped_person_likelihood": 0.78, "aftershock_risk": 0.55},
            {"search_and_rescue_teams": 1},
        ),
        "cyclone": (
            "Coastal Cyclone",
            "Severe wind and storm-surge exposure with evacuation and utility restoration constraints.",
            "high",
            {"wind_severity": 0.88, "storm_surge_exposure": 0.82, "power_outage_severity": 0.75},
            {"evacuation_teams": 1, "utility_crews": 0},
        ),
        "industrial_accident": (
            "West Industrial Release",
            "Toxic release with containment failure and limited hazmat / containment capacity.",
            "critical",
            {"toxic_release_severity": 0.90, "exposure_level": 0.78, "containment_failure": 0.85},
            {"hazmat_teams": 1, "containment_units": 0},
        ),
    }
    scenarios = [flood]
    for hazard, (name, description, severity, factors, base_resources) in profiles.items():
        zones = []
        for index, zone in enumerate(flood.zones):
            zone_factors = {
                key: max(0.05, round(value - index * 0.12, 2))
                for key, value in factors.items()
            }
            # Zone 0 is critically under-resourced; later zones carry surplus for reallocation demos.
            if index == 0:
                zone_resources = {key: 0 for key in base_resources}
            elif index == 1:
                zone_resources = {key: max(1, count) for key, count in base_resources.items()}
            else:
                zone_resources = {key: max(2, count + 2) for key, count in base_resources.items()}
            zones.append(
                dataclasses.replace(
                    zone,
                    hazard_factors=zone_factors,
                    specialist_resources=zone_resources,
                    medical_urgency=min(1.0, zone.medical_urgency + (0.15 if index == 0 else 0.0)),
                    road_accessibility=max(0.1, zone.road_accessibility - (0.15 if index == 0 else 0.0)),
                )
            )
        shelters = flood.shelters
        if hazard == "cyclone":
            # Make shelter pressure visible for cyclone demos.
            shelters = [
                dataclasses.replace(s, current_occupancy=max(s.current_occupancy, s.capacity + 80))
                for s in flood.shelters
            ]
        scenarios.append(
            dataclasses.replace(
                flood,
                scenario_id=f"{hazard}-scenario-001",
                name=name,
                description=description,
                severity=severity,
                zones=zones,
                shelters=shelters,
                hazard_type=hazard,
            )
        )
    return scenarios


if __name__ == "__main__":
    import sys
    import json

    target = sys.argv[1] if len(sys.argv) > 1 else "print"

    if target == "print":
        scenario = get_default_scenario()
        print(f"Scenario: {scenario.scenario_id}")
        print(f"  Zones   : {len(scenario.zones)}")
        print(f"  Shelters: {len(scenario.shelters)}")
        print(f"  Hospitals: {len(scenario.hospitals)}")
        print(f"  population_max: {scenario.population_max}")
    elif target == "--target":
        dest = sys.argv[2] if len(sys.argv) > 2 else "print"
        if dest == "dynamodb":
            import persistence.dynamodb as dynamodb_store
            for scenario in get_all_scenarios():
                dynamodb_store.seed_scenario(scenario)
                print(f"Seeded scenario to DynamoDB: {scenario.scenario_id}")
        else:
            print(f"Unknown target: {dest}")
