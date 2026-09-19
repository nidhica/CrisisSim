import type { HazardType, Hospital, Shelter, Zone } from '../types'

/** ~1 km offset at mid-latitudes — deterministic, not random. */
const CENTROID_OFFSET = 0.009
/** Half-size of each simulated zone polygon in degrees. */
const POLYGON_HALF = 0.0025

const ZONE_LAYOUT: Array<{ zoneId: string; label: string; dLat: number; dLng: number }> = [
  { zoneId: 'zone-1', label: 'NW', dLat: CENTROID_OFFSET, dLng: -CENTROID_OFFSET },
  { zoneId: 'zone-2', label: 'N', dLat: CENTROID_OFFSET, dLng: 0 },
  { zoneId: 'zone-3', label: 'NE', dLat: CENTROID_OFFSET, dLng: CENTROID_OFFSET },
  { zoneId: 'zone-4', label: 'SW', dLat: -CENTROID_OFFSET, dLng: -CENTROID_OFFSET },
  { zoneId: 'zone-5', label: 'SE', dLat: -CENTROID_OFFSET, dLng: CENTROID_OFFSET },
]

const SHELTER_OFFSETS: Array<[number, number]> = [
  [0.004, -0.005],
  [-0.003, 0.006],
  [0.006, 0.003],
]

const HOSPITAL_OFFSETS: Array<[number, number]> = [
  [-0.005, -0.004],
  [0.003, 0.005],
]

function squarePolygon(lat: number, lng: number): [number, number][] {
  return [
    [lat - POLYGON_HALF, lng - POLYGON_HALF],
    [lat - POLYGON_HALF, lng + POLYGON_HALF],
    [lat + POLYGON_HALF, lng + POLYGON_HALF],
    [lat + POLYGON_HALF, lng - POLYGON_HALF],
  ]
}

/**
 * Generate five deterministic simulated zones around a geocoded point.
 * Zone IDs remain zone-1 … zone-5 for backend simulation compatibility.
 * These are simulated areas, not real administrative boundaries.
 */
export function generateLocationScenarioGeometry(
  latitude: number,
  longitude: number,
  _hazardType: HazardType,
  templateZones: Zone[],
): Zone[] {
  const templateById = new Map(templateZones.map(zone => [zone.zone_id, zone]))

  return ZONE_LAYOUT.map((layout, index) => {
    const template = templateById.get(layout.zoneId) ?? templateZones[index]
    const centroidLat = latitude + layout.dLat
    const centroidLng = longitude + layout.dLng

    return {
      ...template,
      zone_id: layout.zoneId,
      name: `Simulated Zone ${index + 1} (${layout.label})`,
      coordinates: squarePolygon(centroidLat, centroidLng),
      centroid: [centroidLat, centroidLng],
    }
  })
}

/**
 * Reposition simulated shelters/hospitals near the selected location.
 * Preserves IDs, capacity, and occupancy from the source template.
 */
export function repositionSimulatedFacilities(
  latitude: number,
  longitude: number,
  shelters: Shelter[],
  hospitals: Hospital[],
): { shelters: Shelter[]; hospitals: Hospital[] } {
  return {
    shelters: shelters.map((shelter, index) => {
      const [dLat, dLng] = SHELTER_OFFSETS[index % SHELTER_OFFSETS.length]
      return {
        ...shelter,
        name: shelter.name.startsWith('Simulated')
          ? shelter.name
          : `Simulated ${shelter.name}`,
        coordinates: [latitude + dLat, longitude + dLng],
      }
    }),
    hospitals: hospitals.map((hospital, index) => {
      const [dLat, dLng] = HOSPITAL_OFFSETS[index % HOSPITAL_OFFSETS.length]
      return {
        ...hospital,
        name: hospital.name.startsWith('Simulated')
          ? hospital.name
          : `Simulated ${hospital.name}`,
        coordinates: [latitude + dLat, longitude + dLng],
      }
    }),
  }
}

/** Short label for auto-generated scenario names (city or first segment). */
export function locationShortName(displayName: string): string {
  const first = displayName.split(',')[0]?.trim()
  return first || displayName
}

export function locationScenarioDescription(displayName: string, hazardLabel: string): string {
  return (
    `Location-aware simulated ${hazardLabel} emergency near ${displayName}. ` +
    'Simulated zones are generated around the selected location. Not real-time disaster data.'
  )
}

/** London demo centroid used by seeded scenarios — for regression checks. */
export const LONDON_REFERENCE = { latitude: 51.505, longitude: -0.09 }

export function isNearLondon(latitude: number, longitude: number, tolerance = 0.05): boolean {
  return (
    Math.abs(latitude - LONDON_REFERENCE.latitude) < tolerance &&
    Math.abs(longitude - LONDON_REFERENCE.longitude) < tolerance
  )
}
