import api from './api'

export const scheduleService = {
  /**
   * Obtener todas las programaciones filtradas por permisos
   * - Superadmin ve todas las programaciones
   * - Usuario regular solo ve programaciones de sus parkings asignados
   */
  getAllSchedules: async (params = {}) => {
    try {
      const queryParams = new URLSearchParams()
      
      if (params.parking_id) queryParams.append('parking_id', params.parking_id)
      if (params.active_only !== undefined) queryParams.append('active_only', params.active_only)
      
      const url = `/api/schedules${queryParams.toString() ? `?${queryParams.toString()}` : ''}`
      const response = await api.get(url)
      return response.data
    } catch (error) {
      console.error('Error obteniendo programaciones:', error)
      throw error
    }
  },

  /**
   * Obtener programaciones de un parking específico
   * - Solo si el usuario tiene acceso al parking
   */
  getParkingSchedules: async (parkingId, activeOnly = true) => {
    try {
      const response = await api.get(`/api/parkings/${parkingId}/schedules?active_only=${activeOnly}`)
      return response.data
    } catch (error) {
      if (error.response?.status === 403) {
        console.warn(`Sin permisos para programaciones del parking ${parkingId}`)
        return { success: true, schedules: [] }
      }
      console.error('Error obteniendo programaciones del parking:', error)
      throw error
    }
  },

  /**
   * Crear nueva programación
   * - Solo superadmin puede crear programaciones
   */
  createSchedule: async (scheduleData) => {
    try {
      const response = await api.post('/api/schedules', scheduleData)
      return response.data
    } catch (error) {
      console.error('Error creando programación:', error)
      throw error
    }
  },

  /**
   * Actualizar programación existente
   * - Solo superadmin puede actualizar programaciones
   */
  updateSchedule: async (scheduleId, scheduleData) => {
    try {
      const response = await api.put(`/api/schedules/${scheduleId}`, scheduleData)
      return response.data
    } catch (error) {
      console.error('Error actualizando programación:', error)
      throw error
    }
  },

  /**
   * Eliminar programación
   * - Solo superadmin puede eliminar programaciones
   */
  deleteSchedule: async (scheduleId) => {
    try {
      const response = await api.delete(`/api/schedules/${scheduleId}`)
      return response.data
    } catch (error) {
      console.error('Error eliminando programación:', error)
      throw error
    }
  },

  /**
   * Activar/Desactivar programación
   */
  toggleSchedule: async (scheduleId, isActive) => {
    try {
      const response = await api.patch(`/api/schedules/${scheduleId}/toggle`, { is_active: isActive })
      return response.data
    } catch (error) {
      console.error('Error cambiando estado de programación:', error)
      throw error
    }
  },

  /**
   * Ejecutar programación manualmente
   */
  executeSchedule: async (scheduleId) => {
    try {
      const response = await api.post(`/api/schedules/${scheduleId}/execute`)
      return response.data
    } catch (error) {
      console.error('Error ejecutando programación:', error)
      throw error
    }
  },

  /**
   * Obtener logs de programaciones
   */
  getScheduleLogs: async (params = {}) => {
    try {
      const queryParams = new URLSearchParams()
      
      if (params.schedule_id) queryParams.append('schedule_id', params.schedule_id)
      if (params.parking_id) queryParams.append('parking_id', params.parking_id)
      if (params.limit) queryParams.append('limit', params.limit)
      
      const url = `/api/schedules/logs${queryParams.toString() ? `?${queryParams.toString()}` : ''}`
      const response = await api.get(url)
      return response.data
    } catch (error) {
      console.error('Error obteniendo logs de programaciones:', error)
      throw error
    }
  }
}

export default scheduleService
