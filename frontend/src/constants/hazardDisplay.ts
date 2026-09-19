import type { HazardType, IncidentStatus } from '../types'

export interface CitizenHazardOption {
  type: HazardType
  emoji: string
  label: string
  subtitle: string
}

export const CITIZEN_HAZARD_OPTIONS: CitizenHazardOption[] = [
  { type: 'fire', emoji: '🔥', label: 'Fire', subtitle: 'Structural fire / smoke emergency' },
  { type: 'flood', emoji: '🌊', label: 'Flood', subtitle: 'Flooding / water emergency' },
  { type: 'earthquake', emoji: '🏚', label: 'Earthquake', subtitle: 'Seismic emergency' },
  { type: 'cyclone', emoji: '🌀', label: 'Cyclone', subtitle: 'Severe storm / cyclone' },
  {
    type: 'industrial_accident',
    emoji: '☣',
    label: 'Industrial',
    subtitle: 'Industrial / hazardous release',
  },
]

const AUTHORITY_HAZARD_LABELS: Record<HazardType, string> = {
  fire: 'Fire',
  flood: 'Flood',
  earthquake: 'Earthquake',
  cyclone: 'Cyclone / Severe Storm',
  industrial_accident: 'Industrial Accident',
}

export function hazardLabel(type: HazardType): string {
  return AUTHORITY_HAZARD_LABELS[type] ?? type.replaceAll('_', ' ')
}

export function hazardEmoji(type: HazardType): string {
  return CITIZEN_HAZARD_OPTIONS.find(option => option.type === type)?.emoji ?? '⚠️'
}

export function formatIncidentStatus(status: IncidentStatus): string {
  return status.replaceAll('_', ' ')
}
