import { useEffect, useState } from 'react'
import { fetchSensorLabels } from './api'
import type { SensorLabel } from './types'

// Empty until the labels have arrived, or if the backend can't be reached. The pages then show plain "sensorN" names.
export function useSensorLabels(): SensorLabel[] {
  const [labels, setLabels] = useState<SensorLabel[]>([])
  useEffect(() => {
    fetchSensorLabels()
      .then(setLabels)
      .catch(() => {})
  }, [])
  return labels
}
