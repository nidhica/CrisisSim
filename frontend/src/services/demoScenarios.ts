import type { GeoLocation, HazardType, Scenario } from '../types'
import {
  generateLocationScenarioGeometry,
  locationScenarioDescription,
  repositionSimulatedFacilities,
} from './generateLocationScenarioGeometry'

export interface EmergencyConfiguration {
  name: string
  severity: Scenario['severity']
  affectedZones: number
  populationAffected: number
  floodSeverity: number
  medicalUrgency: number
  roadAccessibility: number
  rescueTeams: number
  ambulances: number
  hazardType: HazardType
  hazardFactors: Record<string, number>
  specialistResources: Record<string, number>
  location?: GeoLocation
  hazardLabel?: string
  sourceIncidentId?: string
  incidentDescription?: string
}

export interface DemoScenario { id: string; sourceScenarioId: string; scenario: Scenario }
const storageKey = 'crisissim-demo-scenarios'

function read(): DemoScenario[] {
  try { return JSON.parse(sessionStorage.getItem(storageKey) || '[]') as DemoScenario[] } catch { return [] }
}

export function getDemoScenario(id: string): DemoScenario | null { return read().find(item => item.id === id) ?? null }
export function getRecentDemoScenarios(): DemoScenario[] { return read() }

function applyZoneParams(
  zone: Scenario['zones'][number],
  config: EmergencyConfiguration,
): Scenario['zones'][number] {
  return {
    ...zone,
    affected_population: config.populationAffected,
    flood_severity: config.hazardType === 'flood' ? config.floodSeverity : zone.flood_severity,
    medical_urgency: config.medicalUrgency,
    road_accessibility: config.roadAccessibility,
    rescue_teams: config.rescueTeams,
    ambulances: config.ambulances,
    hazard_factors: config.hazardFactors,
    specialist_resources: config.specialistResources,
  }
}

export function createDemoScenario(source: Scenario, config: EmergencyConfiguration): DemoScenario {
  const id = `demo-${Date.now()}`
  const selected = Math.max(1, Math.min(config.affectedZones, source.zones.length))
  const hazardLabel = config.hazardLabel ?? config.hazardType.replaceAll('_', ' ')

  let baseZones = source.zones
  let baseShelters = source.shelters
  let baseHospitals = source.hospitals
  let locationFields: Pick<Scenario, 'location_name' | 'latitude' | 'longitude'> = {}
  let description = `Simulation configuration based on ${source.name}. This is a frontend demo scenario, not a live emergency dispatch record.`

  if (config.location) {
    baseZones = generateLocationScenarioGeometry(
      config.location.latitude,
      config.location.longitude,
      config.hazardType,
      source.zones,
    )
    const facilities = repositionSimulatedFacilities(
      config.location.latitude,
      config.location.longitude,
      source.shelters,
      source.hospitals,
    )
    baseShelters = facilities.shelters
    baseHospitals = facilities.hospitals
    locationFields = {
      location_name: config.location.displayName,
      latitude: config.location.latitude,
      longitude: config.location.longitude,
    }
    description = locationScenarioDescription(config.location.displayName, hazardLabel)
  }

  if (config.sourceIncidentId) {
    const context = `Simulation created from citizen incident ${config.sourceIncidentId}.`
    const citizenNote = config.incidentDescription
      ? ` Citizen report (context only): ${config.incidentDescription}`
      : ''
    description = `${description} ${context}${citizenNote}`
  }

  const scenario: Scenario = {
    ...source,
    name: config.name,
    severity: config.severity,
    hazard_type: config.hazardType,
    description,
    created_at: new Date().toISOString(),
    zones: baseZones.map((zone, index) =>
      index < selected ? applyZoneParams(zone, config) : zone,
    ),
    shelters: baseShelters,
    hospitals: baseHospitals,
    ...locationFields,
    ...(config.sourceIncidentId ? { source_incident_id: config.sourceIncidentId } : {}),
  }

  const item = { id, sourceScenarioId: source.scenario_id, scenario }
  sessionStorage.setItem(storageKey, JSON.stringify([item, ...read()].slice(0, 5)))
  return item
}
