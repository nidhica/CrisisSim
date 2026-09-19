import { useState } from 'react'
import type { HazardType, Zone, ZoneParams } from '../../types'
import { useSimulation } from '../../context/SimulationContext'

const FACTORS: Record<HazardType, [string, string][]> = {
  flood: [['flood_severity', 'Flood Severity']],
  fire: [
    ['fire_intensity', 'Fire Intensity'],
    ['smoke_exposure', 'Smoke Exposure'],
    ['spread_potential', 'Spread Potential'],
  ],
  earthquake: [
    ['structural_damage', 'Structural Damage'],
    ['trapped_person_likelihood', 'Trapped-person Likelihood'],
    ['aftershock_risk', 'Aftershock Risk'],
  ],
  cyclone: [
    ['wind_severity', 'Wind Severity'],
    ['storm_surge_exposure', 'Storm Surge Exposure'],
    ['power_outage_severity', 'Power Outage'],
  ],
  industrial_accident: [
    ['toxic_release_severity', 'Toxic Release'],
    ['exposure_level', 'Exposure Level'],
    ['containment_failure', 'Containment Failure'],
  ],
}

const SPECIALISTS: Record<HazardType, [string, string][]> = {
  flood: [],
  fire: [['fire_crews', 'Fire Crews']],
  earthquake: [['search_and_rescue_teams', 'Search & Rescue']],
  cyclone: [
    ['evacuation_teams', 'Evacuation Teams'],
    ['utility_crews', 'Utility Crews'],
  ],
  industrial_accident: [
    ['hazmat_teams', 'Hazmat Teams'],
    ['containment_units', 'Containment Units'],
  ],
}

interface Props {
  zone: Zone
  params: ZoneParams
  hazardType: HazardType
}

export function ZoneParameterRow({ zone, params, hazardType }: Props) {
  const { updateDraftParam, updateHazardFactor, updateSpecialistResource } = useSimulation()
  const [expanded, setExpanded] = useState(false)
  const activeHazard = hazardType || 'flood'

  return (
    <div className="ops-zone-param-row">
      <button
        type="button"
        onClick={() => setExpanded(value => !value)}
        className="ops-zone-param-toggle"
      >
        <span>{zone.name}</span>
        <span className="muted" aria-hidden>{expanded ? '▲' : '▼'}</span>
      </button>
      {expanded && (
        <div style={{ marginTop: 10 }}>
          {activeHazard === 'flood' ? (
            <Slider
              label="Flood Severity"
              value={params.flood_severity}
              onChange={value => updateDraftParam(zone.zone_id, 'flood_severity', value)}
            />
          ) : (
            FACTORS[activeHazard].map(([key, label]) => (
              <Slider
                key={key}
                label={label}
                value={params.hazard_factors?.[key] ?? 0}
                onChange={value => updateHazardFactor(zone.zone_id, key, value)}
              />
            ))
          )}
          <Slider
            label="Road Accessibility"
            value={params.road_accessibility}
            onChange={value => updateDraftParam(zone.zone_id, 'road_accessibility', value)}
          />
          <Slider
            label="Medical Urgency"
            value={params.medical_urgency}
            onChange={value => updateDraftParam(zone.zone_id, 'medical_urgency', value)}
          />
          {SPECIALISTS[activeHazard].map(([key, label]) => (
            <NumberRow
              key={key}
              label={label}
              value={params.specialist_resources?.[key] ?? 0}
              onChange={value => updateSpecialistResource(zone.zone_id, key, value)}
            />
          ))}
        </div>
      )}
    </div>
  )
}

function Slider({
  label,
  value,
  onChange,
}: {
  label: string
  value: number
  onChange: (value: number) => void
}) {
  return (
    <div className="ops-slider-row">
      <label>{label}</label>
      <input
        type="range"
        min="0"
        max="1"
        step=".01"
        value={value}
        onChange={event => onChange(globalThis.Number(event.target.value))}
      />
      <span className="ops-slider-value">{(value * 100).toFixed(0)}%</span>
    </div>
  )
}

function NumberRow({
  label,
  value,
  onChange,
}: {
  label: string
  value: number
  onChange: (value: number) => void
}) {
  return (
    <div className="ops-slider-row">
      <label>{label}</label>
      <input
        className="ops-number-input"
        type="number"
        min="0"
        value={value}
        onChange={event => onChange(Math.max(0, globalThis.Number(event.target.value) || 0))}
      />
    </div>
  )
}
