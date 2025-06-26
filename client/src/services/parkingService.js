import api from './api'

export const parkingService = {
  /**
   * Obtener todos los parkings
   */
  async getAllParkings() {
    try {
      const response = await api.get('/parkings')
      return response.data
    } catch (error) {
      console.error('Error obteniendo parkings:', error)
      throw error
    }
  },

  /**
   * Obtener un parking específico
   */
  async getParking(parkingId) {
    try {
      const response = await api.get(`/parking/${parkingId}`)
      return response.data
    } catch (error) {
      console.error('Error obteniendo parking:', error)
      throw error
    }
  },

  /**
   * Obtener parkings (alias para getAllParkings)
   */
  async getParkings() {
    return this.getAllParkings()
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
  }
} 