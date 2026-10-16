// Must match make_json_row_for_browser in backend/server.py
export interface EngineRow {
  dataset: string
  unit: number
  cycle: number
  predicted_rul: number
  true_rul: number | null // null iff the backend has no true RUL for the row
  settings: Record<string, number>
  sensors: Record<string, number>
}

// From the DBC file, e.g. { name: "sensor2", short: "T24", description: "Total temperature at LPC outlet", unit: "degR" }
export interface SensorLabel {
  name: string
  short: string
  description: string
  unit: string // "" for sensors without a unit, like the pressure ratio epr
}

// One entry of the answer to /api/engines
export interface EngineCycleCount {
  unit: number
  cycles: number
}

// Answer to /api/start, /api/stop and /api/status
export interface StreamStatus {
  streaming: boolean
  dataset?: string // dataset and unit are only there while streaming
  unit?: number
  error?: string // only after the C++ sender stopped with an error
}
