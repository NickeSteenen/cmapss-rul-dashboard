import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceDot,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { EngineRow } from '../types'

interface Props {
  rows: EngineRow[]
  sensor: string
  label: string
  selectedCycle?: number
  onSelectCycle?: (cycle: number) => void
}

export function SensorChart({ rows, sensor, label, selectedCycle, onSelectCycle }: Props) {
  const selectedRow = rows.find((row) => row.cycle === selectedCycle)

  return (
    <ResponsiveContainer width="100%" height={320}>
      <LineChart
        data={rows}
        margin={{ top: 5, right: 20, bottom: 20, left: 25 }}
        onClick={(state) => state.activeLabel !== undefined && onSelectCycle?.(Number(state.activeLabel))}
        style={{ cursor: onSelectCycle ? 'pointer' : undefined }}
      >
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="cycle" label={{ value: 'Cycle', position: 'insideBottom', offset: -15 }} />
        <YAxis domain={['auto', 'auto']} label={{ value: label, angle: -90, position: 'left', style: { textAnchor: 'middle' } }} />
        <Tooltip />
        <Line
          type="monotone"
          dataKey={(row: EngineRow) => row.sensors[sensor]}
          name={label}
          stroke="#e8590c"
          dot={true}
          isAnimationActive={false}
        />
        {selectedRow && <ReferenceLine x={selectedRow.cycle} stroke="#52606d" strokeDasharray="4 4" />}
        {selectedRow && (
          <ReferenceDot x={selectedRow.cycle} y={selectedRow.sensors[sensor]} r={6} fill="#e8590c" stroke="#ffffff" />
        )}
      </LineChart>
    </ResponsiveContainer>
  )
}
