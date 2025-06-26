import React, { createContext, useContext } from 'react'

const AuthContext = createContext()

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export const AuthProvider = ({ children }) => {
  // Usuario fijo: Toni Alos
  const user = {
    id: 1,
    name: 'Toni Alos',
    email: 'atea.dti@altea.es',
    token: 'default-token-toni-alos'
  }

  // Funciones vacías
  const login = () => {}
  const logout = () => {}
  
  // Siempre autenticado
  const isAuthenticated = true
  const loading = false

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