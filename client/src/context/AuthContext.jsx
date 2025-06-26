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
    // Verificar si hay un usuario guardado en localStorage al cargar
    const savedUser = localStorage.getItem('user')
    const token = localStorage.getItem('token')
    
    if (savedUser && token) {
      try {
        const userData = JSON.parse(savedUser)
        setUser(userData)
        console.log('Usuario cargado desde localStorage:', userData)
      } catch (error) {
        console.error('Error parsing saved user:', error)
        localStorage.removeItem('user')
        localStorage.removeItem('token')
      }
    }
    setLoading(false)
  }, [])

  const login = (userData) => {
    console.log('Login llamado con:', userData)
    setUser(userData)
    // El localStorage ya se maneja en el componente Login
  }

  const logout = () => {
    console.log('Logout llamado')
    setUser(null)
    localStorage.removeItem('user')
    localStorage.removeItem('token')
  }

  const isAuthenticated = !!user

  console.log('Estado actual de autenticación:', { user, isAuthenticated, loading })

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