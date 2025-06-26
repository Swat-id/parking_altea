import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const Login = () => {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()
  const { login } = useAuth()

  // Credenciales predefinidas para acceso directo
  const validCredentials = {
    'atea.dti@altea.es': 'altea2025!',
    'gerenciapstd@altea.es': 'altea2025!',
    'admin': 'admin123' // Credencial de emergencia
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      // Verificación local simple
      if (validCredentials[email] && validCredentials[email] === password) {
        console.log('Login exitoso con credenciales locales')
        
        // Crear objeto de usuario simulado
        const userData = {
          id: email === 'atea.dti@altea.es' ? 1 : email === 'gerenciapstd@altea.es' ? 2 : 999,
          name: email === 'atea.dti@altea.es' ? 'Toni Alos' : 
                email === 'gerenciapstd@altea.es' ? 'Iván Martí' : 'Admin',
          email: email,
          token: 'local-token-' + Date.now()
        }

        // Actualizar contexto (el localStorage se maneja en el contexto)
        login(userData)
        
        // Redirigir al dashboard
        navigate('/dashboard')
        return
      } else {
        setError('Credenciales incorrectas')
      }
    } catch (err) {
      console.error('Error de conexión:', err)
      setError('Error interno del sistema')
    } finally {
      setLoading(false)
    }
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
                required
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                placeholder="Email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <div>
              <label htmlFor="password" className="sr-only">
                Contraseña
              </label>
              <input
                id="password"
                name="password"
                type="password"
                required
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                placeholder="Contraseña"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
          </div>

          {error && (
            <div className="text-red-600 text-sm text-center">
              {error}
            </div>
          )}

          <div>
            <button
              type="submit"
              disabled={loading}
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
            >
              {loading ? 'Iniciando sesión...' : 'Iniciar sesión'}
            </button>
          </div>

          <div className="text-xs text-gray-500 text-center">
            <p>Credenciales de acceso:</p>
            <p>Toni Alos: atea.dti@altea.es / altea2025!</p>
            <p>Iván Martí: gerenciapstd@altea.es / altea2025!</p>
            <p>Admin: admin / admin123</p>
          </div>
        </form>
      </div>
    </div>
  )
}

export default Login 