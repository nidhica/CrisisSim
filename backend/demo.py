"""
Phase 1 demo — runs the full simulation engine on a representative scenario
and prints a concise summary. No AWS, no HTTP.
"""
from engine.models import ZoneParams, Zone, Shelter, Hospital, Scenario
from engine import run_full_simulation


def make_demo_scenario() -> Scenario:
    return Scenario(
        scenario_id="flood-scenario-001",
        name="River Delta Flood — Category 3",
        description="Severe flooding across 5 urban zones following dam overflow.",
        severity="high",
        created_at="2026-09-10T00:00:00Z",
        zones=[
            Zone(zone_id="zone-1", name="North Bank",
                 coordinates=[[51.505,-0.09],[51.51,-0.09],[51.51,-0.08],[51.505,-0.08]],
                 centroid=[51.5075,-0.085],
                 flood_severity=0.9, affected_population=12_000,
                 medical_urgency=0.8, road_accessibility=0.2,
                 rescue_teams=1, ambulances=1, demand_units=8),
            Zone(zone_id="zone-2", name="City Centre",
                 coordinates=[[51.500,-0.09],[51.505,-0.09],[51.505,-0.08],[51.500,-0.08]],
                 centroid=[51.5025,-0.085],
                 flood_severity=0.6, affected_population=8_000,
                 medical_urgency=0.5, road_accessibility=0.5,
                 rescue_teams=3, ambulances=2, demand_units=6),
            Zone(zone_id="zone-3", name="East Suburb",
                 coordinates=[[51.505,-0.08],[51.51,-0.08],[51.51,-0.07],[51.505,-0.07]],
                 centroid=[51.5075,-0.075],
                 flood_severity=0.3, affected_population=3_000,
                 medical_urgency=0.2, road_accessibility=0.8,
                 rescue_teams=4, ambulances=3, demand_units=4),
        ],
        shelters=[
            Shelter(shelter_id="shelter-1", name="Community Centre Alpha",
                    coordinates=[51.508,-0.087], capacity=500, current_occupancy=420),
            Shelter(shelter_id="shelter-2", name="Riverside Hall",
                    coordinates=[51.502,-0.086], capacity=200, current_occupancy=230),
        ],
        hospitals=[
            Hospital(hospital_id="hospital-1", name="North General",
                     coordinates=[51.512,-0.082], capacity=200, surge_capacity=50,
                     current_occupancy=230),
        ],
        population_max=15_000,
    )


def main():
    scenario = make_demo_scenario()
    params = [
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
        for z in scenario.zones
    ]

    result = run_full_simulation(scenario, params)

    print("=" * 60)
    print("CrisisSim Phase 1 — Demo Simulation Output")
    print("=" * 60)
    print(f"Scenario  : {scenario.name}")
    print(f"Result ID : {result.result_id}")
    print(f"Run At    : {result.run_at}")
    print()

    print("── Baseline Zone Results ──")
    for zr in result.baseline_zone_results:
        print(f"  {zr.zone_id:8s}  risk={zr.risk_score:6.2f} ({zr.risk_level:8s})  "
              f"response_time={zr.response_time_minutes:6.2f} min")

    print()
    print("── Primary Bottleneck ──")
    if result.bottlenecks:
        bn = result.bottlenecks[0]
        print(f"  [{bn.type}]  {bn.description}  (severity={bn.severity_score:.4f})")
    else:
        print("  No significant bottlenecks detected.")

    print()
    print("── Intervention Comparison ──")
    header = f"  {'Strategy':<25}  {'AvgRisk':>8}  {'RiskRed%':>9}  "
    header += f"{'AvgRT(min)':>10}  {'RTImp(min)':>10}  {'BnRes':>6}  {'Cost':>5}  {'Score':>7}"
    print(header)
    print("  " + "-" * (len(header) - 2))
    for iv in result.interventions:
        marker = " ★" if iv.strategy == result.recommended_strategy else "  "
        print(
            f"  {iv.label:<25}  {iv.avg_risk_score:8.2f}  {iv.risk_reduction_pct:8.2f}%  "
            f"{iv.avg_response_time_minutes:10.2f}  {iv.response_time_improvement_minutes:10.2f}  "
            f"{iv.bottleneck_resolution_score:6.4f}  {iv.resource_cost:5d}  "
            f"{iv.composite_score:7.4f}{marker}"
        )

    print()
    print(f"★ RECOMMENDED STRATEGY: {result.recommended_strategy.upper()}")
    print("=" * 60)


if __name__ == "__main__":
    main()
