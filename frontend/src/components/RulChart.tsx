import {
  CartesianGrid,
  Legend,
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
  selectedCycle?: number
  onSelectCycle?: (cycle: number) => void
}

// Predicted and true RUL for every cycle of one engine.
export function RulChart({ rows, selectedCycle, onSelectCycle }: Props) {
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
        <YAxis label={{ value: 'RUL (cycles)', angle: -90, position: 'left', style: { textAnchor: 'middle' } }} />
        <Tooltip />
        <Legend verticalAlign="top" />
        <Line type="monotone" dataKey="true_rul" name="True RUL" stroke="#2b8a3e" dot={true} isAnimationActive={false} />
        <Line type="monotone" dataKey="predicted_rul" name="Predicted RUL" stroke="#1971c2" dot={true} isAnimationActive={false} />
        {selectedRow && <ReferenceLine x={selectedRow.cycle} stroke="#52606d" strokeDasharray="4 4" />}
        {selectedRow?.true_rul != null && (
          <ReferenceDot x={selectedRow.cycle} y={selectedRow.true_rul} r={6} fill="#2b8a3e" stroke="#ffffff" />
        )}
        {selectedRow && (
          <ReferenceDot x={selectedRow.cycle} y={selectedRow.predicted_rul} r={6} fill="#1971c2" stroke="#ffffff" />
        )}
      </LineChart>
    </ResponsiveContainer>
  )
}
