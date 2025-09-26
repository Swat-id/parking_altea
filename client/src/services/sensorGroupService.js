/**
 * Servicio para endpoints agrupados de sensores con control de permisos
 * v4.2.0 - Sistema de sensores agrupados por parking y tipo
 */

import api from './api'

export const sensorGroupService = {
  /**
   * Obtener resumen de sensores de un parking específico
   * @param {number} parkingId - ID del parking
   * @returns {Promise} Resumen agrupado por tipo de sensor
   */
  async getParkingSummary(parkingId) {
    try {
      const response = await api.get(`/api/parkings/${parkingId}/sensors/summary`)
      return response.data
    } catch (error) {
      console.error(`Error obteniendo resumen del parking ${parkingId}:`, error)
      throw error
    }
  },

  /**
   * Obtener resumen de sensores de todos los parkings del usuario
   * @returns {Promise} Resumen agrupado por parking y tipo
   */
  async getUserSummary() {
    try {
      const response = await api.get('/api/sensors/summary/user')
      return response.data
    } catch (error) {
      console.error('Error obteniendo resumen del usuario:', error)
      throw error
    }
  },

  /**
   * Obtener resumen de sensores de un tipo específico
   * @param {string} sensorType - Tipo de sensor (PMR, Electrico, etc.)
   * @returns {Promise} Resumen agrupado por parking
   */
  async getSensorTypeSummary(sensorType) {
    try {
      const response = await api.get(`/api/sensors/type/${sensorType}/summary`)
      return response.data
    } catch (error) {
      console.error(`Error obteniendo resumen del tipo ${sensorType}:`, error)
      throw error
    }
  },

  /**
   * Obtener dashboard personalizado del usuario
   * @returns {Promise} Dashboard completo con alertas y estadísticas
   */
  async getUserDashboard() {
    try {
      const response = await api.get('/api/dashboard/user/sensors')
      return response.data
    } catch (error) {
      console.error('Error obteniendo dashboard del usuario:', error)
      throw error
    }
  },

  /**
   * Obtener estado agrupado de sensores (endpoint existente mejorado)
   * @returns {Promise} Estados agrupados por parking
   */
  async getGroupedStatus() {
    try {
      const response = await api.get('/api/sensors/status/grouped')
      return response.data
    } catch (error) {
      console.error('Error obteniendo estados agrupados:', error)
      throw error
    }
  },

  /**
   * Obtener estado completo de sensores (endpoint existente mejorado)
   * @param {Object} filters - Filtros opcionales
   * @param {number} filters.parking_id - ID del parking
   * @param {string} filters.sensor_type - Tipo de sensor
   * @returns {Promise} Estado completo de sensores
   */
  async getCompleteStatus(filters = {}) {
    try {
      const params = new URLSearchParams()
      
      if (filters.parking_id) {
        params.append('parking_id', filters.parking_id)
      }
      if (filters.sensor_type) {
        params.append('sensor_type', filters.sensor_type)
      }

      const response = await api.get(`/api/sensors/status/complete?${params}`)
      return response.data
    } catch (error) {
      console.error('Error obteniendo estado completo:', error)
      throw error
    }
  },

  /**
   * Obtener resumen general (endpoint existente mejorado)
   * @param {number} parkingId - ID del parking (opcional)
   * @returns {Promise} Resumen de sensores
   */
  async getSummary(parkingId = null) {
    try {
      const params = parkingId ? `?parking_id=${parkingId}` : ''
      const response = await api.get(`/api/sensors/summary${params}`)
      return response.data
    } catch (error) {
      console.error('Error obteniendo resumen:', error)
      throw error
    }
  },

  /**
   * Utilidades para procesar datos agrupados
   */
  utils: {
    /**
     * Calcular métricas globales de múltiples parkings
     * @param {Array} parkingsData - Array de datos de parkings
     * @returns {Object} Métricas globales
     */
    calculateGlobalMetrics(parkingsData) {
      const totals = parkingsData.reduce((acc, parking) => {
        Object.values(parking.sensor_types || {}).forEach(typeData => {
          acc.total_sensors += typeData.total || 0
          acc.total_free += typeData.free || 0
          acc.total_busy += typeData.busy || 0
          acc.total_error += typeData.error || 0
        })
        return acc
      }, { total_sensors: 0, total_free: 0, total_busy: 0, total_error: 0 })

      return {
        ...totals,
        occupancy_rate: totals.total_sensors > 0 
          ? Math.round((totals.total_busy / totals.total_sensors) * 100 * 100) / 100 
          : 0,
        health_score: totals.total_sensors > 0 
          ? Math.round(((totals.total_sensors - totals.total_error) / totals.total_sensors) * 100 * 100) / 100 
          : 0
      }
    },

    /**
     * Agrupar datos por tipo de sensor
     * @param {Array} parkingsData - Array de datos de parkings
     * @returns {Object} Datos agrupados por tipo
     */
    groupBySensorType(parkingsData) {
      const grouped = {}
      
      parkingsData.forEach(parking => {
        Object.entries(parking.sensor_types || {}).forEach(([sensorType, typeData]) => {
          if (!grouped[sensorType]) {
            grouped[sensorType] = {
              total: 0,
              free: 0,
              busy: 0,
              error: 0,
              parkings: []
            }
          }
          
          grouped[sensorType].total += typeData.total || 0
          grouped[sensorType].free += typeData.free || 0
          grouped[sensorType].busy += typeData.busy || 0
          grouped[sensorType].error += typeData.error || 0
          grouped[sensorType].parkings.push({
            parking_id: parking.parking_id,
            parking_name: parking.parking_name,
            ...typeData
          })
        })
      })

      // Calcular métricas para cada tipo
      Object.keys(grouped).forEach(sensorType => {
        const typeData = grouped[sensorType]
        typeData.occupancy_rate = typeData.total > 0 
          ? Math.round((typeData.busy / typeData.total) * 100 * 100) / 100 
          : 0
        typeData.health_score = typeData.total > 0 
          ? Math.round(((typeData.total - typeData.error) / typeData.total) * 100 * 100) / 100 
          : 0
      })

      return grouped
    },

    /**
     * Filtrar alertas por severidad
     * @param {Array} alerts - Array de alertas
     * @param {string} severity - Severidad a filtrar (high, medium, low)
     * @returns {Array} Alertas filtradas
     */
    filterAlertsBySeverity(alerts, severity) {
      return alerts.filter(alert => alert.severity === severity)
    },

    /**
     * Obtener parkings con mayor ocupación
     * @param {Array} parkingsData - Array de datos de parkings
     * @param {number} limit - Número máximo de resultados
     * @returns {Array} Parkings ordenados por ocupación
     */
    getMostOccupiedParkings(parkingsData, limit = 5) {
      return parkingsData
        .filter(parking => parking.occupancy_rate !== undefined)
        .sort((a, b) => b.occupancy_rate - a.occupancy_rate)
        .slice(0, limit)
    },

    /**
     * Obtener tipos de sensor disponibles
     * @param {Array} parkingsData - Array de datos de parkings
     * @returns {Array} Lista de tipos de sensor únicos
     */
    getAvailableSensorTypes(parkingsData) {
      const types = new Set()
      parkingsData.forEach(parking => {
        Object.keys(parking.sensor_types || {}).forEach(type => types.add(type))
      })
      return Array.from(types).sort()
    }
  }
}

export default sensorGroupService
