import { describe, expect, it } from 'vitest'
import {
  formatZoneMapTitle,
  formatZoneMapTooltipLines,
  getZoneRiskMapVisual,
  ZONE_RISK_MAP_VISUAL,
} from '../zoneRiskMapVisual'

describe('zoneRiskMapVisual', () => {
  it('maps LOW → green', () => {
    const v = getZoneRiskMapVisual('low')
    expect(v.fillColor).toBe('#22c55e')
    expect(v.strokeColor).toBe('#22c55e')
    expect(v.fillOpacity).toBe(0.3)
  })

  it('maps MEDIUM → yellow', () => {
    const v = getZoneRiskMapVisual('medium')
    expect(v.fillColor).toBe('#facc15')
    expect(v.strokeColor).toBe('#facc15')
    expect(v.fillOpacity).toBe(0.35)
  })

  it('maps HIGH (engine high) → orange elevated', () => {
    const v = getZoneRiskMapVisual('high')
    expect(v.fillColor).toBe('#f97316')
    expect(v.strokeColor).toBe('#f97316')
    expect(v.fillOpacity).toBe(0.4)
    expect(v.badgeLabel).toBe('ELEVATED RISK')
  })

  it('maps CRITICAL (engine critical) → red high tier', () => {
    const v = getZoneRiskMapVisual('critical')
    expect(v.fillColor).toBe('#ef4444')
    expect(v.strokeColor).toBe('#ef4444')
    expect(v.fillOpacity).toBe(0.45)
    expect(v.badgeLabel).toBe('HIGH RISK')
  })

  it('uses consistent stroke opacity and weight across levels', () => {
    for (const level of ['low', 'medium', 'high', 'critical'] as const) {
      const v = ZONE_RISK_MAP_VISUAL[level]
      expect(v.strokeOpacity).toBe(0.9)
      expect(v.strokeWeight).toBeGreaterThanOrEqual(2)
    }
  })

  it('formats simulated zone names for tooltips', () => {
    expect(formatZoneMapTitle('Simulated Zone 1 (NW)')).toBe('ZONE 1 · NW')
  })

  it('builds tooltip lines with semantic risk label', () => {
    const { title, riskLine, visual } = formatZoneMapTooltipLines(
      'Simulated Zone 2 (SE)',
      'critical',
      88.2,
    )
    expect(title).toBe('ZONE 2 · SE')
    expect(riskLine).toContain('HIGH RISK')
    expect(riskLine).toContain('88.2')
    expect(visual.fillColor).toBe('#ef4444')
  })
})
