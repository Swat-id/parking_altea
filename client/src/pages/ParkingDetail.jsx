import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import { authService } from '../services/authService'
import parkingService from '../services/parkingService'
import cameraService from '../services/cameraService'
import { cameraLogService } from '../services/cameraLogService'
import panelService from '../services/panelService'
import { 
  ArrowLeft, 
  Edit, 
  Save, 
  X, 
  MessageSquare, 
  Settings,
  Car,
  Clock,
  AlertCircle,
  CheckCircle,
  TrendingUp,
  MapPin,
  Calendar,
  Send,
  Wifi,
  WifiOff,
  Camera,
  Trash2
} from 'lucide-react'
import toast from 'react-hot-toast'
import CameraAssignmentModal from '../components/CameraAssignmentModal'
import ParkingSensorSection from '../components/ParkingSensorSection'
import { useAuth } from '../context/AuthContext'

const ParkingDetail = () => {
  const { id } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  
  const [isEditing, setIsEditing] = useState(false)
  const [showMessageForm, setShowMessageForm] = useState(false)
  const [messageText, setMessageText] = useState('')
  const [messageDuration, setMessageDuration] = useState(30)
  const [parking, setParking] = useState(null)
  const [cameras, setCameras] = useState([])
  const [panels, setPanels] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [editingLine, setEditingLine] = useState(null)
  const [newLine, setNewLine] = useState('')
  const [updating, setUpdating] = useState(false)
  const [lastUpdate, setLastUpdate] = useState(null)
  const [editingOccupancy, setEditingOccupancy] = useState(false)
  const [newOccupancy, setNewOccupancy] = useState('')
  const [occupancyError, setOccupancyError] = useState('')
  const [saving, setSaving] = useState(false)
  const { isSuperadmin } = useAuth()
  const [showCameraModal, setShowCameraModal] = useState(false)
  const [assignedCameras, setAssignedCameras] = useState([])

  // Obtener datos del parking con manejo de permisos
  const { data: parkingData, isLoading, error: parkingError } = useQuery(
    ['parking', id],
    () => parkingService.getParking(id),
    {
      retry: 1,
      onError: (error) => {
        if (error.response?.status === 403) {
          toast.error('No tienes permisos para acceder a este parking')
          navigate('/parkings')
        } else {
          toast.error('Error al cargar el parking')
          navigate('/parkings')
        }
      }
    }
  )

  // Estados de edición
  const [editForm, setEditForm] = useState({
    plazas_ocupadas: 0,
    total_plazas: 0,
    threshold_dense: 0,
    threshold_full: 0
  })

  // Inicializar formulario cuando se cargan los datos
  useEffect(() => {
    if (parkingData) {
      setEditForm({
        plazas_ocupadas: parkingData.plazas_ocupadas || 0,
        total_plazas: parkingData.total_plazas || 0,
        threshold_dense: parkingData.threshold_dense || 0,
        threshold_full: parkingData.threshold_full || 0
      })
    }
  }, [parkingData])

  // Mutación para actualizar ocupación
  const updateOccupancyMutation = useMutation(
    ({ occupancy }) => parkingService.updateOccupancy(id, occupancy),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['parking', id])
        queryClient.invalidateQueries('userParkings')
        toast.success('Ocupación actualizada correctamente')
      },
      onError: (error) => {
        toast.error(error?.response?.data?.message || 'Error al actualizar la ocupación')
      }
    }
  )

  // Mutación para actualizar configuración
  const updateConfigMutation = useMutation(
    (config) => parkingService.updateConfig(id, config),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['parking', id])
        queryClient.invalidateQueries('userParkings')
        toast.success('Configuración actualizada correctamente')
      },
      onError: (error) => {
        toast.error(error?.response?.data?.message || 'Error al actualizar la configuración')
      }
    }
  )

  // Cerrar modo edición cuando las mutaciones sean exitosas
  useEffect(() => {
    if (updateOccupancyMutation.isSuccess && updateConfigMutation.isSuccess) {
      setIsEditing(false)
    }
  }, [updateOccupancyMutation.isSuccess, updateConfigMutation.isSuccess])

  const sendMessageMutation = useMutation(
    (messageData) => parkingService.sendMessage(id, messageData),
    {
      onSuccess: () => {
        toast.success('Mensaje enviado correctamente')
        setShowMessageForm(false)
        setMessageText('')
        setMessageDuration(30)
      },
      onError: () => {
        toast.error('Error al enviar el mensaje')
      }
    }
  )

  const handleSave = () => {
    // Validaciones
    if (editForm.plazas_ocupadas > editForm.total_plazas) {
      toast.error('Las plazas ocupadas no pueden ser mayores que el total')
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

    // Actualizar ocupación si cambió
    if (editForm.plazas_ocupadas !== parkingData.plazas_ocupadas) {
      updateOccupancyMutation.mutate({ occupancy: editForm.plazas_ocupadas })
    }

    // Actualizar configuración si cambió
    const configChanged = editForm.total_plazas !== parkingData.total_plazas ||
                         editForm.threshold_dense !== parkingData.threshold_dense ||
                         editForm.threshold_full !== parkingData.threshold_full

    if (configChanged) {
      updateConfigMutation.mutate({
        total_plazas: editForm.total_plazas,
        threshold_dense: editForm.threshold_dense,
        threshold_full: editForm.threshold_full
      })
    }

    // Si no hay cambios, cerrar edición
    if (editForm.plazas_ocupadas === parkingData.plazas_ocupadas && !configChanged) {
      setIsEditing(false)
      toast.info('No hay cambios para guardar')
    }
  }

  const handleCancel = () => {
    // Restaurar valores originales
    if (parkingData) {
      setEditForm({
        plazas_ocupadas: parkingData.plazas_ocupadas || 0,
        total_plazas: parkingData.total_plazas || 0,
        threshold_dense: parkingData.threshold_dense || 0,
        threshold_full: parkingData.threshold_full || 0
      })
    }
    setIsEditing(false)
  }

  const handleSendMessage = () => {
    if (!messageText.trim()) {
      toast.error('El mensaje no puede estar vacío')
      return
    }

    sendMessageMutation.mutate({
      message: messageText,
      duration: messageDuration
    })
  }

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

  const getCameraStatusIcon = (status) => {
    switch (status?.toLowerCase()) {
      case 'online':
        return <Wifi className="h-4 w-4 text-green-600" />
      case 'offline':
        return <WifiOff className="h-4 w-4 text-red-600" />
      default:
        return <AlertCircle className="h-4 w-4 text-gray-400" />
    }
  }

  useEffect(() => {
    loadParkingData()
  }, [id])

  const loadParkingData = async () => {
    try {
      setLoading(true)
      setError(null)
      
      // Cargar datos del parking con manejo de permisos
      try {
        const parkingData = await parkingService.getParking(id)
        setParking(parkingData)
      } catch (parkingError) {
        if (parkingError.response?.status === 403) {
          toast.error('No tienes permisos para acceder a este parking')
          navigate('/parkings')
          return
        } else {
          throw parkingError
        }
      }
      
      // Cargar cámaras del parking
      try {
        const camerasData = await cameraService.getParkingCameras(id)
        setCameras(camerasData.cameras || [])
      } catch (err) {
        console.error('Error cargando cámaras:', err)
        setCameras([])
      }
      
      // Cargar paneles del parking - corregir endpoint
      try {
        const panelsData = await panelService.getParkingPanels(id)
        setPanels(panelsData || [])
      } catch (err) {
        console.error('Error cargando paneles:', err)
        setPanels([])
      }
      
      setLastUpdate(new Date())
    } catch (err) {
      setError('Error cargando datos del parking')
      console.error('Error:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleUpdateLine = async (cameraId, currentLine) => {
    if (!newLine || newLine === currentLine.toString()) {
      setEditingLine(null)
      setNewLine('')
      return
    }

    const lineNumber = parseInt(newLine)
    if (isNaN(lineNumber) || lineNumber < 1) {
      alert('La línea debe ser un número positivo')
      return
    }

    try {
      setUpdating(true)
      await cameraService.updateCameraLine(cameraId, lineNumber)
      
      // Recargar datos
      await loadParkingData()
      
      setEditingLine(null)
      setNewLine('')
      alert('Línea actualizada correctamente')
    } catch (err) {
      console.error('Error actualizando línea:', err)
      alert(err.response?.data?.error || 'Error actualizando línea')
    } finally {
      setUpdating(false)
    }
  }

  const startEditLine = (cameraId, currentLine) => {
    setEditingLine(cameraId)
    setNewLine(currentLine.toString())
  }

  const cancelEditLine = () => {
    setEditingLine(null)
    setNewLine('')
  }

  const handleOccupancyUpdate = async () => {
    if (!newOccupancy || isNaN(newOccupancy)) {
      setOccupancyError('Por favor ingrese un número válido')
      return
    }

    const occupancy = parseInt(newOccupancy)
    if (occupancy < 0) {
      setOccupancyError('La ocupación no puede ser negativa')
      return
    }

    try {
      setSaving(true)
      setOccupancyError('')
      
      const response = await parkingService.updateOccupancy(id, occupancy)
      
      // Actualizar el estado local con la respuesta del servidor
      if (response && response.status === 'ok') {
        setParking(prevParking => ({
          ...prevParking,
          plazas_ocupadas: response.occupancy,
          estado: response.parking_status
        }))
        
        // Mostrar mensaje de éxito
        toast.success('Ocupación actualizada correctamente')
      }
      
      setEditingOccupancy(false)
      setNewOccupancy('')
    } catch (err) {
      setOccupancyError('Error actualizando ocupación')
      console.error('Error:', err)
      toast.error('Error al actualizar la ocupación')
    } finally {
      setSaving(false)
    }
  }

  const formatLastUpdate = () => {
    if (!lastUpdate) return 'Nunca'
    return lastUpdate.toLocaleString('es-ES')
  }

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return 'N/A'
    const date = new Date(timestamp)
    return date.toLocaleString('es-ES')
  }

  const getRelativeTime = (timestamp) => {
    if (!timestamp) return ''
    const date = new Date(timestamp)
    const now = new Date()
    const diffMs = now - date
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    
    if (diffMins < 1) return 'Ahora mismo'
    if (diffMins < 60) return `Hace ${diffMins} min`
    if (diffHours < 24) return `Hace ${diffHours}h ${diffMins % 60}min`
    return `Hace ${Math.floor(diffHours / 24)} días`
  }

  // Mutación para actualizar cámaras
  const updateCamerasMutation = useMutation(
    (cameras) => parkingService.updateCameras(id, cameras),
    {
      onSuccess: () => {
        toast.success('Cámaras actualizadas correctamente')
        setShowCameraModal(false)
        loadParkingData()
      },
      onError: () => {
        toast.error('Error al actualizar las cámaras')
      }
    }
  )

  // Abrir modal y cargar cámaras actuales
  const openCameraModal = () => {
    setAssignedCameras(cameras)
    setShowCameraModal(true)
  }

  // Guardar cámaras desde el modal
  const handleCameraAssignment = async (newCameras) => {
    setAssignedCameras(newCameras)
    updateCamerasMutation.mutate(newCameras)
  }

  // Eliminar cámara individual
  const handleRemoveCamera = (cameraId) => {
    if (!window.confirm('¿Seguro que quieres desvincular esta cámara del parking?')) return
    const updatedCameras = cameras.filter(cam => cam.id !== cameraId)
    updateCamerasMutation.mutate(updatedCameras)
  }

  if (loading && !parking) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (error && !parking) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <h2 className="text-lg font-semibold text-red-800">Error</h2>
          <p className="text-red-600">{error}</p>
          <button
            onClick={() => navigate('/parkings')}
            className="mt-4 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
          >
            Volver a Parkings
          </button>
        </div>
      </div>
    )
  }

  if (!parking) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="text-center">
          <h2 className="text-lg font-semibold text-gray-800">Parking no encontrado</h2>
          <button
            onClick={() => navigate('/parkings')}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Volver a Parkings
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">🏢 {parking.name}</h1>
            <p className="text-gray-600">{parking.location}</p>
            {lastUpdate && (
              <p className="text-sm text-gray-500 mt-2">
                Última actualización: {formatLastUpdate()}
              </p>
            )}
          </div>
          <button
            onClick={() => navigate('/parkings')}
            className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"
          >
            ← Volver
          </button>
        </div>
      </div>

      {/* Información General */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500">Capacidad</h3>
          <p className="text-2xl font-bold text-gray-900">{parking.total_plazas}</p>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500">Ocupación Actual</h3>
          <p className="text-2xl font-bold text-blue-600">{parking.plazas_ocupadas || 0}</p>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500">Ocupación %</h3>
          <p className="text-2xl font-bold text-green-600">
            {parking.total_plazas > 0 ? Math.round(((parking.plazas_ocupadas || 0) / parking.total_plazas) * 100) : 0}%
          </p>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500">Estado</h3>
          <div className="flex items-center space-x-2">
            <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(parking.estado)}`}>
              {getStatusIcon(parking.estado)} {parking.estado || 'UNKNOWN'}
            </span>
          </div>
        </div>
      </div>

      {/* Control de Ocupación */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">📊 Control de Ocupación</h2>
        
        <div className="flex items-center space-x-4">
          {editingOccupancy ? (
            <>
              <input
                type="number"
                value={newOccupancy}
                onChange={(e) => setNewOccupancy(e.target.value)}
                placeholder="Nueva ocupación"
                className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button
                onClick={handleOccupancyUpdate}
                disabled={saving}
                className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
              >
                {saving ? '💾 Guardando...' : '💾 Guardar'}
              </button>
              <button
                onClick={() => {
                  setEditingOccupancy(false)
                  setNewOccupancy('')
                  setOccupancyError('')
                }}
                className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"
              >
                ❌ Cancelar
              </button>
            </>
          ) : (
            <>
              <span className="text-lg">Ocupación actual: <strong>{parking.plazas_ocupadas || 0}</strong></span>
              <button
                onClick={() => setEditingOccupancy(true)}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                ✏️ Editar
              </button>
            </>
          )}
        </div>
        
        {occupancyError && (
          <p className="text-red-600 text-sm mt-2">{occupancyError}</p>
        )}
      </div>

      {/* Cámaras */}
      <div className="bg-white rounded-lg shadow mb-6">
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">
            📹 Cámaras ({cameras.length})
          </h2>
          {isSuperadmin && (
            <button
              onClick={openCameraModal}
              className="flex items-center px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200 transition-colors"
            >
              <Camera className="h-4 w-4 mr-1" />
              Editar cámaras
            </button>
          )}
        </div>
        <div className="overflow-x-auto">
          {cameras.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-gray-500">No hay cámaras configuradas para este parking</p>
            </div>
          ) : (
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Cámara
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    IP
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Estado
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Último Mensaje
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Contadores
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Acciones
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {cameras.map((camera) => (
                  <tr key={camera.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      <div>
                        <div className="font-medium">{camera.name}</div>
                        <div className="text-xs text-gray-500">Línea: {camera.line}</div>
                      </div>
                    </td>
                    
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {camera.ip}
                    </td>
                    
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center space-x-2">
                        {getCameraStatusIcon(camera.status)}
                        <span className="text-sm text-gray-900">
                          {camera.status || 'UNKNOWN'}
                        </span>
                      </div>
                      {camera.ping_status && camera.ping_status !== 'UNKNOWN' && (
                        <div className="text-xs text-gray-500">
                          Ping: {camera.ping_status}
                        </div>
                      )}
                    </td>
                    
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <div>
                        <div>{formatTimestamp(camera.last_message_received)}</div>
                        <div className="text-xs">{getRelativeTime(camera.last_message_received)}</div>
                      </div>
                    </td>
                    
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      <div>
                        <div className="text-green-600">In: {camera.last_vehicle_in || 0}</div>
                        <div className="text-red-600">Out: {camera.last_vehicle_out || 0}</div>
                      </div>
                    </td>
                    
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <button
                        onClick={() => navigate(`/camera-logs?parking=${id}&camera=${camera.id}`)}
                        className="text-blue-600 hover:text-blue-900 mr-2"
                      >
                        Ver logs
                      </button>
                      {isSuperadmin && (
                        <button
                          onClick={() => handleRemoveCamera(camera.id)}
                          className="text-red-600 hover:text-red-900"
                          title="Desvincular cámara"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
        {/* Modal de asignación de cámaras */}
        <CameraAssignmentModal
          isOpen={showCameraModal}
          onClose={() => setShowCameraModal(false)}
          onSave={handleCameraAssignment}
          existingCameras={assignedCameras}
        />
      </div>

      {/* Paneles */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">
            🖥️ Paneles ({panels.length})
          </h2>
        </div>
        
        <div className="overflow-x-auto">
          {panels.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-gray-500">No hay paneles configurados para este parking</p>
            </div>
          ) : (
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Panel
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    IP
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Estado
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Última Actividad
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {panels.map((panel) => (
                  <tr key={panel.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      <div>
                        <div className="font-medium">{panel.name}</div>
                        <div className="text-xs text-gray-500">ID: {panel.id}</div>
                      </div>
                    </td>
                    
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {panel.ip_address || panel.ip}
                    </td>
                    
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center space-x-2">
                        {getCameraStatusIcon(panel.status)}
                        <span className="text-sm text-gray-900">
                          {panel.status || 'UNKNOWN'}
                        </span>
                      </div>
                    </td>
                    
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <div>
                        <div>{formatTimestamp(panel.last_update)}</div>
                        <div className="text-xs">{getRelativeTime(panel.last_update)}</div>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Separador visual */}
      <div className="border-t border-gray-200 my-8"></div>

      {/* Sensores Individuales */}
      <ParkingSensorSection 
        parkingId={parking?.id} 
        parkingName={parking?.name} 
      />
    </div>
  )
}

export default ParkingDetail 