import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { parkingService } from '../services/parkingService'
import { statisticsService } from '../services/statisticsService'
import { 
  BarChart3, 
  TrendingUp, 
  Clock, 
  Calendar,
  RefreshCw,
  Download,
  Filter,
  Camera,
  Activity,
  AlertCircle,
  CheckCircle,
  Wifi,
  WifiOff
} from 'lucide-react'
import toast from 'react-hot-toast'

const Statistics = () => {
  const { id } = useParams()
  const navigate = useNavigate()
  const [parkings, setParkings] = useState([])
  const [parking, setParking] = useState(null)
  const [hourlyStats, setHourlyStats] = useState([])
  const [cameraStats, setCameraStats] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [dateFilter, setDateFilter] = useState('today')
  const [customDate, setCustomDate] = useState('')
  const [lastUpdate, setLastUpdate] = useState(null)

  // Validar que tenemos un ID válido
  if (!id) {
    return (
      <div className="max-w-7xl mx-auto p-6">
        <div className="text-center py-8">
          <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Error: Parking no especificado</h2>
          <p className="text-gray-600 mb-4">Debes seleccionar un parking para ver sus estadísticas.</p>
          <button
            onClick={() => window.history.back()}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            ← Volver
          </button>
        </div>
      </div>
    )
  }

  // Cargar lista de parkings al montar
  useEffect(() => {
    async function fetchParkings() {
      try {
        const data = await parkingService.getParkings()
        setParkings(data)
        // Si no hay id, redirigir al primer parking
        if (!id && data.length > 0) {
          navigate(`/statistics/${data[0].id}`, { replace: true })
        }
      } catch (e) {
        toast.error('Error cargando lista de parkings')
      }
    }
    fetchParkings()
  }, [id, navigate])

  useEffect(() => {
    if (id) {
      loadData()
    }
  }, [id, dateFilter, customDate])

  const loadData = async () => {
    try {
      setLoading(true)
      setError(null)
      
      // Cargar información del parking
      const parkingData = await parkingService.getParking(id)
      setParking(parkingData)
      
      // Determinar fecha para estadísticas
      let dateParam = null
      if (dateFilter === 'custom' && customDate) {
        dateParam = customDate
      } else if (dateFilter === 'today') {
        dateParam = new Date().toISOString().split('T')[0]
      }
      
      // Cargar estadísticas por horas
      const statsData = await statisticsService.getHourlyStatistics(id, {
        date: dateParam,
        days: dateFilter === 'week' ? 7 : 1
      })
      
      setHourlyStats(statsData.hourly_statistics || [])
      setCameraStats(statsData.camera_statistics || [])
      setLastUpdate(new Date())
      
    } catch (err) {
      setError('Error cargando estadísticas')
      console.error('Error:', err)
      toast.error('Error cargando estadísticas')
    } finally {
      setLoading(false)
    }
  }

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A'
    const date = new Date(dateString)
    return date.toLocaleDateString('es-ES', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  }

  const formatTime = (dateString) => {
    if (!dateString) return 'N/A'
    const date = new Date(dateString)
    return date.toLocaleTimeString('es-ES', {
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getRelativeTime = (dateString) => {
    if (!dateString) return ''
    const date = new Date(dateString)
    const now = new Date()
    const diffMs = now - date
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    
    if (diffMins < 1) return 'Ahora mismo'
    if (diffMins < 60) return `Hace ${diffMins} min`
    if (diffHours < 24) return `Hace ${diffHours}h ${diffMins % 60}min`
    return `Hace ${Math.floor(diffHours / 24)} días`
  }

  const getStatusIcon = (status) => {
    switch (status?.toLowerCase()) {
      case 'online':
        return <Wifi className="w-4 h-4 text-green-600" />
      case 'offline':
        return <WifiOff className="w-4 h-4 text-red-600" />
      default:
        return <AlertCircle className="w-4 h-4 text-gray-400" />
    }
  }

  if (loading && !parking) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto p-6">
        <div className="text-center py-8">
          <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Error cargando estadísticas</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={loadData}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            🔄 Reintentar
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      {/* Header con selector de parking */}
      <div className="mb-6 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">
            📊 Estadísticas - {parking?.name}
          </h1>
          <p className="text-gray-600">Análisis detallado de ocupación y actividad</p>
          {lastUpdate && (
            <p className="text-sm text-gray-500 mt-2">
              Última actualización: {lastUpdate.toLocaleString('es-ES')}
            </p>
          )}
        </div>
        <div className="w-full md:w-72">
          <label className="block text-sm font-medium text-gray-700 mb-1">Selecciona aparcamiento</label>
          <select
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={id || ''}
            onChange={e => navigate(`/statistics/${e.target.value}`)}
          >
            {parkings.map(p => (
              <option key={p.id} value={p.id}>{p.name}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Filtros */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">🔍 Filtros</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
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
              <option value="custom">Fecha personalizada</option>
            </select>
          </div>

          {dateFilter === 'custom' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Fecha
              </label>
              <input
                type="date"
                value={customDate}
                onChange={(e) => setCustomDate(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          )}

          <div className="flex items-end">
            <button
              onClick={loadData}
              disabled={loading}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? '🔄 Actualizando...' : '🔄 Actualizar'}
            </button>
          </div>
        </div>
      </div>

      {/* Resumen */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500">Total Entradas</h3>
          <p className="text-2xl font-bold text-green-600">
            {hourlyStats.reduce((sum, stat) => sum + stat.total_vehicles_in, 0)}
          </p>
        </div>
        
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500">Total Salidas</h3>
          <p className="text-2xl font-bold text-red-600">
            {hourlyStats.reduce((sum, stat) => sum + stat.total_vehicles_out, 0)}
          </p>
        </div>
        
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500">Cambio Neto</h3>
          <p className="text-2xl font-bold text-blue-600">
            {hourlyStats.reduce((sum, stat) => sum + stat.net_change, 0)}
          </p>
        </div>
        
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500">Mensajes Procesados</h3>
          <p className="text-2xl font-bold text-gray-900">
            {hourlyStats.reduce((sum, stat) => sum + stat.message_count, 0)}
          </p>
        </div>
      </div>

      {/* Gráfico de Ocupación por Horas */}
      <div className="bg-white rounded-lg shadow mb-6">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">
            📈 Ocupación por Horas
          </h2>
        </div>
        
        <div className="p-6">
          {hourlyStats.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-gray-500">No hay datos de ocupación para mostrar</p>
            </div>
          ) : (
            <div className="space-y-4">
              {hourlyStats.map((stat) => (
                <div key={stat.hour} className="flex items-center space-x-4">
                  <div className="w-16 text-sm font-medium text-gray-700">
                    {stat.hour_label}
                  </div>
                  
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-1">
                      <div className="flex-1 bg-gray-200 rounded-full h-4">
                        <div 
                          className="bg-blue-600 h-4 rounded-full"
                          style={{ 
                            width: `${Math.min((stat.avg_occupancy / (parking?.max_capacity || 100)) * 100, 100)}%` 
                          }}
                        ></div>
                      </div>
                      <span className="text-sm font-medium text-gray-900">
                        {stat.avg_occupancy}
                      </span>
                    </div>
                    
                    <div className="flex justify-between text-xs text-gray-500">
                      <span>Min: {stat.min_occupancy}</span>
                      <span>Max: {stat.max_occupancy}</span>
                    </div>
                  </div>
                  
                  <div className="text-right text-sm">
                    <div className="text-green-600">+{stat.total_vehicles_in}</div>
                    <div className="text-red-600">-{stat.total_vehicles_out}</div>
                    <div className="text-gray-600">{stat.message_count} msgs</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Estadísticas de Cámaras */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">
            📷 Estadísticas de Cámaras
          </h2>
        </div>
        
        <div className="overflow-x-auto">
          {cameraStats.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-gray-500">No hay datos de cámaras para mostrar</p>
            </div>
          ) : (
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Cámara
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Estado
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Mensajes
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Tasa de Éxito
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Vehículos
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Último Mensaje
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {cameraStats.map((camera) => (
                  <tr key={camera.camera_id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          {camera.camera_name}
                        </div>
                        <div className="text-sm text-gray-500">
                          {camera.camera_ip} (Línea {camera.camera_line})
                        </div>
                      </div>
                    </td>
                    
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center space-x-2">
                        {getStatusIcon(camera.status)}
                        <span className="text-sm text-gray-900">
                          {camera.status || 'UNKNOWN'}
                        </span>
                      </div>
                    </td>
                    
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      <div>
                        <div>Total: {camera.total_messages}</div>
                        <div className="text-green-600">✓ {camera.processed_messages}</div>
                        <div className="text-red-600">✗ {camera.error_messages}</div>
                        {camera.duplicate_messages > 0 && (
                          <div className="text-yellow-600">🔄 {camera.duplicate_messages}</div>
                        )}
                      </div>
                    </td>
                    
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center space-x-2">
                        <div className="flex-1 bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-green-600 h-2 rounded-full"
                            style={{ width: `${camera.success_rate}%` }}
                          ></div>
                        </div>
                        <span className="text-sm font-medium text-gray-900">
                          {camera.success_rate}%
                        </span>
                      </div>
                    </td>
                    
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      <div>
                        <div className="text-green-600">+{camera.total_vehicles_in}</div>
                        <div className="text-red-600">-{camera.total_vehicles_out}</div>
                      </div>
                    </td>
                    
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <div>
                        <div>{formatTime(camera.last_message)}</div>
                        <div className="text-xs">{getRelativeTime(camera.last_message)}</div>
                      </div>
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

export default Statistics 