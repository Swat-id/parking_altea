import api from './api'

export const panelService = {
  async getAllPanels() {
    try {
      const response = await api.get('/panels')
      return response.data
    } catch (error) {
      console.error('Error obteniendo paneles:', error)
      throw error
    }
  },

  async getParkingPanels(parkingId) {
    try {
      const response = await api.get('/panels?parking_id=' + parkingId)
      return response.data
    } catch (error) {
      console.error('Error obteniendo paneles del parking:', error)
      throw error
    }
  },

  async updatePanelType(panelId, panelTypeId) {
    try {
      const response = await api.put('/panels/' + panelId + '/type', {
        panel_type_id: panelTypeId
      })
      return response.data
    } catch (error) {
      console.error('Error actualizando tipo de panel:', error)
      throw error
    }
  },

  async getPanelWithType(panelId) {
    try {
      const response = await api.get('/panels/' + panelId + '/with-type')
      return response.data
    } catch (error) {
      console.error('Error obteniendo panel con tipo:', error)
      throw error
    }
  },

  async sendMessageToPanel(panelId, messageData) {
    try {
      const panels = await this.getAllPanels()
      const panel = panels.find(p => p.id === panelId)
      if (!panel) {
        throw new Error('Panel no encontrado')
      }
      
      // Enviar mensaje usando el endpoint que maneja automáticamente el protocolo
      const response = await api.post('/panel/' + panelId + '/message', {
        message: messageData.message,
        duration: messageData.duration,
        color: messageData.color || 1,
        fontSize: messageData.fontSize || 2,
        showEffect: messageData.showEffect || 1,
        window: messageData.window || 1 // Para paneles con múltiples ventanas
      })
      
      return {
        success: response.data.success || false,
        message: response.data.message || 'Mensaje enviado',
        panel_id: panelId,
        panel_name: panel.name,
        panel_ip: panel.ip_address,
        panel_type: response.data.panel_type || 'unknown',
        protocol_used: response.data.protocol_used || 'unknown',
        message: messageData.message,
        duration: messageData.duration,
        responseTime: response.data.responseTime || 0
      }
    } catch (error) {
      console.error('Error enviando mensaje al panel:', error)
      throw error
    }
  },

  async sendMessage(panelId, message) {
    try {
      const response = await api.post('/panel/' + panelId + '/message', message)
      return response.data
    } catch (error) {
      console.error('Error enviando mensaje al panel:', error)
      throw error
    }
  },

  async testPanel(panelId) {
    try {
      const panels = await this.getAllPanels()
      const panel = panels.find(p => p.id === panelId)
      if (!panel) {
        throw new Error('Panel no encontrado')
      }
      
      const response = await api.post('/panel/' + panelId + '/test', {
        message: 'PRUEBA',
        color: 2,
        fontSize: 2,
        showEffect: 1
      })
      
      return {
        success: response.data.success || false,
        message: response.data.message || 'Prueba completada',
        panel_id: panelId,
        panel_name: panel.name,
        panel_ip: panel.ip_address,
        panel_type: response.data.panel_type || 'unknown',
        protocol_used: response.data.protocol_used || 'unknown',
        responseTime: response.data.responseTime || 0
      }
    } catch (error) {
      console.error('Error probando panel:', error)
      throw error
    }
  },

  async sendMultiWindowMessage(panelId, messages) {
    try {
      const panels = await this.getAllPanels()
      const panel = panels.find(p => p.id === panelId)
      if (!panel) {
        throw new Error('Panel no encontrado')
      }
      
      const response = await api.post('/panel/' + panelId + '/multi-message', {
        messages: messages // Array de mensajes para múltiples ventanas
      })
      
      return {
        success: response.data.success || false,
        message: response.data.message || 'Mensajes enviados',
        panel_id: panelId,
        panel_name: panel.name,
        panel_ip: panel.ip_address,
        panel_type: response.data.panel_type || 'unknown',
        protocol_used: response.data.protocol_used || 'unknown',
        responseTime: response.data.responseTime || 0
      }
    } catch (error) {
      console.error('Error enviando mensajes multi-ventana:', error)
      throw error
    }
  },

  getPanelStatus: async (panelId) => {
    try {
      const response = await api.get('/panel/' + panelId + '/status')
      return response.data
    } catch (error) {
      console.error('Error obteniendo estado del panel:', error)
      throw error
    }
  },

  async verifyAllPanels() {
    try {
      const response = await api.post('/panels/verify')
      return response.data
    } catch (error) {
      console.error('Error verificando paneles:', error)
      throw error
    }
  },

  async getPanelsStatus() {
    try {
      const response = await api.get('/panels')
      return response.data
    } catch (error) {
      console.error('Error obteniendo estado de paneles:', error)
      throw error
    }
  },

  async getPanelProtocolInfo(panelId) {
    try {
      const response = await api.get('/panel/' + panelId + '/protocol-info')
      return response.data
    } catch (error) {
      console.error('Error obteniendo información del protocolo:', error)
      throw error
    }
  }
} 