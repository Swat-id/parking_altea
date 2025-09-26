import api from './api'

const parkingService = {
  /**
   * Obtener todos los parkings (FILTRADO AUTOMÁTICAMENTE POR PERMISOS)
   * - Superadmin: ve todos los parkings
   * - Usuario regular: solo parkings asignados
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
   * Alias para getAllParkings (compatibilidad)
   */
  getAllParkings() {
    return this.getParkings()
  },

  /**
   * Obtener parkings del usuario con información de permisos
   * NUEVO: Usa endpoint específico que ya filtra por usuario
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
   * Obtener un parking específico por ID
   * - Solo accesible si el usuario tiene permisos
   */
  async getParking(parkingId) {
    try {
      const response = await api.get(`/api/parkings/${parkingId}`)
      return response.data
    } catch (error) {
      if (error.response?.status === 403) {
        console.warn(`Sin permisos para acceder al parking ${parkingId}`)
      }
      throw error
    }
  },

  /**
   * Obtener estado de parkings (FILTRADO POR PERMISOS)
   */
  async getParkingsStatus() {
    try {
      const response = await api.get('/api/parkings/status')
      return response.data
    } catch (error) {
      console.error('Error obteniendo estado de parkings:', error)
      throw error
    }
  },

  /**
   * Crear nuevo parking (solo superadmin)
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
   * Actualizar parking existente (solo si tiene permisos)
   */
  async updateParking(parkingId, parkingData) {
    try {
      const response = await api.put(`/api/parkings/${parkingId}`, parkingData)
      return response.data
    } catch (error) {
      console.error('Error actualizando parking:', error)
      throw error
    }
  },

  /**
   * Eliminar parking (solo superadmin)
   */
  async deleteParking(parkingId) {
    try {
      const response = await api.delete(`/api/parkings/${parkingId}`)
      return response.data
    } catch (error) {
      console.error('Error eliminando parking:', error)
      throw error
    }
  },

  /**
   * Obtener estadísticas de un parking específico
   * - Solo si el usuario tiene acceso al parking
   */
  async getParkingStatistics(parkingId, days = 7) {
    try {
      const response = await api.get(`/api/parkings/${parkingId}/statistics?days=${days}`)
      return response.data
    } catch (error) {
      if (error.response?.status === 403) {
        console.warn(`Sin permisos para estadísticas del parking ${parkingId}`)
      }
      throw error
    }
  },

  /**
   * Obtener ocupación histórica de un parking
   */
  async getParkingOccupancy(parkingId, params = {}) {
    try {
      const queryParams = new URLSearchParams()
      if (params.startDate) queryParams.append('start_date', params.startDate)
      if (params.endDate) queryParams.append('end_date', params.endDate)
      if (params.interval) queryParams.append('interval', params.interval)
      
      const url = `/api/parkings/${parkingId}/occupancy${queryParams.toString() ? `?${queryParams.toString()}` : ''}`
      const response = await api.get(url)
      return response.data
    } catch (error) {
      console.error('Error obteniendo ocupación del parking:', error)
      throw error
    }
  },

  /**
   * Obtener configuración de alarmas de un parking
   */
  async getParkingAlarms(parkingId) {
    try {
      const response = await api.get(`/api/parkings/${parkingId}/alarms`)
      return response.data
    } catch (error) {
      if (error.response?.status === 403) {
        console.warn(`Sin permisos para alarmas del parking ${parkingId}`)
      }
      throw error
    }
  },

  /**
   * NUEVO v4.2.0: Obtener resumen de sensores de un parking
   * - Usa el nuevo endpoint agrupado
   */
  async getParkingSensorsSummary(parkingId) {
    try {
      const response = await api.get(`/api/parkings/${parkingId}/sensors/summary`)
      return response.data
    } catch (error) {
      if (error.response?.status === 403) {
        console.warn(`Sin permisos para sensores del parking ${parkingId}`)
      }
      throw error
    }
  },

  /**
   * NUEVO v4.2.0: Obtener sensores detallados de un parking
   */
  async getParkingSensorsDetailed(parkingId, filters = {}) {
    try {
      const params = new URLSearchParams()
      if (filters.sensor_type) params.append('sensor_type', filters.sensor_type)
      if (filters.status) params.append('status', filters.status)
      
      const url = `/api/parkings/${parkingId}/sensors/detailed${params.toString() ? `?${params.toString()}` : ''}`
      const response = await api.get(url)
      return response.data
    } catch (error) {
      console.error('Error obteniendo sensores detallados del parking:', error)
      throw error
    }
  },

  /**
   * Utilidades para el frontend
   */
  utils: {
    /**
     * Verificar si el usuario tiene acceso a un parking específico
     */
    async hasAccessToParking(parkingId) {
      try {
        await api.get(`/api/parkings/${parkingId}`)
        return true
      } catch (error) {
        if (error.response?.status === 403) {
          return false
        }
        throw error
      }
    },

    /**
     * Filtrar lista de parkings por IDs accesibles
     */
    async filterAccessibleParkings(parkingIds) {
      const accessible = []
      for (const parkingId of parkingIds) {
        try {
          if (await this.hasAccessToParking(parkingId)) {
            accessible.push(parkingId)
          }
        } catch (error) {
          console.warn(`Error verificando acceso al parking ${parkingId}:`, error)
        }
      }
      return accessible
    },

    /**
     * Obtener solo parkings con sensores
     */
    async getParkingsWithSensors() {
      try {
        const parkings = await parkingService.getParkings()
        const parkingsWithSensors = []
        
        for (const parking of parkings) {
          try {
            const summary = await parkingService.getParkingSensorsSummary(parking.id)
            if (summary.totals.total_sensors > 0) {
              parkingsWithSensors.push({
                ...parking,
                sensors_count: summary.totals.total_sensors
              })
            }
          } catch (error) {
            // Si no tiene permisos o no tiene sensores, simplemente no lo incluimos
            continue
          }
        }
        
        return parkingsWithSensors
      } catch (error) {
        console.error('Error obteniendo parkings con sensores:', error)
        throw error
      }
    }
  }
}

export default parkingService