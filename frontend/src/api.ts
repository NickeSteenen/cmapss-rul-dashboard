import type { EngineCycleCount, EngineRow, SensorLabel, StreamStatus } from './types'

// Returns the backend's answer, or throws an error with the backend's own explanation if the request failed.
async function readAnswer<T>(response: Response): Promise<T> {
  let body
  try {
    body = await response.json()
  } catch {
    throw new Error('No answer from the backend. Is it running?')
  }
  if (!response.ok) {
    const detail = body.detail
    if (typeof detail === 'string') throw new Error(detail) // our own HTTPExceptions
    if (Array.isArray(detail) && detail[0]?.msg) throw new Error(detail[0].msg) // FastAPI's validation errors
    throw new Error('The backend could not answer this request')
  }
  return body
}

export async function fetchHistory(dataset: string, unit: number): Promise<EngineRow[]> {
  const query = new URLSearchParams({ dataset, unit: String(unit) })
  return readAnswer(await fetch(`/api/history?${query}`))
}

export async function fetchEngines(dataset: string): Promise<EngineCycleCount[]> {
  return readAnswer(await fetch(`/api/engines?${new URLSearchParams({ dataset })}`))
}

export async function startStream(dataset: string, unit: number, delay: number): Promise<StreamStatus> {
  return readAnswer(
    await fetch('/api/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ dataset, unit, delay }),
    }),
  )
}

export async function stopStream(): Promise<StreamStatus> {
  return readAnswer(await fetch('/api/stop', { method: 'POST' }))
}

export async function fetchSensorLabels(): Promise<SensorLabel[]> {
  return readAnswer(await fetch('/api/sensors'))
}

export async function fetchStatus(): Promise<StreamStatus> {
  return readAnswer(await fetch('/api/status'))
}
