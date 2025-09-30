import api from './api'

export const statisticsService = {
  /**
   * MEJORADO v4.2.0: Obtener estadísticas de todos los parkings del usuario
   * - Ahora filtra automáticamente por permisos
   * - Superadmin ve todos, usuario regular solo sus parkings
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
   * - Solo si el usuario tiene acceso al parking
   */
  getParkingStatistics: async (parkingId, days = 7) => {
    try {
      const response = await api.get(`/api/parkings/${parkingId}/statistics?days=${days}`)
      return response.data
    } catch (error) {
      if (error.response?.status === 403) {
        console.warn(`Sin permisos para estadísticas del parking ${parkingId}`)
        return null
      }
      console.error('Error obteniendo estadísticas del parking:', error)
      throw error
    }
  },

  /**
   * MEJORADO v4.2.0: Obtener logs de actividad filtrados por permisos
   * - Solo muestra logs de parkings/paneles accesibles al usuario
   */
  getActivityLogs: async (params = {}) => {
    try {
      const queryParams = new URLSearchParams()
      
      if (params.userId) queryParams.append('user_id', params.userId)
      if (params.parkingId) queryParams.append('parking_id', params.parkingId)
      if (params.actionType) queryParams.append('action_type', params.actionType)
      if (params.startDate) queryParams.append('start_date', params.startDate)
      if (params.endDate) queryParams.append('end_date', params.endDate)
      if (params.limit) queryParams.append('limit', params.limit)
      
      const response = await api.get(`/api/logs/activity?${queryParams.toString()}`)
      return response.data
    } catch (error) {
      console.error('Error obteniendo logs de actividad:', error)
      throw error
    }
  },

  /**
   * MEJORADO v4.2.0: Obtener logs de mensajes de paneles filtrados
   * - Solo paneles accesibles al usuario
   */
  getPanelLogs: async (params = {}) => {
    try {
      const queryParams = new URLSearchParams()
      
      if (params.panelId) queryParams.append('panel_id', params.panelId)
      if (params.parkingId) queryParams.append('parking_id', params.parkingId)
      if (params.messageType) queryParams.append('message_type', params.messageType)
      if (params.startDate) queryParams.append('start_date', params.startDate)
      if (params.endDate) queryParams.append('end_date', params.endDate)
      if (params.limit) queryParams.append('limit', params.limit)
      
      const response = await api.get(`/api/logs/panels?${queryParams.toString()}`)
      return response.data
    } catch (error) {
      console.error('Error obteniendo logs de paneles:', error)
      throw error
    }
  },

  /**
   * MEJORADO v4.2.0: Obtener logs de cámaras filtrados
   * - Solo cámaras de parkings accesibles al usuario
   */
  getCameraLogs: async (params = {}) => {
    try {
      const queryParams = new URLSearchParams()
      
      if (params.cameraId) queryParams.append('camera_id', params.cameraId)
      if (params.parkingId) queryParams.append('parking_id', params.parkingId)
      if (params.eventType) queryParams.append('event_type', params.eventType)
      if (params.startDate) queryParams.append('start_date', params.startDate)
      if (params.endDate) queryParams.append('end_date', params.endDate)
      if (params.limit) queryParams.append('limit', params.limit)
      
      const response = await api.get(`/api/logs/cameras?${queryParams.toString()}`)
      return response.data
    } catch (error) {
      console.error('Error obteniendo logs de cámaras:', error)
      throw error
    }
  },

  /**
   * NUEVO v4.2.0: Obtener estadísticas del dashboard del usuario
   * - Usa el nuevo endpoint personalizado
   */
  getUserDashboardStats: async () => {
    try {
      const response = await api.get('/api/dashboard/user/sensors')
      return response.data
    } catch (error) {
      console.error('Error obteniendo estadísticas del dashboard del usuario:', error)
      throw error
    }
  },

  /**
   * NUEVO v4.2.0: Obtener resumen de ocupación por usuario
   */
  getUserOccupancySummary: async (days = 7) => {
    try {
      const response = await api.get(`/api/statistics/user/occupancy?days=${days}`)
      return response.data
    } catch (error) {
      console.error('Error obteniendo resumen de ocupación del usuario:', error)
      throw error
    }
  },

  /**
   * NUEVO v4.2.0: Obtener estadísticas de sensores por usuario
   */
  getUserSensorStats: async () => {
    try {
      const response = await api.get('/api/sensors/summary/user')
      return response.data
    } catch (error) {
      console.error('Error obteniendo estadísticas de sensores del usuario:', error)
      throw error
    }
  },

  /**
   * Obtener estadísticas de alarmas (filtradas por permisos)
   */
  getAlarmStatistics: async (days = 30) => {
    try {
      const response = await api.get(`/api/alarms/statistics?days=${days}`)
      return response.data
    } catch (error) {
      console.error('Error obteniendo estadísticas de alarmas:', error)
      throw error
    }
  },

  /**
   * Obtener historial de alarmas (filtrado por permisos)
   */
  getAlarmHistory: async (params = {}) => {
    try {
      const queryParams = new URLSearchParams()
      
      if (params.parkingId) queryParams.append('parking_id', params.parkingId)
      if (params.severity) queryParams.append('severity', params.severity)
      if (params.status) queryParams.append('status', params.status)
      if (params.startDate) queryParams.append('start_date', params.startDate)
      if (params.endDate) queryParams.append('end_date', params.endDate)
      if (params.limit) queryParams.append('limit', params.limit)
      
      const response = await api.get(`/api/alarms/history?${queryParams.toString()}`)
      return response.data
    } catch (error) {
      console.error('Error obteniendo historial de alarmas:', error)
      throw error
    }
  },

  /**
   * NUEVO v4.2.0: Obtener métricas comparativas entre parkings del usuario
   */
  getUserParkingsComparison: async (days = 7) => {
    try {
      const response = await api.get(`/api/statistics/user/comparison?days=${days}`)
      return response.data
    } catch (error) {
      console.error('Error obteniendo comparación de parkings del usuario:', error)
      throw error
    }
  },

  /**
   * NUEVO: Obtener estadísticas por horas de un parking
   */
  getHourlyStatistics: async (parkingId, params = {}) => {
    try {
      const queryParams = new URLSearchParams()
      
      if (params.date) queryParams.append('date', params.date)
      if (params.days) queryParams.append('days', params.days)
      
      const response = await api.get(`/api/parkings/${parkingId}/hourly-statistics?${queryParams.toString()}`)
      return response.data
    } catch (error) {
      console.error('Error obteniendo estadísticas por horas:', error)
      throw error
    }
  },

  /**
   * Utilidades para procesamiento de estadísticas
   */
  utils: {
    /**
     * Procesar datos de ocupación para gráficos
     */
    processOccupancyData: (data) => {
      if (!data || !Array.isArray(data)) return []
      
      return data.map(item => ({
        timestamp: new Date(item.timestamp),
        occupancy: item.occupancy_percentage || 0,
        total_spaces: item.total_spaces || 0,
        occupied_spaces: item.occupied_spaces || 0,
        parking_name: item.parking_name || 'Unknown'
      }))
    },

    /**
     * Calcular métricas de resumen
     */
    calculateSummaryMetrics: (statisticsData) => {
      if (!statisticsData || !Array.isArray(statisticsData)) {
        return {
          averageOccupancy: 0,
          peakOccupancy: 0,
          totalSpaces: 0,
          totalParkings: 0
        }
      }

      const totalSpaces = statisticsData.reduce((sum, item) => sum + (item.total_spaces || 0), 0)
      const totalOccupancy = statisticsData.reduce((sum, item) => sum + (item.occupancy_percentage || 0), 0)
      const averageOccupancy = statisticsData.length > 0 ? totalOccupancy / statisticsData.length : 0
      const peakOccupancy = Math.max(...statisticsData.map(item => item.occupancy_percentage || 0), 0)

      return {
        averageOccupancy: Math.round(averageOccupancy * 100) / 100,
        peakOccupancy: Math.round(peakOccupancy * 100) / 100,
        totalSpaces,
        totalParkings: statisticsData.length
      }
    },

    /**
     * Agrupar logs por fecha
     */
    groupLogsByDate: (logs) => {
      if (!logs || !Array.isArray(logs)) return {}
      
      const grouped = {}
      logs.forEach(log => {
        const date = new Date(log.timestamp).toISOString().split('T')[0]
        if (!grouped[date]) {
          grouped[date] = []
        }
        grouped[date].push(log)
      })
      
      return grouped
    },

    /**
     * Filtrar estadísticas por rango de fechas
     */
    filterByDateRange: (data, startDate, endDate) => {
      if (!data || !Array.isArray(data)) return []
      
      const start = new Date(startDate)
      const end = new Date(endDate)
      
      return data.filter(item => {
        const itemDate = new Date(item.timestamp || item.created_at)
        return itemDate >= start && itemDate <= end
      })
    },

    /**
     * Calcular tendencias (crecimiento/decrecimiento)
     */
    calculateTrends: (currentData, previousData) => {
      if (!currentData || !previousData) return null
      
      const currentValue = currentData.value || 0
      const previousValue = previousData.value || 0
      
      if (previousValue === 0) return currentValue > 0 ? 100 : 0
      
      const percentageChange = ((currentValue - previousValue) / previousValue) * 100
      return Math.round(percentageChange * 100) / 100
    },

    /**
     * Formatear datos para exportación
     */
    formatForExport: (data, type = 'csv') => {
      if (!data || !Array.isArray(data)) return ''
      
      if (type === 'csv') {
        if (data.length === 0) return ''
        
        const headers = Object.keys(data[0]).join(',')
        const rows = data.map(row => 
          Object.values(row).map(value => 
            typeof value === 'string' && value.includes(',') ? `"${value}"` : value
          ).join(',')
        )
        
        return [headers, ...rows].join('\n')
      }
      
      return JSON.stringify(data, null, 2)
    }
  }
}