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
  // Usuario por defecto: Toni Alos
  const defaultUser = {
    id: 1,
    name: 'Toni Alos',
    email: 'atea.dti@altea.es',
    token: 'default-token-toni-alos'
  }

  const [user, setUser] = useState(defaultUser)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    console.log('AuthProvider: Inicializando con usuario por defecto:', defaultUser)
    // Guardar usuario por defecto en localStorage
    localStorage.setItem('user', JSON.stringify(defaultUser))
    localStorage.setItem('token', defaultUser.token)
    setLoading(false)
  }, [])

  const login = (userData) => {
    console.log('AuthProvider: Login llamado con:', userData)
    // Mantener siempre el usuario por defecto
    setUser(defaultUser)
    localStorage.setItem('user', JSON.stringify(defaultUser))
    localStorage.setItem('token', defaultUser.token)
    console.log('AuthProvider: Usuario establecido como Toni Alos')
  }

  const logout = () => {
    console.log('AuthProvider: Logout llamado - pero manteniendo usuario por defecto')
    // No hacer logout, mantener siempre autenticado
    setUser(defaultUser)
    localStorage.setItem('user', JSON.stringify(defaultUser))
    localStorage.setItem('token', defaultUser.token)
  }

  const isAuthenticated = true // Siempre autenticado

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