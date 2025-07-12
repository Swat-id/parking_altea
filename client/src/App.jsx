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
import LoginPage from './pages/Login'
import ProtectedRoute from './components/ProtectedRoute'

function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/" element={
        <Layout>
          <Navigate to="/dashboard" replace />
        </Layout>
      } />
      <Route path="/dashboard" element={
        <Layout>
          <ProtectedRoute><Dashboard /></ProtectedRoute>
        </Layout>
      } />
      <Route path="/parkings" element={
        <Layout>
          <ProtectedRoute><Parkings /></ProtectedRoute>
        </Layout>
      } />
      <Route path="/parking/:id" element={
        <Layout>
          <ProtectedRoute><ParkingDetail /></ProtectedRoute>
        </Layout>
      } />
      <Route path="/panels" element={
        <Layout>
          <ProtectedRoute><Panels /></ProtectedRoute>
        </Layout>
      } />
      <Route path="/schedules" element={
        <Layout>
          <ProtectedRoute><Schedules /></ProtectedRoute>
        </Layout>
      } />
      <Route path="/statistics" element={
        <Layout>
          <Navigate to="/statistics/1" replace />
        </Layout>
      } />
      <Route path="/statistics/:id" element={
        <Layout>
          <ProtectedRoute><Statistics /></ProtectedRoute>
        </Layout>
      } />
      <Route path="/camera-logs" element={
        <Layout>
          <ProtectedRoute><CameraLogs /></ProtectedRoute>
        </Layout>
      } />
      <Route path="/profile" element={
        <Layout>
          <ProtectedRoute><Profile /></ProtectedRoute>
        </Layout>
      } />
      <Route path="/admin" element={
        <Layout>
          <ProtectedRoute requiredRole="superadmin"><AdminDashboard /></ProtectedRoute>
        </Layout>
      } />
      <Route path="/admin/users" element={
        <Layout>
          <ProtectedRoute requiredRole="superadmin"><UserManagement /></ProtectedRoute>
        </Layout>
      } />
      <Route path="*" element={
        <Layout>
          <Navigate to="/dashboard" replace />
        </Layout>
      } />
    </Routes>
  )
}

export default App 