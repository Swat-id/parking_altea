import api from './api'

const parkingService = {
  /**
   * Obtener todos los parkings
   */
  async getParkings() {
    try {
      const response = await api.get('/api/parkings')
      return response.data
    } catch (error) {
      console.error('Error obteniendo parkings:', error)
      throw error
    }
  },

  /**
   * Obtener parkings del usuario autenticado
   */
  async getUserParkings() {
    try {
      const response = await api.get('/api/user/parkings')
      return response.data
    } catch (error) {
      console.error('Error obteniendo parkings del usuario:', error)
      throw error
    }
  },

  /**
   * Obtener un parking específico
   */
  async getParking(id) {
    try {
      const response = await api.get(`/parking/${id}`)
      return response.data
    } catch (error) {
      console.error('Error obteniendo parking:', error)
      throw error
    }
  },

  /**
   * Actualizar ocupación de un parking
   */
  async updateOccupancy(parkingId, occupancy) {
    try {
      const response = await api.post(`/parking/${parkingId}/occupancy`, { occupancy })
      return response.data
    } catch (error) {
      console.error('Error actualizando ocupación:', error)
      throw error
    }
  },

  /**
   * Actualizar configuración de un parking
   */
  async updateConfig(parkingId, config) {
    try {
      const response = await api.post(`/parking/${parkingId}/config`, config)
      return response.data
    } catch (error) {
      console.error('Error actualizando configuración:', error)
      throw error
    }
  },

  /**
   * Actualizar cámaras de un parking
   */
  async updateCameras(parkingId, cameras) {
    try {
      const response = await api.put(`/parking/${parkingId}/cameras`, { cameras })
      return response.data
    } catch (error) {
      console.error('Error actualizando cámaras:', error)
      throw error
    }
  },

  /**
   * Enviar mensaje a un parking
   */
  async sendMessage(parkingId, message) {
    try {
      const response = await api.post(`/parking/${parkingId}/message`, message)
      return response.data
    } catch (error) {
      console.error('Error enviando mensaje:', error)
      throw error
    }
  },

  /**
   * Obtener estadísticas de un parking
   */
  async getStatistics(parkingId) {
    try {
      const response = await api.get(`/parking/${parkingId}/statistics`)
      return response.data
    } catch (error) {
      console.error('Error obteniendo estadísticas:', error)
      throw error
    }
  },

  /**
   * Obtener historial de ocupación de un parking
   */
  async getHistory(parkingId) {
    try {
      const response = await api.get(`/parking/${parkingId}/history`)
      return response.data
    } catch (error) {
      console.error('Error obteniendo historial:', error)
      throw error
    }
  },

  /**
   * Obtener mensajes programados de un parking
   */
  getScheduledMessages: async (parkingId) => {
    try {
      const response = await api.get(`/parking/${parkingId}/message`)
      return response.data
    } catch (error) {
      console.error('Error obteniendo mensajes programados:', error)
      throw error
    }
  },

  /**
   * Eliminar mensaje programado
   */
  deleteScheduledMessage: async (parkingId, messageId) => {
    try {
      const response = await api.delete(`/parking/${parkingId}/message`, {
        data: { message_id: messageId }
      })
      return response.data
    } catch (error) {
      console.error('Error eliminando mensaje programado:', error)
      throw error
    }
  },

  /**
   * Crear un nuevo parking
   */
  async createParking(parkingData) {
    try {
      const response = await api.post('/api/parkings', parkingData)
      return response.data
    } catch (error) {
      console.error('Error creando parking:', error)
      throw error
    }
  },

  /**
   * Editar información general de un parking
   */
  async editParking(parkingId, parkingData) {
    try {
      const response = await api.put(`/parkings/${parkingId}`, parkingData)
      return response.data
    } catch (error) {
      console.error('Error editando parking:', error)
      throw error
    }
  },

  /**
   * Eliminar un parking
   */
  async deleteParking(parkingId) {
    try {
      const response = await api.delete(`/parkings/${parkingId}`)
      return response.data
    } catch (error) {
      console.error('Error eliminando parking:', error)
      throw error
    }
  }
}

export default parkingService 