import api from './api'
import type { ExplanationResult } from '../types'

export async function getExplanation(resultId: string): Promise<ExplanationResult> {
  const res = await api.post('/explain', { result_id: resultId })
  return res.data
}
