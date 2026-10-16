import { useState } from 'react'
import type { EngineRow } from './types'

// Which of an engine's cycles the cards show and the charts mark. Without a pick, or while canPick is false,
// that is the newest cycle. A cycle picked for another engine doesn't count, so a new engine starts at its last cycle.
export function useCycleSelection(rows: EngineRow[], canPick: boolean) {
  const [selection, setSelection] = useState({ engine: '', cycle: 0 })
  const engine = rows.length > 0 ? `${rows[0].dataset} ${rows[0].unit}` : ''

  const pickedIndex = canPick && selection.engine === engine ? rows.findIndex((row) => row.cycle === selection.cycle) : -1
  const shownIndex = pickedIndex >= 0 ? pickedIndex : rows.length - 1

  function selectCycle(cycle: number) {
    setSelection({ engine, cycle })
  }

  return {
    shownRow: rows[shownIndex] as EngineRow | undefined,
    isLastCycle: shownIndex === rows.length - 1,
    clearSelection: () => setSelection({ engine: '', cycle: 0 }),
    // For the cards' arrows. A missing handler disables that arrow at the first or last cycle.
    navigation: canPick
      ? {
          onPrevious: shownIndex > 0 ? () => selectCycle(rows[shownIndex - 1].cycle) : undefined,
          onNext: shownIndex < rows.length - 1 ? () => selectCycle(rows[shownIndex + 1].cycle) : undefined,
        }
      : undefined,
    // For the charts, which cycle to mark and what a click does
    chartSelection: {
      selectedCycle: canPick ? rows[shownIndex]?.cycle : undefined,
      onSelectCycle: canPick ? selectCycle : undefined,
    },
  }
}
