import React, { createContext, useContext, useState, useEffect } from 'react'
import { authService } from '../services/authService'
import toast from 'react-hot-toast'

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
  const [error, setError] = useState(null)

  useEffect(() => {
    // Check for existing token on app load
    const token = localStorage.getItem('token')
    const userData = localStorage.getItem('user')
    
    if (token && userData) {
      try {
        setUser(JSON.parse(userData))
      } catch (e) {
        console.error('Error parsing user data:', e)
        localStorage.removeItem('token')
        localStorage.removeItem('user')
      }
    }
    setLoading(false)
  }, [])

  const login = async (email, password) => {
    try {
      setError(null)
      setLoading(true)
      
      const response = await fetch('http://localhost:6001/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.error || 'Error de autenticación')
      }

      localStorage.setItem('token', data.token)
      localStorage.setItem('user', JSON.stringify(data.user))
      setUser(data.user)
      return { success: true }
    } catch (error) {
      setError(error.message)
      return { success: false, error: error.message }
    } finally {
      setLoading(false)
    }
  }

  const logout = () => {
    try {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      setUser(null)
      setError(null)
      // Redirect to login page
      window.location.href = '/login'
    } catch (error) {
      console.error('Error during logout:', error)
    }
  }

  const clearError = () => {
    setError(null)
  }

  const updatePassword = async (currentPassword, newPassword) => {
    try {
      const response = await authService.updatePassword(currentPassword, newPassword)
      if (response.success) {
        toast.success('Contraseña actualizada correctamente')
        return { success: true }
      } else {
        toast.error(response.error || 'Error al actualizar contraseña')
        return { success: false, error: response.error }
      }
    } catch (error) {
      console.error('Update password error:', error)
      toast.error('Error al actualizar contraseña')
      return { success: false, error: 'Error al actualizar contraseña' }
    }
  }

  const value = {
    user,
    loading,
    error,
    login,
    logout,
    clearError,
    isAuthenticated: !!user,
    updatePassword,
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
} 