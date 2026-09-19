import api from './api'
import type { Scenario, ScenarioSummary } from '../types'

export async function getScenarios(): Promise<ScenarioSummary[]> {
  const res = await api.get('/scenarios')
  return res.data.scenarios
}

export async function getScenario(id: string): Promise<Scenario> {
  const res = await api.get(`/scenarios/${id}`)
  return res.data
}
