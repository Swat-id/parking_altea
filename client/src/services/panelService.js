import api from './api'

export const panelService = {
  /**
   * Obtener todos los paneles
   */
  async getAllPanels() {
    try {
      const response = await api.get('/panels')
      return response.data
    } catch (error) {
      console.error('Error obteniendo paneles:', error)
      throw error
    }
  },

  /**
   * Obtener paneles de un parking específico
   */
  async getParkingPanels(parkingId) {
    try {
      const response = await api.get(`/panels?parking_id=${parkingId}`)
      return response.data
    } catch (error) {
      console.error('Error obteniendo paneles del parking:', error)
      throw error
    }
  },

  /**
   * Enviar mensaje a un panel
   */
  async sendMessage(panelId, message) {
    try {
      const response = await api.post(`/panel/${panelId}/message`, message)
      return response.data
    } catch (error) {
      console.error('Error enviando mensaje al panel:', error)
      throw error
    }
  },

  /**
   * Probar conexión con un panel
   */
  async testPanel(panelId) {
    try {
      const response = await api.post(`/panel/${panelId}/test`)
      return response.data
    } catch (error) {
      console.error('Error probando panel:', error)
      throw error
    }
  },

  /**
   * Obtener estado de un panel
   */
  getPanelStatus: async (panelId) => {
    try {
      const response = await api.get(`/panel/${panelId}/status`)
      return response.data
    } catch (error) {
      console.error('Error obteniendo estado del panel:', error)
      throw error
    }
  },

  /**
   * Verificar el estado de todos los paneles mediante ping
   */
  async verifyAllPanels() {
    try {
      const response = await api.post('/panels/verify')
      return response.data
    } catch (error) {
      console.error('Error verificando paneles:', error)
      throw error
    }
  }
} 