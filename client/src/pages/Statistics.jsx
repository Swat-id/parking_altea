import { useState } from 'react'
import { useQuery } from 'react-query'
import { authService } from '../services/authService'
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

  // Obtener parkings del usuario
  const { data: parkings = [] } = useQuery(
    'userParkings',
    authService.getUserParkings
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

  // Calcular estadísticas
  const totalParkings = parkings.length
  const totalPlazas = parkings.reduce((sum, p) => sum + p.total_plazas, 0)
  const plazasOcupadas = parkings.reduce((sum, p) => sum + p.plazas_ocupadas, 0)
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
              <p className="text-sm font-medium text-gray-500">Ocupación Actual</p>
              <p className="text-lg font-semibold text-gray-900">{porcentajeOcupacion}%</p>
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
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-medium text-gray-900">Tendencia de Ocupación</h2>
          <div className="text-sm text-gray-500">
            {selectedParking === 'all' ? 'Todos los parkings' : 
             parkings.find(p => p.id === parseInt(selectedParking))?.name}
          </div>
        </div>
        
        <div className="h-64 flex items-end justify-between space-x-2">
          {occupancyData.map((data, index) => (
            <div key={index} className="flex-1 flex flex-col items-center">
              <div className="w-full bg-gray-200 rounded-t" style={{ height: '200px' }}>
                <div
                  className="bg-primary-600 rounded-t transition-all duration-300"
                  style={{ 
                    height: `${(data.occupancy / 100) * 200}px`,
                    minHeight: '4px'
                  }}
                />
              </div>
              <div className="text-xs text-gray-500 mt-2 text-center">
                {format(new Date(data.date), 'dd/MM', { locale: es })}
              </div>
              <div className="text-xs font-medium text-gray-700 mt-1">
                {data.occupancy}%
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Tabla de datos */}
      <div className="card">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Datos Detallados</h2>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Fecha
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Parking
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Ocupación
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Total
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Porcentaje
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {occupancyData.slice(0, 10).map((data, index) => (
                <tr key={index} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {format(new Date(data.date), 'dd/MM/yyyy', { locale: es })}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {parkings.find(p => p.id === data.parking_id)?.name || 'N/A'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {data.occupancy}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {data.total}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      data.occupancy < 50 ? 'bg-green-100 text-green-800' :
                      data.occupancy < 80 ? 'bg-yellow-100 text-yellow-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {Math.round((data.occupancy / data.total) * 100)}%
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Resumen por parking */}
      <div className="card">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Resumen por Parking</h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {parkings.map((parking) => (
            <div key={parking.id} className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-medium text-gray-900 truncate">
                  {parking.name}
                </h3>
                <div className={`flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(parking.estado)}`}>
                  {parking.estado}
                </div>
              </div>
              <div className="space-y-1 text-sm text-gray-500">
                <div className="flex justify-between">
                  <span>Ocupadas:</span>
                  <span className="font-medium">{parking.plazas_ocupadas}</span>
                </div>
                <div className="flex justify-between">
                  <span>Libres:</span>
                  <span className="font-medium">{parking.plazas_libres}</span>
                </div>
                <div className="flex justify-between">
                  <span>Total:</span>
                  <span className="font-medium">{parking.total_plazas}</span>
                </div>
                <div className="pt-2">
                  <div className="flex justify-between text-xs mb-1">
                    <span>Ocupación</span>
                    <span>{Math.round((parking.plazas_ocupadas / parking.total_plazas) * 100)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-1">
                    <div
                      className={`h-1 rounded-full ${
                        parking.estado === 'LIBRE' ? 'bg-green-500' :
                        parking.estado === 'DENSO' ? 'bg-yellow-500' : 'bg-red-500'
                      }`}
                      style={{
                        width: `${Math.round((parking.plazas_ocupadas / parking.total_plazas) * 100)}%`
                      }}
                    />
                  </div>
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