import api from './api'

const panelService = {
    /**
     * Obtener todos los paneles (FILTRADO AUTOMÁTICAMENTE POR PERMISOS)
     * - Superadmin: ve todos los paneles
     * - Usuario regular: solo paneles de parkings asignados
     */
    async getAllPanels() {
        try {
            const response = await api.get('/api/user/panels')
            return response.data
        } catch (error) {
            console.error('Error obteniendo paneles:', error)
            throw error
        }
    },

    /**
     * Obtener paneles del usuario (FILTRADO POR PERMISOS)
     * - Usa endpoint que ya filtra por UserPanel assignments
     */
    async getUserPanels() {
        try {
            const response = await api.get('/api/user/panels')
            return response.data
        } catch (error) {
            console.error('Error obteniendo paneles del usuario:', error)
            throw error
        }
    },

    /**
     * Obtener paneles de un parking específico
     * - Solo si el usuario tiene acceso al parking
     */
    async getParkingPanels(parkingId) {
        try {
            const response = await api.get('/api/panels?parking_id=' + parkingId)
            return response.data
        } catch (error) {
            if (error.response?.status === 403) {
                console.warn(`Sin permisos para paneles del parking ${parkingId}`)
                return []
            }
            console.error('Error obteniendo paneles del parking:', error)
            throw error
        }
    },

    /**
     * Obtener un panel específico por ID
     * - Solo si el usuario tiene acceso al panel
     */
    async getPanel(panelId) {
        try {
            const response = await api.get(`/api/panels/${panelId}`)
            return response.data
        } catch (error) {
            if (error.response?.status === 403) {
                console.warn(`Sin permisos para acceder al panel ${panelId}`)
            }
            throw error
        }
    },

    /**
     * Actualizar tipo de panel
     * - Solo si el usuario tiene acceso al panel
     */
    async updatePanelType(panelId, panelTypeId) {
        try {
            const response = await api.put(`/api/panels/${panelId}/type`, {
                panel_type_id: panelTypeId
            })
            return response.data
        } catch (error) {
            console.error('Error actualizando tipo de panel:', error)
            throw error
        }
    },

    /**
     * Crear nuevo panel
     * - Solo si el usuario tiene acceso al parking de destino
     */
    async createPanel(panelData) {
        try {
            const response = await api.post('/api/panels', panelData)
            return response.data
        } catch (error) {
            console.error('Error creando panel:', error)
            throw error
        }
    },

    /**
     * Actualizar panel existente
     */
    async updatePanel(panelId, panelData) {
        try {
            const response = await api.put(`/api/panels/${panelId}`, panelData)
            return response.data
        } catch (error) {
            console.error('Error actualizando panel:', error)
            throw error
        }
    },

    /**
     * Eliminar panel
     */
    async deletePanel(panelId) {
        try {
            const response = await api.delete(`/api/panels/${panelId}`)
            return response.data
        } catch (error) {
            console.error('Error eliminando panel:', error)
            throw error
        }
    },

    /**
     * Obtener logs de mensajes de un panel
     * - Solo si el usuario tiene acceso al panel
     */
    async getPanelLogs(panelId, params = {}) {
        try {
            const queryParams = new URLSearchParams()
            if (params.startDate) queryParams.append('start_date', params.startDate)
            if (params.endDate) queryParams.append('end_date', params.endDate)
            if (params.limit) queryParams.append('limit', params.limit)
            
            const url = `/api/panels/${panelId}/logs${queryParams.toString() ? `?${queryParams.toString()}` : ''}`
            const response = await api.get(url)
            return response.data
        } catch (error) {
            if (error.response?.status === 403) {
                console.warn(`Sin permisos para logs del panel ${panelId}`)
                return []
            }
            console.error('Error obteniendo logs del panel:', error)
            throw error
        }
    },

    /**
     * Obtener estado actual de un panel
     */
    async getPanelStatus(panelId) {
        try {
            const response = await api.get(`/api/panels/${panelId}/status`)
            return response.data
        } catch (error) {
            if (error.response?.status === 403) {
                console.warn(`Sin permisos para estado del panel ${panelId}`)
            }
            throw error
        }
    },

    /**
     * Enviar mensaje a panel
     * - Solo si el usuario tiene acceso al panel
     */
    async sendMessage(panelId, messageData) {
        try {
            const response = await api.post(`/api/panels/${panelId}/message`, messageData)
            return response.data
        } catch (error) {
            console.error('Error enviando mensaje al panel:', error)
            throw error
        }
    },

    /**
     * Obtener programaciones de un panel
     */
    async getPanelSchedules(panelId) {
        try {
            const response = await api.get(`/api/panels/${panelId}/schedules`)
            return response.data
        } catch (error) {
            if (error.response?.status === 403) {
                console.warn(`Sin permisos para programaciones del panel ${panelId}`)
                return []
            }
            console.error('Error obteniendo programaciones del panel:', error)
            throw error
        }
    },

    /**
     * Crear programación para panel
     */
    async createPanelSchedule(panelId, scheduleData) {
        try {
            const response = await api.post(`/api/panels/${panelId}/schedules`, scheduleData)
            return response.data
        } catch (error) {
            console.error('Error creando programación del panel:', error)
            throw error
        }
    },

    /**
     * Verificar el estado de todos los paneles
     * - Realiza ping a todos los paneles y actualiza su estado
     */
    async verifyAllPanels() {
        try {
            const response = await api.post('/api/panels/verify')
            return response.data
        } catch (error) {
            console.error('Error verificando paneles:', error)
            throw error
        }
    },

    /**
     * Test de panel
     */
    async testPanel(panelId) {
        try {
            const response = await api.post(`/api/panels/${panelId}/test`)
            return response.data
        } catch (error) {
            console.error('Error en test de panel:', error)
            throw error
        }
    },

    /**
     * Validar mensaje de panel
     */
    async validatePanelMessage(panelId, messageData) {
        try {
            const response = await api.post(`/api/panels/${panelId}/validate`, messageData)
            return response.data
        } catch (error) {
            console.error('Error validando mensaje:', error)
            throw error
        }
    },

    /**
     * Descubrir device_id de un panel CPower via UDP
     * El device_id es necesario para el protocolo nuevo (CPower)
     */
    async discoverDeviceId(ip, panelId = null) {
        try {
            const response = await api.post('/api/panels/discover-device-id', { 
                ip, 
                panel_id: panelId 
            })
            return response.data
        } catch (error) {
            console.error('Error descubriendo device_id:', error)
            throw error
        }
    },

    /**
     * Descubrir y guardar device_id para un panel existente
     */
    async discoverAndSaveDeviceId(panelId) {
        try {
            const response = await api.post(`/api/panel/${panelId}/discover-device-id`)
            return response.data
        } catch (error) {
            console.error('Error descubriendo device_id para panel:', error)
            throw error
        }
    },

    /**
     * NUEVO v4.2.0: Obtener paneles agrupados por parking del usuario
     */
    async getUserPanelsGrouped() {
        try {
            // Obtener paneles del usuario
            const panels = await this.getUserPanels()
            
            // Agrupar por parking
            const grouped = {}
            panels.forEach(panel => {
                const parkingId = panel.parking_id
                const parkingName = panel.parking_name || `Parking ${parkingId}`
                
                if (!grouped[parkingId]) {
                    grouped[parkingId] = {
                        parking_id: parkingId,
                        parking_name: parkingName,
                        panels: []
                    }
                }
                
                grouped[parkingId].panels.push(panel)
            })
            
            return Object.values(grouped)
        } catch (error) {
            console.error('Error obteniendo paneles agrupados del usuario:', error)
            throw error
        }
    },

    /**
     * Utilidades para el frontend
     */
    utils: {
        /**
         * Verificar si el usuario tiene acceso a un panel específico
         */
        async hasAccessToPanel(panelId) {
            try {
                await api.get(`/api/panels/${panelId}`)
                return true
            } catch (error) {
                if (error.response?.status === 403) {
                    return false
                }
                throw error
            }
        },

        /**
         * Obtener paneles por tipo
         */
        async getPanelsByType(panelType) {
            try {
                const panels = await panelService.getAllPanels()
                return panels.filter(panel => panel.panel_type === panelType)
            } catch (error) {
                console.error('Error obteniendo paneles por tipo:', error)
                throw error
            }
        },

        /**
         * Obtener paneles activos del usuario
         */
        async getActivePanels() {
            try {
                const panels = await panelService.getAllPanels()
                return panels.filter(panel => panel.is_active === true)
            } catch (error) {
                console.error('Error obteniendo paneles activos:', error)
                throw error
            }
        },

        /**
         * Obtener estadísticas de paneles del usuario
         */
        async getPanelsStatistics() {
            try {
                const panels = await panelService.getAllPanels()
                
                const stats = {
                    total: panels.length,
                    active: panels.filter(p => p.is_active).length,
                    inactive: panels.filter(p => !p.is_active).length,
                    by_type: {},
                    by_parking: {}
                }
                
                // Agrupar por tipo
                panels.forEach(panel => {
                    const type = panel.panel_type || 'unknown'
                    stats.by_type[type] = (stats.by_type[type] || 0) + 1
                })
                
                // Agrupar por parking
                panels.forEach(panel => {
                    const parkingId = panel.parking_id
                    const parkingName = panel.parking_name || `Parking ${parkingId}`
                    if (!stats.by_parking[parkingId]) {
                        stats.by_parking[parkingId] = {
                            parking_name: parkingName,
                            count: 0
                        }
                    }
                    stats.by_parking[parkingId].count++
                })
                
                return stats
            } catch (error) {
                console.error('Error obteniendo estadísticas de paneles:', error)
                throw error
            }
        }
    }
}

export default panelService
