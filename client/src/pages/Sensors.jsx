import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import sensorService from '../services/sensorService'
import parkingService from '../services/parkingService'
import { useAuth } from '../context/AuthContext'
import { EditSensorModal, StatusUpdateModal, SensorDetailModal } from '../components/SensorModals'
import { 
  Cpu,
  Battery,
  BatteryLow,
  Wifi,
  WifiOff,
  Plus,
  Edit,
  Trash2,
  Save,
  X,
  Loader,
  AlertCircle,
  CheckCircle,
  Info,
  RefreshCw,
  Filter,
  Search,
  MapPin,
  Calendar,
  Activity,
  BarChart3,
  Settings,
  Eye,
  Power,
  PowerOff,
  Zap
} from 'lucide-react'
import toast from 'react-hot-toast'

const Sensors = () => {
  const { isSuperadmin } = useAuth()
  const queryClient = useQueryClient()
  
  // Estados del componente
  const [selectedSensor, setSelectedSensor] = useState(null)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [showStatusModal, setShowStatusModal] = useState(false)
  const [showDetailModal, setShowDetailModal] = useState(false)
  const [editingForm, setEditingForm] = useState({})
  const [statusForm, setStatusForm] = useState({})
  
  // Estados de filtros
  const [filters, setFilters] = useState({
    parking_id: '',
    sensor_type: '',
    is_active: true,
    search: ''
  })
  const [showFilters, setShowFilters] = useState(false)

  // Estados de vista
  const [viewMode, setViewMode] = useState('table') // 'table', 'cards', 'dashboard'

  // Obtener datos
  const { data: sensors = [], isLoading, refetch } = useQuery(
    ['sensors', filters],
    () => sensorService.getAllSensors({
      parking_id: filters.parking_id || undefined,
      sensor_type: filters.sensor_type || undefined,
      is_active: filters.is_active
    }),
    {
      refetchInterval: 30000, // Refrescar cada 30 segundos
    }
  )

  // Obtener parkings con filtrado por permisos
  const { data: parkings = [] } = useQuery(
    'userParkings',
    () => parkingService.getParkings()
  )

  // Obtener resumen para dashboard
  const { data: summary = [] } = useQuery(
    'sensors-summary',
    () => sensorService.getSensorsSummary(),
    {
      enabled: viewMode === 'dashboard',
      refetchInterval: 30000
    }
  )

  // Mutaciones
  const createSensorMutation = useMutation(
    sensorService.createSensor,
    {
      onSuccess: () => {
        queryClient.invalidateQueries('sensors')
        queryClient.invalidateQueries('sensors-summary')
        toast.success('Sensor creado correctamente')
        setShowCreateModal(false)
        resetCreateForm()
      },
      onError: (error) => {
        toast.error(error?.response?.data?.error || 'Error creando sensor')
      }
    }
  )

  const updateSensorMutation = useMutation(
    ({ sensorId, data }) => sensorService.updateSensor(sensorId, data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('sensors')
        toast.success('Sensor actualizado correctamente')
        setShowEditModal(false)
        setSelectedSensor(null)
      },
      onError: (error) => {
        toast.error(error?.response?.data?.error || 'Error actualizando sensor')
      }
    }
  )

  const deleteSensorMutation = useMutation(
    sensorService.deleteSensor,
    {
      onSuccess: () => {
        queryClient.invalidateQueries('sensors')
        queryClient.invalidateQueries('sensors-summary')
        toast.success('Sensor eliminado correctamente')
      },
      onError: (error) => {
        toast.error(error?.response?.data?.error || 'Error eliminando sensor')
      }
    }
  )

  const updateStatusMutation = useMutation(
    ({ sensorId, statusData }) => sensorService.updateSensorStatus(sensorId, statusData),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('sensors')
        queryClient.invalidateQueries('sensors-summary')
        toast.success('Estado actualizado correctamente')
        setShowStatusModal(false)
        setSelectedSensor(null)
      },
      onError: (error) => {
        toast.error(error?.response?.data?.error || 'Error actualizando estado')
      }
    }
  )

  // Formulario de creación
  const [createForm, setCreateForm] = useState({
    serial_number: '',
    name: '',
    sensor_type: 'PMR',
    parking_id: '',
    description: '',
    location_coordinates: '',
    manufacturer: 'Fleximodo',
    is_active: true
  })

  const resetCreateForm = () => {
    setCreateForm({
      serial_number: '',
      name: '',
      sensor_type: 'PMR',
      parking_id: '',
      description: '',
      location_coordinates: '',
      manufacturer: 'Fleximodo',
      is_active: true
    })
  }

  // Funciones de manejo
  const handleCreateSensor = () => {
    // Validaciones básicas
    if (!createForm.serial_number.trim()) {
      toast.error('El número de serie es obligatorio')
      return
    }
    if (!createForm.name.trim()) {
      toast.error('El nombre es obligatorio')
      return
    }

    const sensorData = {
      ...createForm,
      parking_id: createForm.parking_id || null,
      location_coordinates: createForm.location_coordinates || null,
      description: createForm.description || null
    }

    createSensorMutation.mutate(sensorData)
  }

  const handleEditSensor = (sensor) => {
    setSelectedSensor(sensor)
    setEditingForm({
      serial_number: sensor.serial_number,
      name: sensor.name,
      sensor_type: sensor.sensor_type,
      parking_id: sensor.parking_id || '',
      description: sensor.description || '',
      location_coordinates: sensor.location_coordinates || '',
      manufacturer: sensor.manufacturer,
      is_active: sensor.is_active
    })
    setShowEditModal(true)
  }

  const handleUpdateSensor = () => {
    if (!selectedSensor) return

    const updateData = {
      ...editingForm,
      parking_id: editingForm.parking_id || null,
      location_coordinates: editingForm.location_coordinates || null,
      description: editingForm.description || null
    }

    updateSensorMutation.mutate({ 
      sensorId: selectedSensor.id, 
      data: updateData 
    })
  }

  const handleDeleteSensor = (sensor) => {
    if (window.confirm(`¿Estás seguro de eliminar el sensor "${sensor.name}"?`)) {
      deleteSensorMutation.mutate(sensor.id)
    }
  }

  const handleUpdateStatus = (sensor) => {
    setSelectedSensor(sensor)
    setStatusForm({
      status: sensor.current_status || 'unknown',
      battery_capacity: sensor.battery_info?.capacity || '',
      battery_voltage: sensor.battery_info?.voltage || '',
      temperature: ''
    })
    setShowStatusModal(true)
  }

  const handleSubmitStatus = () => {
    if (!selectedSensor) return

    const statusData = {
      status: statusForm.status,
      ...(statusForm.battery_capacity && { battery_capacity: parseInt(statusForm.battery_capacity) }),
      ...(statusForm.battery_voltage && { battery_voltage: parseFloat(statusForm.battery_voltage) }),
      ...(statusForm.temperature && { temperature: parseFloat(statusForm.temperature) })
    }

    updateStatusMutation.mutate({
      sensorId: selectedSensor.id,
      statusData
    })
  }

  const handleViewDetail = async (sensor) => {
    try {
      const detailData = await sensorService.getSensor(sensor.id)
      setSelectedSensor({ ...sensor, ...detailData })
      setShowDetailModal(true)
    } catch (error) {
      toast.error('Error obteniendo detalles del sensor')
    }
  }

  // Filtrar sensores localmente por búsqueda
  const filteredSensors = sensors.filter(sensor => {
    if (!filters.search) return true
    const searchLower = filters.search.toLowerCase()
    return (
      sensor.serial_number.toLowerCase().includes(searchLower) ||
      sensor.name.toLowerCase().includes(searchLower) ||
      (sensor.parking_name && sensor.parking_name.toLowerCase().includes(searchLower))
    )
  })

  // Funciones de utilidad
  const getStatusIcon = (status) => {
    switch (status) {
      case 'free':
        return <CheckCircle className="h-5 w-5 text-green-500" />
      case 'busy':
        return <AlertCircle className="h-5 w-5 text-red-500" />
      case 'error':
        return <AlertCircle className="h-5 w-5 text-yellow-500" />
      case 'unknown':
        return <Info className="h-5 w-5 text-gray-500" />
      default:
        return <Settings className="h-5 w-5 text-purple-500" />
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'free':
        return 'bg-green-100 text-green-800'
      case 'busy':
        return 'bg-red-100 text-red-800'
      case 'error':
        return 'bg-yellow-100 text-yellow-800'
      case 'unknown':
        return 'bg-gray-100 text-gray-800'
      case 'notcalib':
        return 'bg-purple-100 text-purple-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getTypeColor = (type) => {
    const typeColors = {
      'PMR': 'bg-blue-100 text-blue-800',
      'Electrico': 'bg-green-100 text-green-800',
      'Caravanas': 'bg-orange-100 text-orange-800',
      'Emergencias': 'bg-red-100 text-red-800',
      'Policia': 'bg-purple-100 text-purple-800',
      'Otros': 'bg-gray-100 text-gray-800'
    }
    return typeColors[type] || 'bg-gray-100 text-gray-800'
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader className="h-8 w-8 animate-spin text-primary-600" />
        <span className="ml-2 text-gray-600">Cargando sensores...</span>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Sensores Individuales</h1>
          <p className="text-gray-600">Gestión de sensores PMR, eléctricos y otros tipos</p>
        </div>
        
        <div className="flex space-x-3">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`px-4 py-2 rounded-md flex items-center space-x-2 ${
              showFilters ? 'bg-blue-600 text-white' : 'bg-white text-gray-700 border border-gray-300'
            }`}
          >
            <Filter className="h-4 w-4" />
            <span>Filtros</span>
          </button>
          
          <button
            onClick={() => refetch()}
            disabled={isLoading}
            className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 flex items-center space-x-2"
          >
            <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
            <span>Actualizar</span>
          </button>

          {isSuperadmin && (
            <button
              onClick={() => setShowCreateModal(true)}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 flex items-center space-x-2"
            >
              <Plus className="h-4 w-4" />
              <span>Nuevo Sensor</span>
            </button>
          )}
        </div>
      </div>

      {/* Estadísticas rápidas */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center">
            <Cpu className="h-8 w-8 text-blue-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Total Sensores</p>
              <p className="text-2xl font-bold text-gray-900">{filteredSensors.length}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center">
            <CheckCircle className="h-8 w-8 text-green-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Libres</p>
              <p className="text-2xl font-bold text-gray-900">
                {filteredSensors.filter(s => s.current_status === 'free').length}
              </p>
            </div>
          </div>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center">
            <AlertCircle className="h-8 w-8 text-red-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Ocupados</p>
              <p className="text-2xl font-bold text-gray-900">
                {filteredSensors.filter(s => s.current_status === 'busy').length}
              </p>
            </div>
          </div>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center">
            <BatteryLow className="h-8 w-8 text-yellow-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Batería Baja</p>
              <p className="text-2xl font-bold text-gray-900">
                {filteredSensors.filter(s => s.battery_info?.is_low).length}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Panel de filtros */}
      {showFilters && (
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Búsqueda
              </label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                <input
                  type="text"
                  value={filters.search}
                  onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
                  className="pl-10 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Buscar por serial, nombre..."
                />
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Parking
              </label>
              <select
                value={filters.parking_id}
                onChange={(e) => setFilters(prev => ({ ...prev, parking_id: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Todos los parkings</option>
                {parkings.map(parking => (
                  <option key={parking.id} value={parking.id}>
                    {parking.name}
                  </option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Tipo de Sensor
              </label>
              <select
                value={filters.sensor_type}
                onChange={(e) => setFilters(prev => ({ ...prev, sensor_type: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Todos los tipos</option>
                {sensorService.getSensorTypes().map(type => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Estado
              </label>
              <select
                value={filters.is_active}
                onChange={(e) => setFilters(prev => ({ ...prev, is_active: e.target.value === 'true' }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="true">Solo activos</option>
                <option value="false">Solo inactivos</option>
              </select>
            </div>
          </div>
        </div>
      )}

      {/* Tabla de sensores */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">
            Sensores ({filteredSensors.length})
          </h3>
        </div>
        
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Sensor
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Tipo
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Estado
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Parking
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Batería
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Última Actualización
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Acciones
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredSensors.map((sensor) => (
                <tr key={sensor.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div>
                      <div className="text-sm font-medium text-gray-900">
                        {sensor.name}
                      </div>
                      <div className="text-sm text-gray-500">
                        {sensor.serial_number}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getTypeColor(sensor.sensor_type)}`}>
                      {sensorService.formatSensorType(sensor.sensor_type)}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      {getStatusIcon(sensor.current_status)}
                      <span className={`ml-2 inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(sensor.current_status)}`}>
                        {sensorService.formatSensorStatus(sensor.current_status)}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {sensor.parking_name || 'Sin asignar'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {sensor.battery_info ? (
                      <div className="flex items-center">
                        {sensor.battery_info.is_low ? (
                          <BatteryLow className="h-4 w-4 text-red-500 mr-1" />
                        ) : (
                          <Battery className="h-4 w-4 text-green-500 mr-1" />
                        )}
                        <span className="text-sm text-gray-900">
                          {sensor.battery_info.capacity}%
                        </span>
                      </div>
                    ) : (
                      <span className="text-sm text-gray-400">N/A</span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {sensor.last_update ? (
                      new Date(sensor.last_update).toLocaleString()
                    ) : (
                      'Nunca'
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <div className="flex space-x-2">
                      <button
                        onClick={() => handleViewDetail(sensor)}
                        className="text-blue-600 hover:text-blue-900"
                        title="Ver detalles"
                      >
                        <Eye className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => handleUpdateStatus(sensor)}
                        className="text-green-600 hover:text-green-900"
                        title="Actualizar estado"
                      >
                        <Activity className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => handleEditSensor(sensor)}
                        className="text-indigo-600 hover:text-indigo-900"
                        title="Editar"
                      >
                        <Edit className="h-4 w-4" />
                      </button>
                      {isSuperadmin && (
                        <button
                          onClick={() => handleDeleteSensor(sensor)}
                          className="text-red-600 hover:text-red-900"
                          title="Eliminar"
                        >
                          <Trash2 className="h-4 w-4" />
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

      {/* Modal de creación */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Crear Nuevo Sensor</h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Número de Serie *
                  </label>
                  <input
                    type="text"
                    value={createForm.serial_number}
                    onChange={(e) => setCreateForm(prev => ({ ...prev, serial_number: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Ej: PMR001, ELE002..."
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Nombre *
                  </label>
                  <input
                    type="text"
                    value={createForm.name}
                    onChange={(e) => setCreateForm(prev => ({ ...prev, name: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Ej: Plaza PMR 1, Plaza Eléctrica A..."
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Tipo de Sensor
                  </label>
                  <select
                    value={createForm.sensor_type}
                    onChange={(e) => setCreateForm(prev => ({ ...prev, sensor_type: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {sensorService.getSensorTypes().map(type => (
                      <option key={type.value} value={type.value}>
                        {type.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Parking
                  </label>
                  <select
                    value={createForm.parking_id}
                    onChange={(e) => setCreateForm(prev => ({ ...prev, parking_id: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">Sin asignar</option>
                    {parkings.map(parking => (
                      <option key={parking.id} value={parking.id}>
                        {parking.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Descripción
                  </label>
                  <textarea
                    value={createForm.description}
                    onChange={(e) => setCreateForm(prev => ({ ...prev, description: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    rows="3"
                    placeholder="Descripción opcional del sensor..."
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Coordenadas (lat,lng)
                  </label>
                  <input
                    type="text"
                    value={createForm.location_coordinates}
                    onChange={(e) => setCreateForm(prev => ({ ...prev, location_coordinates: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Ej: 38.5,-0.5"
                  />
                </div>
              </div>

              <div className="flex justify-end space-x-3 mt-6">
                <button
                  onClick={() => {
                    setShowCreateModal(false)
                    resetCreateForm()
                  }}
                  className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
                >
                  Cancelar
                </button>
                <button
                  onClick={handleCreateSensor}
                  disabled={createSensorMutation.isLoading}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
                >
                  {createSensorMutation.isLoading ? 'Creando...' : 'Crear Sensor'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modales adicionales */}
      <EditSensorModal
        show={showEditModal}
        sensor={selectedSensor}
        editingForm={editingForm}
        setEditingForm={setEditingForm}
        onClose={() => {
          setShowEditModal(false)
          setSelectedSensor(null)
        }}
        onUpdate={handleUpdateSensor}
        isLoading={updateSensorMutation.isLoading}
        parkings={parkings}
      />

      <StatusUpdateModal
        show={showStatusModal}
        sensor={selectedSensor}
        statusForm={statusForm}
        setStatusForm={setStatusForm}
        onClose={() => {
          setShowStatusModal(false)
          setSelectedSensor(null)
        }}
        onUpdate={handleSubmitStatus}
        isLoading={updateStatusMutation.isLoading}
      />

      <SensorDetailModal
        show={showDetailModal}
        sensor={selectedSensor}
        onClose={() => setShowDetailModal(false)}
      />
    </div>
  )
}

export default Sensors
