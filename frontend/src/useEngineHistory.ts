import { useEffect, useState } from 'react'
import { fetchHistory } from './api'
import type { EngineRow } from './types'

interface LoadedHistory {
  engine: string
  rows: EngineRow[]
  error: string | null
}

// Loads one engine's history whenever the chosen engine changes. Waits while isEngineValid is false, for example
// right after a dataset switch, when the chosen engine number may not exist yet in the new dataset.
export function useEngineHistory(dataset: string, unit: number, isEngineValid: boolean) {
  const engine = `${dataset} ${unit}`
  const [loaded, setLoaded] = useState<LoadedHistory>({ engine: '', rows: [], error: null })

  useEffect(() => {
    if (!isEngineValid) return
    let isCurrentEngine = true // an answer for an engine the user has already switched away from is ignored
    fetchHistory(dataset, unit)
      .then((rows) => isCurrentEngine && setLoaded({ engine: `${dataset} ${unit}`, rows, error: null }))
      .catch((e) => isCurrentEngine && setLoaded({ engine: `${dataset} ${unit}`, rows: [], error: String(e.message ?? e) }))
    return () => {
      isCurrentEngine = false
    }
  }, [dataset, unit, isEngineValid])

  const isLoaded = loaded.engine === engine
  return {
    rows: loaded.rows, // the previous engine's rows stay visible until the new ones have arrived
    error: isLoaded ? loaded.error : null,
    loading: !isLoaded,
  }
}
