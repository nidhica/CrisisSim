import type { HazardType, IncidentSeverity, Scenario } from '../types'

export const HAZARD_SCENARIO_META: Record<
  HazardType,
  { label: string; factors: string[]; resources: string[] }
> = {
  flood: { label: 'Flood', factors: ['Flood severity'], resources: [] },
  fire: {
    label: 'Fire',
    factors: ['Fire intensity', 'Smoke exposure', 'Spread potential'],
    resources: ['fire_crews'],
  },
  earthquake: {
    label: 'Earthquake',
    factors: ['Structural damage', 'Trapped-person likelihood', 'Aftershock risk'],
    resources: ['search_and_rescue_teams'],
  },
  cyclone: {
    label: 'Cyclone / Severe Storm',
    factors: ['Wind severity', 'Storm surge exposure', 'Power outage severity'],
    resources: ['evacuation_teams', 'utility_crews'],
  },
  industrial_accident: {
    label: 'Industrial Accident',
    factors: ['Toxic release severity', 'Exposure level', 'Containment failure'],
    resources: ['hazmat_teams', 'containment_units'],
  },
}

export const HAZARD_FACTOR_KEYS: Record<HazardType, string[]> = {
  flood: ['flood_severity'],
  fire: ['fire_intensity', 'smoke_exposure', 'spread_potential'],
  earthquake: ['structural_damage', 'trapped_person_likelihood', 'aftershock_risk'],
  cyclone: ['wind_severity', 'storm_surge_exposure', 'power_outage_severity'],
  industrial_accident: ['toxic_release_severity', 'exposure_level', 'containment_failure'],
}

export const DEFAULT_HAZARD_FACTORS: Record<HazardType, number[]> = {
  flood: [0.75],
  fire: [0.8, 0.65, 0.7],
  earthquake: [0.8, 0.65, 0.45],
  cyclone: [0.8, 0.65, 0.7],
  industrial_accident: [0.8, 0.65, 0.7],
}

export function defaultSpecialistResources(hazardType: HazardType): Record<string, number> {
  return Object.fromEntries(
    HAZARD_SCENARIO_META[hazardType].resources.map(key => [key, 2]),
  )
}

export function mapIncidentSeverityToScenario(severity: IncidentSeverity): Scenario['severity'] {
  if (severity === 'moderate') return 'medium'
  return severity
}

export function hazardFactorMap(hazardType: HazardType): Record<string, number> {
  const keys = HAZARD_FACTOR_KEYS[hazardType]
  const values = DEFAULT_HAZARD_FACTORS[hazardType]
  return Object.fromEntries(keys.map((key, index) => [key, values[index] ?? 0]))
}

/** Prototype tuning from incident severity — uses existing default magnitudes only. */
export function incidentResponseProfile(severity: IncidentSeverity): {
  affectedZones: number
  populationAffected: number
  medicalUrgency: number
  roadAccessibility: number
} {
  switch (severity) {
    case 'low':
      return { affectedZones: 1, populationAffected: 800, medicalUrgency: 0.45, roadAccessibility: 0.6 }
    case 'moderate':
      return { affectedZones: 2, populationAffected: 1000, medicalUrgency: 0.55, roadAccessibility: 0.5 }
    case 'high':
      return { affectedZones: 2, populationAffected: 1200, medicalUrgency: 0.6, roadAccessibility: 0.45 }
    case 'critical':
      return { affectedZones: 3, populationAffected: 1800, medicalUrgency: 0.75, roadAccessibility: 0.35 }
  }
}
