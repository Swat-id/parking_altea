import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import panelService from '../services/panelService'
import { panelTypeService } from '../services/panelTypeService'
import { useAuth } from '../context/AuthContext'
import ScheduleInfoModal from '../components/ScheduleInfoModal'
import PanelWindowManager from '../components/PanelWindowManager'
import PanelType4Status from '../components/PanelType4Status'
import windowService from '../services/windowService'
import { 
  Monitor, 
  Wifi, 
  WifiOff, 
  MessageSquare, 
  Send, 
  Settings,
  AlertCircle,
  CheckCircle,
  Clock,
  RefreshCw,
  Zap,
  X,
  Loader,
  Info,
  Eye,
  EyeOff,
  Server,
  Globe,
  Edit,
  Save,
  Type,
  Plus,
  Calendar,
  CalendarDays,
  Timer,
  ExternalLink,
  Trash2
} from 'lucide-react'
import toast from 'react-hot-toast'
import api from '../services/api'

const Panels = () => {
  const { isSuperadmin } = useAuth()
  const queryClient = useQueryClient()
  const [selectedPanel, setSelectedPanel] = useState(null)
  const [showMessageForm, setShowMessageForm] = useState(false)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showScheduleModal, setShowScheduleModal] = useState(false)
  const [selectedSchedule, setSelectedSchedule] = useState(null)
  const [messageText, setMessageText] = useState('')
  const [messageDuration, setMessageDuration] = useState(30)
  const [verificationResults, setVerificationResults] = useState(null)
  const [messageResponse, setMessageResponse] = useState(null)
  const [showResponseDetails, setShowResponseDetails] = useState(false)
  const [selectedColor, setSelectedColor] = useState(1) // 1=Rojo, 2=Verde, 3=Amarillo
  const [selectedWindow, setSelectedWindow] = useState(0) // NUEVO v4.1.0: Ventana seleccionada (0 o 1)
  const [editingPanelId, setEditingPanelId] = useState(null)
  const [editingPanelTypeId, setEditingPanelTypeId] = useState(null)
  const [createForm, setCreateForm] = useState({
    name: '',
    ip: '',
    parking_id: '',
    panel_type_id: '',
    port: 5200,
    windows_count: 1
  })
  // Estado para almacenar asignaciones de ventanas antes de crear el panel
  const [pendingWindowAssignments, setPendingWindowAssignments] = useState([])
  const [showEditModal, setShowEditModal] = useState(false)
  const [editForm, setEditForm] = useState({
    name: '',
    ip: '',
    parking_id: '',
    panel_type_id: '',
    port: 5200,
    is_active: true,
    windows_count: 1
  })
  const [editingPanel, setEditingPanel] = useState(null)

  // Obtener paneles filtrados por permisos del usuario
  const { data: panels = [], isLoading, refetch } = useQuery(
    'userPanels',
    panelService.getAllPanels, // Ya filtra automáticamente por permisos
    {
      refetchInterval: 30000, // Refrescar cada 30 segundos
    }
  )

  // Obtener tipos de panel
  const { data: panelTypes = [], isLoading: panelTypesLoading } = useQuery(
    'panelTypes',
    panelTypeService.getAllPanelTypes,
    {
      refetchInterval: 60000, // Refrescar cada minuto
    }
  )

  // Obtener parkings con filtrado por permisos
  const { data: parkings = [] } = useQuery(
    'userParkings',
    () => api.get('/api/parkings').then(res => res.data)
  )

  // Función para verificar si un panel type es Tipo 4
  const isPanelType4 = (panelTypeId) => {
    if (!panelTypeId) return false
    const panelType = panelTypes.find(pt => pt.id === parseInt(panelTypeId))
    return panelType && (panelType.windows_count === 16 || panelType.id === 4)
  }

  // Función para obtener windows_count del tipo de panel
  const getWindowsCountForType = (panelTypeId) => {
    if (!panelTypeId) return 1
    const panelType = panelTypes.find(pt => pt.id === parseInt(panelTypeId))
    return panelType?.windows_count || 1
  }

  // NUEVO v4.1.0: Estado para validación
  const [validationResult, setValidationResult] = useState(null)
  const [showValidation, setShowValidation] = useState(false)

  // Mutaciones
  const sendMessageMutation = useMutation(
    ({ panelId, messageData }) => panelService.sendMessage(panelId, messageData),
    {
      onSuccess: (data) => {
        setMessageResponse(data)
        setShowResponseDetails(true)
        queryClient.invalidateQueries('panels')
        toast.success('Mensaje enviado correctamente')
      },
      onError: (error) => {
        toast.error(error?.response?.data?.message || 'Error al enviar mensaje')
      }
    }
  )

  const testPanelMutation = useMutation(
    (panelId) => panelService.testPanel(panelId),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('panels')
        toast.success('Test de panel completado')
      },
      onError: (error) => {
        toast.error(error?.response?.data?.message || 'Error en test de panel')
      }
    }
  )

  const verifyPanelsMutation = useMutation(
    () => panelService.verifyAllPanels(),
    {
      onSuccess: (data) => {
        setVerificationResults(data)
        toast.success('Verificación completada')
      },
      onError: (error) => {
        toast.error(error?.response?.data?.message || 'Error en verificación')
      }
    }
  )

  const updatePanelTypeMutation = useMutation(
    ({ panelId, panelTypeId }) => panelService.updatePanelType(panelId, panelTypeId),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('panels')
        setEditingPanelId(null)
        setEditingPanelTypeId(null)
        toast.success('Tipo de panel actualizado')
      },
      onError: (error) => {
        toast.error(error?.response?.data?.message || 'Error actualizando tipo de panel')
      }
    }
  )

  const createPanelMutation = useMutation(
    async (panelData) => {
      const res = await fetch('/api/panels', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(panelData)
      })
      const data = await res.json()
      if (!res.ok) {
        throw new Error(data.error || 'Error al crear el panel')
      }
      return data
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries('panels')
      },
      onError: (error) => {
        toast.error(error?.message || error?.response?.data?.message || 'Error creando panel')
      }
    }
  )

  const updatePanelMutation = useMutation(
    ({ panelId, panelData }) => panelService.updatePanel(panelId, panelData),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('panels')
        setShowEditModal(false)
        setEditingPanel(null)
        toast.success('Panel actualizado correctamente')
      },
      onError: (error) => {
        toast.error(error?.response?.data?.error || 'Error actualizando panel')
      }
    }
  )

  const deletePanelMutation = useMutation(
    (panelId) => panelService.deletePanel(panelId),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('panels')
        toast.success('Panel eliminado correctamente')
      },
      onError: (error) => {
        toast.error(error?.response?.data?.error || 'Error eliminando panel')
      }
    }
  )

  // NUEVO v4.1.0: Mutación de validación
  const validateMessageMutation = useMutation(
    ({ panelId, messageData }) => panelService.validatePanelMessage(panelId, messageData),
    {
      onSuccess: (data) => {
        setValidationResult(data)
        setShowValidation(true)
        if (data.valid) {
          toast.success('Mensaje válido para envío')
        } else {
          toast.warning('Mensaje tiene errores de validación')
        }
      },
      onError: (error) => {
        toast.error('Error validando mensaje: ' + error.message)
      }
    }
  )

  // Funciones auxiliares
  const getStatusColor = (status) => {
    switch (status) {
      case 'ONLINE':
        return 'bg-green-100 text-green-800'
      case 'OFFLINE':
        return 'bg-red-100 text-red-800'
      case 'ERROR':
        return 'bg-yellow-100 text-yellow-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'ONLINE':
        return <Wifi className="h-4 w-4 text-green-600" />
      case 'OFFLINE':
        return <WifiOff className="h-4 w-4 text-red-600" />
      case 'ERROR':
        return <AlertCircle className="h-4 w-4 text-yellow-600" />
      default:
        return <Server className="h-4 w-4 text-gray-600" />
    }
  }

  const getColorName = (colorCode) => {
    switch (colorCode) {
      case 1:
        return 'Rojo'
      case 2:
        return 'Verde'
      case 3:
        return 'Amarillo'
      default:
        return 'Desconocido'
    }
  }

  // Nueva función para obtener el color del tipo de mensaje
  const getMessageTypeColor = (messageType) => {
    switch (messageType) {
      case 'schedule':
        return 'bg-blue-100 text-blue-800'
      case 'occupancy':
        return 'bg-green-100 text-green-800'
      case 'temporary':
        return 'bg-yellow-100 text-yellow-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  // Nueva función para obtener el icono del tipo de mensaje
  const getMessageTypeIcon = (messageType) => {
    switch (messageType) {
      case 'schedule':
        return <Calendar className="h-4 w-4 text-blue-600" />
      case 'occupancy':
        return <Monitor className="h-4 w-4 text-green-600" />
      case 'temporary':
        return <Timer className="h-4 w-4 text-yellow-600" />
      default:
        return <MessageSquare className="h-4 w-4 text-gray-600" />
    }
  }

  // Nueva función para formatear el horario de programación
  const formatScheduleTime = (timeString) => {
    if (!timeString) return ''
    try {
      const time = new Date(`2000-01-01T${timeString}`)
      return time.toLocaleTimeString('es-ES', {
        hour: '2-digit',
        minute: '2-digit'
      })
    } catch (error) {
      return timeString
    }
  }

  // Handlers
  const handleSendMessage = () => {
    if (!selectedPanel || !messageText.trim()) {
      toast.error('Selecciona un panel y escribe un mensaje')
      return
    }

    const messageData = {
      message: messageText,
      duration: messageDuration,
      color: selectedColor,
      fontSize: 2,
      showEffect: "fijo",
      window: selectedWindow // NUEVO v4.1.0: Usar ventana seleccionada dinámicamente
    }

    sendMessageMutation.mutate({ panelId: selectedPanel.id, messageData })
  }

  const handleTestPanel = (panelId) => {
    testPanelMutation.mutate(panelId)
  }

  const handleVerifyAllPanels = () => {
    verifyPanelsMutation.mutate()
  }

  const clearMessageResponse = () => {
    setMessageResponse(null)
    setShowResponseDetails(false)
    setShowMessageForm(false)
    setSelectedPanel(null)
    setMessageText('')
    setMessageDuration(30)
    setSelectedColor(1)
    setSelectedWindow(0) // NUEVO v4.1.0: Resetear ventana seleccionada
    setValidationResult(null) // NUEVO v4.1.0: Limpiar validación
    setShowValidation(false)
  }

  // NUEVO v4.1.0: Función para validar mensaje
  const handleValidateMessage = () => {
    if (!selectedPanel || !messageText.trim()) {
      toast.error('Selecciona un panel y escribe un mensaje')
      return
    }

    const messageData = {
      message: messageText,
      window: selectedWindow,
      color: selectedColor,
      fontSize: 2
    }

    validateMessageMutation.mutate({ panelId: selectedPanel.id, messageData })
  }

  const handleEditPanelType = (panelId, currentPanelTypeId) => {
    setEditingPanelId(panelId)
    // Asegurar que el ID sea un número
    const typeId = currentPanelTypeId ? (typeof currentPanelTypeId === 'number' ? currentPanelTypeId : parseInt(currentPanelTypeId)) : null
    setEditingPanelTypeId(typeId)
  }

  const handleSavePanelType = (panelId) => {
    if (editingPanelTypeId) {
      updatePanelTypeMutation.mutate({ panelId, panelTypeId: editingPanelTypeId })
    }
  }

  const handleCancelEdit = () => {
    setEditingPanelId(null)
    setEditingPanelTypeId(null)
  }

  const getPanelTypeDisplayName = (panelType) => {
    if (!panelType) return 'Sin tipo'
    // Si es un objeto con name y manufacturer
    if (panelType.name && panelType.manufacturer) {
      return `${panelType.name} (${panelType.manufacturer})`
    }
    // Si solo tiene name
    if (panelType.name) {
      return panelType.name
    }
    // Si es un objeto sin estructura esperada, intentar mostrar algo
    return 'Tipo desconocido'
  }

  const handleCreatePanel = async (e) => {
    e.preventDefault()
    
    // Validación básica
    if (!createForm.name || !createForm.ip || !createForm.panel_type_id) {
      toast.error('Completa todos los campos obligatorios')
      return
    }
    
    // Para Tipo 4, parking_id no es obligatorio (cada ventana puede tener su propio parking)
    // Pero el backend lo requiere, así que usamos el primero disponible si no se ha seleccionado
    const isType4 = isPanelType4(createForm.panel_type_id)
    let parkingId = createForm.parking_id
    
    if (isType4 && !parkingId && parkings.length > 0) {
      // Usar el primer parking disponible como valor por defecto para crear el panel
      parkingId = parkings[0].id.toString()
    }
    
    if (!parkingId) {
      toast.error('Debes seleccionar un parking (o al menos uno disponible para Tipo 4)')
      return
    }
    
    // Validar número de ventanas para Tipo 4
    if (isType4 && (!createForm.windows_count || createForm.windows_count < 1 || createForm.windows_count > 16)) {
      toast.error('El número de ventanas debe estar entre 1 y 16 para Tipo 4')
      return
    }
    
    // Crear el panel con el parking_id (puede ser el por defecto para Tipo 4)
    const panelData = {
      ...createForm,
      parking_id: parkingId
    }
    
    createPanelMutation.mutate(panelData, {
      onSuccess: async (response) => {
        const createdPanel = response.panel
        
        // Si hay asignaciones pendientes y es Tipo 4, guardarlas
        if (isType4 && pendingWindowAssignments.length > 0 && createdPanel?.id) {
          try {
            // Guardar todas las asignaciones pendientes
            for (const assignment of pendingWindowAssignments) {
              await windowService.assignParkingToWindow(
                createdPanel.id,
                assignment.window_id,
                assignment.parking_id,
                assignment.sensor_type || null,
                assignment.texto_fijo_previo || null,
                assignment.color || null
              )
            }
            toast.success(`Panel creado y ${pendingWindowAssignments.length} asignación(es) guardada(s)`)
          } catch (error) {
            console.error('Error guardando asignaciones:', error)
            toast.error('Panel creado, pero hubo errores al guardar algunas asignaciones')
          }
        } else {
          toast.success('Panel creado correctamente')
        }
        
        // Limpiar estado y cerrar modal
        setPendingWindowAssignments([])
        setCreateForm({
          name: '',
          ip: '',
          parking_id: '',
          panel_type_id: '',
          port: 5200,
          windows_count: 1
        })
        setShowCreateModal(false)
        queryClient.invalidateQueries('panels')
      }
    })
  }

  // Nueva función para mostrar detalles de programación
  const handleShowScheduleDetails = (panel, schedule) => {
    setSelectedPanel(panel)
    setSelectedSchedule(schedule)
    setShowScheduleModal(true)
  }

  const handleCloseScheduleModal = () => {
    setShowScheduleModal(false)
    setSelectedSchedule(null)
    setSelectedPanel(null)
  }

  const handleEditPanel = (panel) => {
    setEditingPanel(panel)
    // Obtener panel_type_id de panel.panel_type_id o panel.panel_type?.id
    const panelTypeId = panel.panel_type_id || panel.panel_type?.id || ''
    // Obtener IP de panel.ip_address o panel.ip
    const panelIp = panel.ip_address || panel.ip || ''
    // Obtener windows_count del panel o del tipo de panel
    const windowsCount = panel.windows_count || panel.panel_type?.windows_count || 1
    // Obtener parking_id y convertirlo a string
    const parkingId = panel.parking_id ? panel.parking_id.toString() : ''
    
    setEditForm({
      name: panel.name || '',
      ip: panelIp,
      parking_id: parkingId,
      panel_type_id: panelTypeId.toString(),
      port: panel.port || 5200,
      is_active: panel.is_active !== false,
      windows_count: windowsCount
    })
    setShowEditModal(true)
  }

  const handleUpdatePanel = (e) => {
    e.preventDefault()
    if (!editForm.name || !editForm.ip || !editForm.parking_id || !editForm.panel_type_id) {
      toast.error('Todos los campos son obligatorios')
      return
    }
    updatePanelMutation.mutate({ panelId: editingPanel.id, panelData: editForm })
  }

  const handleDeletePanel = (panel) => {
    if (window.confirm(`¿Estás seguro de que quieres eliminar el panel "${panel.name}"?\n\nEsta acción no se puede deshacer.`)) {
      deletePanelMutation.mutate(panel.id)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader className="h-8 w-8 animate-spin text-primary-600" />
        <span className="ml-2 text-gray-600">Cargando paneles...</span>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Gestión de Paneles</h1>
          <p className="text-gray-600">Administra y monitorea los paneles LED del sistema</p>
        </div>
        
        <div className="flex space-x-3">
          <button
            onClick={refetch}
            className="bg-gray-600 text-white px-4 py-2 rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500 flex items-center"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            Actualizar
          </button>
          
          <button
            onClick={handleVerifyAllPanels}
            disabled={verifyPanelsMutation.isLoading}
            className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 disabled:opacity-50 flex items-center"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${verifyPanelsMutation.isLoading ? 'animate-spin' : ''}`} />
            Verificar Todos
          </button>
          
          {verificationResults && (
            <button
              onClick={() => setVerificationResults(null)}
              className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 flex items-center"
            >
              <Info className="h-4 w-4 mr-2" />
              Ver Resultados
            </button>
          )}
          {/* Botón Crear Panel solo para superadmin */}
          {isSuperadmin && (
            <button
              onClick={() => setShowCreateModal(true)}
              className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 flex items-center"
            >
              <Plus className="h-4 w-4 mr-2" />
              Crear Panel
            </button>
          )}
        </div>
      </div>

      {/* Estadísticas */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-5">
        <div className="card">
          <div className="flex items-center">
            <Monitor className="h-8 w-8 text-primary-600" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500">Total</p>
              <p className="text-lg font-semibold text-gray-900">{panels.length}</p>
            </div>
          </div>
        </div>
        <div className="card">
          <div className="flex items-center">
            <CheckCircle className="h-8 w-8 text-green-600" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500">Online</p>
              <p className="text-lg font-semibold text-gray-900">
                {panels.filter(p => p.status === 'ONLINE').length}
              </p>
            </div>
          </div>
        </div>
        <div className="card">
          <div className="flex items-center">
            <AlertCircle className="h-8 w-8 text-red-600" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500">Offline</p>
              <p className="text-lg font-semibold text-gray-900">
                {panels.filter(p => p.status === 'OFFLINE').length}
              </p>
            </div>
          </div>
        </div>
        <div className="card">
          <div className="flex items-center">
            <Calendar className="h-8 w-8 text-blue-600" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500">Con Programación</p>
              <p className="text-lg font-semibold text-gray-900">
                {panels.filter(p => p.active_schedule).length}
              </p>
            </div>
          </div>
        </div>
        <div className="card">
          <div className="flex items-center">
            <Server className="h-8 w-8 text-purple-600" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500">Tipos</p>
              <p className="text-lg font-semibold text-gray-900">{panelTypes.length}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Lista de paneles */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Panel
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Estado
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Ping
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Parking
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Tipo
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Ventanas
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Programación Activa
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Último Mensaje
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Acciones
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {panels.map((panel) => (
                <tr key={panel.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div>
                      <div className="text-sm font-medium text-gray-900">
                        {panel.name}
                      </div>
                      <div className="text-sm text-gray-500">
                        {panel.ip_address || panel.ip || 'Sin IP'}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      {getStatusIcon(panel.status)}
                      <span className={`ml-2 inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(panel.status)}`}>
                        {panel.status}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {verificationResults && verificationResults.results ? (
                      (() => {
                        const result = verificationResults.results.find(r => r.panel_id === panel.id)
                        if (result && result.ping_success) {
                          return (
                            <div className="flex items-center">
                              <CheckCircle className="h-4 w-4 text-green-600 mr-1" />
                              <span>{result.ping_time_ms}ms</span>
                            </div>
                          )
                        } else if (result && !result.ping_success) {
                          return (
                            <div className="flex items-center">
                              <X className="h-4 w-4 text-red-600 mr-1" />
                              <span>Sin respuesta</span>
                            </div>
                          )
                        } else {
                          return <span className="text-gray-400">No verificado</span>
                        }
                      })()
                    ) : (
                      <span className="text-gray-400">No verificado</span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {panel.parking_name || 'Sin parking'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {editingPanelId === panel.id ? (
                      <div className="space-y-2">
                        <select
                          value={editingPanelTypeId ? editingPanelTypeId.toString() : ''}
                          onChange={(e) => setEditingPanelTypeId(e.target.value ? parseInt(e.target.value) : null)}
                          className="w-full px-2 py-1 text-sm border border-gray-300 rounded"
                        >
                          <option value="">Seleccionar tipo...</option>
                          {panelTypes.map(type => (
                            <option key={type.id} value={type.id.toString()}>
                              {type.name}
                            </option>
                          ))}
                        </select>
                        <div className="flex space-x-1">
                          <button
                            onClick={() => handleSavePanelType(panel.id)}
                            className="text-green-600 hover:text-green-900"
                          >
                            <Save className="h-4 w-4" />
                          </button>
                          <button
                            onClick={handleCancelEdit}
                            className="text-red-600 hover:text-red-900"
                          >
                            <X className="h-4 w-4" />
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div className="text-sm text-gray-500">
                        {(() => {
                          // Primero intentar usar panel.panel_type si existe (objeto completo del backend)
                          if (panel.panel_type && panel.panel_type.name) {
                            return getPanelTypeDisplayName(panel.panel_type)
                          }
                          // Si no, buscar en el array panelTypes usando panel_type_id
                          const panelTypeId = panel.panel_type_id || panel.panel_type?.id
                          if (panelTypeId && panelTypes.length > 0) {
                            const panelType = panelTypes.find(pt => pt.id === parseInt(panelTypeId))
                            if (panelType) {
                              return getPanelTypeDisplayName(panelType)
                            }
                          }
                          return 'Sin tipo'
                        })()}
                        <button
                          onClick={() => {
                            const panelTypeId = panel.panel_type_id || panel.panel_type?.id
                            handleEditPanelType(panel.id, panelTypeId)
                          }}
                          className="ml-2 text-blue-600 hover:text-blue-900"
                        >
                          <Edit className="h-3 w-3" />
                        </button>
                      </div>
                    )}
                  </td>
                  {/* NUEVO v4.1.0: Información de ventanas */}
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">
                      {panel.supports_multiple_windows ? (
                        <span className="inline-flex items-center px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded-full">
                          <Monitor className="h-3 w-3 mr-1" />
                          Dual (0,1)
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2 py-1 text-xs font-medium bg-gray-100 text-gray-600 rounded-full">
                          <Monitor className="h-3 w-3 mr-1" />
                          Simple (0)
                        </span>
                      )}
                    </div>
                    {panel.supports_multiple_windows && (
                      <div className="text-xs text-gray-500 mt-1">
                        {panel.windows && panel.windows.length > 0 ? (
                          <div className="space-y-1">
                            {panel.windows.map(window => (
                              <div key={window.id} className="flex items-center">
                                <span className="w-1 h-1 bg-gray-400 rounded-full mr-1"></span>
                                V{window.id}: {window.last_message ? 
                                  window.last_message.substring(0, 15) + (window.last_message.length > 15 ? '...' : '') 
                                  : 'Sin mensaje'}
                              </div>
                            ))}
                          </div>
                        ) : (
                          'Sin info de ventanas'
                        )}
                      </div>
                    )}
                    {/* PanelType4Status para paneles Tipo 4 */}
                    {isPanelType4(panel.panel_type_id) && (
                      <div className="mt-2">
                        <PanelType4Status 
                          panelId={panel.id} 
                          windowsCount={panel.windows_count || 16}
                        />
                      </div>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {panel.active_schedule ? (
                      <div className="flex items-center">
                        <div className="w-2 h-2 bg-green-400 rounded-full mr-2"></div>
                        <div className="flex-1">
                          <div className="font-medium text-green-700">{panel.active_schedule.name}</div>
                          <div className="text-xs text-gray-400">
                            {formatScheduleTime(panel.active_schedule.start_time)} - {formatScheduleTime(panel.active_schedule.end_time)}
                          </div>
                        </div>
                        <button
                          onClick={() => handleShowScheduleDetails(panel, panel.active_schedule)}
                          className="ml-2 text-blue-600 hover:text-blue-900"
                          title="Ver detalles de programación"
                        >
                          <ExternalLink className="h-3 w-3" />
                        </button>
                      </div>
                    ) : (
                      <span className="text-gray-400">Sin programación</span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    <div>
                      <div className="font-medium text-gray-900">
                        {panel.last_message || 'Sin mensajes'}
                      </div>
                      {panel.last_update && (
                        <div className="text-xs text-gray-400">
                          {new Date(panel.last_update).toLocaleString('es-ES', {
                            day: '2-digit',
                            month: '2-digit',
                            hour: '2-digit',
                            minute: '2-digit'
                          })}
                        </div>
                      )}
                      {panel.message_type && (
                        <div className={`text-xs px-2 py-1 rounded mt-1 inline-flex items-center ${getMessageTypeColor(panel.message_type)}`}>
                          {getMessageTypeIcon(panel.message_type)}
                          <span className="ml-1">
                            {panel.message_type === 'schedule' ? 'Programación' :
                             panel.message_type === 'occupancy' ? 'Ocupación' : 'Temporal'}
                          </span>
                        </div>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <div className="flex space-x-2">
                      <button
                        onClick={() => handleTestPanel(panel.id)}
                        className="text-blue-600 hover:text-blue-900"
                        title="Test de conectividad"
                      >
                        <Zap className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => {
                          setSelectedPanel(panel)
                          setShowMessageForm(true)
                        }}
                        className="text-green-600 hover:text-green-900"
                        title="Enviar mensaje"
                      >
                        <Send className="h-4 w-4" />
                      </button>
                      {/* TEMPORAL: Botones visibles para todos los usuarios */}
                      <>
                        <button
                          onClick={() => handleEditPanel(panel)}
                          className="text-orange-600 hover:text-orange-900"
                          title="Editar panel"
                        >
                          <Edit className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleDeletePanel(panel)}
                          className="text-red-600 hover:text-red-900"
                          title="Eliminar panel"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal de envío de mensaje */}
      {showMessageForm && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Enviar Mensaje</h3>
              
              <div className="space-y-4">
                {!selectedPanel && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Seleccionar Panel
                    </label>
                    <select
                      value={selectedPanel?.id || ''}
                      onChange={(e) => {
                        const panel = panels.find(p => p.id === parseInt(e.target.value))
                        setSelectedPanel(panel)
                      }}
                      className="input-field"
                    >
                      <option value="">Selecciona un panel...</option>
                      {panels.map((panel) => (
                        <option key={panel.id} value={panel.id}>
                          {panel.name} ({panel.status})
                        </option>
                      ))}
                    </select>
                  </div>
                )}

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Mensaje
                  </label>
                  <textarea
                    value={messageText}
                    onChange={(e) => setMessageText(e.target.value)}
                    className="input-field"
                    rows="3"
                    placeholder="Escribe el mensaje que se mostrará en el panel..."
                    maxLength="100"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    {messageText.length}/100 caracteres
                  </p>
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
                    min="1"
                    max="3600"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Color
                  </label>
                  <select
                    value={selectedColor}
                    onChange={(e) => setSelectedColor(parseInt(e.target.value))}
                    className="input-field"
                  >
                    <option value={1}>Rojo</option>
                    <option value={2}>Verde</option>
                    <option value={3}>Amarillo</option>
                    <option value={4}>Azul</option>
                    <option value={5}>Magenta</option>
                    <option value={6}>Cian</option>
                    <option value={7}>Blanco</option>
                  </select>
                </div>

                {/* NUEVO v4.1.0: Selector de ventana para paneles Tipo 3 */}
                {selectedPanel?.supports_multiple_windows && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Ventana de Destino
                    </label>
                    <div className="flex space-x-3">
                      <label className="flex items-center">
                        <input
                          type="radio"
                          value={0}
                          checked={selectedWindow === 0}
                          onChange={(e) => setSelectedWindow(parseInt(e.target.value))}
                          className="mr-2 text-blue-600 focus:ring-blue-500"
                        />
                        <span className="text-sm text-gray-700">Ventana 0</span>
                      </label>
                      <label className="flex items-center">
                        <input
                          type="radio"
                          value={1}
                          checked={selectedWindow === 1}
                          onChange={(e) => setSelectedWindow(parseInt(e.target.value))}
                          className="mr-2 text-blue-600 focus:ring-blue-500"
                        />
                        <span className="text-sm text-gray-700">Ventana 1</span>
                      </label>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">
                      {selectedPanel?.panel_type?.name || 'Panel Tipo 3'} soporta múltiples ventanas
                    </p>
                  </div>
                )}
                
                {/* Información para paneles que no soportan múltiples ventanas */}
                {selectedPanel && !selectedPanel?.supports_multiple_windows && (
                  <div className="bg-blue-50 p-3 rounded-md">
                    <div className="flex items-start">
                      <Info className="h-5 w-5 text-blue-400 mt-0.5 mr-2" />
                      <div>
                        <p className="text-sm text-blue-800">
                          Este panel solo soporta una ventana (Ventana 0)
                        </p>
                        <p className="text-xs text-blue-600 mt-1">
                          Tipo: {selectedPanel?.panel_type?.name || 'Estándar'}
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              <div className="flex justify-between items-center mt-6">
                {/* NUEVO v4.1.0: Botón de validación */}
                <button
                  onClick={handleValidateMessage}
                  disabled={validateMessageMutation.isLoading || !selectedPanel || !messageText.trim()}
                  className="px-4 py-2 text-blue-600 border border-blue-300 rounded-md hover:bg-blue-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {validateMessageMutation.isLoading ? 'Validando...' : 'Validar Mensaje'}
                </button>

                <div className="flex space-x-3">
                  <button
                    onClick={clearMessageResponse}
                    className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
                  >
                    Cancelar
                  </button>
                  <button
                    onClick={handleSendMessage}
                    disabled={sendMessageMutation.isLoading}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
                  >
                    {sendMessageMutation.isLoading ? 'Enviando...' : 'Enviar Mensaje'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* NUEVO v4.1.0: Modal de validación de mensaje */}
      {showValidation && validationResult && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-medium text-gray-900">Validación de Mensaje</h3>
                <button
                  onClick={() => setShowValidation(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="h-6 w-6" />
                </button>
              </div>

              {/* Estado de validación */}
              <div className={`p-4 rounded-lg mb-4 ${validationResult.valid ? 'bg-green-50' : 'bg-red-50'}`}>
                <div className="flex items-start">
                  {validationResult.valid ? (
                    <CheckCircle className="h-5 w-5 text-green-400 mt-0.5 mr-2" />
                  ) : (
                    <AlertCircle className="h-5 w-5 text-red-400 mt-0.5 mr-2" />
                  )}
                  <div>
                    <p className={`text-sm font-medium ${validationResult.valid ? 'text-green-800' : 'text-red-800'}`}>
                      {validationResult.valid ? 'Mensaje válido para envío' : 'Mensaje contiene errores'}
                    </p>
                  </div>
                </div>
              </div>

              {/* Información del panel */}
              <div className="bg-blue-50 p-3 rounded-lg mb-4">
                <h4 className="text-sm font-medium text-blue-800 mb-2">Panel de Destino</h4>
                <p className="text-sm text-blue-700">
                  <strong>{validationResult.panel_info.name}</strong> ({validationResult.panel_info.panel_type})
                </p>
                <p className="text-xs text-blue-600">
                  {validationResult.panel_info.supports_multiple_windows ? 'Soporta múltiples ventanas' : 'Solo ventana única'}
                </p>
              </div>

              {/* Errores */}
              {validationResult.errors && validationResult.errors.length > 0 && (
                <div className="mb-4">
                  <h4 className="text-sm font-medium text-red-800 mb-2">Errores:</h4>
                  <ul className="list-disc list-inside text-sm text-red-700 space-y-1">
                    {validationResult.errors.map((error, index) => (
                      <li key={index}>{error}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Advertencias */}
              {validationResult.warnings && validationResult.warnings.length > 0 && (
                <div className="mb-4">
                  <h4 className="text-sm font-medium text-yellow-800 mb-2">Advertencias:</h4>
                  <ul className="list-disc list-inside text-sm text-yellow-700 space-y-1">
                    {validationResult.warnings.map((warning, index) => (
                      <li key={index}>{warning}</li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="flex justify-end space-x-3 mt-6">
                <button
                  onClick={() => setShowValidation(false)}
                  className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
                >
                  Cerrar
                </button>
                {validationResult.valid && (
                  <button
                    onClick={() => {
                      setShowValidation(false)
                      handleSendMessage()
                    }}
                    className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
                  >
                    Enviar Mensaje
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modal de resultados de verificación */}
      {verificationResults && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-3/4 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-medium text-gray-900">Resultados de Verificación</h3>
                <button
                  onClick={() => setVerificationResults(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="h-6 w-6" />
                </button>
              </div>
              
              <div className="grid grid-cols-4 gap-4 mb-6">
                <div className="bg-blue-50 p-4 rounded-lg">
                  <div className="text-2xl font-bold text-blue-600">{verificationResults.total_panels}</div>
                  <div className="text-sm text-blue-800">Total Paneles</div>
                </div>
                <div className="bg-green-50 p-4 rounded-lg">
                  <div className="text-2xl font-bold text-green-600">{verificationResults.online_count}</div>
                  <div className="text-sm text-green-800">Online</div>
                </div>
                <div className="bg-red-50 p-4 rounded-lg">
                  <div className="text-2xl font-bold text-red-600">{verificationResults.offline_count}</div>
                  <div className="text-sm text-red-800">Offline</div>
                </div>
                <div className="bg-yellow-50 p-4 rounded-lg">
                  <div className="text-2xl font-bold text-yellow-600">{verificationResults.updated_count}</div>
                  <div className="text-sm text-yellow-800">Actualizados</div>
                </div>
              </div>
              
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Panel</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">IP</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Estado Anterior</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Estado Nuevo</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Ping</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tiempo</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {verificationResults.results.map((result) => (
                      <tr key={result.panel_id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {result.panel_name}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {result.ip}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(result.previous_status)}`}>
                            {result.previous_status}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(result.new_status)}`}>
                            {result.new_status}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          {result.ping_success ? (
                            <CheckCircle className="h-5 w-5 text-green-600" />
                          ) : (
                            <X className="h-5 w-5 text-red-600" />
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {result.ping_time_ms ? `${result.ping_time_ms}ms` : 'N/A'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modal de creación de panel */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Crear Nuevo Panel</h3>
              <form onSubmit={handleCreatePanel}>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Nombre
                  </label>
                  <input
                    type="text"
                    value={createForm.name}
                    onChange={(e) => setCreateForm({...createForm, name: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Ej: Panel Entrada"
                    required
                  />
                </div>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    IP
                  </label>
                  <input
                    type="text"
                    value={createForm.ip}
                    onChange={(e) => setCreateForm({...createForm, ip: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="192.168.1.100"
                    required
                  />
                </div>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Puerto
                  </label>
                  <input
                    type="number"
                    value={createForm.port}
                    onChange={(e) => setCreateForm({...createForm, port: parseInt(e.target.value) || 5200})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="5200"
                  />
                </div>
                {/* Parking: solo obligatorio si NO es Tipo 4 */}
                {!isPanelType4(createForm.panel_type_id) && (
                  <div className="mb-4">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Parking <span className="text-red-500">*</span>
                    </label>
                    <select
                      value={createForm.parking_id}
                      onChange={(e) => setCreateForm({...createForm, parking_id: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      required
                    >
                      <option value="">Seleccionar parking...</option>
                      {parkings.map(parking => (
                        <option key={parking.id} value={parking.id}>
                          {parking.name}
                        </option>
                      ))}
                    </select>
                  </div>
                )}
                
                {/* Para Tipo 4, mostrar info sobre parking */}
                {isPanelType4(createForm.panel_type_id) && (
                  <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-md">
                    <p className="text-sm text-blue-800">
                      <strong>Panel Tipo 4:</strong> Puedes asignar diferentes parkings a cada ventana. 
                      El parking seleccionado aquí se usará como valor por defecto para crear el panel.
                    </p>
                    <select
                      value={createForm.parking_id}
                      onChange={(e) => setCreateForm({...createForm, parking_id: e.target.value})}
                      className="w-full mt-2 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="">Seleccionar parking por defecto (opcional)...</option>
                      {parkings.map(parking => (
                        <option key={parking.id} value={parking.id}>
                          {parking.name}
                        </option>
                      ))}
                    </select>
                  </div>
                )}
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Tipo de Panel <span className="text-red-500">*</span>
                  </label>
                  <select
                    value={createForm.panel_type_id}
                    onChange={(e) => {
                      const newTypeId = e.target.value
                      const windowsCount = getWindowsCountForType(newTypeId)
                      setCreateForm({
                        ...createForm, 
                        panel_type_id: newTypeId,
                        windows_count: windowsCount
                      })
                      // Limpiar asignaciones pendientes si cambia el tipo
                      if (!isPanelType4(newTypeId)) {
                        setPendingWindowAssignments([])
                      }
                    }}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  >
                    <option value="">Seleccionar tipo...</option>
                    {panelTypes.map(type => (
                      <option key={type.id} value={type.id}>
                        {type.name}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Campo de número de ventanas para Tipo 4 */}
                {isPanelType4(createForm.panel_type_id) && (
                  <div className="mb-4">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Número de Ventanas (1-16) <span className="text-red-500">*</span>
                    </label>
                    <select
                      value={createForm.windows_count || 16}
                      onChange={(e) => {
                        const newCount = parseInt(e.target.value)
                        setCreateForm({...createForm, windows_count: newCount})
                        // Limpiar asignaciones que excedan el nuevo número de ventanas
                        setPendingWindowAssignments(prev => 
                          prev.filter(a => a.window_id < newCount)
                        )
                      }}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      required
                    >
                      {Array.from({ length: 16 }, (_, i) => i + 1).map(num => (
                        <option key={num} value={num}>{num}</option>
                      ))}
                    </select>
                    <p className="mt-1 text-xs text-gray-500">
                      Selecciona cuántas ventanas tendrá este panel (máximo 16)
                    </p>
                  </div>
                )}

                {/* PanelWindowManager para Tipo 4 - ahora se muestra siempre que sea Tipo 4 */}
                {isPanelType4(createForm.panel_type_id) && (
                  <PanelWindowManager
                    panelId={null} // No existe aún
                    parkingId={createForm.parking_id ? parseInt(createForm.parking_id) : null}
                    panelTypeId={parseInt(createForm.panel_type_id)}
                    windowsCount={createForm.windows_count || 16}
                    onWindowsCountChange={(count) => setCreateForm({...createForm, windows_count: count})}
                    isEditing={false}
                    pendingAssignments={pendingWindowAssignments}
                    onPendingAssignmentsChange={setPendingWindowAssignments}
                  />
                )}

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
                    disabled={createPanelMutation.isLoading}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
                  >
                    {createPanelMutation.isLoading ? 'Creando...' : 'Crear Panel'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Modal de edición de panel */}
      {showEditModal && editingPanel && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Editar Panel</h3>
              <form onSubmit={handleUpdatePanel}>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Nombre
                  </label>
                  <input
                    type="text"
                    value={editForm.name}
                    onChange={(e) => setEditForm({...editForm, name: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    IP
                  </label>
                  <input
                    type="text"
                    value={editForm.ip}
                    onChange={(e) => setEditForm({...editForm, ip: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="192.168.1.100"
                    required
                  />
                </div>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Puerto
                  </label>
                  <input
                    type="number"
                    value={editForm.port}
                    onChange={(e) => setEditForm({...editForm, port: parseInt(e.target.value) || 5200})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="5200"
                  />
                </div>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Parking
                  </label>
                  <select
                    value={editForm.parking_id || ''}
                    onChange={(e) => setEditForm({...editForm, parking_id: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  >
                    <option value="">Seleccionar parking...</option>
                    {parkings.map(parking => (
                      <option key={parking.id} value={parking.id.toString()}>
                        {parking.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Tipo de Panel
                  </label>
                  <select
                    value={editForm.panel_type_id || ''}
                    onChange={(e) => {
                      const newTypeId = e.target.value
                      const windowsCount = getWindowsCountForType(newTypeId)
                      setEditForm({
                        ...editForm, 
                        panel_type_id: newTypeId,
                        windows_count: windowsCount
                      })
                    }}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  >
                    <option value="">Seleccionar tipo...</option>
                    {panelTypes.map(type => (
                      <option key={type.id} value={type.id.toString()}>
                        {type.name}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Campo de número de ventanas para Tipo 4 */}
                {isPanelType4(editForm.panel_type_id) && (
                  <div className="mb-4">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Número de Ventanas (1-16) <span className="text-red-500">*</span>
                    </label>
                    <select
                      value={editForm.windows_count || 16}
                      onChange={(e) => {
                        const newCount = parseInt(e.target.value)
                        setEditForm({...editForm, windows_count: newCount})
                      }}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      required
                    >
                      {Array.from({ length: 16 }, (_, i) => i + 1).map(num => (
                        <option key={num} value={num}>{num}</option>
                      ))}
                    </select>
                    <p className="mt-1 text-xs text-gray-500">
                      Selecciona cuántas ventanas tendrá este panel (máximo 16)
                    </p>
                  </div>
                )}

                {/* PanelWindowManager para Tipo 4 */}
                {isPanelType4(editForm.panel_type_id) && editForm.parking_id && editingPanel && (
                  <div className="mb-4">
                    <PanelWindowManager
                      panelId={editingPanel.id}
                      parkingId={parseInt(editForm.parking_id)}
                      panelTypeId={parseInt(editForm.panel_type_id)}
                      windowsCount={editForm.windows_count || 16}
                      onWindowsCountChange={(count) => setEditForm({...editForm, windows_count: count})}
                      isEditing={true}
                    />
                  </div>
                )}

                {/* Mensaje informativo si es Tipo 4 pero no hay parking seleccionado */}
                {isPanelType4(editForm.panel_type_id) && !editForm.parking_id && (
                  <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-md">
                    <p className="text-sm text-blue-800">
                      <strong>Panel Tipo 4:</strong> Selecciona un parking para configurar las ventanas. 
                      Puedes asignar diferentes parkings o grupos de sensores a cada ventana.
                    </p>
                  </div>
                )}

                <div className="mb-6">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={editForm.is_active}
                      onChange={(e) => setEditForm({...editForm, is_active: e.target.checked})}
                      className="mr-2"
                    />
                    <span className="text-sm text-gray-700">Panel activo</span>
                  </label>
                </div>
                <div className="flex justify-end space-x-3">
                  <button
                    type="button"
                    onClick={() => setShowEditModal(false)}
                    className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
                  >
                    Cancelar
                  </button>
                  <button
                    type="submit"
                    disabled={updatePanelMutation.isLoading}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
                  >
                    {updatePanelMutation.isLoading ? 'Actualizando...' : 'Actualizar Panel'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Modal de respuesta del mensaje */}
      {showResponseDetails && messageResponse && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Respuesta del Panel</h3>
              <div className="space-y-2 text-sm">
                <p><strong>Estado:</strong> {messageResponse.status}</p>
                <p><strong>Panel:</strong> {messageResponse.panel_name}</p>
                <p><strong>Mensaje:</strong> {messageResponse.message}</p>
                <p><strong>Duración:</strong> {messageResponse.duration} segundos</p>
                <p><strong>Tiempo de respuesta:</strong> {messageResponse.response_time}ms</p>
              </div>
              <div className="flex justify-end mt-6">
                <button
                  onClick={clearMessageResponse}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  Cerrar
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modal de información de programación */}
      <ScheduleInfoModal
        isOpen={showScheduleModal}
        onClose={handleCloseScheduleModal}
        panel={selectedPanel}
        schedule={selectedSchedule}
      />
    </div>
  )
}

export default Panels 