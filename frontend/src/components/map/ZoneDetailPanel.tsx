import type { HazardType, Zone, ZoneResult } from '../../types'
import { SeverityBadge } from '../common/SeverityBadge'

interface Props {
  zone: Zone
  result: ZoneResult
  hazardType?: HazardType
  onClose: () => void
}

const FACTOR_LABELS: Record<string, string> = {
  flood_severity: 'Flood Severity',
  fire_intensity: 'Fire Intensity',
  smoke_exposure: 'Smoke Exposure',
  spread_potential: 'Spread Potential',
  structural_damage: 'Structural Damage',
  trapped_person_likelihood: 'Trapped-person Likelihood',
  aftershock_risk: 'Aftershock Risk',
  wind_severity: 'Wind Severity',
  storm_surge_exposure: 'Storm Surge Exposure',
  power_outage_severity: 'Power Outage',
  toxic_release_severity: 'Toxic Release',
  exposure_level: 'Exposure Level',
  containment_failure: 'Containment Failure',
}

export function ZoneDetailPanel({ zone, result, hazardType = 'flood', onClose }: Props) {
  const rows: [string, string | number][] = [
    ['Risk Score', `${result.risk_score.toFixed(1)} / 100`],
    ['Response Time', `${result.response_time_minutes.toFixed(1)} min`],
  ]

  if (hazardType === 'flood') {
    rows.push(['Flood Severity', `${(zone.flood_severity * 100).toFixed(0)}%`])
  } else {
    const factors = zone.hazard_factors || {}
    for (const [key, value] of Object.entries(factors)) {
      rows.push([FACTOR_LABELS[key] || key.replaceAll('_', ' '), `${(value * 100).toFixed(0)}%`])
    }
  }

  rows.push(
    ['Affected Population', zone.affected_population.toLocaleString()],
    ['Medical Urgency', `${(zone.medical_urgency * 100).toFixed(0)}%`],
    ['Road Accessibility', `${(zone.road_accessibility * 100).toFixed(0)}%`],
  )

  if (hazardType === 'flood') {
    rows.push(['Rescue Teams', zone.rescue_teams], ['Ambulances', zone.ambulances])
  } else {
    const specialists = zone.specialist_resources || {}
    for (const [key, value] of Object.entries(specialists)) {
      rows.push([key.replaceAll('_', ' '), value])
    }
  }

  return (
    <div className="absolute top-4 right-4 z-[1000] bg-white rounded-xl shadow-xl border border-gray-200 p-4 w-64">
      <div className="flex justify-between items-start mb-3">
        <div>
          <h3 className="font-semibold text-gray-800 text-sm">{zone.name}</h3>
          <SeverityBadge level={result.risk_level} size="sm" />
        </div>
        <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-lg leading-none">
          ×
        </button>
      </div>
      <div className="space-y-1 text-xs">
        {rows.map(([label, value]) => (
          <div key={label} className="flex justify-between py-0.5 border-b border-gray-50">
            <span className="text-gray-500 capitalize">{label}</span>
            <span className="font-medium text-gray-700">{value}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
