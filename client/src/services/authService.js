import api from './api'

export const authService = {
  async login(email, password) {
    try {
      const response = await api.post('/api/auth/login', { email, password })
      
      // Guardar token en localStorage
      if (response.data.token) {
        localStorage.setItem('token', response.data.token)
      }
      
      return response.data
    } catch (error) {
      console.error('Login error:', error)
      throw error
    }
  },

  async register(userData) {
    try {
      const response = await api.post('/api/auth/register', userData)
      return response.data
    } catch (error) {
      console.error('Register error:', error)
      throw error
    }
  },

  async updatePassword(currentPassword, newPassword) {
    try {
      const response = await api.put('/api/auth/password', {
        current_password: currentPassword,
        new_password: newPassword
      })
      return response.data
    } catch (error) {
      console.error('Update password error:', error)
      throw error
    }
  },

  async getPermissions() {
    try {
      const response = await api.get('/api/auth/permissions')
      return response.data
    } catch (error) {
      console.error('Get permissions error:', error)
      throw error
    }
  },

  async getUserParkings() {
    try {
      const response = await api.get('/api/user/parkings')
      return response.data
    } catch (error) {
      console.error('Get user parkings error:', error)
      throw error
    }
  },

  async getUserParking(id) {
    try {
      const response = await api.get(`/api/user/parking/${id}`)
      return response.data
    } catch (error) {
      console.error('Get user parking error:', error)
      throw error
    }
  },

  // Nuevas funciones para gestión de usuarios (solo superadmin)
  async getAllUsers() {
    try {
      const response = await api.get('/api/admin/users')
      return response.data
    } catch (error) {
      console.error('Get all users error:', error)
      throw error
    }
  },

  async getUserDetails(userId) {
    try {
      const response = await api.get(`/api/admin/users/${userId}`)
      return response.data
    } catch (error) {
      console.error('Get user details error:', error)
      throw error
    }
  },

  async createUser(userData) {
    try {
      const response = await api.post('/api/admin/users', userData)
      return response.data
    } catch (error) {
      console.error('Create user error:', error)
      throw error
    }
  },

  async updateUserRole(userId, role) {
    try {
      const response = await api.put(`/api/admin/users/${userId}/role`, { role })
      return response.data
    } catch (error) {
      console.error('Update user role error:', error)
      throw error
    }
  },

  async toggleUserStatus(userId) {
    try {
      const response = await api.post(`/api/admin/users/${userId}/toggle`)
      return response.data
    } catch (error) {
      console.error('Toggle user status error:', error)
      throw error
    }
  },

  async deleteUser(userId) {
    try {
      const response = await api.delete(`/api/admin/users/${userId}`)
      return response.data
    } catch (error) {
      console.error('Delete user error:', error)
      throw error
    }
  },

  async resetUserPassword(userId, newPassword) {
    try {
      const response = await api.put(`/api/admin/users/${userId}/password`, { new_password: newPassword })
      return response.data
    } catch (error) {
      console.error('Reset user password error:', error)
      throw error
    }
  },

  async assignUserResources(userId, resources) {
    try {
      const response = await api.post(`/api/admin/users/${userId}/assign`, resources)
      return response.data
    } catch (error) {
      console.error('Assign user resources error:', error)
      throw error
    }
  },

  // Funciones de utilidad
  getToken() {
    return localStorage.getItem('token')
  },

  removeToken() {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  },

  isTokenExpired(token) {
    if (!token) return true
    
    try {
      const payload = JSON.parse(atob(token.split('.')[1]))
      const currentTime = Date.now() / 1000
      return payload.exp < currentTime
    } catch (error) {
      console.error('Error parsing token:', error)
      return true
    }
  },

  // Verificar si el usuario tiene acceso a un recurso específico
  async checkResourceAccess(resourceType, resourceId) {
    try {
      const permissions = await this.getPermissions()
      if (permissions.success) {
        const { parking_ids, panel_ids, access_ids } = permissions.permissions
        
        switch (resourceType) {
          case 'parking':
            return parking_ids.includes(resourceId)
          case 'panel':
            return panel_ids.includes(resourceId)
          case 'access':
            return access_ids.includes(resourceId)
          default:
            return false
        }
      }
      return false
    } catch (error) {
      console.error('Check resource access error:', error)
      return false
    }
  }
} 