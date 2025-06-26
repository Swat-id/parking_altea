import React, { createContext, useContext, useState, useEffect } from 'react'

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

  useEffect(() => {
    console.log('AuthProvider: useEffect inicial ejecutándose')
    // Verificar si hay un usuario guardado en localStorage al cargar
    const savedUser = localStorage.getItem('user')
    const token = localStorage.getItem('token')
    
    console.log('AuthProvider: Datos del localStorage:', { savedUser, token })
    
    if (savedUser && token) {
      try {
        const userData = JSON.parse(savedUser)
        console.log('AuthProvider: Usuario parseado del localStorage:', userData)
        setUser(userData)
        console.log('AuthProvider: Usuario cargado desde localStorage:', userData)
      } catch (error) {
        console.error('AuthProvider: Error parsing saved user:', error)
        localStorage.removeItem('user')
        localStorage.removeItem('token')
      }
    } else {
      console.log('AuthProvider: No hay datos de usuario en localStorage')
    }
    setLoading(false)
    console.log('AuthProvider: Loading establecido en false')
  }, [])

  const login = (userData) => {
    console.log('AuthProvider: Login llamado con:', userData)
    
    // Asegurar que userData es válido
    if (!userData || !userData.token) {
      console.error('AuthProvider: userData inválido:', userData)
      return
    }
    
    console.log('AuthProvider: Antes de setUser, estado actual:', { user, isAuthenticated: !!user })
    
    // Actualizar estado inmediatamente
    setUser(userData)
    
    // Guardar en localStorage
    localStorage.setItem('user', JSON.stringify(userData))
    localStorage.setItem('token', userData.token)
    
    console.log('AuthProvider: Después de setUser, nuevo estado:', { userData, isAuthenticated: !!userData })
    console.log('AuthProvider: Estado actualizado, usuario guardado en localStorage')
  }

  const logout = () => {
    console.log('AuthProvider: Logout llamado')
    setUser(null)
    localStorage.removeItem('user')
    localStorage.removeItem('token')
  }

  const isAuthenticated = !!user

  console.log('AuthProvider: Estado actual de autenticación:', { 
    user, 
    isAuthenticated, 
    loading,
    userExists: !!user,
    tokenExists: !!localStorage.getItem('token'),
    userType: typeof user,
    userKeys: user ? Object.keys(user) : 'null'
  })

  const value = {
    user,
    login,
    logout,
    isAuthenticated,
    loading
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
} 