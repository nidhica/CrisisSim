import type { ReactNode } from 'react'
import { createContext, useContext, useState } from 'react'
import type { ZoneParams, SimulationResult, ExplanationResult, Scenario } from '../types'
import { runSimulation } from '../services/simulation'
import { getExplanation } from '../services/explanation'

interface SimulationContextType {
  draftParams: ZoneParams[]
  simulationResult: SimulationResult | null
  isRunning: boolean
  error: string | null
  explanation: ExplanationResult | null
  explanationLoading: boolean
  initDraftParams: (scenario: Scenario) => void
  updateDraftParam: (zoneId: string, field: keyof ZoneParams, value: number) => void
  updateHazardFactor: (zoneId: string, factor: string, value: number) => void
  updateSpecialistResource: (zoneId: string, resource: string, value: number) => void
  runSim: () => Promise<void>
  resetParams: (scenario: Scenario) => void
  fetchExplanation: () => Promise<void>
}

const SimulationContext = createContext<SimulationContextType | null>(null)

function scenarioToParams(scenario: Scenario): ZoneParams[] {
  return scenario.zones.map(z => ({
    zone_id: z.zone_id,
    flood_severity: z.flood_severity,
    affected_population: z.affected_population,
    medical_urgency: z.medical_urgency,
    road_accessibility: z.road_accessibility,
    rescue_teams: z.rescue_teams,
    ambulances: z.ambulances,
    demand_units: z.demand_units,
    hazard_factors: z.hazard_factors,
    specialist_resources: z.specialist_resources,
  }))
}

export function SimulationProvider({ children, scenarioId }: { children: ReactNode; scenarioId: string }) {
  const [draftParams, setDraftParams] = useState<ZoneParams[]>([])
  const [simulationResult, setSimulationResult] = useState<SimulationResult | null>(null)
  const [isRunning, setIsRunning] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [explanation, setExplanation] = useState<ExplanationResult | null>(null)
  const [explanationLoading, setExplanationLoading] = useState(false)

  function initDraftParams(scenario: Scenario) {
    setDraftParams(scenarioToParams(scenario))
  }

  function updateDraftParam(zoneId: string, field: keyof ZoneParams, value: number) {
    setDraftParams(prev =>
      prev.map(p => p.zone_id === zoneId ? { ...p, [field]: value } : p)
    )
  }
  function updateHazardFactor(zoneId: string, factor: string, value: number) {
    setDraftParams(prev => prev.map(param => param.zone_id === zoneId ? { ...param, hazard_factors: { ...param.hazard_factors, [factor]: value } } : param))
  }

  function updateSpecialistResource(zoneId: string, resource: string, value: number) {
    setDraftParams(prev =>
      prev.map(param =>
        param.zone_id === zoneId
          ? {
              ...param,
              specialist_resources: {
                ...param.specialist_resources,
                [resource]: Math.max(0, Math.round(value)),
              },
            }
          : param,
      ),
    )
  }

  async function runSim() {
    if (draftParams.length === 0) return
    setIsRunning(true)
    setError(null)
    setExplanation(null)
    try {
      const result = await runSimulation(scenarioId, draftParams)
      setSimulationResult(result)
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } }; message?: string }
      setError(err?.response?.data?.detail || err?.message || 'Simulation failed')
    } finally {
      setIsRunning(false)
    }
  }

  function resetParams(scenario: Scenario) {
    setDraftParams(scenarioToParams(scenario))
    setExplanation(null)
  }

  async function fetchExplanation() {
    if (!simulationResult) return
    setExplanationLoading(true)
    setError(null)
    try {
      const exp = await getExplanation(simulationResult.result_id)
      setExplanation(exp)
    } catch (e: unknown) {
      const err = e as { message?: string }
      setError(err?.message || 'Failed to get explanation')
    } finally {
      setExplanationLoading(false)
    }
  }

  return (
    <SimulationContext.Provider value={{
      draftParams, simulationResult, isRunning, error,
      explanation, explanationLoading,
      initDraftParams, updateDraftParam, updateHazardFactor, updateSpecialistResource, runSim, resetParams, fetchExplanation,
    }}>
      {children}
    </SimulationContext.Provider>
  )
}

export function useSimulation() {
  const ctx = useContext(SimulationContext)
  if (!ctx) throw new Error('useSimulation must be used within SimulationProvider')
  return ctx
}
