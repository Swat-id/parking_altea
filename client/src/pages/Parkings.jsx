import { useState } from 'react'
import { useQuery } from 'react-query'
import { Link } from 'react-router-dom'
import { authService } from '../services/authService'
import { 
  Car, 
  Search, 
  Filter,
  Edit,
  Eye,
  CheckCircle,
  Clock,
  AlertCircle,
  MapPin
} from 'lucide-react'

const Parkings = () => {
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('ALL')

  const { data: parkings = [], isLoading } = useQuery(
    'userParkings',
    authService.getUserParkings
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

  const filteredParkings = parkings.filter(parking => {
    const matchesSearch = parking.name.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesStatus = statusFilter === 'ALL' || parking.estado === statusFilter
    return matchesSearch && matchesStatus
  })

  const getOcupationPercentage = (ocupadas, total) => {
    return total > 0 ? Math.round((ocupadas / total) * 100) : 0
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
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Parkings</h1>
        <p className="mt-1 text-sm text-gray-500">
          Gestión y monitoreo de todos los aparcamientos
        </p>
      </div>

      {/* Filtros */}
      <div className="card">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
              <input
                type="text"
                placeholder="Buscar parking..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="input-field pl-10"
              />
            </div>
          </div>
          <div className="sm:w-48">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="input-field"
            >
              <option value="ALL">Todos los estados</option>
              <option value="LIBRE">Libre</option>
              <option value="DENSO">Denso</option>
              <option value="COMPLETO">Completo</option>
            </select>
          </div>
        </div>
      </div>

      {/* Estadísticas rápidas */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-4">
        <div className="card">
          <div className="flex items-center">
            <Car className="h-8 w-8 text-primary-600" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500">Total</p>
              <p className="text-lg font-semibold text-gray-900">{parkings.length}</p>
            </div>
          </div>
        </div>
        <div className="card">
          <div className="flex items-center">
            <CheckCircle className="h-8 w-8 text-green-600" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500">Libres</p>
              <p className="text-lg font-semibold text-gray-900">
                {parkings.filter(p => p.estado === 'LIBRE').length}
              </p>
            </div>
          </div>
        </div>
        <div className="card">
          <div className="flex items-center">
            <Clock className="h-8 w-8 text-yellow-600" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500">Densos</p>
              <p className="text-lg font-semibold text-gray-900">
                {parkings.filter(p => p.estado === 'DENSO').length}
              </p>
            </div>
          </div>
        </div>
        <div className="card">
          <div className="flex items-center">
            <AlertCircle className="h-8 w-8 text-red-600" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500">Completos</p>
              <p className="text-lg font-semibold text-gray-900">
                {parkings.filter(p => p.estado === 'COMPLETO').length}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Lista de parkings */}
      <div className="card">
        <div className="overflow-hidden">
          {filteredParkings.length === 0 ? (
            <div className="text-center py-12">
              <Car className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No se encontraron parkings</h3>
              <p className="mt-1 text-sm text-gray-500">
                {searchTerm || statusFilter !== 'ALL' 
                  ? 'Intenta ajustar los filtros de búsqueda.'
                  : 'No hay parkings disponibles.'
                }
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
              {filteredParkings.map((parking) => (
                <div key={parking.id} className="border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow duration-200">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                      <h3 className="text-lg font-medium text-gray-900 mb-1">
                        {parking.name}
                      </h3>
                      <div className="flex items-center text-sm text-gray-500">
                        <MapPin className="h-4 w-4 mr-1" />
                        ID: {parking.id}
                      </div>
                    </div>
                    <div className={`flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(parking.estado)}`}>
                      {getStatusIcon(parking.estado)}
                      <span className="ml-1">{parking.estado}</span>
                    </div>
                  </div>

                  <div className="space-y-3">
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-gray-500">Ocupación</span>
                        <span className="font-medium">
                          {getOcupationPercentage(parking.plazas_ocupadas, parking.total_plazas)}%
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full ${
                            parking.estado === 'LIBRE' ? 'bg-green-500' :
                            parking.estado === 'DENSO' ? 'bg-yellow-500' : 'bg-red-500'
                          }`}
                          style={{
                            width: `${getOcupationPercentage(parking.plazas_ocupadas, parking.total_plazas)}%`
                          }}
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <p className="text-gray-500">Ocupadas</p>
                        <p className="font-medium text-gray-900">{parking.plazas_ocupadas}</p>
                      </div>
                      <div>
                        <p className="text-gray-500">Libres</p>
                        <p className="font-medium text-gray-900">{parking.plazas_libres}</p>
                      </div>
                      <div>
                        <p className="text-gray-500">Total</p>
                        <p className="font-medium text-gray-900">{parking.total_plazas}</p>
                      </div>
                      <div>
                        <p className="text-gray-500">Umbral Denso</p>
                        <p className="font-medium text-gray-900">{parking.threshold_dense}</p>
                      </div>
                    </div>

                    <div className="flex space-x-2 pt-2">
                      <Link
                        to={`/parking/${parking.id}`}
                        className="flex-1 btn-primary text-center py-2"
                      >
                        <Eye className="h-4 w-4 inline mr-1" />
                        Ver detalles
                      </Link>
                      <Link
                        to={`/parking/${parking.id}`}
                        className="btn-secondary py-2 px-3"
                      >
                        <Edit className="h-4 w-4" />
                      </Link>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default Parkings 