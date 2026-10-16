import { useEffect } from 'react'
import type { EngineCycleCount } from '../types'

interface Props {
  engines: EngineCycleCount[]
  unit: number
  onUnitChange: (unit: number) => void
  disabled?: boolean
}

export function EngineSelect({ engines, unit, onUnitChange, disabled = false }: Props) {
  // The chosen engine may not exist after switching dataset, since FD002 has 259 test engines and FD001 only 100
  useEffect(() => {
    if (engines.length > 0 && !engines.some((engine) => engine.unit === unit)) {
      onUnitChange(engines[0].unit)
    }
  }, [engines, unit, onUnitChange])

  return (
    <select value={unit} onChange={(e) => onUnitChange(Number(e.target.value))} disabled={disabled || engines.length === 0}>
      {engines.length === 0 && <option value={unit}>Loading engines...</option>}
      {engines.map((engine) => (
        <option key={engine.unit} value={engine.unit}>
          Engine {engine.unit} ({engine.cycles} cycles)
        </option>
      ))}
    </select>
  )
}
