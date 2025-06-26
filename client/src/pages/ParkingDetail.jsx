import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import { authService } from '../services/authService'
import { parkingService } from '../services/parkingService'
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

  // Obtener datos del parking
  const { data: parking, isLoading, error } = useQuery(
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
    if (parking) {
      setEditForm({
        plazas_ocupadas: parking.plazas_ocupadas || 0,
        total_plazas: parking.total_plazas || 0,
        threshold_dense: parking.threshold_dense || 0,
        threshold_full: parking.threshold_full || 0
      })
    }
  }, [parking])

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

    if (editForm.threshold_dense >= editForm.threshold_full) {
      toast.error('El umbral denso debe ser menor que el umbral completo')
      return
    }

    if (editForm.threshold_full > 100) {
      toast.error('El umbral completo no puede ser mayor al 100%')
      return
    }

    // Actualizar ocupación si cambió
    if (editForm.plazas_ocupadas !== parking.plazas_ocupadas) {
      updateOccupancyMutation.mutate({ occupancy: editForm.plazas_ocupadas })
    }

    // Actualizar configuración si cambió
    const configChanged = editForm.total_plazas !== parking.total_plazas ||
                         editForm.threshold_dense !== parking.threshold_dense ||
                         editForm.threshold_full !== parking.threshold_full

    if (configChanged) {
      updateConfigMutation.mutate({
        total_plazas: editForm.total_plazas,
        threshold_dense: editForm.threshold_dense,
        threshold_full: editForm.threshold_full
      })
    }

    // Si no hay cambios, cerrar edición
    if (editForm.plazas_ocupadas === parking.plazas_ocupadas && !configChanged) {
      setIsEditing(false)
      toast.info('No hay cambios para guardar')
    }
  }

  const handleCancel = () => {
    // Restaurar valores originales
    if (parking) {
      setEditForm({
        plazas_ocupadas: parking.plazas_ocupadas || 0,
        total_plazas: parking.total_plazas || 0,
        threshold_dense: parking.threshold_dense || 0,
        threshold_full: parking.threshold_full || 0
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

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (error || !parking) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="mx-auto h-12 w-12 text-red-500" />
        <h3 className="mt-2 text-sm font-medium text-gray-900">Error al cargar el parking</h3>
        <p className="mt-1 text-sm text-gray-500">No se pudo cargar la información del parking.</p>
        <button
          onClick={() => navigate('/parkings')}
          className="mt-4 btn-primary"
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
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <button
            onClick={() => navigate('/parkings')}
            className="p-2 text-gray-400 hover:text-gray-600"
          >
            <ArrowLeft className="h-6 w-6" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{parking.name}</h1>
            <p className="text-sm text-gray-500">ID: {parking.id}</p>
          </div>
        </div>
        <div className="flex space-x-2">
          <button
            onClick={() => setIsEditing(!isEditing)}
            className={`flex items-center px-3 py-2 rounded-lg text-sm font-medium ${
              isEditing 
                ? 'bg-gray-100 text-gray-700' 
                : 'bg-primary-100 text-primary-700'
            }`}
          >
            <Edit className="h-4 w-4 mr-1" />
            {isEditing ? 'Cancelar' : 'Editar'}
          </button>
          <button
            onClick={() => setShowMessageForm(!showMessageForm)}
            className="flex items-center px-3 py-2 bg-blue-100 text-blue-700 rounded-lg text-sm font-medium"
          >
            <MessageSquare className="h-4 w-4 mr-1" />
            Mensaje
          </button>
        </div>
      </div>

      {/* Estado actual */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Información principal */}
        <div className="card lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-medium text-gray-900">Información del Parking</h2>
            <div className={`flex items-center px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(parking.estado)}`}>
              {getStatusIcon(parking.estado)}
              <span className="ml-1">{parking.estado}</span>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
            <div>
              <h3 className="text-sm font-medium text-gray-500 mb-2">Ocupación</h3>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Ocupadas</span>
                  <span className="font-medium">{parking.plazas_ocupadas}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Libres</span>
                  <span className="font-medium">{parking.plazas_libres}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Total</span>
                  <span className="font-medium">{parking.total_plazas}</span>
                </div>
                <div className="pt-2">
                  <div className="flex justify-between text-sm mb-1">
                    <span>Porcentaje</span>
                    <span className="font-medium">{ocupationPercentage}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${
                        parking.estado === 'LIBRE' ? 'bg-green-500' :
                        parking.estado === 'DENSO' ? 'bg-yellow-500' : 'bg-red-500'
                      }`}
                      style={{ width: `${ocupationPercentage}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>

            <div>
              <h3 className="text-sm font-medium text-gray-500 mb-2">Configuración</h3>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Umbral Denso</span>
                  <span className="font-medium">{parking.threshold_dense}%</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Umbral Completo</span>
                  <span className="font-medium">{parking.threshold_full}%</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Ubicación</span>
                  <span className="font-medium text-xs">{parking.location}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Acciones rápidas */}
        <div className="card">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Acciones Rápidas</h2>
          <div className="space-y-3">
            <button
              onClick={() => setShowMessageForm(true)}
              className="w-full flex items-center justify-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Send className="h-4 w-4 mr-2" />
              Enviar Mensaje
            </button>
            <button
              onClick={() => setIsEditing(true)}
              className="w-full flex items-center justify-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
            >
              <Settings className="h-4 w-4 mr-2" />
              Editar Configuración
            </button>
          </div>
        </div>
      </div>

      {/* Formulario de edición */}
      {isEditing && (
        <div className="card">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Editar Configuración</h2>
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Plazas Ocupadas
              </label>
              <input
                type="number"
                value={editForm.plazas_ocupadas}
                onChange={(e) => setEditForm({
                  ...editForm,
                  plazas_ocupadas: parseInt(e.target.value) || 0
                })}
                className={`input-field ${
                  editForm.plazas_ocupadas > editForm.total_plazas ? 'border-red-300 focus:border-red-500 focus:ring-red-500' : ''
                }`}
                min="0"
                max={editForm.total_plazas}
              />
              {editForm.plazas_ocupadas > editForm.total_plazas && (
                <p className="mt-1 text-sm text-red-600">
                  Las plazas ocupadas no pueden ser mayores que el total
                </p>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Total de Plazas
              </label>
              <input
                type="number"
                value={editForm.total_plazas}
                onChange={(e) => setEditForm({
                  ...editForm,
                  total_plazas: parseInt(e.target.value) || 0
                })}
                className="input-field"
                min="1"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Umbral Denso (%)
              </label>
              <input
                type="number"
                value={editForm.threshold_dense}
                onChange={(e) => setEditForm({
                  ...editForm,
                  threshold_dense: parseInt(e.target.value) || 0
                })}
                className={`input-field ${
                  editForm.threshold_dense >= editForm.threshold_full ? 'border-red-300 focus:border-red-500 focus:ring-red-500' : ''
                }`}
                min="0"
                max="100"
              />
              {editForm.threshold_dense >= editForm.threshold_full && (
                <p className="mt-1 text-sm text-red-600">
                  El umbral denso debe ser menor que el umbral completo
                </p>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Umbral Completo (%)
              </label>
              <input
                type="number"
                value={editForm.threshold_full}
                onChange={(e) => setEditForm({
                  ...editForm,
                  threshold_full: parseInt(e.target.value) || 0
                })}
                className={`input-field ${
                  editForm.threshold_full > 100 ? 'border-red-300 focus:border-red-500 focus:ring-red-500' : ''
                }`}
                min="0"
                max="100"
              />
              {editForm.threshold_full > 100 && (
                <p className="mt-1 text-sm text-red-600">
                  El umbral completo no puede ser mayor al 100%
                </p>
              )}
            </div>
          </div>
          <div className="flex space-x-3 mt-6">
            <button
              onClick={handleSave}
              disabled={updateConfigMutation.isLoading || 
                       editForm.plazas_ocupadas > editForm.total_plazas ||
                       editForm.threshold_dense >= editForm.threshold_full ||
                       editForm.threshold_full > 100}
              className="btn-primary flex items-center disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Save className="h-4 w-4 mr-2" />
              {updateConfigMutation.isLoading ? 'Guardando...' : 'Guardar Cambios'}
            </button>
            <button
              onClick={handleCancel}
              className="btn-secondary"
            >
              Cancelar
            </button>
          </div>
        </div>
      )}

      {/* Formulario de mensaje */}
      {showMessageForm && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-medium text-gray-900">
              Enviar Mensaje a {parking.name}
            </h2>
            <button
              onClick={() => {
                setShowMessageForm(false)
                setMessageText('')
                setMessageDuration(30)
              }}
              className="text-gray-400 hover:text-gray-600"
            >
              <X className="h-6 w-6" />
            </button>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Mensaje
              </label>
              <textarea
                value={messageText}
                onChange={(e) => setMessageText(e.target.value)}
                className="input-field"
                rows="3"
                placeholder="Escribe tu mensaje aquí..."
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Duración (segundos)
              </label>
              <input
                type="number"
                value={messageDuration}
                onChange={(e) => setMessageDuration(parseInt(e.target.value) || 30)}
                className="input-field"
                min="5"
                max="300"
              />
            </div>
            <div className="flex space-x-3">
              <button
                onClick={handleSendMessage}
                disabled={sendMessageMutation.isLoading || !messageText.trim()}
                className="btn-primary flex items-center disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Send className="h-4 w-4 mr-2" />
                {sendMessageMutation.isLoading ? 'Enviando...' : 'Enviar Mensaje'}
              </button>
              <button
                onClick={() => {
                  setShowMessageForm(false)
                  setMessageText('')
                  setMessageDuration(30)
                }}
                className="btn-secondary"
              >
                Cancelar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default ParkingDetail 