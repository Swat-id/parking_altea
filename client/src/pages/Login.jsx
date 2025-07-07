import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const Login = () => {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const navigate = useNavigate()
  const { login, isAuthenticated, loading: authLoading } = useAuth()

  console.log('Login: Componente renderizado, estado actual:', { isAuthenticated, email, loading })

  // Efecto para navegar cuando el usuario esté autenticado
  useEffect(() => {
    console.log('Login: useEffect detectando cambio en isAuthenticated:', isAuthenticated)
    if (isAuthenticated && !authLoading) {
      console.log('Login: Usuario autenticado, navegando a dashboard')
      navigate('/dashboard')
    }
  }, [isAuthenticated, authLoading, navigate])

  // Validación de email
  const validateEmail = (email) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    return emailRegex.test(email)
  }

  // Validación de formulario
  const validateForm = () => {
    if (!email.trim()) {
      setError('El email es requerido')
      return false
    }
    
    if (!validateEmail(email)) {
      setError('El formato del email no es válido')
      return false
    }
    
    if (!password.trim()) {
      setError('La contraseña es requerida')
      return false
    }
    
    if (password.length < 6) {
      setError('La contraseña debe tener al menos 6 caracteres')
      return false
    }
    
    return true
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    // Limpiar errores previos
    setError('')
    
    // Validar formulario
    if (!validateForm()) {
      return
    }
    
    setLoading(true)
    
    try {
      const result = await login(email, password)
      
      if (result.success) {
        // El login fue exitoso, el useEffect se encargará de la navegación
        console.log('Login exitoso')
      } else {
        setError(result.error || 'Error de autenticación')
      }
    } catch (err) {
      console.error('Login error:', err)
      
      // Manejar diferentes tipos de errores
      if (err.response?.status === 401) {
        setError('Credenciales incorrectas')
      } else if (err.response?.status === 400) {
        setError(err.response.data?.error || 'Datos de entrada inválidos')
      } else if (err.response?.status >= 500) {
        setError('Error del servidor. Inténtelo más tarde.')
      } else if (err.code === 'NETWORK_ERROR' || err.message?.includes('Network Error')) {
        setError('Error de conexión. Verifique su conexión a internet.')
      } else {
        setError('Error inesperado. Inténtelo de nuevo.')
      }
    } finally {
      setLoading(false)
    }
  }

  // Manejar cambio de email
  const handleEmailChange = (e) => {
    setEmail(e.target.value)
    if (error) setError('') // Limpiar error al escribir
  }

  // Manejar cambio de contraseña
  const handlePasswordChange = (e) => {
    setPassword(e.target.value)
    if (error) setError('') // Limpiar error al escribir
  }

  // Mostrar/ocultar contraseña
  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword)
  }

  // Si está cargando la autenticación inicial, mostrar spinner
  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Cargando...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Parking Altea
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Sistema de Gestión de Aparcamientos
          </p>
        </div>
        
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="rounded-md shadow-sm -space-y-px">
            <div>
              <label htmlFor="email" className="sr-only">
                Email
              </label>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                className={`appearance-none rounded-none relative block w-full px-3 py-2 border placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm ${
                  error && !email ? 'border-red-300' : 'border-gray-300'
                }`}
                placeholder="Email"
                value={email}
                onChange={handleEmailChange}
                disabled={loading}
              />
            </div>
            <div className="relative">
              <label htmlFor="password" className="sr-only">
                Contraseña
              </label>
              <input
                id="password"
                name="password"
                type={showPassword ? 'text' : 'password'}
                autoComplete="current-password"
                required
                className={`appearance-none rounded-none relative block w-full px-3 py-2 border placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm pr-10 ${
                  error && !password ? 'border-red-300' : 'border-gray-300'
                }`}
                placeholder="Contraseña"
                value={password}
                onChange={handlePasswordChange}
                disabled={loading}
              />
              <button
                type="button"
                className="absolute inset-y-0 right-0 pr-3 flex items-center"
                onClick={togglePasswordVisibility}
                disabled={loading}
              >
                {showPassword ? (
                  <svg className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L3 3m6.878 6.878L21 21" />
                  </svg>
                ) : (
                  <svg className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                )}
              </button>
            </div>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-md p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <p className="text-sm text-red-800">{error}</p>
                </div>
              </div>
            </div>
          )}

          <div>
            <button
              type="submit"
              disabled={loading}
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Iniciando sesión...
                </>
              ) : (
                'Iniciar sesión'
              )}
            </button>
          </div>

          <div className="text-xs text-gray-500 text-center space-y-1">
            <p className="font-medium">Credenciales de acceso:</p>
            <p>Superadmin: info@swat-id.com / admin123</p>
            <p>Usuario: user@test.com / test123</p>
            <p className="text-xs mt-2">
              Para crear nuevas cuentas, contacte al administrador del sistema.
            </p>
          </div>
        </form>
      </div>
    </div>
  )
}

export default Login 