import axios from 'axios'
import api from './api'
import type { CreateIncidentInput, Incident, IncidentStatus } from '../types'

export async function createIncident(input: CreateIncidentInput): Promise<Incident> {
  const res = await api.post<Incident>('/incidents', input)
  return res.data
}

export async function getIncidents(): Promise<Incident[]> {
  const res = await api.get<{ incidents: Incident[] }>('/incidents')
  return res.data.incidents
}

export async function getIncident(incidentId: string): Promise<Incident | null> {
  try {
    const res = await api.get<Incident>(`/incidents/${incidentId}`)
    return res.data
  } catch (error) {
    if (axios.isAxiosError(error) && error.response?.status === 404) {
      return null
    }
    throw error
  }
}

export async function updateIncident(
  incidentId: string,
  status: IncidentStatus,
): Promise<Incident> {
  const res = await api.patch<Incident>(`/incidents/${incidentId}`, { status })
  return res.data
}
