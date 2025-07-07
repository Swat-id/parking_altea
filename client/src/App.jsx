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
import UserManagement from './pages/UserManagement'
import AdminDashboard from './pages/AdminDashboard'
import ProtectedRoute from './components/ProtectedRoute'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/dashboard" element={
          <ProtectedRoute><Dashboard /></ProtectedRoute>
        } />
        <Route path="/parkings" element={
          <ProtectedRoute><Parkings /></ProtectedRoute>
        } />
        <Route path="/parking/:id" element={
          <ProtectedRoute><ParkingDetail /></ProtectedRoute>
        } />
        <Route path="/panels" element={
          <ProtectedRoute><Panels /></ProtectedRoute>
        } />
        <Route path="/schedules" element={
          <ProtectedRoute><Schedules /></ProtectedRoute>
        } />
        <Route path="/statistics" element={<Navigate to="/statistics/1" replace />} />
        <Route path="/statistics/:id" element={
          <ProtectedRoute><Statistics /></ProtectedRoute>
        } />
        <Route path="/camera-logs" element={
          <ProtectedRoute><CameraLogs /></ProtectedRoute>
        } />
        <Route path="/profile" element={
          <ProtectedRoute><Profile /></ProtectedRoute>
        } />
        <Route path="/admin" element={
          <ProtectedRoute requireSuperadmin><AdminDashboard /></ProtectedRoute>
        } />
        <Route path="/admin/users" element={
          <ProtectedRoute requireSuperadmin><UserManagement /></ProtectedRoute>
        } />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </Layout>
  )
}

// Importar LoginPage dinámicamente para evitar bucles
import LoginPage from './pages/Login'

export default App 