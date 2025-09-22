import api from './api'

export const cameraLogService = {
  /**
   * Obtener logs de cámaras con filtros
   * @param {Object} filters - Filtros de búsqueda
   * @returns {Promise<Object>} Logs de cámaras
   */
  async getCameraLogs(filters = {}) {
    try {
      const params = new URLSearchParams()
      
      if (filters.parking_id) params.append('parking_id', filters.parking_id)
      if (filters.camera_id) params.append('camera_id', filters.camera_id)
      if (filters.date_filter) params.append('date_filter', filters.date_filter)
      if (filters.level) params.append('level', filters.level)
      if (filters.limit) params.append('limit', filters.limit)
      
      const response = await api.get(`/api/camera/logs?${params.toString()}`)
      return response.data
    } catch (error) {
      console.error('Error obteniendo logs de cámaras:', error)
      throw error
    }
  },

  /**
   * Obtener estadísticas de logs de cámaras
   * @param {Object} filters - Filtros de búsqueda
   * @returns {Promise<Object>} Estadísticas de logs
   */
  async getCameraLogsStats(filters = {}) {
    try {
      const params = new URLSearchParams()
      
      if (filters.parking_id) params.append('parking_id', filters.parking_id)
      if (filters.days) params.append('days', filters.days)
      
      const response = await api.get(`/api/camera/logs/stats?${params.toString()}`)
      return response.data
    } catch (error) {
      console.error('Error obteniendo estadísticas de logs:', error)
      throw error
    }
  },

  /**
   * Obtener logs de actividad
   * @param {Object} filters - Filtros de búsqueda
   * @returns {Promise<Object>} Logs de actividad
   */
  async getActivityLogs(filters = {}) {
    try {
      const params = new URLSearchParams()
      
      if (filters.parking_id) params.append('parking_id', filters.parking_id)
      if (filters.limit) params.append('limit', filters.limit)
      
      const response = await api.get(`/api/logs/activity?${params.toString()}`)
      return response.data
    } catch (error) {
      console.error('Error obteniendo logs de actividad:', error)
      throw error
    }
  },

  /**
   * Obtener logs de paneles
   * @param {Object} filters - Filtros de búsqueda
   * @returns {Promise<Object>} Logs de paneles
   */
  async getPanelLogs(filters = {}) {
    try {
      const params = new URLSearchParams()
      
      if (filters.panel_id) params.append('panel_id', filters.panel_id)
      if (filters.limit) params.append('limit', filters.limit)
      
      const response = await api.get(`/api/logs/panels?${params.toString()}`)
      return response.data
    } catch (error) {
      console.error('Error obteniendo logs de paneles:', error)
      throw error
    }
  },

  /**
   * Obtener logs de un parking específico
   */
  getParkingCameraLogs: async (parkingId, limit = 50) => {
    try {
      const response = await api.get(`/api/camera/logs?parking_id=${parkingId}&limit=${limit}`)
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
      const response = await api.get(`/api/camera/logs?status=error&limit=${limit}`)
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
      const response = await api.get(`/api/camera/logs?status=processed&limit=${limit}`)
      return response.data
    } catch (error) {
      console.error('Error obteniendo logs procesados:', error)
      throw error
    }
  },

  /**
   * Obtener logs de cámaras con filtros avanzados (v2)
   * @param {Object} filters - Filtros para aplicar
   * @param {Object} pagination - Configuración de paginación
   * @returns {Promise<Object>} Logs paginados con metadatos
   */
  async getCameraLogsV2(filters = {}, pagination = {}) {
    try {
      const params = new URLSearchParams()
      
      // Filtros básicos
      if (filters.parkingId) params.append('parking_id', filters.parkingId)
      if (filters.accessId) params.append('access_id', filters.accessId)
      if (filters.cameraIp) params.append('camera_ip', filters.cameraIp)
      if (filters.cameraName) params.append('camera_name', filters.cameraName)
      if (filters.status) params.append('status', filters.status)
      
      // Filtros de fecha y hora
      if (filters.dateFrom) params.append('date_from', filters.dateFrom)
      if (filters.dateTo) params.append('date_to', filters.dateTo)
      if (filters.timeFrom) params.append('time_from', filters.timeFrom)
      if (filters.timeTo) params.append('time_to', filters.timeTo)
      
      // Filtros especiales
      if (filters.hasChanges !== undefined) params.append('has_changes', filters.hasChanges)
      if (filters.errorOnly !== undefined) params.append('error_only', filters.errorOnly)
      
      // Ordenación
      if (filters.orderBy) params.append('order_by', filters.orderBy)
      if (filters.orderDirection) params.append('order_direction', filters.orderDirection)
      
      // Paginación
      if (pagination.page) params.append('page', pagination.page)
      if (pagination.perPage) params.append('per_page', pagination.perPage)
      
      const response = await api.get(`/api/camera-logs-v2?${params.toString()}`)
      return response.data
    } catch (error) {
      console.error('Error obteniendo logs de cámaras v2:', error)
      throw error
    }
  }
} 