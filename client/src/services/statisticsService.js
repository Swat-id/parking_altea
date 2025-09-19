import api from './api'

export const statisticsService = {
  /**
   * Obtener estadísticas de todos los parkings
   */
  getAllStatistics: async (days = 7) => {
    try {
      const response = await api.get(`/api/statistics?days=${days}`)
      return response.data
    } catch (error) {
      console.error('Error obteniendo estadísticas generales:', error)
      throw error
    }
  },

  /**
   * Obtener estadísticas de un parking específico
   */
  getParkingStatistics: async (parkingId, days = 7) => {
    try {
      const response = await api.get(`/api/parkings/${parkingId}/statistics?days=${days}`)
      return response.data
    } catch (error) {
      console.error('Error obteniendo estadísticas del parking:', error)
      throw error
    }
  },

  /**
   * Obtener logs de actividad
   */
  getActivityLogs: async (params = {}) => {
    try {
      const queryParams = new URLSearchParams()
      
      if (params.userId) queryParams.append('user_id', params.userId)
      if (params.parkingId) queryParams.append('parking_id', params.parkingId)
      if (params.actionType) queryParams.append('action_type', params.actionType)
      if (params.limit) queryParams.append('limit', params.limit)
      
      const response = await api.get(`/logs/activity?${queryParams.toString()}`)
      return response.data
    } catch (error) {
      console.error('Error obteniendo logs de actividad:', error)
      throw error
    }
  },

  /**
   * Obtener logs de mensajes de paneles
   */
  getPanelLogs: async (params = {}) => {
    try {
      const queryParams = new URLSearchParams()
      
      if (params.panelId) queryParams.append('panel_id', params.panelId)
      if (params.parkingId) queryParams.append('parking_id', params.parkingId)
      if (params.limit) queryParams.append('limit', params.limit)
      
      const response = await api.get(`/logs/panels?${queryParams.toString()}`)
      return response.data
    } catch (error) {
      console.error('Error obteniendo logs de paneles:', error)
      throw error
    }
  },

  /**
   * Exportar datos de estadísticas
   */
  exportData: async (parkingId, days = 7, format = 'csv') => {
    try {
      const response = await api.get(`/api/parkings/${parkingId}/statistics?days=${days}&format=${format}`, {
        responseType: 'blob'
      })
      
      // Crear descarga del archivo
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `parking_${parkingId}_statistics_${days}days.${format}`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
      
      return { success: true }
    } catch (error) {
      console.error('Error exportando datos:', error)
      throw error
    }
  },

  /**
   * Obtener estadísticas por horas de un parking
   * @param {number} parkingId - ID del parking
   * @param {Object} options - Opciones de filtrado
   * @returns {Promise<Object>} Estadísticas por horas
   */
  async getHourlyStatistics(parkingId, options = {}) {
    try {
      const params = new URLSearchParams()
      
      if (options.date) params.append('date', options.date)
      if (options.days) params.append('days', options.days)
      
      const response = await api.get(`/parking/${parkingId}/hourly-statistics?${params.toString()}`)
      return response.data
    } catch (error) {
      console.error('Error obteniendo estadísticas por horas:', error)
      throw error
    }
  },
} 