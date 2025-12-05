import { useQuery } from 'react-query'
import { Link } from 'react-router-dom'
import parkingService from '../services/parkingService'
import sensorService from '../services/sensorService'
import SensorDashboardSection from '../components/SensorDashboardSection'
import ParkingMap from '../components/ParkingMap'
import { 
  Car, 
  Monitor, 
  TrendingUp, 
  AlertCircle,
  CheckCircle,
  Clock,
  MapPin,
  Cpu,
  Activity,
  Map
} from 'lucide-react'

const Dashboard = () => {
  // Usar la API con filtrado por permisos
  const { data: parkings = [], isLoading: parkingsLoading, error: parkingsError } = useQuery(
    'userParkings',
    parkingService.getParkings,
    {
      retry: 2,
      refetchOnWindowFocus: false,
      staleTime: 30000, // 30 segundos
    }
  )

  // Obtener estadísticas completas del dashboard
  const { data: dashboardStats, isLoading: statsLoading } = useQuery(
    'dashboard-complete',
    () => sensorService.getDashboardComplete(),
    {
      retry: 2,
      refetchInterval: 60000, // Refrescar cada minuto
      staleTime: 30000
    }
  )

  const getStatusColor = (status) => {
    switch (status) {
      case 'LIBRE':
        return 'text-green-600 bg-green-100'
      case 'DENSO':
        return 'text-yellow-600 bg-yellow-100'
      case 'COMPLETO':
        return 'text-red-600 bg-red-100'
      default:
        return 'text-gray-600 bg-gray-100'
    }
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'LIBRE':
        return <CheckCircle className="h-5 w-5" />
      case 'DENSO':
        return <Clock className="h-5 w-5" />
      case 'COMPLETO':
        return <AlertCircle className="h-5 w-5" />
      default:
        return <Clock className="h-5 w-5" />
    }
  }

  // Mostrar loading mientras se cargan los datos
  if (parkingsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Cargando datos de parkings...</p>
        </div>
      </div>
    )
  }

  // Mostrar error si falla la carga
  if (parkingsError) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <p className="text-red-600">Error al cargar los datos de parkings</p>
          <p className="text-sm text-gray-500 mt-2">Por favor, inténtalo de nuevo más tarde</p>
        </div>
      </div>
    )
  }

  const totalParkings = parkings.length
  const totalPlazas = parkings.reduce((sum, parking) => sum + (parking.total_plazas || 0), 0)
  const plazasOcupadas = parkings.reduce((sum, parking) => sum + (parking.plazas_ocupadas || 0), 0)
  const porcentajeOcupacion = totalPlazas > 0 ? Math.round((plazasOcupadas / totalPlazas) * 100) : 0

  const parkingsLibres = parkings.filter(p => p.estado === 'LIBRE').length
  const parkingsDensos = parkings.filter(p => p.estado === 'DENSO').length
  const parkingsCompletos = parkings.filter(p => p.estado === 'COMPLETO').length

  // Estadísticas de sensores desde dashboardStats
  const sensorStats = dashboardStats?.sensor_stats || {}
  const totalSensors = sensorStats.total_sensors || 0
  const totalPanels = dashboardStats?.summary?.total_panels || 0

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-1 text-sm text-gray-500">
          Resumen general del sistema de parkings de Altea
        </p>
      </div>

      {/* Estadísticas principales */}
      <div className="grid grid-cols-1 gap-4 sm:gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <Car className="h-6 w-6 sm:h-8 sm:w-8 text-primary-600" />
            </div>
            <div className="ml-3 sm:ml-5 w-0 flex-1 min-w-0">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">
                  Total Parkings
                </dt>
                <dd className="text-lg font-medium text-gray-900">
                  {totalParkings}
                </dd>
              </dl>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <TrendingUp className="h-6 w-6 sm:h-8 sm:w-8 text-green-600" />
            </div>
            <div className="ml-3 sm:ml-5 w-0 flex-1 min-w-0">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">
                  Ocupación Total
                </dt>
                <dd className="text-lg font-medium text-gray-900">
                  {porcentajeOcupacion}%
                </dd>
              </dl>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <Monitor className="h-6 w-6 sm:h-8 sm:w-8 text-blue-600" />
            </div>
            <div className="ml-3 sm:ml-5 w-0 flex-1 min-w-0">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">
                  Plazas Ocupadas
                </dt>
                <dd className="text-lg font-medium text-gray-900">
                  {plazasOcupadas} / {totalPlazas}
                </dd>
              </dl>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <MapPin className="h-6 w-6 sm:h-8 sm:w-8 text-purple-600" />
            </div>
            <div className="ml-3 sm:ml-5 w-0 flex-1 min-w-0">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">
                  Estado General
                </dt>
                <dd className="text-lg font-medium text-gray-900">
                  {parkingsLibres} libres
                </dd>
              </dl>
            </div>
          </div>
        </div>
      </div>

      {/* Estado por categorías */}
      <div className="grid grid-cols-1 gap-4 sm:gap-5 sm:grid-cols-3">
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-500">Libres</p>
              <p className="text-xl sm:text-2xl font-bold text-green-600">{parkingsLibres}</p>
            </div>
            <CheckCircle className="h-6 w-6 sm:h-8 sm:w-8 text-green-600" />
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-500">Densos</p>
              <p className="text-xl sm:text-2xl font-bold text-yellow-600">{parkingsDensos}</p>
            </div>
            <Clock className="h-6 w-6 sm:h-8 sm:w-8 text-yellow-600" />
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-500">Completos</p>
              <p className="text-xl sm:text-2xl font-bold text-red-600">{parkingsCompletos}</p>
            </div>
            <AlertCircle className="h-6 w-6 sm:h-8 sm:w-8 text-red-600" />
          </div>
        </div>
      </div>

      {/* Mapa de Parkings */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center">
            <Map className="h-5 w-5 text-primary-600 mr-2" />
            <h2 className="text-lg font-medium text-gray-900">Mapa de Parkings</h2>
          </div>
          <div className="flex items-center gap-4 text-sm">
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-green-500"></span>
              <span className="text-gray-600">Libre</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-yellow-500"></span>
              <span className="text-gray-600">Denso</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-red-500"></span>
              <span className="text-gray-600">Completo</span>
            </div>
          </div>
        </div>
        <ParkingMap 
          parkings={parkings} 
          height="450px"
          className="rounded-lg overflow-hidden"
        />
        <p className="mt-3 text-sm text-gray-500 text-center">
          Haz clic en un parking para ver su información detallada
        </p>
      </div>

      {/* Lista de parkings */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-medium text-gray-900">Parkings</h2>
          <Link
            to="/parkings"
            className="text-sm font-medium text-primary-600 hover:text-primary-500"
          >
            Ver todos →
          </Link>
        </div>
        
        <div className="overflow-hidden">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {parkings.slice(0, 6).map((parking) => (
              <Link
                key={parking.id}
                to={`/parking/${parking.id}`}
                className="block p-4 border border-gray-200 rounded-lg hover:border-primary-300 hover:shadow-md transition-all duration-200"
              >
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-sm font-medium text-gray-900 truncate">
                    {parking.name}
                  </h3>
                  <div className={`flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(parking.estado)}`}>
                    {getStatusIcon(parking.estado)}
                    <span className="ml-1">{parking.estado}</span>
                  </div>
                </div>
                <div className="text-sm text-gray-500">
                  <p>{parking.plazas_ocupadas || 0} / {parking.total_plazas || 0} plazas</p>
                  <p className="mt-1">
                    {parking.plazas_libres || 0} plazas libres
                  </p>
                </div>
              </Link>
            ))}
          </div>
        </div>
      </div>

      {/* Sección de Sensores Individuales */}
      <SensorDashboardSection />
    </div>
  )
}

export default Dashboard 