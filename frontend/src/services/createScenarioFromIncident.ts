import type { Incident, Scenario, ScenarioSummary } from '../types'
import { hazardLabel } from '../constants/hazardDisplay'
import {
  DEFAULT_HAZARD_FACTORS,
  HAZARD_SCENARIO_META,
  defaultSpecialistResources,
  hazardFactorMap,
  incidentResponseProfile,
  mapIncidentSeverityToScenario,
} from '../constants/hazardScenarioDefaults'
import { locationShortName } from './generateLocationScenarioGeometry'
import { createDemoScenario, type DemoScenario } from './demoScenarios'
import { getScenario } from './scenarios'

export class ScenarioFromIncidentError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'ScenarioFromIncidentError'
  }
}

export function incidentSimulationName(incident: Incident): string {
  const place = locationShortName(incident.location_name)
  return `${place} ${hazardLabel(incident.hazard_type)} Emergency — ${incident.incident_id}`
}

export function buildEmergencyConfigurationFromIncident(incident: Incident) {
  if (
    !incident.location_name ||
    incident.latitude == null ||
    incident.longitude == null ||
    Number.isNaN(incident.latitude) ||
    Number.isNaN(incident.longitude)
  ) {
    throw new ScenarioFromIncidentError('Incident location is missing or invalid.')
  }

  const hazardType = incident.hazard_type
  const factors = DEFAULT_HAZARD_FACTORS[hazardType]
  const profile = incidentResponseProfile(incident.severity)

  return {
    name: incidentSimulationName(incident),
    severity: mapIncidentSeverityToScenario(incident.severity),
    affectedZones: profile.affectedZones,
    populationAffected: profile.populationAffected,
    floodSeverity: factors[0],
    medicalUrgency: profile.medicalUrgency,
    roadAccessibility: profile.roadAccessibility,
    rescueTeams: 4,
    ambulances: 2,
    hazardType,
    hazardFactors: hazardFactorMap(hazardType),
    specialistResources: defaultSpecialistResources(hazardType),
    location: {
      displayName: incident.location_name,
      latitude: incident.latitude,
      longitude: incident.longitude,
    },
    hazardLabel: HAZARD_SCENARIO_META[hazardType].label,
    sourceIncidentId: incident.incident_id,
    incidentDescription: incident.description,
  }
}

export function createScenarioFromIncident(
  incident: Incident,
  sourceScenario: Scenario,
): DemoScenario {
  const config = buildEmergencyConfigurationFromIncident(incident)
  return createDemoScenario(sourceScenario, config)
}

export function findHazardScenarioSummary(
  summaries: ScenarioSummary[],
  hazardType: Incident['hazard_type'],
): ScenarioSummary | undefined {
  return summaries.find(summary => summary.hazard_type === hazardType)
}

export async function createDemoScenarioFromIncident(
  incident: Incident,
  summaries: ScenarioSummary[],
): Promise<DemoScenario> {
  const summary = findHazardScenarioSummary(summaries, incident.hazard_type)
  if (!summary) {
    throw new ScenarioFromIncidentError(
      'Unable to create a simulation template for this hazard.',
    )
  }
  const source = await getScenario(summary.scenario_id)
  return createScenarioFromIncident(incident, source)
}
