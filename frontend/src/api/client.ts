import axios from 'axios'
import type { Action, HealthResponse, ResetResponse, SchemaResponse, StateResponse, StepResponse } from '../types/api'
import { API_PATHS, BACKEND_URL } from './endpoints'

const client = axios.create({
  baseURL: BACKEND_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

export async function healthCheck() {
  const response = await client.get<HealthResponse>(API_PATHS.health)
  return response.data
}

export async function resetEpisode(taskId: string) {
  const response = await client.post<ResetResponse>(API_PATHS.reset, { task_id: taskId })
  return response.data
}

export async function executeStep(action: Action) {
  const response = await client.post<StepResponse>(API_PATHS.step, { action })
  return response.data
}

export async function getState() {
  const response = await client.get<StateResponse>(API_PATHS.state)
  return response.data
}

export async function getSchema() {
  const response = await client.get<SchemaResponse>(API_PATHS.schema)
  return response.data
}
