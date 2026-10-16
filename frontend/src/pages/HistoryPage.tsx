import { useState } from 'react'
import { CycleStatCards } from '../components/CycleStatCards'
import { EngineSelect } from '../components/EngineSelect'
import { RulChart } from '../components/RulChart'
import { SensorSection } from '../components/SensorSection'
import { DATASETS } from '../constants'
import { useCycleSelection } from '../useCycleSelection'
import { useEngineHistory } from '../useEngineHistory'
import { useEngines } from '../useEngines'
import { useSensorLabels } from '../useSensorLabels'

export function HistoryPage() {
  const [dataset, setDataset] = useState('FD001')
  const [unit, setUnit] = useState(1)
  const [sensor, setSensor] = useState('sensor2')
  const sensorLabels = useSensorLabels()
  const engines = useEngines(dataset)
  const isEngineValid = engines.some((engine) => engine.unit === unit)
  const { rows, error, loading } = useEngineHistory(dataset, unit, isEngineValid)
  const { shownRow, isLastCycle, navigation, chartSelection } = useCycleSelection(rows, true)

  return (
    <main>
      <h1>Engine history</h1>

      <div className="controls">
        <label>
          Dataset
          <select value={dataset} onChange={(e) => setDataset(e.target.value)}>
            {DATASETS.map((name) => (
              <option key={name}>{name}</option>
            ))}
          </select>
        </label>
        <label>
          Engine
          <EngineSelect engines={engines} unit={unit} onUnitChange={setUnit} />
        </label>
        {loading && <span className="loading">Loading...</span>}
      </div>

      {error && <p className="error">{error}</p>}

      {shownRow && (
        <>
          <p className="hint">
            {isLastCycle ? "At the engine's last cycle." : `At cycle ${shownRow.cycle}.`} Use the arrows or click a chart to
            see another cycle.
          </p>
          <CycleStatCards row={shownRow} cyclesInEngine={rows.length} navigation={navigation} />

          <h2>
            {rows[0].dataset} engine {rows[0].unit}: remaining useful life
          </h2>
          <RulChart rows={rows} {...chartSelection} />

          <SensorSection rows={rows} sensor={sensor} onSensorChange={setSensor} labels={sensorLabels} {...chartSelection} />
        </>
      )}
    </main>
  )
}
