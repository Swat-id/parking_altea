import api from './api'

const windowService = {
  /**
   * Asignar parking o grupo de sensores a una ventana
   * @param {number} panelId - ID del panel
   * @param {number} windowId - ID de la ventana (0-15)
   * @param {number} parkingId - ID del parking
   * @param {string|null} sensorType - Tipo de sensor ('PMR', 'Electrico', 'Caravanas', etc.) o null para parking general
   * @param {string|null} textoFijoPrevio - Texto fijo previo para sensores (ej: "PMR", "ELÉCTRICO")
   */
  async assignParkingToWindow(panelId, windowId, parkingId, sensorType = null, textoFijoPrevio = null) {
    try {
      const response = await api.post(
        `/api/v1/panels/${panelId}/windows/${windowId}/assign`,
        {
          parking_id: parkingId,
          sensor_type: sensorType,
          texto_fijo_previo: textoFijoPrevio
        }
      )
      return response.data
    } catch (error) {
      console.error('Error asignando parking a ventana:', error)
      throw error
    }
  },

  /**
   * Eliminar asignación de parking/sensor de una ventana
   * @param {number} panelId - ID del panel
   * @param {number} windowId - ID de la ventana
   * @param {number} parkingId - ID del parking
   * @param {string|null} sensorType - Tipo de sensor o null
   */
  async unassignParkingFromWindow(panelId, windowId, parkingId, sensorType = null) {
    try {
      const response = await api.delete(
        `/api/v1/panels/${panelId}/windows/${windowId}/unassign`,
        {
          data: {
            parking_id: parkingId,
            sensor_type: sensorType
          }
        }
      )
      return response.data
    } catch (error) {
      console.error('Error eliminando asignación:', error)
      throw error
    }
  },

  /**
   * Obtener todas las asignaciones de ventanas de un panel
   * @param {number} panelId - ID del panel
   */
  async getWindowAssignments(panelId) {
    try {
      const response = await api.get(`/api/v1/panels/${panelId}/windows`)
      return response.data
    } catch (error) {
      console.error('Error obteniendo asignaciones de ventanas:', error)
      throw error
    }
  },

  /**
   * Obtener todas las ventanas asignadas a un parking
   * @param {number} parkingId - ID del parking
   */
  async getParkingWindows(parkingId) {
    try {
      const response = await api.get(`/api/v1/parkings/${parkingId}/windows`)
      return response.data
    } catch (error) {
      console.error('Error obteniendo ventanas del parking:', error)
      throw error
    }
  },

  /**
   * Obtener tipos de sensores disponibles en un parking
   * @param {number} parkingId - ID del parking
   */
  async getParkingSensorTypes(parkingId) {
    try {
      const response = await api.get(`/api/v1/parkings/${parkingId}/sensor-types`)
      return response.data.sensor_types || []
    } catch (error) {
      console.error('Error obteniendo tipos de sensores:', error)
      throw error
    }
  },

  /**
   * Actualizar configuración de rotación para una ventana
   * @param {number} parkingId - ID del parking
   * @param {number} panelId - ID del panel
   * @param {number} windowId - ID de la ventana
   * @param {object} config - Configuración (rotation_enabled, rotation_order, refresh_time_seconds, company_id)
   */
  async updateWindowConfig(parkingId, panelId, windowId, config) {
    try {
      const response = await api.put(
        `/api/v1/parkings/${parkingId}/panels/${panelId}/windows/${windowId}/config`,
        config
      )
      return response.data
    } catch (error) {
      console.error('Error actualizando configuración de ventana:', error)
      throw error
    }
  },

  /**
   * Obtener configuración de rotación de una ventana
   * @param {number} parkingId - ID del parking
   * @param {number} panelId - ID del panel
   * @param {number} windowId - ID de la ventana
   * @param {number|null} companyId - ID de empresa (para superadmin) o null
   */
  async getWindowConfig(parkingId, panelId, windowId, companyId = null) {
    try {
      const params = companyId ? { company_id: companyId } : {}
      const response = await api.get(
        `/api/v1/parkings/${parkingId}/panels/${panelId}/windows/${windowId}/config`,
        { params }
      )
      return response.data
    } catch (error) {
      if (error.response?.status === 404) {
        return null // Configuración no encontrada
      }
      console.error('Error obteniendo configuración de ventana:', error)
      throw error
    }
  },

  /**
   * Obtener contenido actual para una ventana (según rotación)
   * @param {number} panelId - ID del panel
   * @param {number} windowId - ID de la ventana
   */
  async getWindowContent(panelId, windowId) {
    try {
      const response = await api.get(`/api/v1/panels/${panelId}/windows/${windowId}/content`)
      return response.data
    } catch (error) {
      if (error.response?.status === 404) {
        return null // No hay contenido asignado
      }
      console.error('Error obteniendo contenido de ventana:', error)
      throw error
    }
  },

  /**
   * Obtener próximos cambios programados para una ventana
   * @param {number} panelId - ID del panel
   * @param {number} windowId - ID de la ventana (0-15)
   */
  async getWindowNextChanges(panelId, windowId) {
    try {
      const response = await api.get(
        `/api/v1/panels/${panelId}/windows/${windowId}/next-changes`
      )
      return response.data
    } catch (error) {
      console.error('Error obteniendo próximos cambios:', error)
      throw error
    }
  },

  /**
   * Forzar actualización de un panel Tipo 4
   * @param {number} panelId - ID del panel
   */
  async updatePanelType4(panelId) {
    try {
      const response = await api.post(
        `/api/v1/panels/${panelId}/update-type4`
      )
      return response.data
    } catch (error) {
      console.error('Error actualizando panel Tipo 4:', error)
      throw error
    }
  }
}

export default windowService

