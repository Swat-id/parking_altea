import api from './api'

export const panelService = {
  /**
   * Obtener todos los paneles
   */
  getAllPanels: async () => {
    try {
      const response = await api.get('/panels')
      return response.data
    } catch (error) {
      console.error('Error obteniendo paneles:', error)
      throw error
    }
  },

  /**
   * Obtener un panel específico
   */
  getPanel: async (panelId) => {
    try {
      const response = await api.get(`/panel/${panelId}`)
      return response.data
    } catch (error) {
      console.error('Error obteniendo panel:', error)
      throw error
    }
  },

  /**
   * Enviar mensaje a un panel específico
   */
  sendMessageToPanel: async (panelId, messageData) => {
    try {
      const response = await api.post(`/panel/${panelId}/message`, messageData)
      return response.data
    } catch (error) {
      console.error('Error enviando mensaje al panel:', error)
      throw error
    }
  },

  /**
   * Probar comunicación con un panel
   */
  testPanel: async (panelId) => {
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
  }
} 