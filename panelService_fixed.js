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
      const response = await api.get(`/panels?parking_id=${parkingId}`)
      return response.data
    } catch (error) {
      console.error('Error obteniendo paneles del parking:', error)
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
      
      // Usar la API del backend en lugar de llamar directamente al servicio Java
      const response = await api.post(`/panel/${panelId}/message`, {
        message: messageData.message,
        duration: messageData.duration,
        color: messageData.color || 1,
        fontSize: 2,
        showEffect: 1
      })
      
      return {
        success: response.data.success || false,
        message: response.data.message || 'Mensaje enviado',
        panel_id: panelId,
        panel_name: panel.name,
        panel_ip: panel.ip_address,
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
      const response = await api.post(`/panel/${panelId}/message`, message)
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
      
      // Usar la API del backend para enviar mensaje de prueba
      const response = await api.post(`/panel/${panelId}/test`, {
        message: 'PRUEBA',
        color: 2, // Verde para prueba
        fontSize: 2,
        showEffect: 1
      })
      
      return {
        success: response.data.success || false,
        message: response.data.message || 'Prueba completada',
        panel_id: panelId,
        panel_name: panel.name,
        panel_ip: panel.ip_address,
        responseTime: response.data.responseTime || 0
      }
    } catch (error) {
      console.error('Error probando panel:', error)
      throw error
    }
  },

  getPanelStatus: async (panelId) => {
    try {
      const response = await api.get(`/panel/${panelId}/status`)
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
      // Usar el endpoint del backend para obtener estado de paneles
      const response = await api.get('/panels')
      if (!response.ok) {
        throw new Error(`Error del servicio: ${response.status}`)
      }
      return await response.json()
    } catch (error) {
      console.error('Error obteniendo estado de paneles:', error)
      throw error
    }
  },

  async sendOccupancyToPanel(panelId, occupancyData) {
    try {
      const panels = await this.getAllPanels()
      const panel = panels.find(p => p.id === panelId)
      if (!panel) {
        throw new Error('Panel no encontrado')
      }
      
      // Usar el nuevo servicio para enviar ocupación
      const response = await fetch('http://157.180.91.63:5656/sendMulti', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ip: panel.ip_address,
          itemNum: 1,
          texts: [occupancyData.status || 'LLIURE'],
          colors: [occupancyData.color || 2], // Verde por defecto
          fontSizes: [2],
          showEffects: [1]
        })
      })
      
      if (!response.ok) {
        throw new Error(`Error del servicio: ${response.status}`)
      }
      
      const result = await response.json()
      return {
        success: result.success || false,
        message: result.message || 'Ocupación enviada',
        panel_id: panelId,
        panel_name: panel.name,
        panel_ip: panel.ip_address
      }
    } catch (error) {
      console.error('Error enviando ocupación al panel:', error)
      throw error
    }
  },

  async broadcastMessage(message) {
    try {
      // Obtener todos los paneles
      const panels = await this.getAllPanels()
      
      // Enviar mensaje a todos los paneles
      const results = []
      for (const panel of panels) {
        try {
          const response = await fetch('http://157.180.91.63:5656/sendMulti', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              ip: panel.ip_address,
              itemNum: 1,
              texts: [message],
              colors: [1], // Rojo para broadcast
              fontSizes: [2],
              showEffects: [1]
            })
          })
          
          if (response.ok) {
            const result = await response.json()
            results.push({
              panel_id: panel.id,
              panel_name: panel.name,
              panel_ip: panel.ip_address,
              success: true,
              message: result.message || 'Mensaje enviado'
            })
          } else {
            results.push({
              panel_id: panel.id,
              panel_name: panel.name,
              panel_ip: panel.ip_address,
              success: false,
              message: `Error: ${response.status}`
            })
          }
        } catch (error) {
          results.push({
            panel_id: panel.id,
            panel_name: panel.name,
            panel_ip: panel.ip_address,
            success: false,
            message: error.message
          })
        }
      }
      
      return {
        success: results.some(r => r.success),
        results: results,
        total: results.length,
        successful: results.filter(r => r.success).length
      }
    } catch (error) {
      console.error('Error enviando broadcast:', error)
      throw error
    }
  }
} 