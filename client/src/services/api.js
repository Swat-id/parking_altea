import axios from 'axios'

// Determinar la URL base según el entorno
const isProduction = window.location.hostname === '157.180.91.63' || 
                     window.location.hostname === 'localhost' ||
                     window.location.port === '5789'
const API_BASE_URL = isProduction 
  ? 'http://157.180.91.63:6001'  // Usar URL directa temporalmente
  : (import.meta.env.VITE_API_URL || 'http://157.180.91.63:6001')

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // Aumentar timeout a 30 segundos para operaciones pesadas
  headers: {
    'Content-Type': 'application/json',
  },
})

// Interceptor para agregar el token automáticamente
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Interceptor para manejar respuestas y errores
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    console.error('API Error:', error.response?.status, error.response?.data)
    
    // Manejar errores de autenticación
    if (error.response?.status === 401) {
      // Token expirado o inválido
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      
      // Redirigir a login solo si no estamos ya en la página de login
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    
    // Manejar errores de permisos
    if (error.response?.status === 403) {
      console.error('Acceso denegado:', error.response.data?.error)
      // No redirigir, solo mostrar error
    }
    
    return Promise.reject(error)
  }
)

export default api 