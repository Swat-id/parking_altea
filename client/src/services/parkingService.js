import api from './api'

export const parkingService = {
  /**
   * Obtener todos los parkings
   */
  getAllParkings: async () => {
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
  getParking: async (parkingId) => {
    try {
      const response = await api.get(`/parking/${parkingId}`)
      return response.data
    } catch (error) {
      console.error('Error obteniendo parking:', error)
      throw error
    }
  },

  /**
   * Actualizar ocupación de un parking
   */
  updateOccupancy: async (parkingId, occupancy) => {
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
  updateConfig: async (parkingId, config) => {
    try {
      const response = await api.post(`/parking/${parkingId}/config`, config)
      return response.data
    } catch (error) {
      console.error('Error actualizando configuración:', error)
      throw error
    }
  },

  /**
   * Enviar mensaje a todos los paneles de un parking
   */
  sendMessage: async (parkingId, messageData) => {
    try {
      const response = await api.post(`/parking/${parkingId}/message`, messageData)
      return response.data
    } catch (error) {
      console.error('Error enviando mensaje:', error)
      throw error
    }
  },

  /**
   * Obtener estadísticas de un parking
   */
  getStatistics: async (parkingId, days = 7) => {
    try {
      const response = await api.get(`/parking/${parkingId}/statistics?days=${days}`)
      return response.data
    } catch (error) {
      console.error('Error obteniendo estadísticas:', error)
      throw error
    }
  },

  /**
   * Obtener historial de ocupación de un parking
   */
  getHistory: async (parkingId, limit = 100) => {
    try {
      const response = await api.get(`/parking/${parkingId}/history?limit=${limit}`)
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