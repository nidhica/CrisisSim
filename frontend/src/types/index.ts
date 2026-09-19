export interface GeoLocation {
  displayName: string
  latitude: number
  longitude: number
}

export interface ZoneParams {
  zone_id: string
  flood_severity: number
  affected_population: number
  medical_urgency: number
  road_accessibility: number
  rescue_teams: number
  ambulances: number
  demand_units: number
  hazard_factors?: Record<string, number>
  specialist_resources?: Record<string, number>
}

export interface Zone extends ZoneParams {
  name: string
  coordinates: [number, number][]
  centroid: [number, number]
}

export interface Shelter {
  shelter_id: string
  name: string
  coordinates: [number, number]
  capacity: number
  current_occupancy: number
}

export interface Hospital {
  hospital_id: string
  name: string
  coordinates: [number, number]
  capacity: number
  surge_capacity: number
  current_occupancy: number
}

export interface Scenario {
  scenario_id: string
  name: string
  description: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  created_at: string
  zones: Zone[]
  shelters: Shelter[]
  hospitals: Hospital[]
  population_max: number
  hazard_type: HazardType
  location_name?: string
  latitude?: number
  longitude?: number
  source_incident_id?: string
}

export interface ScenarioSummary {
  scenario_id: string
  name: string
  description: string
  severity: string
  hazard_type?: HazardType
}

export interface RiskComponents {
  affected_population_score: number
  flood_severity_score: number
  medical_urgency_score: number
  road_accessibility_score: number
  resource_shortage_score: number
  hazard_intensity_score?: number
  hazard_specific_scores?: Record<string, number>
}

export interface ZoneResult {
  zone_id: string
  risk_score: number
  risk_level: 'low' | 'medium' | 'high' | 'critical'
  response_time_minutes: number
  risk_components: RiskComponents
}

export interface Bottleneck {
  type: string
  zone_id: string | null
  facility_id: string | null
  description: string
  severity_score: number
}

export interface InterventionResult {
  strategy: 'baseline' | 'resource_reallocation' | 'capacity_expansion' | 'combined'
  label: string
  zone_results: ZoneResult[]
  avg_risk_score: number
  avg_response_time_minutes: number
  risk_reduction_pct: number
  response_time_improvement_minutes: number
  bottleneck_resolution_score: number
  resource_cost: number
  composite_score: number
}

export interface SimulationResult {
  result_id: string
  scenario_id: string
  run_at: string
  params_used: ZoneParams[]
  baseline_zone_results: ZoneResult[]
  bottlenecks: Bottleneck[]
  interventions: InterventionResult[]
  recommended_strategy: string
  hazard_type?: HazardType
}

export interface ExplanationResult {
  explanation: string
  strategy_explained: string
  generated_at: string
  fallback: boolean
}
export type HazardType = 'flood' | 'fire' | 'earthquake' | 'cyclone' | 'industrial_accident'

export type IncidentSeverity = 'low' | 'moderate' | 'high' | 'critical'

export type IncidentStatus =
  | 'reported'
  | 'acknowledged'
  | 'assessing'
  | 'response_dispatched'
  | 'resolved'

export interface Incident {
  incident_id: string
  hazard_type: HazardType
  location_name: string
  latitude: number
  longitude: number
  severity: IncidentSeverity
  description: string
  status: IncidentStatus
  created_at: string
  evidence_url?: string
}

export interface CreateIncidentInput {
  hazard_type: HazardType
  location_name: string
  latitude: number
  longitude: number
  severity: IncidentSeverity
  description: string
  evidence_url?: string
}
