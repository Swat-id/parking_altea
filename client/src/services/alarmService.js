import api from './api';

class AlarmService {
  // Configuraciones de alarmas
  async getAlarmConfigurations() {
    try {
      const response = await api.get('/api/alarms/configurations');
      return response.data;
    } catch (error) {
      console.error('Error fetching alarm configurations:', error);
      throw error;
    }
  }

  async createAlarmConfiguration(config) {
    try {
      const response = await api.post('/api/alarms/configurations', config);
      return response.data;
    } catch (error) {
      console.error('Error creating alarm configuration:', error);
      throw error;
    }
  }

  async updateAlarmConfiguration(id, config) {
    try {
      const response = await api.put(`/api/alarms/configurations/${id}`, config);
      return response.data;
    } catch (error) {
      console.error('Error updating alarm configuration:', error);
      throw error;
    }
  }

  async deleteAlarmConfiguration(id) {
    try {
      const response = await api.delete(`/api/alarms/configurations/${id}`);
      return response.data;
    } catch (error) {
      console.error('Error deleting alarm configuration:', error);
      throw error;
    }
  }

  async getAlarmConfiguration(id) {
    try {
      const response = await api.get(`/api/alarms/configurations/${id}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching alarm configuration:', error);
      throw error;
    }
  }

  // Alarmas activas
  async getActiveAlarms() {
    try {
      const response = await api.get('/api/alarms');
      return response.data;
    } catch (error) {
      console.error('Error fetching active alarms:', error);
      throw error;
    }
  }

  async resolveAlarm(id, resolution) {
    try {
      const response = await api.post(`/api/alarms/${id}/resolve`, resolution);
      return response.data;
    } catch (error) {
      console.error('Error resolving alarm:', error);
      throw error;
    }
  }

  // Estado de equipos
  async getEquipmentStatus() {
    try {
      const response = await api.get('/api/alarms/equipment-status');
      return response.data;
    } catch (error) {
      console.error('Error fetching equipment status:', error);
      throw error;
    }
  }

  // Histórico de alarmas
  async getAlarmHistory(filters = {}) {
    try {
      const params = new URLSearchParams();
      
      if (filters.severity) params.append('severity', filters.severity);
      if (filters.status) params.append('status', filters.status);
      if (filters.alarm_type) params.append('alarm_type', filters.alarm_type);
      if (filters.start_date) params.append('start_date', filters.start_date);
      if (filters.end_date) params.append('end_date', filters.end_date);
      if (filters.limit) params.append('limit', filters.limit);

      const response = await api.get(`/api/alarms/history?${params.toString()}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching alarm history:', error);
      throw error;
    }
  }

  // Estadísticas de alarmas
  async getAlarmStatistics() {
    try {
      const response = await api.get('/api/alarms/statistics');
      return response.data;
    } catch (error) {
      console.error('Error fetching alarm statistics:', error);
      throw error;
    }
  }

  // Utilidades para tipos de alarma
  getAlarmTypeLabel(type) {
    const types = {
      'panel': 'Panel',
      'camera': 'Cámara',
      'parking': 'Aparcamiento'
    };
    return types[type] || type;
  }

  // Utilidades para severidad
  getSeverityLabel(severity) {
    const severities = {
      'LEVE': 'Leve',
      'NORMAL': 'Normal',
      'GRAVE': 'Grave'
    };
    return severities[severity] || severity;
  }

  getSeverityColor(severity) {
    const colors = {
      'LEVE': 'warning',
      'NORMAL': 'info',
      'GRAVE': 'danger'
    };
    return colors[severity] || 'secondary';
  }

  // Utilidades para estado
  getStatusLabel(status) {
    const statuses = {
      'active': 'Activa',
      'resolved': 'Resuelta',
      'paused': 'Pausada'
    };
    return statuses[status] || status;
  }

  getStatusColor(status) {
    const colors = {
      'active': 'danger',
      'resolved': 'success',
      'paused': 'warning'
    };
    return colors[status] || 'secondary';
  }
}

export default new AlarmService(); 