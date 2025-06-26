import React, { useState, useEffect } from 'react'
import { useQuery } from 'react-query'
import { cameraLogService } from '../services/cameraLogService'
import { parkingService } from '../services/parkingService'
import { cameraService } from '../services/cameraService'
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
import { useSearchParams } from 'react-router-dom'

const CameraLogs = () => {
  const [searchParams] = useSearchParams()
  const [logs, setLogs] = useState([])
  const [cameras, setCameras] = useState([])
  const [parkings, setParkings] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedParking, setSelectedParking] = useState(searchParams.get('parking') || '')
  const [selectedCamera, setSelectedCamera] = useState('')
  const [dateFilter, setDateFilter] = useState('today')
  const [logLevel, setLogLevel] = useState('all')
  const [lastUpdate, setLastUpdate] = useState(null)
  const [stats, setStats] = useState({})

  useEffect(() => {
    loadData()
  }, [selectedParking, selectedCamera, dateFilter, logLevel])

  const loadData = async () => {
    try {
      setLoading(true)
      setError(null)
      
      // Cargar parkings
      const parkingsData = await parkingService.getParkings()
      setParkings(parkingsData || [])
      
      // Cargar cámaras si hay parking seleccionado
      if (selectedParking) {
        try {
          const camerasData = await cameraService.getParkingCameras(selectedParking)
          setCameras(camerasData.cameras || [])
        } catch (err) {
          console.error('Error cargando cámaras:', err)
          setCameras([])
        }
      } else {
        setCameras([])
      }
      
      // Cargar logs con filtros
      const logsData = await cameraLogService.getCameraLogs({
        parking_id: selectedParking || undefined,
        camera_id: selectedCamera || undefined,
        date_filter: dateFilter,
        level: logLevel === 'all' ? undefined : logLevel,
        limit: 100
      })
      
      setLogs(logsData.logs || [])
      
      // Cargar estadísticas
      try {
        const statsData = await cameraLogService.getCameraLogsStats({
          parking_id: selectedParking || undefined,
          days: 7
        })
        setStats(statsData || {})
      } catch (err) {
        console.error('Error cargando estadísticas:', err)
        setStats({})
      }
      
      setLastUpdate(new Date())
    } catch (err) {
      setError('Error cargando datos')
      console.error('Error:', err)
    } finally {
      setLoading(false)
    }
  }

  const getLogLevelColor = (level) => {
    switch (level?.toLowerCase()) {
      case 'error':
        return 'text-red-600 bg-red-100'
      case 'warning':
        return 'text-yellow-600 bg-yellow-100'
      case 'info':
        return 'text-blue-600 bg-blue-100'
      default:
        return 'text-gray-600 bg-gray-100'
    }
  }

  const getLogLevelIcon = (level) => {
    switch (level?.toLowerCase()) {
      case 'error':
        return '❌'
      case 'warning':
        return '⚠️'
      case 'info':
        return 'ℹ️'
      default:
        return '📝'
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

  const formatLastUpdate = () => {
    if (!lastUpdate) return 'Nunca'
    return lastUpdate.toLocaleString('es-ES')
  }

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
        <h1 className="text-3xl font-bold text-gray-900">📋 Logs de Cámaras</h1>
        <p className="text-gray-600">Registro de actividad y eventos de las cámaras</p>
        {lastUpdate && (
          <p className="text-sm text-gray-500 mt-2">
            Última actualización: {formatLastUpdate()}
          </p>
        )}
      </div>

      {/* Filtros */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">🔍 Filtros</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Filtro por Parking */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Parking
            </label>
            <select
              value={selectedParking}
              onChange={(e) => setSelectedParking(e.target.value)}
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

          {/* Filtro por Cámara */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Cámara
            </label>
            <select
              value={selectedCamera}
              onChange={(e) => setSelectedCamera(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={!selectedParking}
            >
              <option value="">Todas las cámaras</option>
              {cameras.map((camera) => (
                <option key={camera.id} value={camera.id}>
                  {camera.name} ({camera.ip})
                </option>
              ))}
            </select>
          </div>

          {/* Filtro por Fecha */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Período
            </label>
            <select
              value={dateFilter}
              onChange={(e) => setDateFilter(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="today">Hoy</option>
              <option value="yesterday">Ayer</option>
              <option value="week">Última semana</option>
              <option value="month">Último mes</option>
              <option value="all">Todo</option>
            </select>
          </div>

          {/* Filtro por Nivel */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Nivel
            </label>
            <select
              value={logLevel}
              onChange={(e) => setLogLevel(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">Todos</option>
              <option value="error">Error</option>
              <option value="warning">Warning</option>
              <option value="info">Info</option>
            </select>
          </div>
        </div>

        {/* Botón de actualizar */}
        <div className="mt-4 flex items-center space-x-4">
          <button
            onClick={loadData}
            disabled={loading}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? '🔄 Actualizando...' : '🔄 Actualizar'}
          </button>
          
          {error && (
            <span className="text-red-600 text-sm">{error}</span>
          )}
        </div>
      </div>

      {/* Estadísticas */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500">Total Logs</h3>
          <p className="text-2xl font-bold text-gray-900">{logs.length}</p>
        </div>
        
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500">Errores</h3>
          <p className="text-2xl font-bold text-red-600">
            {logs.filter(log => log.level?.toLowerCase() === 'error').length}
          </p>
        </div>
        
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500">Warnings</h3>
          <p className="text-2xl font-bold text-yellow-600">
            {logs.filter(log => log.level?.toLowerCase() === 'warning').length}
          </p>
        </div>
        
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500">Info</h3>
          <p className="text-2xl font-bold text-blue-600">
            {logs.filter(log => log.level?.toLowerCase() === 'info').length}
          </p>
        </div>
      </div>

      {/* Lista de Logs */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">
            Registros ({logs.length})
          </h2>
        </div>
        
        <div className="overflow-x-auto">
          {logs.length === 0 ? (
            <div className="text-center py-8">
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
                    Nivel
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Parking
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Cámara
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Mensaje
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Detalles
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {logs.map((log) => (
                  <tr key={log.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      <div>
                        <div className="font-medium">{formatTimestamp(log.received_at || log.timestamp)}</div>
                        <div className="text-xs text-gray-500">{getRelativeTime(log.received_at || log.timestamp)}</div>
                      </div>
                    </td>
                    
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getLogLevelColor(log.level)}`}>
                        {getLogLevelIcon(log.level)} {log.level || 'INFO'}
                      </span>
                    </td>
                    
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {log.parking_name || 'N/A'}
                    </td>
                    
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      <div>
                        <div className="font-medium">{log.camera_name || 'N/A'}</div>
                        <div className="text-xs text-gray-500">{log.camera_ip || ''}</div>
                      </div>
                    </td>
                    
                    <td className="px-6 py-4 text-sm text-gray-900">
                      <div className="max-w-xs truncate" title={log.message || log.error_message}>
                        {log.message || log.error_message || 'Sin mensaje'}
                      </div>
                    </td>
                    
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {(log.raw_message || log.details) && (
                        <details className="text-xs">
                          <summary className="cursor-pointer hover:text-gray-700">
                            Ver detalles
                          </summary>
                          <pre className="mt-2 p-2 bg-gray-100 rounded text-xs overflow-x-auto">
                            {JSON.stringify(log.raw_message || log.details, null, 2)}
                          </pre>
                        </details>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  )
}

export default CameraLogs 