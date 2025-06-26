import { useState } from 'react'
import { useQuery } from 'react-query'
import { parkingService } from '../services/parkingService'
import { 
  BarChart3, 
  TrendingUp, 
  Calendar, 
  Clock,
  Download,
  Filter,
  Car,
  CheckCircle,
  AlertCircle
} from 'lucide-react'
import { format, subDays, startOfDay, endOfDay } from 'date-fns'
import { es } from 'date-fns/locale'

const Statistics = () => {
  const [selectedParking, setSelectedParking] = useState('all')
  const [dateRange, setDateRange] = useState('7d') // 7d, 30d, 90d
  const [selectedDate, setSelectedDate] = useState(new Date())

  // Obtener todos los parkings
  const { data: parkings = [], isLoading: parkingsLoading, error: parkingsError } = useQuery(
    'allParkings',
    parkingService.getAllParkings,
    {
      retry: 2,
      refetchOnWindowFocus: false,
      staleTime: 30000, // 30 segundos
    }
  )

  // Obtener datos de ocupación (simulado por ahora)
  const { data: occupancyData = [] } = useQuery(
    ['occupancy', selectedParking, dateRange, selectedDate],
    () => {
      // Simular datos de ocupación
      const days = dateRange === '7d' ? 7 : dateRange === '30d' ? 30 : 90
      const data = []
      
      for (let i = days - 1; i >= 0; i--) {
        const date = subDays(new Date(), i)
        data.push({
          date: format(date, 'yyyy-MM-dd'),
          occupancy: Math.floor(Math.random() * 100),
          total: 500,
          parking_id: selectedParking === 'all' ? 1 : parseInt(selectedParking)
        })
      }
      
      return data
    },
    {
      enabled: !!parkings.length
    }
  )

  // Mostrar loading mientras se cargan los datos
  if (parkingsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Cargando estadísticas...</p>
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
          <p className="text-red-600">Error al cargar las estadísticas</p>
          <p className="text-sm text-gray-500 mt-2">Por favor, inténtalo de nuevo más tarde</p>
        </div>
      </div>
    )
  }

  // Calcular estadísticas
  const totalParkings = parkings.length
  const totalPlazas = parkings.reduce((sum, p) => sum + (p.total_plazas || 0), 0)
  const plazasOcupadas = parkings.reduce((sum, p) => sum + (p.plazas_ocupadas || 0), 0)
  const porcentajeOcupacion = totalPlazas > 0 ? Math.round((plazasOcupadas / totalPlazas) * 100) : 0

  const parkingsLibres = parkings.filter(p => p.estado === 'LIBRE').length
  const parkingsDensos = parkings.filter(p => p.estado === 'DENSO').length
  const parkingsCompletos = parkings.filter(p => p.estado === 'COMPLETO').length

  // Calcular tendencias
  const averageOccupancy = occupancyData.length > 0 
    ? Math.round(occupancyData.reduce((sum, d) => sum + d.occupancy, 0) / occupancyData.length)
    : 0

  const maxOccupancy = occupancyData.length > 0 
    ? Math.max(...occupancyData.map(d => d.occupancy))
    : 0

  const minOccupancy = occupancyData.length > 0 
    ? Math.min(...occupancyData.map(d => d.occupancy))
    : 0

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

  const exportData = () => {
    const csvContent = [
      ['Fecha', 'Parking', 'Ocupación', 'Total Plazas', 'Porcentaje'],
      ...occupancyData.map(d => [
        d.date,
        parkings.find(p => p.id === d.parking_id)?.name || 'N/A',
        d.occupancy,
        d.total,
        `${Math.round((d.occupancy / d.total) * 100)}%`
      ])
    ].map(row => row.join(',')).join('\n')

    const blob = new Blob([csvContent], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `parking_occupancy_${format(new Date(), 'yyyy-MM-dd')}.csv`
    a.click()
    window.URL.revokeObjectURL(url)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Estadísticas</h1>
          <p className="mt-1 text-sm text-gray-500">
            Análisis y tendencias de ocupación de parkings
          </p>
        </div>
        <button
          onClick={exportData}
          className="btn-secondary flex items-center"
        >
          <Download className="h-4 w-4 mr-2" />
          Exportar
        </button>
      </div>

      {/* Filtros */}
      <div className="card">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Parking
            </label>
            <select
              value={selectedParking}
              onChange={(e) => setSelectedParking(e.target.value)}
              className="input-field"
            >
              <option value="all">Todos los parkings</option>
              {parkings.map((parking) => (
                <option key={parking.id} value={parking.id}>
                  {parking.name}
                </option>
              ))}
            </select>
          </div>
          <div className="sm:w-48">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Período
            </label>
            <select
              value={dateRange}
              onChange={(e) => setDateRange(e.target.value)}
              className="input-field"
            >
              <option value="7d">Últimos 7 días</option>
              <option value="30d">Últimos 30 días</option>
              <option value="90d">Últimos 90 días</option>
            </select>
          </div>
        </div>
      </div>

      {/* Estadísticas principales */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <div className="card">
          <div className="flex items-center">
            <BarChart3 className="h-8 w-8 text-primary-600" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500">Ocupación Promedio</p>
              <p className="text-lg font-semibold text-gray-900">{averageOccupancy}%</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <TrendingUp className="h-8 w-8 text-green-600" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500">Máxima Ocupación</p>
              <p className="text-lg font-semibold text-gray-900">{maxOccupancy}%</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <TrendingUp className="h-8 w-8 text-blue-600" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500">Mínima Ocupación</p>
              <p className="text-lg font-semibold text-gray-900">{minOccupancy}%</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <Car className="h-8 w-8 text-purple-600" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500">Total Parkings</p>
              <p className="text-lg font-semibold text-gray-900">{totalParkings}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Estado actual de parkings */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-3">
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-500">Libres</p>
              <p className="text-2xl font-bold text-green-600">{parkingsLibres}</p>
            </div>
            <CheckCircle className="h-8 w-8 text-green-600" />
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-500">Densos</p>
              <p className="text-2xl font-bold text-yellow-600">{parkingsDensos}</p>
            </div>
            <Clock className="h-8 w-8 text-yellow-600" />
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-500">Completos</p>
              <p className="text-2xl font-bold text-red-600">{parkingsCompletos}</p>
            </div>
            <AlertCircle className="h-8 w-8 text-red-600" />
          </div>
        </div>
      </div>

      {/* Gráfico de ocupación */}
      <div className="card">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Tendencia de Ocupación</h3>
        <div className="space-y-4">
          {occupancyData.map((day) => (
            <div key={day.date} className="flex items-center space-x-4">
              <div className="w-24 text-sm text-gray-500">
                {format(new Date(day.date), 'dd/MM', { locale: es })}
              </div>
              <div className="flex-1">
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-500">Ocupación</span>
                  <span className="font-medium">{day.occupancy}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${
                      day.occupancy < 50 ? 'bg-green-500' :
                      day.occupancy < 80 ? 'bg-yellow-500' : 'bg-red-500'
                    }`}
                    style={{ width: `${day.occupancy}%` }}
                  />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default Statistics 