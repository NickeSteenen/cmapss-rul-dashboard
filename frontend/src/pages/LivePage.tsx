import { useEffect, useState } from 'react'
import { fetchStatus, startStream, stopStream } from '../api'
import { CycleStatCards } from '../components/CycleStatCards'
import { EngineSelect } from '../components/EngineSelect'
import { RulChart } from '../components/RulChart'
import { SensorSection } from '../components/SensorSection'
import { DATASETS } from '../constants'
import type { EngineRow, StreamStatus } from '../types'
import { useCycleSelection } from '../useCycleSelection'
import { useEngines } from '../useEngines'
import { useSensorLabels } from '../useSensorLabels'

export function LivePage() {
  const [dataset, setDataset] = useState('FD001')
  const [unit, setUnit] = useState(1)
  const [delay, setDelay] = useState(0.5)
  const [status, setStatus] = useState<StreamStatus>({ streaming: false })
  const [busy, setBusy] = useState(false) // waiting for the backend to answer Start or Stop
  const [error, setError] = useState<string | null>(null)
  const [rows, setRows] = useState<EngineRow[]>([])
  const [connected, setConnected] = useState(false)
  const [sensor, setSensor] = useState('sensor2')
  const sensorLabels = useSensorLabels()
  const engines = useEngines(dataset)
  // While streaming, the cards follow the newest cycle. Once the stream has ended, any received cycle can be picked.
  const { shownRow, isLastCycle, clearSelection, navigation, chartSelection } = useCycleSelection(rows, !status.streaming)

  useEffect(() => {
    const socket = new WebSocket(`ws://${window.location.host}/api/live`)
    socket.onopen = () => setConnected(true)
    socket.onclose = () => setConnected(false)
    socket.onmessage = (event) => {
      const row: EngineRow = JSON.parse(event.data)
      setRows((previous) => {
        const last = previous[previous.length - 1]
        const isNextCycleOfSameEngine =
          last && last.dataset === row.dataset && last.unit === row.unit && row.cycle > last.cycle
        return isNextCycleOfSameEngine ? [...previous, row] : [row]
      })
    }
    return () => {
      socket.onclose = null // in development StrictMode reconnects at once, and this old socket mustn't mark the new one as closed
      socket.close()
    }
  }, [])

  // Only the backend knows when a stream starts in another tab, ends by itself, or fails, so ask it every second
  useEffect(() => {
    function refreshStatus() {
      fetchStatus()
        .then(setStatus)
        .catch(() => setStatus({ streaming: false }))
    }
    refreshStatus()
    const timer = setInterval(refreshStatus, 1000)
    return () => clearInterval(timer)
  }, [])

  async function start() {
    setBusy(true)
    setError(null)
    try {
      setStatus(await startStream(dataset, unit, delay))
      setRows([]) // only after the backend has said yes, so a refused Start keeps the old charts
      clearSelection()
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setBusy(false)
    }
  }

  async function stop() {
    setBusy(true)
    setError(null)
    try {
      setStatus(await stopStream())
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setBusy(false)
    }
  }

  const latest = rows[rows.length - 1]
  const cyclesInStream =
    latest && latest.dataset === dataset ? engines.find((engine) => engine.unit === latest.unit)?.cycles : undefined

  function streamMessage() {
    if (status.streaming) return `Streaming ${status.dataset} engine ${status.unit}`
    if (!latest || status.error) return null
    if (latest.cycle === cyclesInStream) {
      return `Finished: all ${cyclesInStream} cycles of ${latest.dataset} engine ${latest.unit} replayed`
    }
    return `Stopped after cycle ${latest.cycle}${cyclesInStream ? ` of ${cyclesInStream}` : ''}`
  }

  const message = streamMessage()

  return (
    <main>
      <h1>Live streaming</h1>
      <p className={connected ? 'status connected' : 'status'}>
        {connected ? 'Connected to the backend' : 'Not connected. Start the backend, then reload this page.'}
      </p>

      <div className="controls">
        <label>
          Dataset
          <select value={dataset} onChange={(e) => setDataset(e.target.value)} disabled={status.streaming}>
            {DATASETS.map((name) => (
              <option key={name}>{name}</option>
            ))}
          </select>
        </label>
        <label>
          Engine
          <EngineSelect engines={engines} unit={unit} onUnitChange={setUnit} disabled={status.streaming} />
        </label>
        <label>
          Seconds between cycles
          <input
            type="number"
            min={0}
            step={0.1}
            value={delay}
            onChange={(e) => setDelay(Number(e.target.value))}
            disabled={status.streaming}
          />
        </label>
        <button onClick={start} disabled={busy || status.streaming}>
          Start
        </button>
        <button onClick={stop} disabled={busy || !status.streaming}>
          Stop
        </button>
      </div>

      {message && <p>{message}</p>}
      {status.error && <p className="error">The C++ sender stopped with an error: {status.error}</p>}
      {error && <p className="error">{error}</p>}

      {shownRow ? (
        <>
          {!status.streaming && (
            <p className="hint">
              {isLastCycle ? 'At the last cycle streamed.' : `At cycle ${shownRow.cycle}.`} Use the arrows or click a chart
              to see another cycle.
            </p>
          )}
          <CycleStatCards row={shownRow} cyclesInEngine={cyclesInStream} navigation={navigation} />

          <h2>Remaining useful life</h2>
          <RulChart rows={rows} {...chartSelection} />

          <SensorSection rows={rows} sensor={sensor} onSensorChange={setSensor} labels={sensorLabels} {...chartSelection} />
        </>
      ) : (
        <p>{status.streaming ? 'Waiting for the first cycle...' : 'Choose an engine and press Start.'}</p>
      )}
    </main>
  )
}
