import api from './api'

export const authService = {
  async login(email, password) {
    try {
      const response = await api.post('/auth/login', { email, password })
      return response.data
    } catch (error) {
      console.error('Login error:', error)
      throw error
    }
  },

  async register(userData) {
    try {
      const response = await api.post('/auth/register', userData)
      return response.data
    } catch (error) {
      console.error('Register error:', error)
      throw error
    }
  },

  async updatePassword(currentPassword, newPassword) {
    try {
      const response = await api.put('/auth/password', {
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
      const response = await api.get('/auth/permissions')
      return response.data
    } catch (error) {
      console.error('Get permissions error:', error)
      throw error
    }
  },

  async getUserParkings() {
    try {
      const response = await api.get('/user/parkings')
      return response.data
    } catch (error) {
      console.error('Get user parkings error:', error)
      throw error
    }
  },

  async getUserParking(id) {
    try {
      const response = await api.get(`/user/parking/${id}`)
      return response.data
    } catch (error) {
      console.error('Get user parking error:', error)
      throw error
    }
  }
} 