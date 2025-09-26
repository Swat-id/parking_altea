/**
 * Servicio de Logs con Control de Permisos v4.2.0
 * - Todos los logs se filtran automáticamente por permisos del usuario
 * - Superadmin ve todos los logs, usuario regular solo logs de sus recursos
 */

import api from './api'

export const logService = {
  /**
   * MEJORADO v4.2.0: Obtener logs de actividad filtrados por permisos
   * - Solo muestra actividad de parkings/paneles accesibles al usuario
   */
  getActivityLogs: async (params = {}) => {
    try {
      const queryParams = new URLSearchParams()
      
      // Parámetros de filtrado
      if (params.userId) queryParams.append('user_id', params.userId)
      if (params.parkingId) queryParams.append('parking_id', params.parkingId)
      if (params.panelId) queryParams.append('panel_id', params.panelId)
      if (params.actionType) queryParams.append('action_type', params.actionType)
      if (params.startDate) queryParams.append('start_date', params.startDate)
      if (params.endDate) queryParams.append('end_date', params.endDate)
      if (params.limit) queryParams.append('limit', params.limit)
      if (params.offset) queryParams.append('offset', params.offset)
      
      const response = await api.get(`/api/logs/activity?${queryParams.toString()}`)
      return response.data
    } catch (error) {
      console.error('Error obteniendo logs de actividad:', error)
      throw error
    }
  },

  /**
   * MEJORADO v4.2.0: Obtener logs de paneles filtrados por permisos
   * - Solo paneles de parkings accesibles al usuario
   */
  getPanelLogs: async (params = {}) => {
    try {
      const queryParams = new URLSearchParams()
      
      if (params.panelId) queryParams.append('panel_id', params.panelId)
      if (params.parkingId) queryParams.append('parking_id', params.parkingId)
      if (params.messageType) queryParams.append('message_type', params.messageType)
      if (params.status) queryParams.append('status', params.status)
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
   * MEJORADO v4.2.0: Obtener logs de cámaras filtrados por permisos
   * - Solo cámaras de parkings accesibles al usuario
   */
  getCameraLogs: async (params = {}) => {
    try {
      const queryParams = new URLSearchParams()
      
      if (params.cameraId) queryParams.append('camera_id', params.cameraId)
      if (params.accessId) queryParams.append('access_id', params.accessId)
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
   * NUEVO v4.2.0: Obtener logs de sensores individuales
   * - Solo sensores de parkings accesibles al usuario
   */
  getSensorLogs: async (params = {}) => {
    try {
      const queryParams = new URLSearchParams()
      
      if (params.sensorId) queryParams.append('sensor_id', params.sensorId)
      if (params.parkingId) queryParams.append('parking_id', params.parkingId)
      if (params.sensorType) queryParams.append('sensor_type', params.sensorType)
      if (params.statusChange) queryParams.append('status_change', params.statusChange)
      if (params.startDate) queryParams.append('start_date', params.startDate)
      if (params.endDate) queryParams.append('end_date', params.endDate)
      if (params.limit) queryParams.append('limit', params.limit)
      
      const response = await api.get(`/api/logs/sensors?${queryParams.toString()}`)
      return response.data
    } catch (error) {
      console.error('Error obteniendo logs de sensores:', error)
      throw error
    }
  },

  /**
   * NUEVO v4.2.0: Obtener logs de alarmas filtrados por permisos
   */
  getAlarmLogs: async (params = {}) => {
    try {
      const queryParams = new URLSearchParams()
      
      if (params.alarmId) queryParams.append('alarm_id', params.alarmId)
      if (params.parkingId) queryParams.append('parking_id', params.parkingId)
      if (params.severity) queryParams.append('severity', params.severity)
      if (params.status) queryParams.append('status', params.status)
      if (params.startDate) queryParams.append('start_date', params.startDate)
      if (params.endDate) queryParams.append('end_date', params.endDate)
      if (params.limit) queryParams.append('limit', params.limit)
      
      const response = await api.get(`/api/logs/alarms?${queryParams.toString()}`)
      return response.data
    } catch (error) {
      console.error('Error obteniendo logs de alarmas:', error)
      throw error
    }
  },

  /**
   * NUEVO v4.2.0: Obtener logs del usuario (actividad propia)
   */
  getUserLogs: async (params = {}) => {
    try {
      const queryParams = new URLSearchParams()
      
      if (params.actionType) queryParams.append('action_type', params.actionType)
      if (params.resourceType) queryParams.append('resource_type', params.resourceType)
      if (params.startDate) queryParams.append('start_date', params.startDate)
      if (params.endDate) queryParams.append('end_date', params.endDate)
      if (params.limit) queryParams.append('limit', params.limit)
      
      const response = await api.get(`/api/logs/user?${queryParams.toString()}`)
      return response.data
    } catch (error) {
      console.error('Error obteniendo logs del usuario:', error)
      throw error
    }
  },

  /**
   * NUEVO v4.2.0: Obtener resumen de logs por parking
   */
  getLogsSummaryByParking: async (parkingId, days = 7) => {
    try {
      const response = await api.get(`/api/logs/parking/${parkingId}/summary?days=${days}`)
      return response.data
    } catch (error) {
      if (error.response?.status === 403) {
        console.warn(`Sin permisos para logs del parking ${parkingId}`)
        return null
      }
      console.error('Error obteniendo resumen de logs del parking:', error)
      throw error
    }
  },

  /**
   * NUEVO v4.2.0: Obtener logs consolidados del dashboard del usuario
   */
  getUserDashboardLogs: async (limit = 50) => {
    try {
      const response = await api.get(`/api/logs/user/dashboard?limit=${limit}`)
      return response.data
    } catch (error) {
      console.error('Error obteniendo logs del dashboard del usuario:', error)
      throw error
    }
  },

  /**
   * Obtener tipos de logs disponibles
   */
  getLogTypes: () => {
    return {
      activity: {
        name: 'Actividad',
        types: [
          'user_login', 'user_logout', 'parking_created', 'parking_updated',
          'panel_message_sent', 'sensor_created', 'sensor_updated', 'alarm_triggered'
        ]
      },
      panels: {
        name: 'Paneles',
        types: [
          'message_sent', 'message_failed', 'status_change', 'configuration_updated'
        ]
      },
      cameras: {
        name: 'Cámaras',
        types: [
          'vehicle_detected', 'count_updated', 'connection_lost', 'connection_restored'
        ]
      },
      sensors: {
        name: 'Sensores',
        types: [
          'status_changed', 'battery_low', 'calibration_updated', 'error_detected'
        ]
      },
      alarms: {
        name: 'Alarmas',
        types: [
          'alarm_triggered', 'alarm_acknowledged', 'alarm_resolved', 'configuration_changed'
        ]
      }
    }
  },

  /**
   * Utilidades para procesamiento de logs
   */
  utils: {
    /**
     * Agrupar logs por fecha
     */
    groupByDate: (logs) => {
      if (!logs || !Array.isArray(logs)) return {}
      
      const grouped = {}
      logs.forEach(log => {
        const date = new Date(log.timestamp || log.created_at).toISOString().split('T')[0]
        if (!grouped[date]) {
          grouped[date] = []
        }
        grouped[date].push(log)
      })
      
      // Ordenar fechas descendente
      const sortedKeys = Object.keys(grouped).sort((a, b) => new Date(b) - new Date(a))
      const sortedGrouped = {}
      sortedKeys.forEach(key => {
        sortedGrouped[key] = grouped[key]
      })
      
      return sortedGrouped
    },

    /**
     * Agrupar logs por tipo de acción
     */
    groupByActionType: (logs) => {
      if (!logs || !Array.isArray(logs)) return {}
      
      const grouped = {}
      logs.forEach(log => {
        const actionType = log.action_type || log.event_type || 'unknown'
        if (!grouped[actionType]) {
          grouped[actionType] = []
        }
        grouped[actionType].push(log)
      })
      
      return grouped
    },

    /**
     * Filtrar logs por rango de fechas
     */
    filterByDateRange: (logs, startDate, endDate) => {
      if (!logs || !Array.isArray(logs)) return []
      
      const start = new Date(startDate)
      const end = new Date(endDate)
      end.setHours(23, 59, 59, 999) // Incluir todo el día final
      
      return logs.filter(log => {
        const logDate = new Date(log.timestamp || log.created_at)
        return logDate >= start && logDate <= end
      })
    },

    /**
     * Obtener estadísticas de logs
     */
    getLogsStatistics: (logs) => {
      if (!logs || !Array.isArray(logs)) {
        return {
          total: 0,
          byType: {},
          byDate: {},
          mostActive: null
        }
      }

      const byType = {}
      const byDate = {}
      const byUser = {}

      logs.forEach(log => {
        // Por tipo
        const type = log.action_type || log.event_type || 'unknown'
        byType[type] = (byType[type] || 0) + 1

        // Por fecha
        const date = new Date(log.timestamp || log.created_at).toISOString().split('T')[0]
        byDate[date] = (byDate[date] || 0) + 1

        // Por usuario
        const userId = log.user_id || log.created_by
        if (userId) {
          byUser[userId] = (byUser[userId] || 0) + 1
        }
      })

      // Usuario más activo
      const mostActiveUserId = Object.keys(byUser).reduce((a, b) => byUser[a] > byUser[b] ? a : b, null)
      const mostActive = mostActiveUserId ? {
        userId: mostActiveUserId,
        count: byUser[mostActiveUserId]
      } : null

      return {
        total: logs.length,
        byType,
        byDate,
        byUser,
        mostActive
      }
    },

    /**
     * Formatear log para mostrar
     */
    formatLogForDisplay: (log) => {
      const timestamp = new Date(log.timestamp || log.created_at)
      const formattedTime = timestamp.toLocaleString()
      
      return {
        id: log.id,
        timestamp: formattedTime,
        type: log.action_type || log.event_type || 'unknown',
        message: log.message || log.description || 'Sin descripción',
        user: log.user_name || log.created_by_name || 'Sistema',
        resource: log.resource_type || 'unknown',
        resourceId: log.resource_id || log.parking_id || log.panel_id || null,
        severity: log.severity || 'info',
        details: log.details || {}
      }
    },

    /**
     * Exportar logs a CSV
     */
    exportToCSV: (logs) => {
      if (!logs || !Array.isArray(logs) || logs.length === 0) {
        return 'No hay datos para exportar'
      }

      const headers = ['Fecha/Hora', 'Tipo', 'Mensaje', 'Usuario', 'Recurso', 'Severidad']
      const csvContent = [
        headers.join(','),
        ...logs.map(log => {
          const formatted = logService.utils.formatLogForDisplay(log)
          return [
            `"${formatted.timestamp}"`,
            `"${formatted.type}"`,
            `"${formatted.message.replace(/"/g, '""')}"`,
            `"${formatted.user}"`,
            `"${formatted.resource}"`,
            `"${formatted.severity}"`
          ].join(',')
        })
      ].join('\n')

      return csvContent
    }
  }
}

export default logService
