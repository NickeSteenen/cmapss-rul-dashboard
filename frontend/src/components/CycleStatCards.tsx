import type { EngineRow } from '../types'
import { StatCard } from './StatCard'

interface Props {
  row: EngineRow
  cyclesInEngine?: number
  navigation?: { onPrevious?: () => void; onNext?: () => void } // shows arrows on the Cycle card, and a missing handler disables its arrow
}

function difference(row: EngineRow) {
  if (row.true_rul === null) return '-'
  const value = Math.round(row.predicted_rul - row.true_rul)
  return value > 0 ? `+${value}` : String(value)
}

export function CycleStatCards({ row, cyclesInEngine, navigation }: Props) {
  const cycleText = cyclesInEngine ? `${row.cycle} of ${cyclesInEngine}` : String(row.cycle)

  return (
    <div className="stat-cards">
      <StatCard label="Predicted RUL (cycles)" value={row.predicted_rul.toFixed(0)} color="#1971c2" />
      <StatCard label="True RUL (cycles)" value={row.true_rul === null ? '-' : String(row.true_rul)} color="#2b8a3e" />
      <StatCard label="Predicted − true" value={difference(row)} />
      {navigation ? (
        <div className="stat-card">
          <div className="stat-label">Cycle</div>
          <div className="cycle-navigation">
            <button onClick={navigation.onPrevious} disabled={!navigation.onPrevious} aria-label="Previous cycle">
              ‹
            </button>
            <span className="stat-value">{cycleText}</span>
            <button onClick={navigation.onNext} disabled={!navigation.onNext} aria-label="Next cycle">
              ›
            </button>
          </div>
        </div>
      ) : (
        <StatCard label="Cycle" value={cycleText} />
      )}
    </div>
  )
}
