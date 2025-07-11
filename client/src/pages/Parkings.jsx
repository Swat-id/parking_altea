import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import { Link } from 'react-router-dom'
import { parkingService } from '../services/parkingService'
import CameraAssignmentModal from '../components/CameraAssignmentModal'
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
  X,
  Plus,
  Camera
} from 'lucide-react'
import toast from 'react-hot-toast'

const Parkings = () => {
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('ALL')
  const [editingParking, setEditingParking] = useState(null)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showCameraModal, setShowCameraModal] = useState(false)
  const [editForm, setEditForm] = useState({
    total_plazas: 0,
    threshold_dense: 0,
    threshold_full: 0
  })
  const [createForm, setCreateForm] = useState({
    name: '',
    location: '',
    total_plazas: 0,
    threshold_dense: 0,
    threshold_full: 0
  })
  const [assignedCameras, setAssignedCameras] = useState([])

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

  // Mutación para crear parking
  const createParkingMutation = useMutation(
    (parkingData) => parkingService.createParking(parkingData),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('allParkings')
        toast.success('Parking creado correctamente')
        setShowCreateModal(false)
        setCreateForm({
          name: '',
          location: '',
          total_plazas: 0,
          threshold_dense: 0,
          threshold_full: 0
        })
        setAssignedCameras([])
      },
      onError: (error) => {
        toast.error(error?.response?.data?.message || 'Error al crear el parking')
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
    if (total <= 0) return 0
    const percentage = Math.round((ocupadas / total) * 100)
    // Limitar al 100% máximo para evitar que la barra se desborde
    return Math.min(percentage, 100)
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

  const handleCreateParking = (e) => {
    e.preventDefault()
    
    // Validaciones
    if (!createForm.name.trim()) {
      toast.error('El nombre del parking es requerido')
      return
    }

    if (createForm.total_plazas <= 0) {
      toast.error('El total de plazas debe ser mayor que 0')
      return
    }

    if (createForm.threshold_dense <= createForm.threshold_full) {
      toast.error('El umbral denso debe ser mayor que el umbral completo')
      return
    }

    // Incluir cámaras asignadas en los datos del parking
    const parkingData = {
      ...createForm,
      cameras: assignedCameras
    }

    createParkingMutation.mutate(parkingData)
  }

  const handleCameraAssignment = (cameras) => {
    setAssignedCameras(cameras)
    setShowCameraModal(false)
  }

  const openCameraModal = () => {
    setShowCameraModal(true)
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
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Parkings</h1>
          <p className="mt-1 text-sm text-gray-500">
            Gestión y monitoreo de todos los aparcamientos
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 flex items-center"
        >
          <Plus className="h-4 w-4 mr-2" />
          Crear Parking
        </button>
      </div>

      {/* Filtros */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Buscar
            </label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Buscar por nombre..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Estado
            </label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="ALL">Todos los estados</option>
              <option value="LIBRE">Libre</option>
              <option value="DENSO">Denso</option>
              <option value="COMPLETO">Completo</option>
            </select>
          </div>
          <div className="flex items-end">
            <div className="text-sm text-gray-500">
              {filteredParkings.length} de {parkings.length} parkings
            </div>
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
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Parking
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Estado
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Ocupación
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Configuración
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Acciones
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredParkings.map((parking) => (
                <tr key={parking.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div>
                      <div className="text-sm font-medium text-gray-900">
                        {parking.name}
                      </div>
                      {parking.location && (
                        <div className="text-sm text-gray-500 flex items-center">
                          <MapPin className="h-3 w-3 mr-1" />
                          {parking.location}
                        </div>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      {getStatusIcon(parking.estado)}
                      <span className={`ml-2 inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(parking.estado)}`}>
                        {parking.estado}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div>
                      <div className="text-sm text-gray-900">
                        {parking.plazas_ocupadas} / {parking.total_plazas}
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
                        <div
                          className="bg-blue-600 h-2 rounded-full"
                          style={{ width: `${getOcupationPercentage(parking.plazas_ocupadas, parking.total_plazas)}%` }}
                        ></div>
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        {parking.plazas_libres} plazas libres
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {editingParking === parking.id ? (
                      <div className="space-y-2">
                        <div>
                          <label className="block text-xs text-gray-500">Total plazas</label>
                          <input
                            type="number"
                            value={editForm.total_plazas}
                            onChange={(e) => setEditForm({...editForm, total_plazas: parseInt(e.target.value) || 0})}
                            className="w-20 px-2 py-1 text-sm border border-gray-300 rounded"
                          />
                        </div>
                        <div>
                          <label className="block text-xs text-gray-500">Umbral denso</label>
                          <input
                            type="number"
                            value={editForm.threshold_dense}
                            onChange={(e) => setEditForm({...editForm, threshold_dense: parseInt(e.target.value) || 0})}
                            className="w-20 px-2 py-1 text-sm border border-gray-300 rounded"
                          />
                        </div>
                        <div>
                          <label className="block text-xs text-gray-500">Umbral completo</label>
                          <input
                            type="number"
                            value={editForm.threshold_full}
                            onChange={(e) => setEditForm({...editForm, threshold_full: parseInt(e.target.value) || 0})}
                            className="w-20 px-2 py-1 text-sm border border-gray-300 rounded"
                          />
                        </div>
                        <div className="flex space-x-1">
                          <button
                            onClick={() => saveConfig(parking.id)}
                            className="text-green-600 hover:text-green-900"
                          >
                            <Save className="h-4 w-4" />
                          </button>
                          <button
                            onClick={cancelEditing}
                            className="text-red-600 hover:text-red-900"
                          >
                            <X className="h-4 w-4" />
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div className="text-sm text-gray-500">
                        <div>Denso: {parking.threshold_dense}</div>
                        <div>Completo: {parking.threshold_full}</div>
                      </div>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <div className="flex space-x-2">
                      <Link
                        to={`/parking/${parking.id}`}
                        className="text-blue-600 hover:text-blue-900"
                      >
                        <Eye className="h-4 w-4" />
                      </Link>
                      {editingParking !== parking.id && (
                        <button
                          onClick={() => startEditing(parking)}
                          className="text-green-600 hover:text-green-900"
                        >
                          <Edit className="h-4 w-4" />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal de creación de parking */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Crear Nuevo Parking</h3>
              <form onSubmit={handleCreateParking}>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Nombre
                  </label>
                  <input
                    type="text"
                    value={createForm.name}
                    onChange={(e) => setCreateForm({...createForm, name: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Ej: P. Centro Comercial"
                    required
                  />
                </div>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Ubicación (GPS)
                  </label>
                  <input
                    type="text"
                    value={createForm.location}
                    onChange={(e) => setCreateForm({...createForm, location: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Ej: 38.607426920203615,-0.04519652478288384"
                  />
                </div>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Total de Plazas
                  </label>
                  <input
                    type="number"
                    value={createForm.total_plazas}
                    onChange={(e) => setCreateForm({...createForm, total_plazas: parseInt(e.target.value) || 0})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="100"
                    required
                  />
                </div>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Umbral Denso
                  </label>
                  <input
                    type="number"
                    value={createForm.threshold_dense}
                    onChange={(e) => setCreateForm({...createForm, threshold_dense: parseInt(e.target.value) || 0})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="25"
                    required
                  />
                </div>
                <div className="mb-6">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Umbral Completo
                  </label>
                  <input
                    type="number"
                    value={createForm.threshold_full}
                    onChange={(e) => setCreateForm({...createForm, threshold_full: parseInt(e.target.value) || 0})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="5"
                    required
                  />
                </div>
                
                {/* Sección de Cámaras */}
                <div className="mb-6">
                  <div className="flex items-center justify-between mb-2">
                    <label className="block text-sm font-medium text-gray-700">
                      Cámaras Asignadas
                    </label>
                    <button
                      type="button"
                      onClick={openCameraModal}
                      className="flex items-center px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200 transition-colors"
                    >
                      <Camera className="h-4 w-4 mr-1" />
                      {assignedCameras.length > 0 ? 'Editar' : 'Añadir'} Cámaras
                    </button>
                  </div>
                  
                  {assignedCameras.length > 0 ? (
                    <div className="space-y-2">
                      {assignedCameras.map((camera, index) => (
                        <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded-md">
                          <div className="flex-1">
                            <div className="text-sm font-medium text-gray-900">
                              {camera.name || `Cámara ${index + 1}`}
                            </div>
                            <div className="text-xs text-gray-500">
                              {camera.ip} - Línea {camera.line}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-sm text-gray-500 italic">
                      No hay cámaras asignadas. Haga clic en "Añadir Cámaras" para configurar.
                    </div>
                  )}
                </div>
                <div className="flex justify-end space-x-3">
                  <button
                    type="button"
                    onClick={() => setShowCreateModal(false)}
                    className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
                  >
                    Cancelar
                  </button>
                  <button
                    type="submit"
                    disabled={createParkingMutation.isLoading}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
                  >
                    {createParkingMutation.isLoading ? 'Creando...' : 'Crear Parking'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Modal de asignación de cámaras */}
      <CameraAssignmentModal
        isOpen={showCameraModal}
        onClose={() => setShowCameraModal(false)}
        onSave={handleCameraAssignment}
        existingCameras={assignedCameras}
      />
    </div>
  )
}

export default Parkings 