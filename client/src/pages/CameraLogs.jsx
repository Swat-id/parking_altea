import { useState, useEffect } from 'react'
import { useQuery } from 'react-query'
import { cameraLogService } from '../services/cameraLogService'
import { parkingService } from '../services/parkingService'
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
  WifiOff
} from 'lucide-react'
import toast from 'react-hot-toast'

const CameraLogs = () => {
  const [filters, setFilters] = useState({
    parking_id: '',
    status: '',
    limit: 50
  })
  
  const [showFilters, setShowFilters] = useState(false)
  const [selectedLog, setSelectedLog] = useState(null)

  // Obtener parkings para el filtro
  const { data: parkings = [] } = useQuery(
    'parkings',
    parkingService.getAllParkings
  )

  // Obtener logs de cámaras
  const { data: logsData, isLoading, refetch } = useQuery(
    ['cameraLogs', filters],
    () => cameraLogService.getCameraLogs(filters),
    {
      refetchInterval: 30000, // Refrescar cada 30 segundos
    }
  )

  // Obtener estadísticas
  const { data: statsData } = useQuery(
    ['cameraLogsStats', filters.parking_id],
    () => cameraLogService.getCameraLogsStats({ 
      parking_id: filters.parking_id || undefined,
      days: 7 
    })
  )

  const logs = logsData?.logs || []
  const stats = statsData || {}

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({
      ...prev,
      [key]: value
    }))
  }

  const clearFilters = () => {
    setFilters({
      parking_id: '',
      status: '',
      limit: 50
    })
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'processed':
        return <CheckCircle className="h-4 w-4 text-green-600" />
      case 'error':
        return <AlertCircle className="h-4 w-4 text-red-600" />
      case 'discarded':
        return <EyeOff className="h-4 w-4 text-yellow-600" />
      default:
        return <Clock className="h-4 w-4 text-gray-600" />
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'processed':
        return 'text-green-600 bg-green-100'
      case 'error':
        return 'text-red-600 bg-red-100'
      case 'discarded':
        return 'text-yellow-600 bg-yellow-100'
      default:
        return 'text-gray-600 bg-gray-100'
    }
  }

  const formatDateTime = (dateString) => {
    if (!dateString) return 'N/A'
    return new Date(dateString).toLocaleString('es-ES')
  }

  const formatProcessingTime = (time) => {
    if (!time) return 'N/A'
    return `${time.toFixed(2)}ms`
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Logs de Cámaras</h1>
          <p className="mt-1 text-sm text-gray-500">
            Monitoreo y análisis de mensajes de cámaras
          </p>
        </div>
        <div className="flex space-x-2">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="btn-secondary flex items-center"
          >
            <Filter className="h-4 w-4 mr-2" />
            Filtros
          </button>
          <button
            onClick={() => refetch()}
            className="btn-secondary flex items-center"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Actualizar
          </button>
        </div>
      </div>

      {/* Estadísticas */}
      {stats && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-4">
          <div className="card">
            <div className="flex items-center">
              <Camera className="h-8 w-8 text-primary-600" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-500">Total Logs</p>
                <p className="text-lg font-semibold text-gray-900">{stats.total_logs || 0}</p>
              </div>
            </div>
          </div>
          <div className="card">
            <div className="flex items-center">
              <CheckCircle className="h-8 w-8 text-green-600" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-500">Procesados</p>
                <p className="text-lg font-semibold text-gray-900">{stats.processed_logs || 0}</p>
              </div>
            </div>
          </div>
          <div className="card">
            <div className="flex items-center">
              <AlertCircle className="h-8 w-8 text-red-600" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-500">Errores</p>
                <p className="text-lg font-semibold text-gray-900">{stats.error_logs || 0}</p>
              </div>
            </div>
          </div>
          <div className="card">
            <div className="flex items-center">
              <BarChart3 className="h-8 w-8 text-blue-600" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-500">Tasa Éxito</p>
                <p className="text-lg font-semibold text-gray-900">
                  {stats.success_rate ? `${stats.success_rate.toFixed(1)}%` : '0%'}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Filtros */}
      {showFilters && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">Filtros</h3>
            <button
              onClick={clearFilters}
              className="text-sm text-gray-500 hover:text-gray-700"
            >
              Limpiar
            </button>
          </div>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Parking
              </label>
              <select
                value={filters.parking_id}
                onChange={(e) => handleFilterChange('parking_id', e.target.value)}
                className="input-field"
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
                className="input-field"
              >
                <option value="">Todos los estados</option>
                <option value="processed">Procesados</option>
                <option value="error">Errores</option>
                <option value="discarded">Descartados</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Límite
              </label>
              <select
                value={filters.limit}
                onChange={(e) => handleFilterChange('limit', parseInt(e.target.value))}
                className="input-field"
              >
                <option value={25}>25 registros</option>
                <option value={50}>50 registros</option>
                <option value={100}>100 registros</option>
                <option value={200}>200 registros</option>
              </select>
            </div>
          </div>
        </div>
      )}

      {/* Lista de logs */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-medium text-gray-900">
            Logs de Cámaras ({logs.length})
          </h2>
          <div className="text-sm text-gray-500">
            {logsData?.total_count && `Total: ${logsData.total_count}`}
          </div>
        </div>

        {logs.length === 0 ? (
          <div className="text-center py-12">
            <Camera className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No hay logs disponibles</h3>
            <p className="mt-1 text-sm text-gray-500">
              No se encontraron logs de cámaras con los filtros aplicados.
            </p>
          </div>
        ) : (
          <div className="overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Cámara
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Parking
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Estado
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Contadores
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Ocupación
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Tiempo
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Fecha
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Acciones
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {logs.map((log) => (
                    <tr key={log.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <div className="text-sm font-medium text-gray-900">
                            {log.camera_name || 'N/A'}
                          </div>
                          <div className="text-sm text-gray-500">
                            {log.camera_ip}:{log.camera_line}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">
                          {log.parking_name || 'N/A'}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(log.status)}`}>
                          {getStatusIcon(log.status)}
                          <span className="ml-1">{log.status}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">
                          <div>In: {log.vehicle_in || 0}</div>
                          <div>Out: {log.vehicle_out || 0}</div>
                          {log.delta_in !== null && log.delta_out !== null && (
                            <div className="text-xs text-gray-500">
                              Δ: +{log.delta_in} / -{log.delta_out}
                            </div>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">
                          {log.new_occupancy !== null ? log.new_occupancy : 'N/A'}
                          {log.occupancy_change !== null && (
                            <div className="text-xs text-gray-500">
                              {log.occupancy_change > 0 ? '+' : ''}{log.occupancy_change}
                            </div>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">
                          {formatProcessingTime(log.processing_time)}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">
                          {formatDateTime(log.received_at)}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <button
                          onClick={() => setSelectedLog(selectedLog?.id === log.id ? null : log)}
                          className="text-primary-600 hover:text-primary-900"
                        >
                          {selectedLog?.id === log.id ? 'Ocultar' : 'Ver'}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* Modal de detalles del log */}
      {selectedLog && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-11/12 md:w-3/4 lg:w-1/2 shadow-lg rounded-md bg-white">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900">
                Detalles del Log - {selectedLog.camera_name}
              </h3>
              <button
                onClick={() => setSelectedLog(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                <span className="sr-only">Cerrar</span>
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Cámara</label>
                  <p className="text-sm text-gray-900">{selectedLog.camera_name || 'N/A'}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">IP y Línea</label>
                  <p className="text-sm text-gray-900">{selectedLog.camera_ip}:{selectedLog.camera_line}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Parking</label>
                  <p className="text-sm text-gray-900">{selectedLog.parking_name || 'N/A'}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Estado</label>
                  <div className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(selectedLog.status)}`}>
                    {getStatusIcon(selectedLog.status)}
                    <span className="ml-1">{selectedLog.status}</span>
                  </div>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Mensaje JSON</label>
                <pre className="mt-1 p-3 bg-gray-100 rounded text-xs overflow-auto max-h-40">
                  {selectedLog.raw_message || 'N/A'}
                </pre>
              </div>

              {selectedLog.error_message && (
                <div>
                  <label className="block text-sm font-medium text-gray-700">Error</label>
                  <p className="text-sm text-red-600">{selectedLog.error_message}</p>
                </div>
              )}

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Tiempo de Procesamiento</label>
                  <p className="text-sm text-gray-900">{formatProcessingTime(selectedLog.processing_time)}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Estado del Parking</label>
                  <p className="text-sm text-gray-900">{selectedLog.parking_status || 'N/A'}</p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Recibido</label>
                  <p className="text-sm text-gray-900">{formatDateTime(selectedLog.received_at)}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Procesado</label>
                  <p className="text-sm text-gray-900">{formatDateTime(selectedLog.processed_at)}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default CameraLogs 