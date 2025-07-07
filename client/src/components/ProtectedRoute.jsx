import React from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

/**
 * Componente para proteger rutas privadas.
 * @param {ReactNode} children - Componente hijo a renderizar si está autenticado
 * @param {string} requiredRole - Rol requerido (opcional)
 * @param {function} canAccess - Función de acceso personalizada (opcional)
 */
const ProtectedRoute = ({ children, requiredRole, canAccess }) => {
  const { isAuthenticated, user, loading } = useAuth()

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Cargando...</p>
        </div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  if (requiredRole && user?.role !== requiredRole) {
    return <Navigate to="/" replace />
  }

  if (canAccess && !canAccess(user)) {
    return <Navigate to="/" replace />
  }

  return children
}

export default ProtectedRoute 