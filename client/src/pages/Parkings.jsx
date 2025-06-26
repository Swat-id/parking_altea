import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import { Link } from 'react-router-dom'
import { parkingService } from '../services/parkingService'
import { 
  Car, 
  Search, 
  Filter,
  Edit,
  Eye,
  CheckCircle,
  Clock,
  AlertCircle,
  MapPin,
  Save,
  X
} from 'lucide-react'
import toast from 'react-hot-toast'

const Parkings = () => {
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('ALL')
  const [editingParking, setEditingParking] = useState(null)
  const [editForm, setEditForm] = useState({
    total_plazas: 0,
    threshold_dense: 0,
    threshold_full: 0
  })

  const queryClient = useQueryClient()

  const { data: parkings = [], isLoading, error } = useQuery(
    'allParkings',
    parkingService.getAllParkings,
    {
      retry: 2,
      refetchOnWindowFocus: false,
      staleTime: 30000, // 30 segundos
    }
  )

  // Mutación para actualizar configuración
  const updateConfigMutation = useMutation(
    ({ parkingId, config }) => parkingService.updateConfig(parkingId, config),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('allParkings')
        toast.success('Configuración actualizada correctamente')
        setEditingParking(null)
      },
      onError: (error) => {
        toast.error(error?.response?.data?.message || 'Error al actualizar la configuración')
      }
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

  const filteredParkings = parkings.filter(parking => {
    const matchesSearch = parking.name.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesStatus = statusFilter === 'ALL' || parking.estado === statusFilter
    return matchesSearch && matchesStatus
  })

  const getOcupationPercentage = (ocupadas, total) => {
    return total > 0 ? Math.round((ocupadas / total) * 100) : 0
  }

  const startEditing = (parking) => {
    setEditingParking(parking.id)
    setEditForm({
      total_plazas: parking.total_plazas || 0,
      threshold_dense: parking.threshold_dense || 0,
      threshold_full: parking.threshold_full || 0
    })
  }

  const cancelEditing = () => {
    setEditingParking(null)
    setEditForm({
      total_plazas: 0,
      threshold_dense: 0,
      threshold_full: 0
    })
  }

  const saveConfig = (parkingId) => {
    // Validaciones
    if (editForm.total_plazas <= 0) {
      toast.error('El total de plazas debe ser mayor que 0')
      return
    }

    if (editForm.threshold_dense <= editForm.threshold_full) {
      toast.error('El umbral denso debe ser mayor que el umbral completo')
      return
    }

    if (editForm.threshold_full > 100) {
      toast.error('El umbral completo no puede ser mayor al 100%')
      return
    }

    if (editForm.threshold_dense > 100) {
      toast.error('El umbral denso no puede ser mayor al 100%')
      return
    }

    updateConfigMutation.mutate({
      parkingId,
      config: {
        total_plazas: editForm.total_plazas,
        threshold_dense: editForm.threshold_dense,
        threshold_full: editForm.threshold_full
      }
    })
  }

  // Mostrar loading mientras se cargan los datos
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Cargando parkings...</p>
        </div>
      </div>
    )
  }

  // Mostrar error si falla la carga
  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <p className="text-red-600">Error al cargar los parkings</p>
          <p className="text-sm text-gray-500 mt-2">Por favor, inténtalo de nuevo más tarde</p>
        </div>
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
            <div className="grid grid-cols-1 gap-4 sm:gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {filteredParkings.map((parking) => (
                <div key={parking.id} className="border border-gray-200 rounded-lg p-4 sm:p-6 hover:shadow-md transition-all duration-200 bg-white">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1 min-w-0">
                      <h3 className="text-base sm:text-lg font-medium text-gray-900 mb-1 truncate">
                        {parking.name}
                      </h3>
                      <div className="flex items-center text-sm text-gray-500">
                        <MapPin className="h-4 w-4 mr-1 flex-shrink-0" />
                        <span className="truncate">ID: {parking.id}</span>
                      </div>
                    </div>
                    <div className={`flex items-center px-2 py-1 rounded-full text-xs font-medium ml-2 flex-shrink-0 ${getStatusColor(parking.estado)}`}>
                      {getStatusIcon(parking.estado)}
                      <span className="ml-1 hidden sm:inline">{parking.estado}</span>
                      <span className="ml-1 sm:hidden">{parking.estado.charAt(0)}</span>
                    </div>
                  </div>

                  <div className="space-y-3">
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-gray-500">Ocupación</span>
                        <span className="font-medium">
                          {getOcupationPercentage(parking.plazas_ocupadas || 0, parking.total_plazas || 0)}%
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full transition-all duration-300 ${
                            getOcupationPercentage(parking.plazas_ocupadas || 0, parking.total_plazas || 0) < 50
                              ? 'bg-green-500'
                              : getOcupationPercentage(parking.plazas_ocupadas || 0, parking.total_plazas || 0) < 80
                              ? 'bg-yellow-500'
                              : 'bg-red-500'
                          }`}
                          style={{
                            width: `${getOcupationPercentage(parking.plazas_ocupadas || 0, parking.total_plazas || 0)}%`
                          }}
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-2 sm:gap-4 text-sm">
                      <div className="text-center sm:text-left">
                        <div className="text-gray-500 text-xs sm:text-sm">Ocupadas</div>
                        <div className="font-medium text-sm sm:text-base">{parking.plazas_ocupadas || 0}</div>
                      </div>
                      <div className="text-center sm:text-left">
                        <div className="text-gray-500 text-xs sm:text-sm">Libres</div>
                        <div className="font-medium text-sm sm:text-base">{parking.plazas_libres || 0}</div>
                      </div>
                      <div className="col-span-2 text-center sm:text-left">
                        <div className="text-gray-500 text-xs sm:text-sm">Total</div>
                        <div className="font-medium text-sm sm:text-base">{parking.total_plazas || 0} plazas</div>
                      </div>
                    </div>

                    {/* Configuración de umbrales */}
                    {editingParking === parking.id ? (
                      <div className="space-y-2 border-t pt-3">
                        <div className="text-xs font-medium text-gray-700">Configuración de Umbrales</div>
                        <div className="grid grid-cols-2 gap-2 text-xs">
                          <div>
                            <label className="block text-gray-500">Denso</label>
                            <input
                              type="number"
                              value={editForm.threshold_dense}
                              onChange={(e) => setEditForm({...editForm, threshold_dense: parseInt(e.target.value) || 0})}
                              className="w-full px-2 py-1 border border-gray-300 rounded text-xs"
                              min="0"
                              max="100"
                            />
                          </div>
                          <div>
                            <label className="block text-gray-500">Completo</label>
                            <input
                              type="number"
                              value={editForm.threshold_full}
                              onChange={(e) => setEditForm({...editForm, threshold_full: parseInt(e.target.value) || 0})}
                              className="w-full px-2 py-1 border border-gray-300 rounded text-xs"
                              min="0"
                              max="100"
                            />
                          </div>
                        </div>
                        <div>
                          <label className="block text-gray-500">Total Plazas</label>
                          <input
                            type="number"
                            value={editForm.total_plazas}
                            onChange={(e) => setEditForm({...editForm, total_plazas: parseInt(e.target.value) || 0})}
                            className="w-full px-2 py-1 border border-gray-300 rounded text-xs"
                            min="1"
                          />
                        </div>
                        <div className="flex space-x-1">
                          <button
                            onClick={() => saveConfig(parking.id)}
                            disabled={updateConfigMutation.isLoading}
                            className="flex-1 px-2 py-1 bg-green-600 text-white text-xs rounded hover:bg-green-700 disabled:opacity-50"
                          >
                            {updateConfigMutation.isLoading ? 'Guardando...' : 'Guardar'}
                          </button>
                          <button
                            onClick={cancelEditing}
                            className="px-2 py-1 bg-gray-600 text-white text-xs rounded hover:bg-gray-700"
                          >
                            Cancelar
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div className="text-xs text-gray-500 border-t pt-3">
                        <div>Umbral Denso: {parking.threshold_dense || 0}</div>
                        <div>Umbral Completo: {parking.threshold_full || 0}</div>
                      </div>
                    )}
                  </div>

                  <div className="mt-4 flex space-x-2">
                    <Link
                      to={`/parking/${parking.id}`}
                      className="flex-1 bg-primary-600 text-white text-center py-2 px-3 sm:px-4 rounded-md hover:bg-primary-700 transition-colors duration-200 text-sm font-medium"
                    >
                      <Eye className="h-4 w-4 inline mr-1" />
                      <span className="hidden sm:inline">Ver detalles</span>
                      <span className="sm:hidden">Detalles</span>
                    </Link>
                    {editingParking !== parking.id && (
                      <button
                        onClick={() => startEditing(parking)}
                        className="px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors duration-200 text-sm"
                      >
                        <Edit className="h-4 w-4" />
                      </button>
                    )}
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