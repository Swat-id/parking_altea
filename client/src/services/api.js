import axios from 'axios'

// Determinar la URL base según el entorno
const isProduction = window.location.hostname === '157.180.91.63' || 
                     window.location.hostname === 'localhost' ||
                     window.location.port === '5789'
const API_BASE_URL = isProduction 
  ? '/api'  // Usar ruta relativa para nginx proxy
  : (import.meta.env.VITE_API_URL || 'http://157.180.91.63:6001')

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Interceptor simple para agregar el token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token') || 'default-token-toni-alos'
    config.headers.Authorization = `Bearer ${token}`
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Interceptor simple para manejar errores sin redirecciones
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    console.error('API Error:', error.response?.status, error.response?.data)
    return Promise.reject(error)
  }
)

export default api 