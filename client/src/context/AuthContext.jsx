import React, { createContext, useContext, useState } from 'react'

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

  const [user] = useState(defaultUser)
  const [loading] = useState(false)

  // Guardar usuario por defecto en localStorage una sola vez
  if (!localStorage.getItem('user')) {
    localStorage.setItem('user', JSON.stringify(defaultUser))
    localStorage.setItem('token', defaultUser.token)
  }

  const login = (userData) => {
    // No hacer nada, mantener siempre el usuario por defecto
    console.log('Login llamado pero manteniendo usuario por defecto')
  }

  const logout = () => {
    // No hacer nada, mantener siempre autenticado
    console.log('Logout llamado pero manteniendo usuario por defecto')
  }

  const isAuthenticated = true // Siempre autenticado

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