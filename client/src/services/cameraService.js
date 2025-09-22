import api from './api';

const cameraService = {
  /**
   * Obtener cámaras de un parking específico
   */
  async getParkingCameras(parkingId) {
    try {
      const response = await api.get(`/api/parkings/${parkingId}/cameras`);
      return response.data;
    } catch (error) {
      console.error('Error obteniendo cámaras del parking:', error);
      throw error;
    }
  },

  /**
   * Obtener todas las cámaras del usuario autenticado
   */
  async getUserCameras() {
    try {
      const response = await api.get('/api/user/cameras');
      return response.data;
    } catch (error) {
      console.error('Error obteniendo cámaras del usuario:', error);
      throw error;
    }
  },

  /**
   * Obtener todas las cámaras (público)
   */
  async getCameras() {
    try {
      const response = await api.get('/api/cameras');
      return response.data;
    } catch (error) {
      console.error('Error obteniendo cámaras:', error);
      throw error;
    }
  },

  /**
   * Actualizar línea de una cámara
   * @param {number} accessId - ID del acceso/cámara
   * @param {number} newLine - Nueva línea
   * @returns {Promise<Object>} Resultado de la actualización
   */
  async updateCameraLine(accessId, newLine) {
    try {
      const response = await api.put(`/api/access/${accessId}/line`, { line: newLine });
      return response.data;
    } catch (error) {
      console.error('Error actualizando línea de cámara:', error);
      throw error;
    }
  },

  /**
   * Obtener estado de todas las cámaras
   * @returns {Promise<Object>} Estado de todas las cámaras
   */
  async getAllCamerasStatus() {
    try {
      const response = await api.get('/api/cameras/status');
      return response.data;
    } catch (error) {
      console.error('Error obteniendo estado de cámaras:', error);
      throw error;
    }
  },

  /**
   * Verificar estado de una cámara por IP
   * @param {string} ip - IP de la cámara
   * @returns {Promise<boolean>} True si está online, false si está offline
   */
  async checkCameraStatus(ip) {
    try {
      // Usar un endpoint simple de ping o verificar conectividad
      const response = await api.get(`/api/cameras/status`);
      const camera = response.data.cameras.find(c => c.ip === ip);
      return camera ? camera.ping_status === 'ONLINE' : false;
    } catch (error) {
      console.error('Error verificando estado de cámara:', error);
      return false;
    }
  },

  /**
   * Obtener logs de cámaras con filtros avanzados (v2)
   * @param {Object} filters - Filtros para aplicar
   * @param {Object} pagination - Configuración de paginación
   * @returns {Promise<Object>} Logs paginados con metadatos
   */
  async getCameraLogsV2(filters = {}, pagination = {}) {
    try {
      const params = new URLSearchParams();
      
      // Filtros
      if (filters.parkingId) params.append('parking_id', filters.parkingId);
      if (filters.accessId) params.append('access_id', filters.accessId);
      if (filters.cameraIp) params.append('camera_ip', filters.cameraIp);
      if (filters.cameraName) params.append('camera_name', filters.cameraName);
      if (filters.status) params.append('status', filters.status);
      if (filters.dateFrom) params.append('date_from', filters.dateFrom);
      if (filters.dateTo) params.append('date_to', filters.dateTo);
      if (filters.timeFrom) params.append('time_from', filters.timeFrom);
      if (filters.timeTo) params.append('time_to', filters.timeTo);
      if (filters.hasChanges !== undefined) params.append('has_changes', filters.hasChanges);
      if (filters.errorOnly !== undefined) params.append('error_only', filters.errorOnly);
      
      // Ordenación
      if (filters.orderBy) params.append('order_by', filters.orderBy);
      if (filters.orderDirection) params.append('order_direction', filters.orderDirection);
      
      // Paginación
      if (pagination.page) params.append('page', pagination.page);
      if (pagination.perPage) params.append('per_page', pagination.perPage);
      
      const response = await api.get(`/api/camera-logs-v2?${params.toString()}`);
      return response.data;
    } catch (error) {
      console.error('Error obteniendo logs de cámaras v2:', error);
      throw error;
    }
  },

  /**
   * Obtener logs de cámaras (endpoint original)
   * @param {Object} filters - Filtros básicos
   * @returns {Promise<Array>} Array de logs
   */
  async getCameraLogs(filters = {}) {
    try {
      const params = new URLSearchParams();
      
      if (filters.parkingId) params.append('parking_id', filters.parkingId);
      if (filters.accessId) params.append('access_id', filters.accessId);
      if (filters.status) params.append('status', filters.status);
      if (filters.limit) params.append('limit', filters.limit);
      if (filters.offset) params.append('offset', filters.offset);
      
      const response = await api.get(`/api/camera/logs?${params.toString()}`);
      return response.data;
    } catch (error) {
      console.error('Error obteniendo logs de cámaras:', error);
      throw error;
    }
  },

  /**
   * Obtener estadísticas de logs de cámaras
   * @param {Object} filters - Filtros para estadísticas
   * @returns {Promise<Object>} Estadísticas de logs
   */
  async getCameraLogsStats(filters = {}) {
    try {
      const params = new URLSearchParams();
      
      if (filters.parkingId) params.append('parking_id', filters.parkingId);
      if (filters.days) params.append('days', filters.days);
      
      const response = await api.get(`/api/camera/logs/stats?${params.toString()}`);
      return response.data;
    } catch (error) {
      console.error('Error obteniendo estadísticas de logs:', error);
      throw error;
    }
  },

  /**
   * Formatear timestamp para mostrar
   * @param {string} timestamp - Timestamp ISO
   * @returns {string} Timestamp formateado
   */
  formatTimestamp(timestamp) {
    if (!timestamp) return 'Nunca';
    
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) return 'Ahora mismo';
    if (diffMins < 60) return `Hace ${diffMins} min`;
    if (diffHours < 24) return `Hace ${diffHours}h ${diffMins % 60}min`;
    if (diffDays < 7) return `Hace ${diffDays} días`;
    
    return date.toLocaleDateString('es-ES', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  },

  /**
   * Obtener color de estado para UI
   * @param {string} status - Estado de la cámara
   * @returns {string} Clase CSS para el color
   */
  getStatusColor(status) {
    switch (status) {
      case 'ONLINE':
        return 'text-green-600 bg-green-100';
      case 'OFFLINE':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  },

  /**
   * Obtener icono de estado para UI
   * @param {string} status - Estado de la cámara
   * @returns {string} Icono
   */
  getStatusIcon(status) {
    switch (status) {
      case 'ONLINE':
        return '🟢';
      case 'OFFLINE':
        return '🔴';
      default:
        return '🟡';
    }
      }
};

export default cameraService 