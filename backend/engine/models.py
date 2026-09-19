"""
CrisisSim data models — pure Python dataclasses.
No AWS, HTTP, or external dependencies.
"""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class ZoneParams:
    """Adjustable per-zone parameters used as simulation input."""
    zone_id: str
    flood_severity: float        # 0.0–1.0
    affected_population: int     # absolute count
    medical_urgency: float       # 0.0–1.0
    road_accessibility: float    # 0.0–1.0 (1 = fully accessible)
    rescue_teams: int            # count deployed
    ambulances: int              # count deployed
    demand_units: int            # total demand units for this zone
    # Additive fields: legacy flood callers may omit both maps.
    hazard_factors: dict[str, float] = field(default_factory=dict)
    specialist_resources: dict[str, int] = field(default_factory=dict)


@dataclass
class Zone:
    """Full zone definition including geographic data and default parameters."""
    zone_id: str
    name: str
    coordinates: list[list[float]]   # polygon [[lat, lng], ...]
    centroid: list[float]            # [lat, lng]
    flood_severity: float
    affected_population: int
    medical_urgency: float
    road_accessibility: float
    rescue_teams: int
    ambulances: int
    demand_units: int
    hazard_factors: dict[str, float] = field(default_factory=dict)
    specialist_resources: dict[str, int] = field(default_factory=dict)


@dataclass
class Shelter:
    """Emergency shelter with capacity tracking."""
    shelter_id: str
    name: str
    coordinates: list[float]   # [lat, lng]
    capacity: int
    current_occupancy: int


@dataclass
class Hospital:
    """Hospital with base and surge capacity tracking."""
    hospital_id: str
    name: str
    coordinates: list[float]   # [lat, lng]
    capacity: int
    surge_capacity: int
    current_occupancy: int


@dataclass
class Scenario:
    """
    A pre-loaded emergency scenario (flood by default for legacy compatibility).
    population_max is the reference maximum used for population normalization
    across all zones in this scenario.
    hazard_type selects the deterministic multi-hazard scoring path.
    """
    scenario_id: str
    name: str
    description: str
    severity: str           # "low" | "medium" | "high" | "critical"
    created_at: str         # ISO 8601
    zones: list[Zone]
    shelters: list[Shelter]
    hospitals: list[Hospital]
    population_max: int     # normalization ceiling for affected_population
    hazard_type: str = "flood"


@dataclass
class SimulationState:
    """
    Complete state passed through the simulation engine.
    Interventions produce modified SimulationState instances —
    resource reallocation modifies zones, capacity expansion modifies
    shelters/hospitals, combined modifies all three.
    """
    zones: list[ZoneParams]
    shelters: list[Shelter]
    hospitals: list[Hospital]
    hazard_type: str = "flood"


@dataclass
class RiskComponents:
    """Weighted contribution breakdown for a zone's risk score."""
    affected_population_score: float
    flood_severity_score: float
    medical_urgency_score: float
    road_accessibility_score: float
    resource_shortage_score: float
    hazard_intensity_score: float = 0.0
    hazard_specific_scores: dict[str, float] = field(default_factory=dict)


@dataclass
class ZoneResult:
    """Computed results for a single zone after running the simulation."""
    zone_id: str
    risk_score: float                   # 0–100, rounded to 2dp
    risk_level: str                     # "low" | "medium" | "high" | "critical"
    response_time_minutes: float        # clamped to [5, 120]
    risk_components: RiskComponents


@dataclass
class Bottleneck:
    """A detected constraint in the emergency response."""
    type: str           # "resource_shortage" | "shelter_capacity" | "hospital_capacity" | "road_access"
    zone_id: str | None # None for facility-level bottlenecks
    facility_id: str | None  # shelter_id or hospital_id, None for zone-level
    description: str
    severity_score: float   # 0.0–1.0


@dataclass
class InterventionResult:
    """Evaluated result for a single intervention strategy."""
    strategy: str       # "baseline" | "resource_reallocation" | "capacity_expansion" | "combined"
    label: str
    zone_results: list[ZoneResult]
    avg_risk_score: float
    avg_response_time_minutes: float
    risk_reduction_pct: float
    response_time_improvement_minutes: float
    bottleneck_resolution_score: float
    resource_cost: int
    composite_score: float


@dataclass
class SimulationResult:
    """Complete output of a simulation run, ready for persistence and API response."""
    result_id: str
    scenario_id: str
    run_at: str                              # ISO 8601
    params_used: list[ZoneParams]
    baseline_zone_results: list[ZoneResult]
    bottlenecks: list[Bottleneck]
    interventions: list[InterventionResult]
    recommended_strategy: str
    hazard_type: str = "flood"
