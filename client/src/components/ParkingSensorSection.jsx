import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import sensorService from '../services/sensorService'
import { 
  Cpu,
  Battery,
  BatteryLow,
  CheckCircle,
  AlertCircle,
  Info,
  Settings,
  Activity,
  RefreshCw,
  Eye,
  Edit,
  Plus,
  Loader
} from 'lucide-react'
import toast from 'react-hot-toast'
import { StatusUpdateModal, SensorDetailModal } from './SensorModals'

const ParkingSensorSection = ({ parkingId, parkingName }) => {
  const queryClient = useQueryClient()
  
  // Estados
  const [selectedSensor, setSelectedSensor] = useState(null)
  const [showStatusModal, setShowStatusModal] = useState(false)
  const [showDetailModal, setShowDetailModal] = useState(false)
  const [statusForm, setStatusForm] = useState({})
  const [expandedTypes, setExpandedTypes] = useState({})

  // Obtener sensores del parking
  const { data: sensors = [], isLoading, refetch } = useQuery(
    ['parking-sensors', parkingId],
    () => sensorService.getAllSensors({ parking_id: parkingId }),
    {
      refetchInterval: 30000, // Refrescar cada 30 segundos
      enabled: !!parkingId
    }
  )

  // Obtener resumen agrupado
  const { data: summary = [] } = useQuery(
    ['parking-sensors-summary', parkingId],
    () => sensorService.getSensorsSummary(parkingId),
    {
      refetchInterval: 30000,
      enabled: !!parkingId
    }
  )

  // Mutación para actualizar estado
  const updateStatusMutation = useMutation(
    ({ sensorId, statusData }) => sensorService.updateSensorStatus(sensorId, statusData),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['parking-sensors', parkingId])
        queryClient.invalidateQueries(['parking-sensors-summary', parkingId])
        toast.success('Estado actualizado correctamente')
        setShowStatusModal(false)
        setSelectedSensor(null)
      },
      onError: (error) => {
        toast.error(error?.response?.data?.error || 'Error actualizando estado')
      }
    }
  )

  // Agrupar sensores por tipo
  const sensorsByType = sensors.reduce((acc, sensor) => {
    const type = sensor.sensor_type
    if (!acc[type]) {
      acc[type] = []
    }
    acc[type].push(sensor)
    return acc
  }, {})

  // Funciones de utilidad
  const getStatusIcon = (status) => {
    switch (status) {
      case 'free':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'busy':
        return <AlertCircle className="h-4 w-4 text-red-500" />
      case 'error':
        return <AlertCircle className="h-4 w-4 text-yellow-500" />
      case 'unknown':
        return <Info className="h-4 w-4 text-gray-500" />
      default:
        return <Settings className="h-4 w-4 text-purple-500" />
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
      'PMR': 'bg-blue-100 text-blue-800 border-blue-200',
      'Electrico': 'bg-green-100 text-green-800 border-green-200',
      'Caravanas': 'bg-orange-100 text-orange-800 border-orange-200',
      'Emergencias': 'bg-red-100 text-red-800 border-red-200',
      'Policia': 'bg-purple-100 text-purple-800 border-purple-200',
      'Otros': 'bg-gray-100 text-gray-800 border-gray-200'
    }
    return typeColors[type] || 'bg-gray-100 text-gray-800 border-gray-200'
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

  const toggleTypeExpansion = (type) => {
    setExpandedTypes(prev => ({
      ...prev,
      [type]: !prev[type]
    }))
  }

  const getSummaryForType = (type) => {
    return summary.find(s => s.sensor_type === type) || {
      total_sensors: 0,
      free_count: 0,
      busy_count: 0,
      error_count: 0,
      unknown_count: 0
    }
  }

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">
            📡 Sensores Individuales
          </h2>
        </div>
        <div className="flex items-center justify-center py-8">
          <Loader className="h-6 w-6 animate-spin text-blue-600 mr-2" />
          <span className="text-gray-600">Cargando sensores...</span>
        </div>
      </div>
    )
  }

  if (sensors.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex justify-between items-center">
            <h2 className="text-lg font-semibold text-gray-900">
              📡 Sensores Individuales (0)
            </h2>
            <button
              onClick={() => window.open('/sensors', '_blank')}
              className="px-3 py-1 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 flex items-center space-x-1"
            >
              <Plus className="h-4 w-4" />
              <span>Añadir Sensores</span>
            </button>
          </div>
        </div>
        <div className="text-center py-8">
          <Cpu className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500 mb-2">No hay sensores configurados para este parking</p>
          <p className="text-sm text-gray-400">
            Los sensores individuales permiten monitorizar plazas PMR, eléctricas y otros tipos específicos
          </p>
        </div>
      </div>
    )
  }

  return (
    <>
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex justify-between items-center">
            <h2 className="text-lg font-semibold text-gray-900">
              📡 Sensores Individuales ({sensors.length})
            </h2>
            <div className="flex space-x-2">
              <button
                onClick={() => refetch()}
                disabled={isLoading}
                className="px-3 py-1 bg-gray-600 text-white text-sm rounded-md hover:bg-gray-700 flex items-center space-x-1"
              >
                <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
                <span>Actualizar</span>
              </button>
              <button
                onClick={() => window.open('/sensors', '_blank')}
                className="px-3 py-1 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 flex items-center space-x-1"
              >
                <Edit className="h-4 w-4" />
                <span>Gestionar</span>
              </button>
            </div>
          </div>
        </div>

        <div className="p-6 space-y-6">
          {/* Resumen general */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
              <div className="flex items-center">
                <Cpu className="h-6 w-6 text-blue-600 mr-2" />
                <div>
                  <p className="text-sm font-medium text-blue-800">Total</p>
                  <p className="text-xl font-bold text-blue-900">{sensors.length}</p>
                </div>
              </div>
            </div>
            
            <div className="bg-green-50 p-4 rounded-lg border border-green-200">
              <div className="flex items-center">
                <CheckCircle className="h-6 w-6 text-green-600 mr-2" />
                <div>
                  <p className="text-sm font-medium text-green-800">Libres</p>
                  <p className="text-xl font-bold text-green-900">
                    {sensors.filter(s => s.current_status === 'free').length}
                  </p>
                </div>
              </div>
            </div>
            
            <div className="bg-red-50 p-4 rounded-lg border border-red-200">
              <div className="flex items-center">
                <AlertCircle className="h-6 w-6 text-red-600 mr-2" />
                <div>
                  <p className="text-sm font-medium text-red-800">Ocupados</p>
                  <p className="text-xl font-bold text-red-900">
                    {sensors.filter(s => s.current_status === 'busy').length}
                  </p>
                </div>
              </div>
            </div>
            
            <div className="bg-yellow-50 p-4 rounded-lg border border-yellow-200">
              <div className="flex items-center">
                <BatteryLow className="h-6 w-6 text-yellow-600 mr-2" />
                <div>
                  <p className="text-sm font-medium text-yellow-800">Batería Baja</p>
                  <p className="text-xl font-bold text-yellow-900">
                    {sensors.filter(s => s.battery_info?.is_low).length}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Sensores agrupados por tipo */}
          <div className="space-y-4">
            {Object.entries(sensorsByType).map(([type, typeSensors]) => {
              const typeSummary = getSummaryForType(type)
              const isExpanded = expandedTypes[type]
              
              return (
                <div key={type} className={`border rounded-lg ${getTypeColor(type)}`}>
                  {/* Header del tipo */}
                  <div 
                    className="p-4 cursor-pointer hover:bg-opacity-80"
                    onClick={() => toggleTypeExpansion(type)}
                  >
                    <div className="flex justify-between items-center">
                      <div className="flex items-center space-x-3">
                        <h3 className="font-semibold text-lg">
                          {sensorService.formatSensorType(type)} ({typeSensors.length})
                        </h3>
                        <div className="flex space-x-2 text-sm">
                          <span className="bg-green-200 text-green-800 px-2 py-1 rounded">
                            {typeSummary.free_count} libres
                          </span>
                          <span className="bg-red-200 text-red-800 px-2 py-1 rounded">
                            {typeSummary.busy_count} ocupados
                          </span>
                          {typeSummary.error_count > 0 && (
                            <span className="bg-yellow-200 text-yellow-800 px-2 py-1 rounded">
                              {typeSummary.error_count} errores
                            </span>
                          )}
                        </div>
                      </div>
                      <div className="text-sm font-medium">
                        {isExpanded ? '▼' : '▶'}
                      </div>
                    </div>
                  </div>

                  {/* Lista de sensores */}
                  {isExpanded && (
                    <div className="border-t bg-white bg-opacity-50">
                      <div className="p-4 space-y-2">
                        {typeSensors.map((sensor) => (
                          <div key={sensor.id} className="flex items-center justify-between p-3 bg-white rounded-lg shadow-sm border">
                            <div className="flex items-center space-x-3">
                              <div className="flex items-center space-x-2">
                                {getStatusIcon(sensor.current_status)}
                                <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(sensor.current_status)}`}>
                                  {sensorService.formatSensorStatus(sensor.current_status)}
                                </span>
                              </div>
                              
                              <div>
                                <div className="font-medium text-gray-900">{sensor.name}</div>
                                <div className="text-sm text-gray-500">{sensor.serial_number}</div>
                              </div>
                              
                              {sensor.battery_info && (
                                <div className="flex items-center space-x-1">
                                  {sensor.battery_info.is_low ? (
                                    <BatteryLow className="h-4 w-4 text-red-500" />
                                  ) : (
                                    <Battery className="h-4 w-4 text-green-500" />
                                  )}
                                  <span className="text-sm text-gray-600">
                                    {sensor.battery_info.capacity}%
                                  </span>
                                </div>
                              )}
                              
                              <div className="text-xs text-gray-500">
                                {sensor.last_update ? (
                                  <>Actualizado: {new Date(sensor.last_update).toLocaleString()}</>
                                ) : (
                                  'Sin actualizar'
                                )}
                              </div>
                            </div>

                            <div className="flex space-x-2">
                              <button
                                onClick={() => handleViewDetail(sensor)}
                                className="text-blue-600 hover:text-blue-800"
                                title="Ver detalles"
                              >
                                <Eye className="h-4 w-4" />
                              </button>
                              <button
                                onClick={() => handleUpdateStatus(sensor)}
                                className="text-green-600 hover:text-green-800"
                                title="Actualizar estado"
                              >
                                <Activity className="h-4 w-4" />
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      </div>

      {/* Modales */}
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
    </>
  )
}

export default ParkingSensorSection
