import type { ZoneResult } from '../types'

export type ZoneRiskLevel = ZoneResult['risk_level']

export interface ZoneRiskMapVisual {
  /** Polygon fill (Leaflet fillColor) */
  fillColor: string
  /** Polygon stroke (Leaflet color) */
  strokeColor: string
  fillOpacity: number
  strokeOpacity: number
  strokeWeight: number
  legendLabel: string
  badgeLabel: string
}

/**
 * Single source of truth: simulation risk_level → map colors.
 * critical = highest tier (legend: HIGH), high = ELEVATED, medium, low.
 */
export const ZONE_RISK_MAP_VISUAL: Record<ZoneRiskLevel, ZoneRiskMapVisual> = {
  critical: {
    fillColor: '#ef4444',
    strokeColor: '#ef4444',
    fillOpacity: 0.45,
    strokeOpacity: 0.9,
    strokeWeight: 2.5,
    legendLabel: 'HIGH RISK',
    badgeLabel: 'HIGH RISK',
  },
  high: {
    fillColor: '#f97316',
    strokeColor: '#f97316',
    fillOpacity: 0.4,
    strokeOpacity: 0.9,
    strokeWeight: 2.5,
    legendLabel: 'ELEVATED RISK',
    badgeLabel: 'ELEVATED RISK',
  },
  medium: {
    fillColor: '#facc15',
    strokeColor: '#facc15',
    fillOpacity: 0.35,
    strokeOpacity: 0.9,
    strokeWeight: 2.5,
    legendLabel: 'MEDIUM RISK',
    badgeLabel: 'MEDIUM RISK',
  },
  low: {
    fillColor: '#22c55e',
    strokeColor: '#22c55e',
    fillOpacity: 0.3,
    strokeOpacity: 0.9,
    strokeWeight: 2,
    legendLabel: 'LOWER RISK',
    badgeLabel: 'LOW RISK',
  },
}

/** Legend order: highest severity first */
export const ZONE_RISK_LEGEND_LEVELS: ZoneRiskLevel[] = ['critical', 'high', 'medium', 'low']

export function getZoneRiskMapVisual(level: ZoneRiskLevel | undefined | null): ZoneRiskMapVisual {
  if (!level) {
    return ZONE_RISK_MAP_VISUAL.low
  }
  return ZONE_RISK_MAP_VISUAL[level]
}

const SIMULATED_ZONE_NAME = /^Simulated Zone (\d+) \(([^)]+)\)$/i

export function formatZoneMapTitle(zoneName: string): string {
  const match = SIMULATED_ZONE_NAME.exec(zoneName.trim())
  if (match) {
    return `ZONE ${match[1]} · ${match[2].toUpperCase()}`
  }
  const short = zoneName.replace(/^Simulated\s+/i, '').trim()
  return short.toUpperCase()
}

export function formatZoneMapTooltipLines(
  zoneName: string,
  level: ZoneRiskLevel | undefined | null,
  riskScore: number | null,
): { title: string; riskLine: string; visual: ZoneRiskMapVisual } {
  const visual = getZoneRiskMapVisual(level)
  const title = formatZoneMapTitle(zoneName)
  const riskLine =
    riskScore != null
      ? `● ${visual.badgeLabel} (${riskScore.toFixed(1)})`
      : `● ${visual.badgeLabel}`
  return { title, riskLine, visual }
}
