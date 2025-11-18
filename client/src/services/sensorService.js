import api from './api'

const sensorService = {
  // ============================================================================
  // CRUD BÁSICO DE SENSORES (MEJORADO v4.2.0 CON FILTRADO POR PERMISOS)
  // ============================================================================
  
  /**
   * MEJORADO v4.2.0: Obtener todos los sensores del usuario
   * - Ahora filtra automáticamente por parkings accesibles
   * - Superadmin ve todos, usuario regular solo sensores de sus parkings
   */
  async getAllSensors(filters = {}) {
    try {
      const params = new URLSearchParams()
      if (filters.parking_id) params.append('parking_id', filters.parking_id)
      if (filters.sensor_type) params.append('sensor_type', filters.sensor_type)
      if (filters.is_active !== undefined) params.append('is_active', filters.is_active)
      // NUEVO v4.3.0: Buscar por serial_number (incluye sensores no accesibles)
      if (filters.search_serial) params.append('search_serial', filters.search_serial)
      
      const url = `/api/sensors${params.toString() ? `?${params.toString()}` : ''}`
      const response = await api.get(url)
      return response.data
    } catch (error) {
      console.error('Error obteniendo sensores:', error)
      throw error
    }
  },

  /**
   * NUEVO v4.3.0: Buscar un sensor específico por serial_number
   * Útil para encontrar sensores que no aparecen en el listado normal
   */
  async getSensorBySerial(serialNumber) {
    try {
      const response = await api.get(`/api/sensors/by-serial/${serialNumber}`)
      return response.data
    } catch (error) {
      if (error.response?.status === 404) {
        return null
      }
      console.error(`Error obteniendo sensor por serial ${serialNumber}:`, error)
      throw error
    }
  },

  async getSensor(sensorId) {
    try {
      const response = await api.get(`/api/sensors/${sensorId}`)
      return response.data
    } catch (error) {
      console.error(`Error obteniendo sensor ${sensorId}:`, error)
      throw error
    }
  },

  async createSensor(sensorData) {
    try {
      const response = await api.post('/api/sensors', sensorData)
      return response.data
    } catch (error) {
      console.error('Error creando sensor:', error)
      throw error
    }
  },

  async updateSensor(sensorId, sensorData) {
    try {
      const response = await api.put(`/api/sensors/${sensorId}`, sensorData)
      return response.data
    } catch (error) {
      console.error(`Error actualizando sensor ${sensorId}:`, error)
      throw error
    }
  },

  async deleteSensor(sensorId) {
    try {
      const response = await api.delete(`/api/sensors/${sensorId}`)
      return response.data
    } catch (error) {
      console.error(`Error eliminando sensor ${sensorId}:`, error)
      throw error
    }
  },

  // ============================================================================
  // GESTIÓN DE ESTADOS
  // ============================================================================

  async updateSensorStatus(sensorId, statusData) {
    try {
      const response = await api.put(`/api/sensors/${sensorId}/status`, statusData)
      return response.data
    } catch (error) {
      console.error(`Error actualizando estado del sensor ${sensorId}:`, error)
      throw error
    }
  },

  // ============================================================================
  // CONSULTAS Y RESÚMENES
  // ============================================================================

  async getSensorsSummary(parkingId = null) {
    try {
      const url = parkingId ? `/api/sensors/summary?parking_id=${parkingId}` : '/api/sensors/summary'
      const response = await api.get(url)
      return response.data
    } catch (error) {
      console.error('Error obteniendo resumen de sensores:', error)
      throw error
    }
  },

  async getCompleteStatus(filters = {}) {
    try {
      const params = new URLSearchParams()
      if (filters.parking_id) params.append('parking_id', filters.parking_id)
      if (filters.sensor_type) params.append('sensor_type', filters.sensor_type)
      
      const url = `/api/sensors/status/complete${params.toString() ? `?${params.toString()}` : ''}`
      const response = await api.get(url)
      return response.data
    } catch (error) {
      console.error('Error obteniendo estado completo de sensores:', error)
      throw error
    }
  },

  /**
   * MEJORADO v4.2.0: Obtener estado agrupado filtrado por permisos
   */
  async getGroupedStatus() {
    try {
      const response = await api.get('/api/sensors/status/grouped')
      return response.data
    } catch (error) {
      console.error('Error obteniendo datos agrupados de sensores:', error)
      throw error
    }
  },

  // ============================================================================
  // NUEVOS MÉTODOS v4.2.0: ENDPOINTS AGRUPADOS CON PERMISOS
  // ============================================================================

  /**
   * NUEVO v4.2.0: Obtener resumen personalizado del usuario
   */
  async getUserSensorsSummary() {
    try {
      const response = await api.get('/api/sensors/summary/user')
      return response.data
    } catch (error) {
      console.error('Error obteniendo resumen de sensores del usuario:', error)
      throw error
    }
  },

  /**
   * NUEVO v4.2.0: Obtener sensores por tipo específico
   */
  async getSensorsByType(sensorType) {
    try {
      const response = await api.get(`/api/sensors/type/${sensorType}/summary`)
      return response.data
    } catch (error) {
      console.error(`Error obteniendo sensores tipo ${sensorType}:`, error)
      throw error
    }
  },

  /**
   * NUEVO v4.2.0: Obtener dashboard personalizado de sensores
   */
  async getUserDashboard() {
    try {
      const response = await api.get('/api/dashboard/user/sensors')
      return response.data
    } catch (error) {
      console.error('Error obteniendo dashboard de sensores del usuario:', error)
      throw error
    }
  },

  /**
   * NUEVO v4.2.0: Obtener resumen de un parking específico
   */
  async getParkingSummary(parkingId) {
    try {
      const response = await api.get(`/api/parkings/${parkingId}/sensors/summary`)
      return response.data
    } catch (error) {
      if (error.response?.status === 403) {
        console.warn(`Sin permisos para sensores del parking ${parkingId}`)
        return null
      }
      console.error(`Error obteniendo resumen del parking ${parkingId}:`, error)
      throw error
    }
  },

  // ============================================================================
  // UTILIDADES Y CONSTANTES
  // ============================================================================

  getSensorTypes() {
    return [
      { value: 'PMR', label: 'PMR', color: 'blue' },
      { value: 'Electrico', label: 'Eléctrico', color: 'green' },
      { value: 'Caravanas', label: 'Caravanas', color: 'orange' },
      { value: 'Emergencias', label: 'Emergencias', color: 'red' },
      { value: 'Policia', label: 'Policía', color: 'purple' },
      { value: 'Otros', label: 'Otros', color: 'gray' }
    ]
  },

  getSensorStatuses() {
    return [
      { value: 'free', label: 'Libre', color: 'green', icon: '🟢' },
      { value: 'busy', label: 'Ocupado', color: 'red', icon: '🔴' },
      { value: 'error', label: 'Error', color: 'yellow', icon: '⚠️' },
      { value: 'unknown', label: 'Desconocido', color: 'gray', icon: '❓' },
      { value: 'notcalib', label: 'Sin calibrar', color: 'purple', icon: '🔧' }
    ]
  },

  getManufacturers() {
    return [
      { value: 'Fleximodo', label: 'Fleximodo' }
    ]
  },

  // Utilidades para formateo
  formatSensorType(type) {
    const types = this.getSensorTypes()
    const found = types.find(t => t.value === type)
    return found ? found.label : type
  },

  formatSensorStatus(status) {
    const statuses = this.getSensorStatuses()
    const found = statuses.find(s => s.value === status)
    return found ? found.label : status
  },

  getSensorTypeColor(type) {
    const types = this.getSensorTypes()
    const found = types.find(t => t.value === type)
    return found ? found.color : 'gray'
  },

  getSensorStatusColor(status) {
    const statuses = this.getSensorStatuses()
    const found = statuses.find(s => s.value === status)
    return found ? found.color : 'gray'
  },

  getSensorStatusIcon(status) {
    const statuses = this.getSensorStatuses()
    const found = statuses.find(s => s.value === status)
    return found ? found.icon : '❓'
  },

  // ============================================================================
  // ESTADÍSTICAS PARA DASHBOARD
  // ============================================================================

  async getSensorStats() {
    try {
      const response = await api.get('/api/sensors/stats')
      return response.data
    } catch (error) {
      console.error('Error obteniendo estadísticas de sensores:', error)
      throw error
    }
  },

  async getDashboardComplete() {
    try {
      const response = await api.get('/api/dashboard/complete')
      return response.data
    } catch (error) {
      console.error('Error obteniendo datos completos del dashboard:', error)
      throw error
    }
  }
}

export default sensorService
