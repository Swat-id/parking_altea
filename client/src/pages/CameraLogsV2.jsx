import React, { useState, useEffect } from 'react'
import { useQuery } from 'react-query'
import { cameraLogService } from '../services/cameraLogService'
import parkingService from '../services/parkingService'
import cameraService from '../services/cameraService'
import { 
  Camera, 
  AlertCircle, 
  CheckCircle, 
  Clock, 
  Filter,
  RefreshCw,
  Search,
  BarChart3,
  Eye,
  EyeOff,
  Download,
  Calendar,
  Wifi,
  WifiOff,
  ChevronLeft,
  ChevronRight,
  ArrowUpDown,
  TrendingUp,
  TrendingDown,
  Activity
} from 'lucide-react'
import toast from 'react-hot-toast'
import { useSearchParams } from 'react-router-dom'

const CameraLogsV2 = () => {
  const [searchParams, setSearchParams] = useSearchParams()
  
  // Estados de datos
  const [data, setData] = useState({ logs: [], pagination: {}, stats: {} })
  const [cameras, setCameras] = useState([])
  const [parkings, setParkings] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  
  // Estados de filtros
  const [filters, setFilters] = useState({
    parkingId: searchParams.get('parking') || '',
    cameraIp: '',
    cameraName: '',
    status: '',
    dateFrom: '',
    dateTo: '',
    timeFrom: '',
    timeTo: '',
    hasChanges: false,
    errorOnly: false,
    orderBy: 'received_at',
    orderDirection: 'desc'
  })
  
  // Estados de paginación
  const [pagination, setPagination] = useState({
    page: parseInt(searchParams.get('page')) || 1,
    perPage: parseInt(searchParams.get('per_page')) || 20
  })
  
  // Estados de UI
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false)
  const [lastUpdate, setLastUpdate] = useState(null)

  // Cargar datos cuando cambien filtros o paginación
  useEffect(() => {
    loadData()
  }, [filters, pagination])

  // Cargar cámaras cuando cambie el parking seleccionado
  useEffect(() => {
    if (filters.parkingId) {
      loadCameras(filters.parkingId)
    } else {
      setCameras([])
    }
  }, [filters.parkingId])

  // Cargar parkings al inicio
  useEffect(() => {
    loadParkings()
  }, [])

  const loadParkings = async () => {
    try {
      // Cargar parkings con filtrado por permisos
      const parkingsData = await parkingService.getParkings()
      setParkings(parkingsData || [])
    } catch (err) {
      console.error('Error cargando parkings:', err)
    }
  }

  const loadCameras = async (parkingId) => {
    try {
      const camerasData = await cameraService.getParkingCameras(parkingId)
      setCameras(camerasData.cameras || [])
    } catch (err) {
      console.error('Error cargando cámaras:', err)
      setCameras([])
    }
  }

  const loadData = async () => {
    try {
      setLoading(true)
      setError(null)
      
      // Preparar filtros para la API
      const apiFilters = {
        ...filters,
        parkingId: filters.parkingId || undefined,
        cameraIp: filters.cameraIp || undefined,
        cameraName: filters.cameraName || undefined,
        status: filters.status || undefined,
        dateFrom: filters.dateFrom || undefined,
        dateTo: filters.dateTo || undefined,
        timeFrom: filters.timeFrom || undefined,
        timeTo: filters.timeTo || undefined,
        hasChanges: filters.hasChanges || undefined,
        errorOnly: filters.errorOnly || undefined
      }
      
      // Eliminar valores vacíos
      Object.keys(apiFilters).forEach(key => {
        if (apiFilters[key] === undefined || apiFilters[key] === '') {
          delete apiFilters[key]
        }
      })
      
      const result = await cameraLogService.getCameraLogsV2(apiFilters, pagination)
      setData(result)
      setLastUpdate(new Date())
      
    } catch (err) {
      setError('Error cargando datos de logs de cámaras')
      console.error('Error:', err)
      toast.error('Error cargando logs de cámaras')
    } finally {
      setLoading(false)
    }
  }

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({
      ...prev,
      [key]: value
    }))
    
    // Reset página al cambiar filtros
    if (pagination.page !== 1) {
      setPagination(prev => ({ ...prev, page: 1 }))
    }
  }

  const handlePageChange = (newPage) => {
    setPagination(prev => ({ ...prev, page: newPage }))
    
    // Actualizar URL
    const newSearchParams = new URLSearchParams(searchParams)
    newSearchParams.set('page', newPage.toString())
    setSearchParams(newSearchParams)
  }

  const handlePerPageChange = (newPerPage) => {
    setPagination(prev => ({ ...prev, perPage: newPerPage, page: 1 }))
  }

  const getStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'processed':
        return 'text-green-700 bg-green-100'
      case 'error':
        return 'text-red-700 bg-red-100'
      case 'discarded':
        return 'text-yellow-700 bg-yellow-100'
      default:
        return 'text-gray-700 bg-gray-100'
    }
  }

  const getStatusIcon = (status) => {
    switch (status?.toLowerCase()) {
      case 'processed':
        return <CheckCircle className="w-4 h-4" />
      case 'error':
        return <AlertCircle className="w-4 h-4" />
      case 'discarded':
        return <Clock className="w-4 h-4" />
      default:
        return <Activity className="w-4 h-4" />
    }
  }

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return 'N/A'
    const date = new Date(timestamp)
    return date.toLocaleString('es-ES', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  }

  const getRelativeTime = (timestamp) => {
    if (!timestamp) return ''
    const date = new Date(timestamp)
    const now = new Date()
    const diffMs = now - date
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    
    if (diffMins < 1) return 'Ahora mismo'
    if (diffMins < 60) return `Hace ${diffMins} min`
    if (diffHours < 24) return `Hace ${diffHours}h ${diffMins % 60}min`
    return `Hace ${Math.floor(diffHours / 24)} días`
  }

  const resetFilters = () => {
    setFilters({
      parkingId: '',
      cameraIp: '',
      cameraName: '',
      status: '',
      dateFrom: '',
      dateTo: '',
      timeFrom: '',
      timeTo: '',
      hasChanges: false,
      errorOnly: false,
      orderBy: 'received_at',
      orderDirection: 'desc'
    })
    setPagination({ page: 1, perPage: 20 })
  }

  const quickFilters = [
    {
      label: 'Solo errores',
      action: () => handleFilterChange('errorOnly', !filters.errorOnly),
      active: filters.errorOnly,
      color: 'red'
    },
    {
      label: 'Solo cambios',
      action: () => handleFilterChange('hasChanges', !filters.hasChanges),
      active: filters.hasChanges,
      color: 'blue'
    },
    {
      label: 'Hoy',
      action: () => {
        const today = new Date().toISOString().split('T')[0]
        handleFilterChange('dateFrom', today)
        handleFilterChange('dateTo', today)
      },
      active: filters.dateFrom === new Date().toISOString().split('T')[0],
      color: 'green'
    }
  ]

  if (loading && !lastUpdate) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">📋 Logs de Cámaras v2</h1>
        <p className="text-gray-600">
          Análisis avanzado de eventos y evolución de ocupación de parkings
        </p>
        {lastUpdate && (
          <p className="text-sm text-gray-500 mt-2">
            Última actualización: {lastUpdate.toLocaleString('es-ES')}
          </p>
        )}
      </div>

      {/* Estadísticas rápidas */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500">Total Logs</h3>
          <p className="text-2xl font-bold text-gray-900">
            {data.pagination?.total_count || 0}
          </p>
        </div>
        
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500">Procesados</h3>
          <p className="text-2xl font-bold text-green-600">
            {data.stats?.processed_count || 0}
          </p>
        </div>
        
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500">Errores</h3>
          <p className="text-2xl font-bold text-red-600">
            {data.stats?.error_count || 0}
          </p>
        </div>
        
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500">Con Cambios</h3>
          <p className="text-2xl font-bold text-blue-600">
            {data.stats?.total_changes || 0}
          </p>
        </div>
      </div>

      {/* Filtros */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">🔍 Filtros</h2>
          <div className="flex space-x-2">
            <button
              onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
              className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-50"
            >
              {showAdvancedFilters ? 'Ocultar avanzados' : 'Mostrar avanzados'}
            </button>
            <button
              onClick={resetFilters}
              className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
            >
              Limpiar filtros
            </button>
          </div>
        </div>

        {/* Filtros rápidos */}
        <div className="flex flex-wrap gap-2 mb-4">
          {quickFilters.map((filter) => (
            <button
              key={filter.label}
              onClick={filter.action}
              className={`px-3 py-1 text-sm rounded-full transition-colors ${
                filter.active
                  ? `bg-${filter.color}-100 text-${filter.color}-700 border-${filter.color}-300`
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              } border`}
            >
              {filter.label}
            </button>
          ))}
        </div>
        
        {/* Filtros básicos */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Parking
            </label>
            <select
              value={filters.parkingId}
              onChange={(e) => handleFilterChange('parkingId', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Todos los parkings</option>
              {parkings.map((parking) => (
                <option key={parking.id} value={parking.id}>
                  {parking.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Estado
            </label>
            <select
              value={filters.status}
              onChange={(e) => handleFilterChange('status', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Todos los estados</option>
              <option value="processed">Procesado</option>
              <option value="error">Error</option>
              <option value="discarded">Descartado</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Fecha desde
            </label>
            <input
              type="date"
              value={filters.dateFrom}
              onChange={(e) => handleFilterChange('dateFrom', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Fecha hasta
            </label>
            <input
              type="date"
              value={filters.dateTo}
              onChange={(e) => handleFilterChange('dateTo', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        {/* Filtros avanzados */}
        {showAdvancedFilters && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 border-t pt-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                IP de Cámara
              </label>
              <input
                type="text"
                value={filters.cameraIp}
                onChange={(e) => handleFilterChange('cameraIp', e.target.value)}
                placeholder="192.168.1.100"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Nombre de Cámara
              </label>
              <input
                type="text"
                value={filters.cameraName}
                onChange={(e) => handleFilterChange('cameraName', e.target.value)}
                placeholder="CAM-01"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Hora desde
              </label>
              <input
                type="time"
                value={filters.timeFrom}
                onChange={(e) => handleFilterChange('timeFrom', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Hora hasta
              </label>
              <input
                type="time"
                value={filters.timeTo}
                onChange={(e) => handleFilterChange('timeTo', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
        )}

        {/* Ordenación y paginación */}
        <div className="flex items-center justify-between mt-4 pt-4 border-t">
          <div className="flex items-center space-x-4">
            <div>
              <label className="text-sm font-medium text-gray-700 mr-2">
                Ordenar por:
              </label>
              <select
                value={filters.orderBy}
                onChange={(e) => handleFilterChange('orderBy', e.target.value)}
                className="px-3 py-1 border border-gray-300 rounded text-sm"
              >
                <option value="received_at">Fecha recepción</option>
                <option value="processed_at">Fecha procesamiento</option>
                <option value="processing_time">Tiempo procesamiento</option>
              </select>
            </div>
            
            <button
              onClick={() => handleFilterChange('orderDirection', 
                filters.orderDirection === 'asc' ? 'desc' : 'asc'
              )}
              className="px-2 py-1 border border-gray-300 rounded text-sm hover:bg-gray-50"
            >
              {filters.orderDirection === 'asc' ? '↑ Ascendente' : '↓ Descendente'}
            </button>
          </div>

          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-600">Elementos por página:</span>
            <select
              value={pagination.perPage}
              onChange={(e) => handlePerPageChange(parseInt(e.target.value))}
              className="px-3 py-1 border border-gray-300 rounded text-sm"
            >
              <option value={10}>10</option>
              <option value={20}>20</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
            </select>
          </div>
        </div>

        {/* Botón de actualizar */}
        <div className="mt-4">
          <button
            onClick={loadData}
            disabled={loading}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            {loading ? 'Actualizando...' : 'Actualizar'}
          </button>
          
          {error && (
            <p className="text-red-600 text-sm mt-2">{error}</p>
          )}
        </div>
      </div>

      {/* Información de paginación */}
      {data.pagination && (
        <div className="flex items-center justify-between mb-4">
          <div className="text-sm text-gray-700">
            Mostrando {((data.pagination.current_page - 1) * data.pagination.per_page) + 1} - {Math.min(data.pagination.current_page * data.pagination.per_page, data.pagination.total_count)} de {data.pagination.total_count} registros
          </div>
          
          <div className="flex items-center space-x-2">
            <button
              onClick={() => handlePageChange(data.pagination.current_page - 1)}
              disabled={!data.pagination.has_prev}
              className="px-3 py-1 border border-gray-300 rounded text-sm hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            
            <span className="text-sm text-gray-700">
              Página {data.pagination.current_page} de {data.pagination.total_pages}
            </span>
            
            <button
              onClick={() => handlePageChange(data.pagination.current_page + 1)}
              disabled={!data.pagination.has_next}
              className="px-3 py-1 border border-gray-300 rounded text-sm hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Lista de Logs */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">
            Registros de Cámaras
          </h2>
        </div>
        
        <div className="overflow-x-auto">
          {data.logs?.length === 0 ? (
            <div className="text-center py-8">
              <Camera className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500">No hay logs para mostrar con los filtros actuales</p>
              <button
                onClick={loadData}
                className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                🔄 Recargar datos
              </button>
            </div>
          ) : (
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Timestamp
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Estado
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Parking / Cámara
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Contadores
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Cambios
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Ocupación
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Detalles
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {data.logs?.map((log) => (
                  <tr key={log.id} className="hover:bg-gray-50">
                    {/* Timestamp */}
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      <div>
                        <div className="font-medium">{formatTimestamp(log.received_at)}</div>
                        <div className="text-xs text-gray-500">{getRelativeTime(log.received_at)}</div>
                      </div>
                    </td>
                    
                    {/* Estado */}
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex items-center px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(log.status)}`}>
                        {getStatusIcon(log.status)}
                        <span className="ml-1">{log.status || 'N/A'}</span>
                      </span>
                    </td>
                    
                    {/* Parking / Cámara */}
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      <div>
                        <div className="font-medium">{log.parking_name || 'N/A'}</div>
                        <div className="text-xs text-gray-500">
                          {log.camera_name || 'Sin nombre'} ({log.camera_ip})
                        </div>
                        <div className="text-xs text-gray-400">
                          Línea: {log.camera_line || 'N/A'}
                        </div>
                      </div>
                    </td>
                    
                    {/* Contadores */}
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      <div className="space-y-1">
                        <div className="flex space-x-4">
                          <span className="text-green-600 font-medium">
                            In: {log.vehicle_in || 0}
                          </span>
                          <span className="text-red-600 font-medium">
                            Out: {log.vehicle_out || 0}
                          </span>
                        </div>
                        {(log.previous_vehicle_in !== undefined || log.previous_vehicle_out !== undefined) && (
                          <div className="text-xs text-gray-500">
                            Anterior: In:{log.previous_vehicle_in || 0} Out:{log.previous_vehicle_out || 0}
                          </div>
                        )}
                      </div>
                    </td>
                    
                    {/* Cambios (Deltas) */}
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      <div className="space-y-1">
                        {(log.delta_in !== undefined && log.delta_out !== undefined) ? (
                          <>
                            {log.delta_in > 0 && (
                              <div className="text-green-600 font-medium flex items-center">
                                <TrendingUp className="w-3 h-3 mr-1" />
                                +{log.delta_in} entradas
                              </div>
                            )}
                            {log.delta_out > 0 && (
                              <div className="text-red-600 font-medium flex items-center">
                                <TrendingDown className="w-3 h-3 mr-1" />
                                +{log.delta_out} salidas
                              </div>
                            )}
                            {log.delta_in === 0 && log.delta_out === 0 && (
                              <div className="text-gray-500 text-xs">Sin cambios</div>
                            )}
                          </>
                        ) : (
                          <div className="text-gray-400 text-xs">N/A</div>
                        )}
                      </div>
                    </td>
                    
                    {/* Ocupación */}
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      <div>
                        {log.new_occupancy !== undefined ? (
                          <>
                            <div className="font-medium">{log.new_occupancy}</div>
                            {log.occupancy_change !== undefined && log.occupancy_change !== 0 && (
                              <div className={`text-xs ${log.occupancy_change > 0 ? 'text-green-600' : 'text-red-600'}`}>
                                ({log.occupancy_change > 0 ? '+' : ''}{log.occupancy_change})
                              </div>
                            )}
                          </>
                        ) : (
                          <div className="text-gray-400 text-xs">N/A</div>
                        )}
                      </div>
                    </td>
                    
                    {/* Detalles */}
                    <td className="px-6 py-4 text-sm text-gray-500">
                      <div className="space-y-2">
                        {/* Tiempo de procesamiento */}
                        {log.processing_time !== undefined && (
                          <div className="text-xs">
                            <span className="font-medium">Tiempo:</span> {log.processing_time}ms
                          </div>
                        )}
                        
                        {/* Estado del parking */}
                        {log.parking_status && (
                          <div className="text-xs">
                            <span className="font-medium">Estado:</span> {log.parking_status}
                          </div>
                        )}
                        
                        {/* Mensaje de error */}
                        {log.error_message && (
                          <div className="text-xs text-red-600">
                            <span className="font-medium">Error:</span> {log.error_message}
                          </div>
                        )}
                        
                        {/* Mensaje raw */}
                        {log.raw_message && (
                          <details className="text-xs">
                            <summary className="cursor-pointer hover:text-gray-700 font-medium">
                              📄 Ver mensaje raw
                            </summary>
                            <div className="mt-2 p-2 bg-gray-100 rounded text-xs overflow-x-auto max-h-32 overflow-y-auto">
                              <pre className="whitespace-pre-wrap">
                                {typeof log.raw_message === 'string' ? log.raw_message : 
                                 JSON.stringify(log.raw_message, null, 2)}
                              </pre>
                            </div>
                          </details>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Paginación inferior */}
      {data.pagination && data.pagination.total_pages > 1 && (
        <div className="flex items-center justify-center mt-6 space-x-2">
          <button
            onClick={() => handlePageChange(1)}
            disabled={data.pagination.current_page === 1}
            className="px-3 py-2 border border-gray-300 rounded text-sm hover:bg-gray-50 disabled:opacity-50"
          >
            Primera
          </button>
          
          <button
            onClick={() => handlePageChange(data.pagination.current_page - 1)}
            disabled={!data.pagination.has_prev}
            className="px-3 py-2 border border-gray-300 rounded text-sm hover:bg-gray-50 disabled:opacity-50"
          >
            Anterior
          </button>
          
          <span className="px-4 py-2 text-sm text-gray-700">
            {data.pagination.current_page} / {data.pagination.total_pages}
          </span>
          
          <button
            onClick={() => handlePageChange(data.pagination.current_page + 1)}
            disabled={!data.pagination.has_next}
            className="px-3 py-2 border border-gray-300 rounded text-sm hover:bg-gray-50 disabled:opacity-50"
          >
            Siguiente
          </button>
          
          <button
            onClick={() => handlePageChange(data.pagination.total_pages)}
            disabled={data.pagination.current_page === data.pagination.total_pages}
            className="px-3 py-2 border border-gray-300 rounded text-sm hover:bg-gray-50 disabled:opacity-50"
          >
            Última
          </button>
        </div>
      )}
    </div>
  )
}

export default CameraLogsV2
