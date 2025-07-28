import React, { useState, useEffect } from 'react';
import { 
  ClockHistory, 
  Filter, 
  Search, 
  Eye, 
  Calendar, 
  AlertTriangle, 
  AlertCircle, 
  AlertOctagon, 
  X, 
  ChevronLeft, 
  ChevronRight 
} from 'lucide-react';
import AlarmStatusCard from '../components/AlarmStatusCard';
import alarmService from '../services/alarmService';

const AlarmHistory = () => {
  const [alarms, setAlarms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [selectedAlarm, setSelectedAlarm] = useState(null);
  
  // Estados para filtros
  const [filters, setFilters] = useState({
    severity: '',
    status: '',
    alarm_type: '',
    start_date: '',
    end_date: '',
    limit: 50
  });
  
  // Estados para paginación
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalAlarms, setTotalAlarms] = useState(0);

  useEffect(() => {
    loadAlarmHistory();
  }, [filters, currentPage]);

  const loadAlarmHistory = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const historyData = await alarmService.getAlarmHistory({
        ...filters,
        page: currentPage
      });
      
      setAlarms(historyData.alarms || historyData);
      setTotalAlarms(historyData.total || historyData.length);
      setTotalPages(historyData.pages || 1);
    } catch (err) {
      console.error('Error loading alarm history:', err);
      setError('Error al cargar el histórico de alarmas');
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (field, value) => {
    setFilters(prev => ({
      ...prev,
      [field]: value
    }));
    setCurrentPage(1); // Reset to first page when filters change
  };

  const handleClearFilters = () => {
    setFilters({
      severity: '',
      status: '',
      alarm_type: '',
      start_date: '',
      end_date: '',
      limit: 50
    });
    setCurrentPage(1);
  };

  const handleViewDetails = (alarm) => {
    setSelectedAlarm(alarm);
    setShowDetailsModal(true);
  };

  const getSeverityIcon = (severity) => {
    const icons = {
      'LEVE': <AlertTriangle className="text-yellow-500" size={20} />,
      'NORMAL': <AlertCircle className="text-blue-500" size={20} />,
      'GRAVE': <AlertOctagon className="text-red-500" size={20} />
    };
    return icons[severity] || <AlertTriangle className="text-yellow-500" size={20} />;
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

  const getStatusBadge = (status) => {
    const colors = {
      'active': 'bg-red-100 text-red-800',
      'resolved': 'bg-green-100 text-green-800',
      'paused': 'bg-yellow-100 text-yellow-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const renderPagination = () => {
    if (totalPages <= 1) return null;

    const pages = [];
    const maxVisiblePages = 5;
    let startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2));
    let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);

    if (endPage - startPage + 1 < maxVisiblePages) {
      startPage = Math.max(1, endPage - maxVisiblePages + 1);
    }

    return (
      <div className="flex justify-center items-center space-x-2 mt-6">
        <button
          onClick={() => setCurrentPage(currentPage - 1)}
          disabled={currentPage === 1}
          className="px-3 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <ChevronLeft size={16} />
        </button>

        {startPage > 1 && (
          <>
            <button
              onClick={() => setCurrentPage(1)}
              className="px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
            >
              1
            </button>
            {startPage > 2 && <span className="px-2 text-gray-500">...</span>}
          </>
        )}

        {Array.from({ length: endPage - startPage + 1 }, (_, i) => startPage + i).map(page => (
          <button
            key={page}
            onClick={() => setCurrentPage(page)}
            className={`px-3 py-2 text-sm font-medium rounded-md ${
              currentPage === page
                ? 'bg-blue-600 text-white'
                : 'text-gray-700 bg-white border border-gray-300 hover:bg-gray-50'
            }`}
          >
            {page}
          </button>
        ))}

        {endPage < totalPages && (
          <>
            {endPage < totalPages - 1 && <span className="px-2 text-gray-500">...</span>}
            <button
              onClick={() => setCurrentPage(totalPages)}
              className="px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
            >
              {totalPages}
            </button>
          </>
        )}

        <button
          onClick={() => setCurrentPage(currentPage + 1)}
          disabled={currentPage === totalPages}
          className="px-3 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <ChevronRight size={16} />
        </button>
      </div>
    );
  };

  if (loading && alarms.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Cargando histórico de alarmas...</p>
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
            <ClockHistory className="h-8 w-8 text-blue-600 mr-3" />
            <h1 className="text-3xl font-bold text-gray-900">Histórico de Alarmas</h1>
          </div>
          <p className="text-gray-600">
            Historial completo de alarmas generadas y resueltas
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

        {/* Filtros */}
        <div className="bg-white rounded-lg shadow mb-6">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900 flex items-center">
              <Filter className="h-5 w-5 mr-2" />
              Filtros de Búsqueda
            </h3>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Severidad
                </label>
                <select
                  value={filters.severity}
                  onChange={(e) => handleFilterChange('severity', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Todas las severidades</option>
                  <option value="LEVE">Leve</option>
                  <option value="NORMAL">Normal</option>
                  <option value="GRAVE">Grave</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Estado
                </label>
                <select
                  value={filters.status}
                  onChange={(e) => handleFilterChange('status', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Todos los estados</option>
                  <option value="active">Activa</option>
                  <option value="resolved">Resuelta</option>
                  <option value="paused">Pausada</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Tipo de Alarma
                </label>
                <select
                  value={filters.alarm_type}
                  onChange={(e) => handleFilterChange('alarm_type', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Todos los tipos</option>
                  <option value="panel">Panel</option>
                  <option value="camera">Cámara</option>
                  <option value="parking">Aparcamiento</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Límite de resultados
                </label>
                <select
                  value={filters.limit}
                  onChange={(e) => handleFilterChange('limit', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value={25}>25 resultados</option>
                  <option value={50}>50 resultados</option>
                  <option value={100}>100 resultados</option>
                </select>
              </div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Fecha de Inicio
                </label>
                <input
                  type="date"
                  value={filters.start_date}
                  onChange={(e) => handleFilterChange('start_date', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Fecha de Fin
                </label>
                <input
                  type="date"
                  value={filters.end_date}
                  onChange={(e) => handleFilterChange('end_date', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              
              <div className="flex items-end space-x-2">
                <button
                  onClick={handleClearFilters}
                  className="flex-1 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  Limpiar Filtros
                </button>
                <button
                  onClick={loadAlarmHistory}
                  className="flex-1 px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 flex items-center justify-center"
                >
                  <Search className="h-4 w-4 mr-2" />
                  Buscar
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Resultados */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
            <h3 className="text-lg font-medium text-gray-900">
              Resultados ({totalAlarms} alarmas)
            </h3>
            {loading && (
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
            )}
          </div>
          
          <div className="p-6">
            {alarms.length === 0 ? (
              <div className="text-center py-12">
                <ClockHistory className="mx-auto h-12 w-12 text-gray-400" />
                <p className="mt-4 text-gray-600">No se encontraron alarmas con los filtros aplicados</p>
              </div>
            ) : (
              <div className="space-y-4">
                {alarms.map(alarm => (
                  <AlarmStatusCard
                    key={alarm.id}
                    alarm={alarm}
                    onViewDetails={handleViewDetails}
                  />
                ))}
                
                {renderPagination()}
              </div>
            )}
          </div>
        </div>

        {/* Modal de Detalles */}
        {showDetailsModal && (
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
              
              {selectedAlarm && (
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
                  
                  {selectedAlarm.affected_targets && selectedAlarm.affected_targets.length > 0 && (
                    <div>
                      <h5 className="font-medium text-gray-900 mb-3">Objetivos Afectados</h5>
                      <ul className="list-disc list-inside space-y-1 text-sm text-gray-600">
                        {selectedAlarm.affected_targets.map((target, index) => (
                          <li key={index}>{target.name || `ID: ${target.target_id}`}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  
                  {selectedAlarm.resolution_description && (
                    <div>
                      <h5 className="font-medium text-gray-900 mb-3">Descripción de la Resolución</h5>
                      <p className="text-sm text-gray-600">{selectedAlarm.resolution_description}</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AlarmHistory; 