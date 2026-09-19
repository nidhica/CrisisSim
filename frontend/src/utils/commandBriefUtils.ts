import type { Bottleneck, InterventionResult, Scenario, SimulationResult, ZoneResult } from '../types'

export function averageBaselineRisk(result: SimulationResult): number | null {
  const zones = result.baseline_zone_results
  if (!zones.length) return null
  return zones.reduce((sum, z) => sum + z.risk_score, 0) / zones.length
}

export function averageBaselineResponseTime(result: SimulationResult): number | null {
  const zones = result.baseline_zone_results
  if (!zones.length) return null
  return zones.reduce((sum, z) => sum + z.response_time_minutes, 0) / zones.length
}

export function highestRiskZone(
  result: SimulationResult,
  scenario: Scenario,
): { zoneId: string; zoneName: string; riskLevel: ZoneResult['risk_level']; riskScore: number } | null {
  const zones = result.baseline_zone_results
  if (!zones.length) return null
  const top = zones.reduce((best, current) =>
    current.risk_score > best.risk_score ? current : best,
  )
  const zone = scenario.zones.find(z => z.zone_id === top.zone_id)
  return {
    zoneId: top.zone_id,
    zoneName: zone?.name ?? top.zone_id,
    riskLevel: top.risk_level,
    riskScore: top.risk_score,
  }
}

export function primaryBottleneck(result: SimulationResult): Bottleneck | null {
  return result.bottlenecks[0] ?? null
}

export function findIntervention(
  result: SimulationResult,
  strategy: string,
): InterventionResult | undefined {
  return result.interventions.find(iv => iv.strategy === strategy)
}

export function findRecommendedIntervention(result: SimulationResult): InterventionResult | null {
  return findIntervention(result, result.recommended_strategy) ?? null
}

export function findBaselineIntervention(result: SimulationResult): InterventionResult | null {
  return findIntervention(result, 'baseline') ?? null
}

export function riskLevelHeadline(level: ZoneResult['risk_level'] | null): string {
  if (!level) return 'RISK PENDING'
  const label = level === 'medium' ? 'moderate' : level
  return `${label} risk`.toUpperCase()
}

export function buildWhyRecommendation(
  bottleneck: Bottleneck | null,
  recommended: InterventionResult | null,
): string | null {
  if (!recommended) return null
  if (bottleneck) {
    return `The deterministic simulation identifies "${bottleneck.description}" as the dominant bottleneck and ranks ${recommended.label} highest under the current prototype assumptions. This is decision-support output, not a real emergency directive.`
  }
  return `The deterministic simulation ranks ${recommended.label} highest by composite score under the current prototype assumptions. This is decision-support output, not a real emergency directive.`
}

export function percentChange(before: number, after: number): number | null {
  if (before === 0) return null
  return ((after - before) / before) * 100
}
