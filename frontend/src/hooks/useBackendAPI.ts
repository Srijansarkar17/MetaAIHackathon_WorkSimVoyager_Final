import { useCallback, useState } from 'react'
import type { Action, HealthResponse, ResetResponse, SchemaResponse, StateResponse, StepResponse } from '../types/api'
import { executeStep, getSchema, getState, healthCheck, resetEpisode } from '../api/client'

export function useBackendAPI() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const callHealth = useCallback(async (): Promise<HealthResponse | null> => {
    setLoading(true)
    setError(null)

    try {
      return await healthCheck()
    } catch (err) {
      setError('Unable to reach backend')
      return null
    } finally {
      setLoading(false)
    }
  }, [])

  const callReset = useCallback(async (taskId: string): Promise<ResetResponse | null> => {
    setLoading(true)
    setError(null)

    try {
      return await resetEpisode(taskId)
    } catch (err) {
      setError('Reset failed. Verify the backend URL and task id.')
      return null
    } finally {
      setLoading(false)
    }
  }, [])

  const callStep = useCallback(async (action: Action): Promise<StepResponse | null> => {
    setLoading(true)
    setError(null)

    try {
      return await executeStep(action)
    } catch (err) {
      setError('Step execution failed. Check action payload and backend availability.')
      return null
    } finally {
      setLoading(false)
    }
  }, [])

  const callState = useCallback(async (): Promise<StateResponse | null> => {
    setLoading(true)
    setError(null)

    try {
      return await getState()
    } catch (err) {
      setError('Unable to fetch state from backend.')
      return null
    } finally {
      setLoading(false)
    }
  }, [])

  const callSchema = useCallback(async (): Promise<SchemaResponse | null> => {
    setLoading(true)
    setError(null)

    try {
      return await getSchema()
    } catch (err) {
      setError('Unable to fetch schema from backend.')
      return null
    } finally {
      setLoading(false)
    }
  }, [])

  return {
    loading,
    error,
    callHealth,
    callReset,
    callStep,
    callState,
    callSchema,
  }
}
