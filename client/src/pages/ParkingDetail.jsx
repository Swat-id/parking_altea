import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import { authService } from '../services/authService'
import { parkingService } from '../services/parkingService'
import { cameraService } from '../services/cameraService'
import { cameraLogService } from '../services/cameraLogService'
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
  Send
} from 'lucide-react'
import toast from 'react-hot-toast'

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
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [editingLine, setEditingLine] = useState(null)
  const [newLine, setNewLine] = useState('')
  const [updating, setUpdating] = useState(false)

  // Obtener datos del parking
  const { data: parkingData, isLoading, error: parkingError } = useQuery(
    ['parking', id],
    () => parkingService.getParking(id),
    {
      retry: 1,
      onError: () => {
        toast.error('Error al cargar el parking')
        navigate('/parkings')
      }
    }
  )

  // Obtener datos públicos del parking (redundante ahora, pero mantener por compatibilidad)
  const { data: publicParking } = useQuery(
    ['publicParking', id],
    () => parkingService.getParking(id),
    {
      enabled: !!parking
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
        queryClient.invalidateQueries(['publicParking', id])
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
        queryClient.invalidateQueries(['publicParking', id])
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

  useEffect(() => {
    loadParkingData()
  }, [id])

  const loadParkingData = async () => {
    try {
      setLoading(true)
      const [parkingData, camerasData] = await Promise.all([
        parkingService.getParking(id),
        cameraService.getParkingCameras(id)
      ])
      
      setParking(parkingData)
      setCameras(camerasData.cameras || [])
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

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (error || !parking) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">{error || 'Parking no encontrado'}</p>
        <button
          onClick={() => navigate('/parkings')}
          className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
        >
          Volver a Parkings
        </button>
      </div>
    )
  }

  const ocupationPercentage = parking.total_plazas > 0 
    ? Math.round((parking.plazas_ocupadas / parking.total_plazas) * 100) 
    : 0

  return (
    <div className="max-w-6xl mx-auto p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">{parking.name}</h1>
          <p className="text-gray-600">ID: {parking.id}</p>
        </div>
        <button
          onClick={() => navigate('/parkings')}
          className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
        >
          ← Volver
        </button>
      </div>

      {/* Información del Parking */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Ocupación Actual</h3>
          <p className="text-3xl font-bold text-blue-600">{parking.current_occupancy || 0}</p>
          <p className="text-sm text-gray-600">vehículos</p>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Capacidad Total</h3>
          <p className="text-3xl font-bold text-green-600">{parking.capacity || 0}</p>
          <p className="text-sm text-gray-600">plazas</p>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Porcentaje</h3>
          <p className="text-3xl font-bold text-orange-600">
            {parking.capacity ? Math.round(((parking.current_occupancy || 0) / parking.capacity) * 100) : 0}%
          </p>
          <p className="text-sm text-gray-600">ocupación</p>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Cámaras</h3>
          <p className="text-3xl font-bold text-purple-600">{cameras.length}</p>
          <p className="text-sm text-gray-600">configuradas</p>
        </div>
      </div>

      {/* Sección de Cámaras */}
      <div className="bg-white rounded-lg shadow mb-8">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">📷 Cámaras del Parking</h2>
          <p className="text-sm text-gray-600">Estado y configuración de las cámaras</p>
        </div>
        
        <div className="p-6">
          {cameras.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-gray-500">No hay cámaras configuradas para este parking</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {cameras.map((camera) => (
                <div key={camera.id} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <h3 className="font-semibold text-gray-900">{camera.name}</h3>
                      <p className="text-sm text-gray-600">{camera.ip}</p>
                    </div>
                    <div className={`px-2 py-1 rounded-full text-xs font-medium ${cameraService.getStatusColor(camera.status)}`}>
                      {cameraService.getStatusIcon(camera.status)} {camera.status}
                    </div>
                  </div>
                  
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Línea:</span>
                      {editingLine === camera.id ? (
                        <div className="flex items-center space-x-2">
                          <input
                            type="number"
                            value={newLine}
                            onChange={(e) => setNewLine(e.target.value)}
                            className="w-16 px-2 py-1 border border-gray-300 rounded text-sm"
                            min="1"
                          />
                          <button
                            onClick={() => handleUpdateLine(camera.id, camera.line)}
                            disabled={updating}
                            className="px-2 py-1 bg-green-600 text-white rounded text-xs hover:bg-green-700 disabled:opacity-50"
                          >
                            ✓
                          </button>
                          <button
                            onClick={cancelEditLine}
                            className="px-2 py-1 bg-gray-600 text-white rounded text-xs hover:bg-gray-700"
                          >
                            ✕
                          </button>
                        </div>
                      ) : (
                        <div className="flex items-center space-x-2">
                          <span className="font-medium">{camera.line}</span>
                          <button
                            onClick={() => startEditLine(camera.id, camera.line)}
                            className="px-2 py-1 bg-blue-600 text-white rounded text-xs hover:bg-blue-700"
                          >
                            ✏️
                          </button>
                        </div>
                      )}
                    </div>
                    
                    <div className="flex justify-between">
                      <span className="text-gray-600">Ping:</span>
                      <span className={`font-medium ${camera.ping_status === 'ONLINE' ? 'text-green-600' : 'text-red-600'}`}>
                        {camera.ping_status}
                      </span>
                    </div>
                    
                    <div className="flex justify-between">
                      <span className="text-gray-600">Último mensaje:</span>
                      <span className="text-xs text-gray-500">
                        {cameraService.formatTimestamp(camera.last_message_received)}
                      </span>
                    </div>
                    
                    <div className="flex justify-between">
                      <span className="text-gray-600">Último ping:</span>
                      <span className="text-xs text-gray-500">
                        {cameraService.formatTimestamp(camera.last_ping_check)}
                      </span>
                    </div>
                    
                    <div className="flex justify-between">
                      <span className="text-gray-600">Vehículos IN:</span>
                      <span className="font-medium">{camera.last_vehicle_in || 0}</span>
                    </div>
                    
                    <div className="flex justify-between">
                      <span className="text-gray-600">Vehículos OUT:</span>
                      <span className="font-medium">{camera.last_vehicle_out || 0}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Botones de Acción */}
      <div className="flex space-x-4">
        <button
          onClick={() => navigate(`/camera-logs?parking=${id}`)}
          className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
        >
          📋 Ver Logs de Cámaras
        </button>
        
        <button
          onClick={loadParkingData}
          className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          🔄 Actualizar Datos
        </button>
      </div>
    </div>
  )
}

export default ParkingDetail 