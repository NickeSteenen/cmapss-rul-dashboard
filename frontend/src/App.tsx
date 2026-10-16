import { Navigate, NavLink, Route, Routes } from 'react-router'
import { HistoryPage } from './pages/HistoryPage'
import { LivePage } from './pages/LivePage'

// The whole app, with a menu at the top and below it whichever page the address in the browser points to.
function App() {
  return (
    <>
      <nav className="menu">
        <span className="app-name">CMAPSS RUL Dashboard</span>
        <NavLink to="/live">Live</NavLink>
        <NavLink to="/history">History</NavLink>
      </nav>

      <Routes>
        <Route path="/" element={<Navigate to="/history" replace />} />
        <Route path="/history" element={<HistoryPage />} />
        <Route path="/live" element={<LivePage />} />
      </Routes>
    </>
  )
}

export default App
