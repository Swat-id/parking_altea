import api from './api'

export const cameraLogService = {
  /**
   * Obtener logs de cámaras con filtros
   */
  getCameraLogs: async (filters = {}) => {
    try {
      const params = new URLSearchParams()
      
      if (filters.parking_id) params.append('parking_id', filters.parking_id)
      if (filters.access_id) params.append('access_id', filters.access_id)
      if (filters.status) params.append('status', filters.status)
      if (filters.limit) params.append('limit', filters.limit)
      if (filters.offset) params.append('offset', filters.offset)
      
      const response = await api.get(`/camera/logs?${params.toString()}`)
      return response.data
    } catch (error) {
      console.error('Error obteniendo logs de cámaras:', error)
      throw error
    }
  },

  /**
   * Obtener estadísticas de logs de cámaras
   */
  getCameraLogsStats: async (filters = {}) => {
    try {
      const params = new URLSearchParams()
      
      if (filters.parking_id) params.append('parking_id', filters.parking_id)
      if (filters.days) params.append('days', filters.days)
      
      const response = await api.get(`/camera/logs/stats?${params.toString()}`)
      return response.data
    } catch (error) {
      console.error('Error obteniendo estadísticas de logs de cámaras:', error)
      throw error
    }
  },

  /**
   * Obtener logs de un parking específico
   */
  getParkingCameraLogs: async (parkingId, limit = 50) => {
    try {
      const response = await api.get(`/camera/logs?parking_id=${parkingId}&limit=${limit}`)
      return response.data
    } catch (error) {
      console.error('Error obteniendo logs de cámaras del parking:', error)
      throw error
    }
  },

  /**
   * Obtener logs de errores
   */
  getErrorLogs: async (limit = 100) => {
    try {
      const response = await api.get(`/camera/logs?status=error&limit=${limit}`)
      return response.data
    } catch (error) {
      console.error('Error obteniendo logs de errores:', error)
      throw error
    }
  },

  /**
   * Obtener logs procesados exitosamente
   */
  getProcessedLogs: async (limit = 100) => {
    try {
      const response = await api.get(`/camera/logs?status=processed&limit=${limit}`)
      return response.data
    } catch (error) {
      console.error('Error obteniendo logs procesados:', error)
      throw error
    }
  }
} 