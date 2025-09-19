import { useQuery } from 'react-query'
import { Link } from 'react-router-dom'
import sensorService from '../services/sensorService'
import { 
  Cpu,
  Battery,
  BatteryLow,
  CheckCircle,
  AlertCircle,
  Info,
  Settings,
  TrendingUp,
  Activity,
  Zap,
  Car,
  RefreshCw,
  ArrowRight,
  Loader
} from 'lucide-react'

const SensorDashboardSection = () => {
  // Obtener estadísticas de sensores
  const { data: stats, isLoading: statsLoading, refetch: refetchStats } = useQuery(
    'sensor-dashboard-stats',
    () => sensorService.getSensorStats(),
    {
      refetchInterval: 30000, // Refrescar cada 30 segundos
      retry: 2
    }
  )

  // Obtener resumen agrupado
  const { data: groupedStatus = [], isLoading: groupedLoading } = useQuery(
    'sensor-grouped-status',
    () => sensorService.getGroupedStatus(),
    {
      refetchInterval: 30000,
      retry: 2
    }
  )

  // Obtener sensores con batería baja
  const { data: lowBatterySensors = [], isLoading: batteryLoading } = useQuery(
    'low-battery-sensors',
    () => sensorService.getAllSensors().then(sensors => 
      sensors.filter(s => s.battery_info?.is_low)
    ),
    {
      refetchInterval: 60000, // Refrescar cada minuto
      retry: 2
    }
  )

  const isLoading = statsLoading || groupedLoading || batteryLoading

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-center h-32">
          <Loader className="h-6 w-6 animate-spin text-blue-600 mr-2" />
          <span className="text-gray-600">Cargando estadísticas de sensores...</span>
        </div>
      </div>
    )
  }

  // Calcular métricas generales
  const totalSensors = stats?.total_sensors || 0
  const statusDistribution = stats?.status_distribution || {}
  const typeDistribution = stats?.type_distribution || {}

  const freeSensors = statusDistribution.free || 0
  const busySensors = statusDistribution.busy || 0
  const errorSensors = statusDistribution.error || 0
  const unknownSensors = statusDistribution.unknown || 0

  const occupancyRate = totalSensors > 0 ? ((busySensors / totalSensors) * 100).toFixed(1) : 0
  const healthRate = totalSensors > 0 ? (((totalSensors - errorSensors - unknownSensors) / totalSensors) * 100).toFixed(1) : 100

  // Función para obtener color por tipo
  const getTypeColor = (type) => {
    const colors = {
      'PMR': 'bg-blue-100 text-blue-800 border-blue-200',
      'Electrico': 'bg-green-100 text-green-800 border-green-200',
      'Caravanas': 'bg-orange-100 text-orange-800 border-orange-200',
      'Emergencias': 'bg-red-100 text-red-800 border-red-200',
      'Policia': 'bg-purple-100 text-purple-800 border-purple-200',
      'Otros': 'bg-gray-100 text-gray-800 border-gray-200'
    }
    return colors[type] || colors['Otros']
  }

  return (
    <div className="space-y-6">
      {/* Header con acciones */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-xl font-bold text-gray-900">Sensores Individuales</h2>
          <p className="text-sm text-gray-600">Monitorización en tiempo real de plazas PMR, eléctricas y especiales</p>
        </div>
        <div className="flex space-x-2">
          <button
            onClick={() => {
              refetchStats()
            }}
            className="px-3 py-2 bg-gray-600 text-white text-sm rounded-md hover:bg-gray-700 flex items-center space-x-1"
          >
            <RefreshCw className="h-4 w-4" />
            <span>Actualizar</span>
          </button>
          <Link
            to="/sensors"
            className="px-3 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 flex items-center space-x-1"
          >
            <Settings className="h-4 w-4" />
            <span>Gestionar</span>
          </Link>
        </div>
      </div>

      {/* Métricas principales */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {/* Total Sensores */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <Cpu className="h-8 w-8 text-blue-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Total Sensores</p>
              <p className="text-2xl font-bold text-gray-900">{totalSensors}</p>
            </div>
          </div>
        </div>

        {/* Libres */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <CheckCircle className="h-8 w-8 text-green-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Libres</p>
              <p className="text-2xl font-bold text-green-600">{freeSensors}</p>
            </div>
          </div>
        </div>

        {/* Ocupados */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <Car className="h-8 w-8 text-red-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Ocupados</p>
              <p className="text-2xl font-bold text-red-600">{busySensors}</p>
            </div>
          </div>
        </div>

        {/* Batería Baja */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <BatteryLow className="h-8 w-8 text-yellow-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Batería Baja</p>
              <p className="text-2xl font-bold text-yellow-600">{lowBatterySensors.length}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Métricas secundarias */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {/* Tasa de Ocupación */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-500">Tasa de Ocupación</p>
              <p className="text-3xl font-bold text-blue-600">{occupancyRate}%</p>
            </div>
            <TrendingUp className="h-8 w-8 text-blue-600" />
          </div>
          <div className="mt-2">
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-blue-600 h-2 rounded-full" 
                style={{ width: `${occupancyRate}%` }}
              ></div>
            </div>
          </div>
        </div>

        {/* Estado de Salud */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-500">Estado de Salud</p>
              <p className="text-3xl font-bold text-green-600">{healthRate}%</p>
            </div>
            <Activity className="h-8 w-8 text-green-600" />
          </div>
          <div className="mt-2">
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-green-600 h-2 rounded-full" 
                style={{ width: `${healthRate}%` }}
              ></div>
            </div>
          </div>
        </div>

        {/* Errores */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-500">Con Errores</p>
              <p className="text-3xl font-bold text-red-600">{errorSensors + unknownSensors}</p>
            </div>
            <AlertCircle className="h-8 w-8 text-red-600" />
          </div>
          <div className="mt-2 text-xs text-gray-500">
            {errorSensors} errores + {unknownSensors} desconocidos
          </div>
        </div>
      </div>

      {/* Distribución por tipos */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Distribución por Tipos</h3>
        </div>
        <div className="p-6">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {Object.entries(typeDistribution).map(([type, count]) => (
              <div key={type} className={`p-4 rounded-lg border ${getTypeColor(type)}`}>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">{sensorService.formatSensorType(type)}</p>
                    <p className="text-2xl font-bold">{count}</p>
                  </div>
                  <div className="text-right">
                    <Zap className="h-6 w-6 mb-1" />
                    <p className="text-xs">
                      {totalSensors > 0 ? ((count / totalSensors) * 100).toFixed(1) : 0}%
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Alertas de batería baja */}
      {lowBatterySensors.length > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center">
              <BatteryLow className="h-6 w-6 text-yellow-600 mr-2" />
              <h3 className="text-lg font-medium text-yellow-800">
                Sensores con Batería Baja ({lowBatterySensors.length})
              </h3>
            </div>
            <Link
              to="/sensors?filter=low_battery"
              className="text-yellow-700 hover:text-yellow-800 flex items-center text-sm"
            >
              <span>Ver todos</span>
              <ArrowRight className="h-4 w-4 ml-1" />
            </Link>
          </div>
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {lowBatterySensors.slice(0, 6).map((sensor) => (
              <div key={sensor.id} className="flex items-center justify-between p-3 bg-white rounded-lg border">
                <div>
                  <p className="font-medium text-gray-900">{sensor.name}</p>
                  <p className="text-sm text-gray-500">{sensor.serial_number}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium text-yellow-700">
                    {sensor.battery_info?.capacity}%
                  </p>
                  <p className="text-xs text-gray-500">{sensor.parking_name || 'Sin parking'}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Resumen por parkings */}
      {groupedStatus.length > 0 && (
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-medium text-gray-900">Resumen por Parkings</h3>
              <Link
                to="/parkings"
                className="text-blue-600 hover:text-blue-800 flex items-center text-sm"
              >
                <span>Ver parkings</span>
                <ArrowRight className="h-4 w-4 ml-1" />
              </Link>
            </div>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {groupedStatus.slice(0, 5).map((parkingData) => (
                <div key={parkingData.parking_id} className="border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="font-medium text-gray-900">{parkingData.parking_name}</h4>
                    <Link
                      to={`/parking/${parkingData.parking_id}`}
                      className="text-blue-600 hover:text-blue-800 text-sm flex items-center"
                    >
                      <span>Ver detalle</span>
                      <ArrowRight className="h-3 w-3 ml-1" />
                    </Link>
                  </div>
                  <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
                    <div className="text-center">
                      <p className="text-sm text-gray-500">Total</p>
                      <p className="text-lg font-semibold text-gray-900">{parkingData.total_sensors}</p>
                    </div>
                    <div className="text-center">
                      <p className="text-sm text-gray-500">Libres</p>
                      <p className="text-lg font-semibold text-green-600">{parkingData.free_sensors}</p>
                    </div>
                    <div className="text-center">
                      <p className="text-sm text-gray-500">Ocupados</p>
                      <p className="text-lg font-semibold text-red-600">{parkingData.busy_sensors}</p>
                    </div>
                    <div className="text-center">
                      <p className="text-sm text-gray-500">Errores</p>
                      <p className="text-lg font-semibold text-yellow-600">{parkingData.error_sensors}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default SensorDashboardSection
