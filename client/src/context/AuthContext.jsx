import { createContext, useContext, useState, useEffect } from 'react'
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
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('token')
    const userData = localStorage.getItem('user')
    
    if (token && userData) {
      try {
        setUser(JSON.parse(userData))
        setIsAuthenticated(true)
      } catch (error) {
        console.error('Error parsing user data:', error)
        logout()
      }
    }
    setLoading(false)
  }, [])

  const login = async (email, password) => {
    try {
      setLoading(true)
      const response = await authService.login(email, password)
      
      if (response.success) {
        const { token, user: userData } = response
        localStorage.setItem('token', token)
        localStorage.setItem('user', JSON.stringify(userData))
        
        setUser(userData)
        setIsAuthenticated(true)
        
        toast.success(`Bienvenido, ${userData.name}`)
        return { success: true }
      } else {
        toast.error('Credenciales incorrectas')
        return { success: false, error: 'Credenciales incorrectas' }
      }
    } catch (error) {
      console.error('Login error:', error)
      toast.error('Error al iniciar sesión')
      return { success: false, error: 'Error al iniciar sesión' }
    } finally {
      setLoading(false)
    }
  }

  const logout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    setUser(null)
    setIsAuthenticated(false)
    toast.success('Sesión cerrada correctamente')
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
    isAuthenticated,
    loading,
    login,
    logout,
    updatePassword,
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
} 