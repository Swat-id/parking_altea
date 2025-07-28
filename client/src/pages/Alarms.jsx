import React, { useState, useEffect } from 'react';
import { 
  Plus, 
  AlertTriangle, 
  AlertCircle, 
  AlertOctagon,
  Bell,
  Gear,
  Trash,
  Pencil,
  Eye,
  CheckCircle,
  X
} from 'lucide-react';
import AlarmStatusCard from '../components/AlarmStatusCard';
import AlarmConfigurationForm from '../components/AlarmConfigurationForm';
import alarmService from '../services/alarmService';

const Alarms = () => {
  const [activeTab, setActiveTab] = useState('configurations');
  const [configurations, setConfigurations] = useState([]);
  const [activeAlarms, setActiveAlarms] = useState([]);
  const [statistics, setStatistics] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Estados para modales
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showResolveModal, setShowResolveModal] = useState(false);
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  
  // Estados para formularios
  const [selectedConfiguration, setSelectedConfiguration] = useState(null);
  const [selectedAlarm, setSelectedAlarm] = useState(null);
  const [alarmType, setAlarmType] = useState('panel');
  const [resolutionDescription, setResolutionDescription] = useState('');
  const [formLoading, setFormLoading] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const [configsData, alarmsData, statsData] = await Promise.all([
        alarmService.getAlarmConfigurations(),
        alarmService.getActiveAlarms(),
        alarmService.getAlarmStatistics()
      ]);
      
      setConfigurations(configsData);
      setActiveAlarms(alarmsData);
      setStatistics(statsData);
    } catch (err) {
      console.error('Error loading alarm data:', err);
      setError('Error al cargar los datos de alarmas');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateConfiguration = async (configData) => {
    setFormLoading(true);
    try {
      await alarmService.createAlarmConfiguration(configData);
      setShowCreateModal(false);
      setAlarmType('panel');
      loadData();
    } catch (err) {
      console.error('Error creating configuration:', err);
      setError('Error al crear la configuración');
    } finally {
      setFormLoading(false);
    }
  };

  const handleUpdateConfiguration = async (configData) => {
    setFormLoading(true);
    try {
      await alarmService.updateAlarmConfiguration(selectedConfiguration.id, configData);
      setShowEditModal(false);
      setSelectedConfiguration(null);
      loadData();
    } catch (err) {
      console.error('Error updating configuration:', err);
      setError('Error al actualizar la configuración');
    } finally {
      setFormLoading(false);
    }
  };

  const handleDeleteConfiguration = async (configId) => {
    if (window.confirm('¿Estás seguro de que quieres eliminar esta configuración?')) {
      try {
        await alarmService.deleteAlarmConfiguration(configId);
        loadData();
      } catch (err) {
        console.error('Error deleting configuration:', err);
        setError('Error al eliminar la configuración');
      }
    }
  };

  const handleResolveAlarm = async () => {
    if (!selectedAlarm || !resolutionDescription.trim()) return;
    
    setFormLoading(true);
    try {
      await alarmService.resolveAlarm(selectedAlarm.id, {
        resolution_description: resolutionDescription
      });
      setShowResolveModal(false);
      setSelectedAlarm(null);
      setResolutionDescription('');
      loadData();
    } catch (err) {
      console.error('Error resolving alarm:', err);
      setError('Error al resolver la alarma');
    } finally {
      setFormLoading(false);
    }
  };

  const getSeverityIcon = (severity) => {
    const icons = {
      'LEVE': <AlertTriangle className="text-yellow-500" size={20} />,
      'NORMAL': <AlertCircle className="text-blue-500" size={20} />,
      'GRAVE': <AlertOctagon className="text-red-500" size={20} />
    };
    return icons[severity] || <AlertTriangle className="text-yellow-500" size={20} />;
  };

  const getStatusBadge = (status) => {
    const colors = {
      'active': 'bg-red-100 text-red-800',
      'resolved': 'bg-green-100 text-green-800',
      'paused': 'bg-yellow-100 text-yellow-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString('es-ES', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Cargando alarmas...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center mb-2">
            <Bell className="h-8 w-8 text-blue-600 mr-3" />
            <h1 className="text-3xl font-bold text-gray-900">Sistema de Alarmas</h1>
          </div>
          <p className="text-gray-600">
            Gestión de configuraciones y alarmas activas del sistema
          </p>
        </div>

        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-md p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <AlertTriangle className="h-5 w-5 text-red-400" />
              </div>
              <div className="ml-3">
                <p className="text-sm text-red-800">{error}</p>
              </div>
              <div className="ml-auto pl-3">
                <button
                  onClick={() => setError(null)}
                  className="inline-flex text-red-400 hover:text-red-600"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Tabs */}
        <div className="bg-white rounded-lg shadow mb-6">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8 px-6">
              <button
                onClick={() => setActiveTab('configurations')}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'configurations'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <Gear className="h-4 w-4 inline mr-2" />
                Configuraciones
              </button>
              <button
                onClick={() => setActiveTab('active')}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'active'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <Bell className="h-4 w-4 inline mr-2" />
                Alarmas Activas ({activeAlarms.length})
              </button>
              <button
                onClick={() => setActiveTab('statistics')}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'statistics'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <CheckCircle className="h-4 w-4 inline mr-2" />
                Estadísticas
              </button>
            </nav>
          </div>

          <div className="p-6">
            {/* Tab: Configuraciones */}
            {activeTab === 'configurations' && (
              <div>
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-xl font-semibold text-gray-900">Configuraciones de Alarmas</h2>
                  <button
                    onClick={() => setShowCreateModal(true)}
                    className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    <Plus className="h-4 w-4 mr-2" />
                    Nueva Configuración
                  </button>
                </div>

                {configurations.length === 0 ? (
                  <div className="text-center py-12">
                    <Gear className="mx-auto h-12 w-12 text-gray-400" />
                    <p className="mt-4 text-gray-600">No hay configuraciones de alarmas</p>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {configurations.map(config => (
                      <div key={config.id} className="bg-white border border-gray-200 rounded-lg shadow-sm hover:shadow-md transition-shadow">
                        <div className="px-6 py-4 border-b border-gray-200">
                          <div className="flex justify-between items-start">
                            <div className="flex items-center space-x-3">
                              {getSeverityIcon(config.severity)}
                              <div>
                                <h3 className="font-semibold text-gray-900">{config.name}</h3>
                                <p className="text-sm text-gray-600">{config.description}</p>
                              </div>
                            </div>
                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusBadge(config.status)}`}>
                              {alarmService.getStatusLabel(config.status)}
                            </span>
                          </div>
                        </div>
                        
                        <div className="px-6 py-4">
                          <div className="space-y-2 text-sm">
                            <p><span className="font-medium">Tipo:</span> {alarmService.getAlarmTypeLabel(config.alarm_type)}</p>
                            <p><span className="font-medium">Severidad:</span> {alarmService.getSeverityLabel(config.severity)}</p>
                            <p><span className="font-medium">Condición:</span> {config.condition}</p>
                            {config.threshold && (
                              <p><span className="font-medium">Umbral:</span> {config.threshold}</p>
                            )}
                          </div>
                        </div>
                        
                        <div className="px-6 py-3 bg-gray-50 border-t border-gray-200 rounded-b-lg">
                          <div className="flex justify-between items-center">
                            <div className="text-xs text-gray-500">
                              Creada: {formatDate(config.created_at)}
                            </div>
                            <div className="flex space-x-2">
                              <button
                                onClick={() => {
                                  setSelectedConfiguration(config);
                                  setShowEditModal(true);
                                }}
                                className="inline-flex items-center px-2 py-1 border border-gray-300 shadow-sm text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50"
                              >
                                <Pencil className="h-3 w-3 mr-1" />
                                Editar
                              </button>
                              <button
                                onClick={() => handleDeleteConfiguration(config.id)}
                                className="inline-flex items-center px-2 py-1 border border-red-300 shadow-sm text-xs font-medium rounded text-red-700 bg-white hover:bg-red-50"
                              >
                                <Trash className="h-3 w-3 mr-1" />
                                Eliminar
                              </button>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Tab: Alarmas Activas */}
            {activeTab === 'active' && (
              <div>
                <h2 className="text-xl font-semibold text-gray-900 mb-6">Alarmas Activas</h2>
                
                {activeAlarms.length === 0 ? (
                  <div className="text-center py-12">
                    <Bell className="mx-auto h-12 w-12 text-gray-400" />
                    <p className="mt-4 text-gray-600">No hay alarmas activas</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {activeAlarms.map(alarm => (
                      <AlarmStatusCard
                        key={alarm.id}
                        alarm={alarm}
                        onViewDetails={(alarm) => {
                          setSelectedAlarm(alarm);
                          setShowDetailsModal(true);
                        }}
                        onResolve={(alarm) => {
                          setSelectedAlarm(alarm);
                          setShowResolveModal(true);
                        }}
                      />
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Tab: Estadísticas */}
            {activeTab === 'statistics' && (
              <div>
                <h2 className="text-xl font-semibold text-gray-900 mb-6">Estadísticas de Alarmas</h2>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="bg-white border border-gray-200 rounded-lg p-6">
                    <div className="flex items-center">
                      <div className="flex-shrink-0">
                        <Bell className="h-8 w-8 text-blue-600" />
                      </div>
                      <div className="ml-4">
                        <p className="text-sm font-medium text-gray-500">Total de Alarmas</p>
                        <p className="text-2xl font-semibold text-gray-900">{statistics.total_alarms || 0}</p>
                      </div>
                    </div>
                  </div>
                  
                  <div className="bg-white border border-gray-200 rounded-lg p-6">
                    <div className="flex items-center">
                      <div className="flex-shrink-0">
                        <AlertTriangle className="h-8 w-8 text-red-600" />
                      </div>
                      <div className="ml-4">
                        <p className="text-sm font-medium text-gray-500">Alarmas Activas</p>
                        <p className="text-2xl font-semibold text-gray-900">{statistics.active_alarms || 0}</p>
                      </div>
                    </div>
                  </div>
                  
                  <div className="bg-white border border-gray-200 rounded-lg p-6">
                    <div className="flex items-center">
                      <div className="flex-shrink-0">
                        <CheckCircle className="h-8 w-8 text-green-600" />
                      </div>
                      <div className="ml-4">
                        <p className="text-sm font-medium text-gray-500">Resueltas Hoy</p>
                        <p className="text-2xl font-semibold text-gray-900">{statistics.resolved_today || 0}</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Modal de Crear Configuración */}
        {showCreateModal && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
            <div className="relative top-20 mx-auto p-5 border w-11/12 md:w-3/4 lg:w-1/2 shadow-lg rounded-md bg-white">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-medium text-gray-900">Nueva Configuración de Alarma</h3>
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="h-6 w-6" />
                </button>
              </div>
              
              <AlarmConfigurationForm
                onSubmit={handleCreateConfiguration}
                onCancel={() => setShowCreateModal(false)}
                loading={formLoading}
                alarmType={alarmType}
                setAlarmType={setAlarmType}
              />
            </div>
          </div>
        )}

        {/* Modal de Editar Configuración */}
        {showEditModal && selectedConfiguration && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
            <div className="relative top-20 mx-auto p-5 border w-11/12 md:w-3/4 lg:w-1/2 shadow-lg rounded-md bg-white">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-medium text-gray-900">Editar Configuración de Alarma</h3>
                <button
                  onClick={() => setShowEditModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="h-6 w-6" />
                </button>
              </div>
              
              <AlarmConfigurationForm
                configuration={selectedConfiguration}
                onSubmit={handleUpdateConfiguration}
                onCancel={() => setShowEditModal(false)}
                loading={formLoading}
                alarmType={selectedConfiguration.alarm_type}
                setAlarmType={setAlarmType}
              />
            </div>
          </div>
        )}

        {/* Modal de Resolver Alarma */}
        {showResolveModal && selectedAlarm && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
            <div className="relative top-20 mx-auto p-5 border w-11/12 md:w-3/4 lg:w-1/2 shadow-lg rounded-md bg-white">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-medium text-gray-900">Resolver Alarma</h3>
                <button
                  onClick={() => setShowResolveModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="h-6 w-6" />
                </button>
              </div>
              
              <div className="space-y-4">
                <div>
                  <h4 className="font-medium text-gray-900">{selectedAlarm.configuration_name}</h4>
                  <p className="text-gray-600">{selectedAlarm.message}</p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Descripción de la Resolución
                  </label>
                  <textarea
                    value={resolutionDescription}
                    onChange={(e) => setResolutionDescription(e.target.value)}
                    rows={4}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Describe cómo se resolvió la alarma..."
                  />
                </div>
                
                <div className="flex justify-end space-x-3">
                  <button
                    onClick={() => setShowResolveModal(false)}
                    className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                  >
                    Cancelar
                  </button>
                  <button
                    onClick={handleResolveAlarm}
                    disabled={!resolutionDescription.trim() || formLoading}
                    className="px-4 py-2 text-sm font-medium text-white bg-green-600 border border-transparent rounded-md hover:bg-green-700 disabled:opacity-50"
                  >
                    {formLoading ? 'Resolviendo...' : 'Resolver Alarma'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Modal de Detalles de Alarma */}
        {showDetailsModal && selectedAlarm && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
            <div className="relative top-20 mx-auto p-5 border w-11/12 md:w-3/4 lg:w-1/2 shadow-lg rounded-md bg-white">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-medium text-gray-900">Detalles de la Alarma</h3>
                <button
                  onClick={() => setShowDetailsModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="h-6 w-6" />
                </button>
              </div>
              
              <div className="space-y-4">
                <div>
                  <h4 className="text-lg font-semibold text-gray-900">{selectedAlarm.configuration_name}</h4>
                  <p className="text-gray-600 mt-1">{selectedAlarm.message}</p>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h5 className="font-medium text-gray-900 mb-3">Información General</h5>
                    <div className="space-y-2 text-sm">
                      <p><span className="font-medium">ID:</span> {selectedAlarm.id}</p>
                      <p><span className="font-medium">Tipo:</span> {alarmService.getAlarmTypeLabel(selectedAlarm.alarm_type)}</p>
                      <p><span className="font-medium">Severidad:</span> {alarmService.getSeverityLabel(selectedAlarm.severity)}</p>
                      <p><span className="font-medium">Estado:</span> {alarmService.getStatusLabel(selectedAlarm.status)}</p>
                    </div>
                  </div>
                  
                  <div>
                    <h5 className="font-medium text-gray-900 mb-3">Fechas</h5>
                    <div className="space-y-2 text-sm">
                      <p><span className="font-medium">Creada:</span> {formatDate(selectedAlarm.created_at)}</p>
                      {selectedAlarm.resolved_at && (
                        <p><span className="font-medium">Resuelta:</span> {formatDate(selectedAlarm.resolved_at)}</p>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Alarms; 