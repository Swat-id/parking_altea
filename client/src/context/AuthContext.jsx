import React, { createContext, useContext, useState, useEffect } from 'react'
import { authService } from '../services/authService'

const AuthContext = createContext()

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [userResources, setUserResources] = useState({
    parkings: [],
    panels: [],
    accesses: []
  })

  // Verificar token al cargar la aplicación
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        const token = localStorage.getItem('token')
        if (token) {
          // Verificar si el token es válido
          const userData = JSON.parse(localStorage.getItem('user'))
          if (userData) {
            setUser(userData)
            
            // Cargar recursos del usuario
            try {
              const permissions = await authService.getPermissions()
              if (permissions.success) {
                setUserResources(permissions.permissions)
              }
            } catch (error) {
              console.warn('Error loading user permissions:', error)
            }
          } else {
            // Token inválido, limpiar
            localStorage.removeItem('token')
            localStorage.removeItem('user')
          }
        }
      } catch (error) {
        console.error('Error initializing auth:', error)
        localStorage.removeItem('token')
        localStorage.removeItem('user')
      } finally {
        setLoading(false)
      }
    }

    initializeAuth()
  }, [])

  // Función de login
  const login = async (email, password) => {
    try {
      setLoading(true)
      const response = await authService.login(email, password)
      
      if (response.token && response.user) {
        // Guardar token y datos del usuario
        localStorage.setItem('token', response.token)
        localStorage.setItem('user', JSON.stringify(response.user))
        
        setUser(response.user)
        
        // Cargar recursos del usuario
        try {
          const permissions = await authService.getPermissions()
          if (permissions.success) {
            setUserResources(permissions.permissions)
          }
        } catch (error) {
          console.warn('Error loading user permissions:', error)
        }
        
        return { success: true }
      } else {
        throw new Error('Respuesta de login inválida')
      }
    } catch (error) {
      console.error('Login error:', error)
      return { 
        success: false, 
        error: error.response?.data?.error || 'Error de autenticación' 
      }
    } finally {
      setLoading(false)
    }
  }

  // Función de logout
  const logout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    setUser(null)
    setUserResources({
      parkings: [],
      panels: [],
      accesses: []
    })
  }

  // Verificar si el usuario está autenticado
  const isAuthenticated = !!user

  // Verificar si el usuario es superadmin
  const isSuperadmin = user?.role === 'superadmin'

  // Verificar acceso a un parking específico
  const hasParkingAccess = (parkingId) => {
    if (isSuperadmin) return true
    return userResources.parking_ids?.includes(parkingId) || false
  }

  // Verificar acceso a un panel específico
  const hasPanelAccess = (panelId) => {
    if (isSuperadmin) return true
    return userResources.panel_ids?.includes(panelId) || false
  }

  // Verificar acceso a una cámara específica
  const hasAccessControl = (accessId) => {
    if (isSuperadmin) return true
    return userResources.access_ids?.includes(accessId) || false
  }

  // Actualizar recursos del usuario
  const refreshUserResources = async () => {
    try {
      const permissions = await authService.getPermissions()
      if (permissions.success) {
        setUserResources(permissions.permissions)
      }
    } catch (error) {
      console.error('Error refreshing user resources:', error)
    }
  }

  const value = {
    user,
    login,
    logout,
    isAuthenticated,
    isSuperadmin,
    loading,
    userResources,
    hasParkingAccess,
    hasPanelAccess,
    hasAccessControl,
    refreshUserResources
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
} 