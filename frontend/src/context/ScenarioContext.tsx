import { createContext, useContext, useState } from 'react'
import type { ReactNode } from 'react'
import type { Scenario } from '../types'
import { getScenario } from '../services/scenarios'

interface ScenarioContextType {
  scenario: Scenario | null
  loading: boolean
  error: string | null
  loadScenario: (id: string, demoScenario?: Scenario | null) => Promise<void>
}

const ScenarioContext = createContext<ScenarioContextType | null>(null)

export function ScenarioProvider({ children }: { children: ReactNode }) {
  const [scenario, setScenario] = useState<Scenario | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function loadScenario(id: string, demoScenario?: Scenario | null) {
    setLoading(true)
    setError(null)
    try {
      const s = await getScenario(id)
      setScenario(demoScenario ?? s)
    } catch (e: unknown) {
      const err = e as { message?: string }
      setError(err?.message || 'Failed to load scenario')
    } finally {
      setLoading(false)
    }
  }

  return (
    <ScenarioContext.Provider value={{ scenario, loading, error, loadScenario }}>
      {children}
    </ScenarioContext.Provider>
  )
}

export function useScenario() {
  const ctx = useContext(ScenarioContext)
  if (!ctx) throw new Error('useScenario must be used within ScenarioProvider')
  return ctx
}
