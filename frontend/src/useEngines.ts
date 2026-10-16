import { useEffect, useState } from 'react'
import { fetchEngines } from './api'
import type { EngineCycleCount } from './types'

// Empty until the list for this dataset has arrived, or if the backend can't be reached.
export function useEngines(dataset: string): EngineCycleCount[] {
  const [loaded, setLoaded] = useState({ dataset: '', engines: [] as EngineCycleCount[] })
  useEffect(() => {
    let isCurrentDataset = true // an answer for a dataset the user has already switched away from is ignored
    fetchEngines(dataset)
      .then((engines) => isCurrentDataset && setLoaded({ dataset, engines }))
      .catch(() => {})
    return () => {
      isCurrentDataset = false
    }
  }, [dataset])
  return loaded.dataset === dataset ? loaded.engines : []
}
