import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Parkings from './pages/Parkings'
import ParkingDetail from './pages/ParkingDetail'
import Panels from './pages/Panels'
import Schedules from './pages/Schedules'
import Statistics from './pages/Statistics'
import CameraLogs from './pages/CameraLogs'
import Profile from './pages/Profile'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/login" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/parkings" element={<Parkings />} />
        <Route path="/parking/:id" element={<ParkingDetail />} />
        <Route path="/panels" element={<Panels />} />
        <Route path="/schedules" element={<Schedules />} />
        <Route path="/statistics" element={<Navigate to="/statistics/1" replace />} />
        <Route path="/statistics/:id" element={<Statistics />} />
        <Route path="/camera-logs" element={<CameraLogs />} />
        <Route path="/profile" element={<Profile />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </Layout>
  )
}

export default App 