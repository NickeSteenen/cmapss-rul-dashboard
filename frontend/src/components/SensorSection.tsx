import { SENSORS } from '../constants'
import type { EngineRow, SensorLabel } from '../types'
import { SensorChart } from './SensorChart'

interface Props {
  rows: EngineRow[]
  sensor: string
  onSensorChange: (sensor: string) => void
  labels: SensorLabel[] // empty until they've arrived
  selectedCycle?: number
  onSelectCycle?: (cycle: number) => void
}

// "sensor2 - T24: Total temperature at LPC outlet (degR)", or just "sensor2" if its label isn't known
function dropdownText(name: string, label?: SensorLabel) {
  if (!label) return name
  return `${name} - ${label.short}: ${label.description}${label.unit ? ` (${label.unit})` : ''}`
}

// "T24 (degR)", or just "sensor2" if its label isn't known
function lineName(name: string, label?: SensorLabel) {
  if (!label) return name
  return `${label.short}${label.unit ? ` (${label.unit})` : ''}`
}

export function SensorSection({ rows, sensor, onSensorChange, labels, selectedCycle, onSelectCycle }: Props) {
  const labelOf = (name: string) => labels.find((label) => label.name === name)

  return (
    <>
      <h2>
        Sensor{' '}
        <select value={sensor} onChange={(e) => onSensorChange(e.target.value)}>
          {SENSORS.map((name) => (
            <option key={name} value={name}>
              {dropdownText(name, labelOf(name))}
            </option>
          ))}
        </select>
      </h2>
      <SensorChart
        rows={rows}
        sensor={sensor}
        label={lineName(sensor, labelOf(sensor))}
        selectedCycle={selectedCycle}
        onSelectCycle={onSelectCycle}
      />
    </>
  )
}
