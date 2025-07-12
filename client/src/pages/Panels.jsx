import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import { panelService } from '../services/panelService'
import { panelTypeService } from '../services/panelTypeService'
import { useAuth } from '../context/AuthContext'
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
  Plus
} from 'lucide-react'
import toast from 'react-hot-toast'

const Panels = () => {
  const { isSuperadmin } = useAuth()
  const queryClient = useQueryClient()
  const [selectedPanel, setSelectedPanel] = useState(null)
  const [showMessageForm, setShowMessageForm] = useState(false)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [messageText, setMessageText] = useState('')
  const [messageDuration, setMessageDuration] = useState(30)
  const [verificationResults, setVerificationResults] = useState(null)
  const [messageResponse, setMessageResponse] = useState(null)
  const [showResponseDetails, setShowResponseDetails] = useState(false)
  const [selectedColor, setSelectedColor] = useState(1) // 1=Rojo, 2=Verde, 3=Amarillo
  const [editingPanelId, setEditingPanelId] = useState(null)
  const [editingPanelTypeId, setEditingPanelTypeId] = useState(null)
  const [createForm, setCreateForm] = useState({
    name: '',
    ip: '',
    parking_id: '',
    panel_type_id: '',
    port: 5200
  })

  // Obtener paneles
  const { data: panels = [], isLoading, refetch } = useQuery(
    'panels',
    panelService.getAllPanels,
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

  // Obtener parkings para el formulario de creación
  const { data: parkings = [] } = useQuery(
    'parkings',
    () => fetch('/api/parkings').then(res => res.json())
  )

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
        queryClient.invalidateQueries('panels')
        toast.success('Verificación de paneles completada')
      },
      onError: (error) => {
        toast.error(error?.response?.data?.message || 'Error en verificación de paneles')
      }
    }
  )

  const updatePanelTypeMutation = useMutation(
    ({ panelId, panelTypeId }) => panelService.updatePanelType(panelId, panelTypeId),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('panels')
        toast.success('Tipo de panel actualizado correctamente')
        setEditingPanelId(null)
        setEditingPanelTypeId(null)
      },
      onError: (error) => {
        toast.error(error?.response?.data?.message || 'Error al actualizar tipo de panel')
      }
    }
  )

  // Mutación para crear panel
  const createPanelMutation = useMutation(
    (panelData) => panelService.createPanel(panelData),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('panels')
        toast.success('Panel creado correctamente')
        setShowCreateModal(false)
        setCreateForm({
          name: '',
          ip: '',
          parking_id: '',
          panel_type_id: '',
          port: 5200
        })
      },
      onError: (error) => {
        toast.error(error?.response?.data?.message || 'Error al crear el panel')
      }
    }
  )

  const getStatusColor = (status) => {
    switch (status) {
      case 'ONLINE':
        return 'text-green-600 bg-green-100'
      case 'OFFLINE':
        return 'text-red-600 bg-red-100'
      default:
        return 'text-gray-600 bg-gray-100'
    }
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'ONLINE':
        return <Wifi className="h-5 w-5" />
      case 'OFFLINE':
        return <WifiOff className="h-5 w-5" />
      default:
        return <Clock className="h-5 w-5" />
    }
  }

  const getColorName = (colorCode) => {
    switch (colorCode) {
      case 1: return 'Rojo'
      case 2: return 'Verde'
      case 3: return 'Amarillo'
      case 4: return 'Azul'
      case 5: return 'Magenta'
      case 6: return 'Cian'
      case 7: return 'Blanco'
      default: return 'Rojo'
    }
  }

  const handleSendMessage = () => {
    if (!selectedPanel) {
      toast.error('Selecciona un panel')
      return
    }

    if (!messageText.trim()) {
      toast.error('El mensaje no puede estar vacío')
      return
    }

    sendMessageMutation.mutate({
      panelId: selectedPanel.id,
      messageData: {
        message: messageText,
        duration: messageDuration,
        color: selectedColor,
        fontSize: 2,
        showEffect: "fijo"
      }
    })
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
  }

  // Funciones para manejar la edición del tipo de panel
  const handleEditPanelType = (panelId, currentPanelTypeId) => {
    setEditingPanelId(panelId)
    setEditingPanelTypeId(currentPanelTypeId)
  }

  const handleSavePanelType = (panelId) => {
    if (editingPanelTypeId) {
      updatePanelTypeMutation.mutate({
        panelId: panelId,
        panelTypeId: editingPanelTypeId
      })
    }
  }

  const handleCancelEdit = () => {
    setEditingPanelId(null)
    setEditingPanelTypeId(null)
  }

  const getPanelTypeDisplayName = (panelType) => {
    if (!panelType) return 'Sin tipo'
    return `${panelType.manufacturer} - ${panelType.name} (${panelType.protocol})`
  }

  const handleCreatePanel = (e) => {
    e.preventDefault()
    
    // Validaciones
    if (!createForm.name.trim()) {
      toast.error('El nombre del panel es requerido')
      return
    }

    if (!createForm.ip.trim()) {
      toast.error('La IP del panel es requerida')
      return
    }

    if (!createForm.parking_id) {
      toast.error('Debe seleccionar un parking')
      return
    }

    if (!createForm.panel_type_id) {
      toast.error('Debe seleccionar un tipo de panel')
      return
    }

    createPanelMutation.mutate(createForm)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Paneles</h1>
          <p className="mt-1 text-sm text-gray-500">
            Gestión y control de paneles informativos
          </p>
        </div>
        <div className="flex space-x-2">
          <button
            onClick={handleVerifyAllPanels}
            disabled={verifyPanelsMutation.isLoading}
            className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 disabled:opacity-50 flex items-center"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${verifyPanelsMutation.isLoading ? 'animate-spin' : ''}`} />
            Verificar Todos
          </button>
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
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-4">
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
            <Server className="h-8 w-8 text-blue-600" />
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
                  Parking
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Tipo
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
                        {panel.ip}:{panel.port || 5200}
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
                    {panel.parking_name || 'Sin parking'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {editingPanelId === panel.id ? (
                      <div className="space-y-2">
                        <select
                          value={editingPanelTypeId || ''}
                          onChange={(e) => setEditingPanelTypeId(e.target.value)}
                          className="w-full px-2 py-1 text-sm border border-gray-300 rounded"
                        >
                          <option value="">Seleccionar tipo...</option>
                          {panelTypes.map(type => (
                            <option key={type.id} value={type.id}>
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
                        {panel.panel_type ? getPanelTypeDisplayName(panel.panel_type) : 'Sin tipo'}
                        <button
                          onClick={() => handleEditPanelType(panel.id, panel.panel_type?.id)}
                          className="ml-2 text-blue-600 hover:text-blue-900"
                        >
                          <Edit className="h-3 w-3" />
                        </button>
                      </div>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {panel.last_message || 'Sin mensajes'}
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
              </div>

              <div className="flex justify-end space-x-3 mt-6">
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
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Parking
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
                <div className="mb-6">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Tipo de Panel
                  </label>
                  <select
                    value={createForm.panel_type_id}
                    onChange={(e) => setCreateForm({...createForm, panel_type_id: e.target.value})}
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
    </div>
  )
}

export default Panels 