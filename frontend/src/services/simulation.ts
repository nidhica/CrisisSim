import api from './api'
import type { ZoneParams, SimulationResult } from '../types'

export async function runSimulation(scenarioId: string, params: ZoneParams[]): Promise<SimulationResult> {
  const res = await api.post('/simulate', { scenario_id: scenarioId, params })
  return res.data
}

export async function getLatestResult(scenarioId: string): Promise<SimulationResult> {
  const res = await api.get(`/results/${scenarioId}/latest`)
  return res.data
}
