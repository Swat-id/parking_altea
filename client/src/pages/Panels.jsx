import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import { panelService } from '../services/panelService'
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
  X
} from 'lucide-react'
import toast from 'react-hot-toast'

const Panels = () => {
  const queryClient = useQueryClient()
  const [selectedPanel, setSelectedPanel] = useState(null)
  const [showMessageForm, setShowMessageForm] = useState(false)
  const [messageText, setMessageText] = useState('')
  const [messageDuration, setMessageDuration] = useState(30)

  // Obtener paneles
  const { data: panels = [], isLoading, refetch } = useQuery(
    'panels',
    panelService.getAllPanels,
    {
      refetchInterval: 30000, // Refrescar cada 30 segundos
    }
  )

  // Mutaciones
  const sendMessageMutation = useMutation(
    ({ panelId, messageData }) => panelService.sendMessageToPanel(panelId, messageData),
    {
      onSuccess: () => {
        toast.success('Mensaje enviado correctamente')
        setShowMessageForm(false)
        setMessageText('')
        setMessageDuration(30)
        setSelectedPanel(null)
        queryClient.invalidateQueries('panels')
      },
      onError: () => {
        toast.error('Error al enviar el mensaje')
      }
    }
  )

  const testPanelMutation = useMutation(
    (panelId) => panelService.testPanel(panelId),
    {
      onSuccess: () => {
        toast.success('Prueba de panel enviada')
        queryClient.invalidateQueries('panels')
      },
      onError: () => {
        toast.error('Error al probar el panel')
      }
    }
  )

  const getStatusIcon = (status) => {
    switch (status) {
      case 'ONLINE':
        return <Wifi className="h-5 w-5 text-green-600" />
      case 'OFFLINE':
        return <WifiOff className="h-5 w-5 text-red-600" />
      default:
        return <Clock className="h-5 w-5 text-yellow-600" />
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'ONLINE':
        return 'text-green-600 bg-green-100'
      case 'OFFLINE':
        return 'text-red-600 bg-red-100'
      default:
        return 'text-yellow-600 bg-yellow-100'
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
        duration: messageDuration
      }
    })
  }

  const handleTestPanel = (panelId) => {
    testPanelMutation.mutate(panelId)
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  const onlinePanels = panels.filter(p => p.status === 'ONLINE').length
  const offlinePanels = panels.filter(p => p.status === 'OFFLINE').length

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Paneles Electrónicos</h1>
          <p className="mt-1 text-sm text-gray-500">
            Gestión y comunicación con paneles informativos
          </p>
        </div>
        <button
          onClick={() => refetch()}
          className="btn-secondary flex items-center"
        >
          <RefreshCw className="h-4 w-4 mr-2" />
          Actualizar
        </button>
      </div>

      {/* Estadísticas */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="card">
          <div className="flex items-center">
            <Monitor className="h-8 w-8 text-primary-600" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500">Total Paneles</p>
              <p className="text-lg font-semibold text-gray-900">{panels.length}</p>
            </div>
          </div>
        </div>
        <div className="card">
          <div className="flex items-center">
            <CheckCircle className="h-8 w-8 text-green-600" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500">En Línea</p>
              <p className="text-lg font-semibold text-gray-900">{onlinePanels}</p>
            </div>
          </div>
        </div>
        <div className="card">
          <div className="flex items-center">
            <AlertCircle className="h-8 w-8 text-red-600" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500">Desconectados</p>
              <p className="text-lg font-semibold text-gray-900">{offlinePanels}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Lista de paneles */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-medium text-gray-900">Paneles Disponibles</h2>
          <button
            onClick={() => setShowMessageForm(true)}
            className="btn-primary flex items-center"
          >
            <MessageSquare className="h-4 w-4 mr-2" />
            Enviar Mensaje
          </button>
        </div>

        {panels.length === 0 ? (
          <div className="text-center py-12">
            <Monitor className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No hay paneles configurados</h3>
            <p className="mt-1 text-sm text-gray-500">
              Los paneles aparecerán aquí cuando estén configurados en el sistema.
            </p>
          </div>
        ) : (
          <div className="overflow-hidden">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {panels.map((panel) => (
                <div
                  key={panel.id}
                  className={`border rounded-lg p-4 transition-all duration-200 ${
                    selectedPanel?.id === panel.id
                      ? 'border-primary-300 bg-primary-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <h3 className="text-sm font-medium text-gray-900 mb-1">
                        {panel.name}
                      </h3>
                      <p className="text-xs text-gray-500">ID: {panel.id}</p>
                      <p className="text-xs text-gray-500">IP: {panel.ip_address}</p>
                    </div>
                    <div className={`flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(panel.status)}`}>
                      {getStatusIcon(panel.status)}
                      <span className="ml-1">{panel.status}</span>
                    </div>
                  </div>

                  <div className="space-y-2 mb-3">
                    <div className="text-xs text-gray-500">
                      <span className="font-medium">Parking:</span> {panel.parking_name || 'No asignado'}
                    </div>
                    {panel.last_message && (
                      <div className="text-xs text-gray-500">
                        <span className="font-medium">Último mensaje:</span> {panel.last_message}
                      </div>
                    )}
                    {panel.last_update && (
                      <div className="text-xs text-gray-500">
                        <span className="font-medium">Última actualización:</span> {new Date(panel.last_update).toLocaleString()}
                      </div>
                    )}
                  </div>

                  <div className="flex space-x-2">
                    <button
                      onClick={() => {
                        setSelectedPanel(panel)
                        setShowMessageForm(true)
                      }}
                      className="flex-1 btn-primary text-xs py-1"
                    >
                      <Send className="h-3 w-3 mr-1" />
                      Mensaje
                    </button>
                    <button
                      onClick={() => handleTestPanel(panel.id)}
                      disabled={testPanelMutation.isLoading}
                      className="btn-secondary text-xs py-1 px-2"
                      title="Probar panel"
                    >
                      <Zap className="h-3 w-3" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Formulario de mensaje */}
      {showMessageForm && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-medium text-gray-900">
              Enviar Mensaje
              {selectedPanel && ` a ${selectedPanel.name}`}
            </h2>
            <button
              onClick={() => {
                setShowMessageForm(false)
                setSelectedPanel(null)
                setMessageText('')
                setMessageDuration(30)
              }}
              className="text-gray-400 hover:text-gray-600"
            >
              <X className="h-6 w-6" />
            </button>
          </div>

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
                className="input-field w-32"
                min="10"
                max="300"
              />
            </div>

            {selectedPanel && (
              <div className="bg-gray-50 p-3 rounded-lg">
                <h4 className="text-sm font-medium text-gray-700 mb-2">Panel Seleccionado</h4>
                <div className="text-sm text-gray-600">
                  <p><strong>Nombre:</strong> {selectedPanel.name}</p>
                  <p><strong>IP:</strong> {selectedPanel.ip_address}</p>
                  <p><strong>Estado:</strong> {selectedPanel.status}</p>
                  {selectedPanel.parking_name && (
                    <p><strong>Parking:</strong> {selectedPanel.parking_name}</p>
                  )}
                </div>
              </div>
            )}
          </div>

          <div className="flex space-x-3 mt-6">
            <button
              onClick={handleSendMessage}
              disabled={sendMessageMutation.isLoading || !selectedPanel}
              className="btn-primary flex items-center"
            >
              <Send className="h-4 w-4 mr-2" />
              {sendMessageMutation.isLoading ? 'Enviando...' : 'Enviar Mensaje'}
            </button>
            <button
              onClick={() => {
                setShowMessageForm(false)
                setSelectedPanel(null)
                setMessageText('')
                setMessageDuration(30)
              }}
              className="btn-secondary"
            >
              Cancelar
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default Panels 