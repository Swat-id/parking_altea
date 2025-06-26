import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './context/AuthContext'
import Layout from './components/Layout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Parkings from './pages/Parkings'
import ParkingDetail from './pages/ParkingDetail'
import Panels from './pages/Panels'
import Statistics from './pages/Statistics'
import Profile from './pages/Profile'

function App() {
  const { isAuthenticated, loading } = useAuth()

  // Mostrar loading mientras se verifica la autenticación
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Cargando...</p>
        </div>
      </div>
    )
  }

  // Siempre mostrar las rutas protegidas (sin login)
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/login" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/parkings" element={<Parkings />} />
        <Route path="/parking/:id" element={<ParkingDetail />} />
        <Route path="/panels" element={<Panels />} />
        <Route path="/statistics" element={<Statistics />} />
        <Route path="/profile" element={<Profile />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </Layout>
  )
}

export default App 