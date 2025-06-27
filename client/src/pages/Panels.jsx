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
  X,
  Loader,
  Info,
  Eye,
  EyeOff
} from 'lucide-react'
import toast from 'react-hot-toast'

const Panels = () => {
  const queryClient = useQueryClient()
  const [selectedPanel, setSelectedPanel] = useState(null)
  const [showMessageForm, setShowMessageForm] = useState(false)
  const [messageText, setMessageText] = useState('')
  const [messageDuration, setMessageDuration] = useState(30)
  const [verificationResults, setVerificationResults] = useState(null)
  const [messageResponse, setMessageResponse] = useState(null)
  const [showResponseDetails, setShowResponseDetails] = useState(false)

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
      onSuccess: (data) => {
        setMessageResponse(data)
        setShowResponseDetails(true)
        
        if (data.success) {
          toast.success('Mensaje enviado correctamente')
        } else {
          toast.error('Error al enviar el mensaje')
        }
        
        queryClient.invalidateQueries('panels')
      },
      onError: (error) => {
        setMessageResponse({
          success: false,
          message: error.message,
          errorCode: -1,
          responseTime: 0
        })
        setShowResponseDetails(true)
        toast.error('Error al enviar el mensaje')
      }
    }
  )

  const testPanelMutation = useMutation(
    (panelId) => panelService.testPanel(panelId),
    {
      onSuccess: (data) => {
        setMessageResponse(data)
        setShowResponseDetails(true)
        
        if (data.success) {
          toast.success('Prueba de panel exitosa')
        } else {
          toast.error('Error en la prueba del panel')
        }
        
        queryClient.invalidateQueries('panels')
      },
      onError: (error) => {
        setMessageResponse({
          success: false,
          message: error.message,
          errorCode: -1,
          responseTime: 0
        })
        setShowResponseDetails(true)
        toast.error('Error al probar el panel')
      }
    }
  )

  // Nueva mutación para verificar todos los paneles
  const verifyPanelsMutation = useMutation(
    () => panelService.verifyAllPanels(),
    {
      onSuccess: (data) => {
        setVerificationResults(data)
        toast.success(`Verificación completada: ${data.updated_count} paneles actualizados`)
        
        // Forzar refetch después de un pequeño delay para asegurar que el backend haya terminado
        setTimeout(() => {
          refetch()
        }, 500)
        
        // Ocultar resultados después de 5 segundos
        setTimeout(() => {
          setVerificationResults(null)
        }, 5000)
      },
      onError: () => {
        toast.error('Error al verificar paneles')
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
        <div className="flex space-x-3">
          <button
            onClick={handleVerifyAllPanels}
            disabled={verifyPanelsMutation.isLoading}
            className="btn-primary flex items-center"
          >
            {verifyPanelsMutation.isLoading ? (
              <Loader className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <Zap className="h-4 w-4 mr-2" />
            )}
            {verifyPanelsMutation.isLoading ? 'Verificando...' : 'Verificar Estado'}
          </button>
          <button
            onClick={() => refetch()}
            className="btn-secondary flex items-center"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Actualizar
          </button>
        </div>
      </div>

      {/* Resultados de verificación */}
      {verificationResults && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <CheckCircle className="h-5 w-5 text-blue-600 mr-2" />
              <h3 className="text-sm font-medium text-blue-900">
                Verificación Completada
              </h3>
            </div>
            <button
              onClick={() => setVerificationResults(null)}
              className="text-blue-400 hover:text-blue-600"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
          <div className="mt-2 text-sm text-blue-700">
            <p>Total de paneles verificados: {verificationResults.total_panels}</p>
            <p>Paneles actualizados: {verificationResults.updated_count}</p>
            {verificationResults.updated_count > 0 && (
              <div className="mt-2">
                <p className="font-medium">Cambios realizados:</p>
                <ul className="mt-1 space-y-1">
                  {verificationResults.results
                    .filter(result => result.status_changed)
                    .map((result, index) => (
                      <li key={index} className="text-xs">
                        • {result.panel_name}: {result.previous_status} → {result.new_status}
                        {result.response_time && ` (${result.response_time.toFixed(0)}ms)`}
                      </li>
                    ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Respuesta detallada del mensaje */}
      {messageResponse && showResponseDetails && (
        <div className={`border rounded-lg p-4 ${messageResponse.success ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              {messageResponse.success ? (
                <CheckCircle className="h-5 w-5 text-green-600 mr-2" />
              ) : (
                <AlertCircle className="h-5 w-5 text-red-600 mr-2" />
              )}
              <h3 className="text-sm font-medium text-gray-900">
                Respuesta del Servicio C#
              </h3>
            </div>
            <div className="flex space-x-2">
              <button
                onClick={() => setShowResponseDetails(!showResponseDetails)}
                className="text-gray-400 hover:text-gray-600"
              >
                {showResponseDetails ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
              <button
                onClick={clearMessageResponse}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          </div>
          
          {showResponseDetails && (
            <div className="mt-3 space-y-2 text-sm">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <span className="font-medium text-gray-700">Estado:</span>
                  <span className={`ml-2 px-2 py-1 rounded-full text-xs font-medium ${
                    messageResponse.success ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                  }`}>
                    {messageResponse.success ? 'EXITOSO' : 'FALLIDO'}
                  </span>
                </div>
                <div>
                  <span className="font-medium text-gray-700">Tiempo de respuesta:</span>
                  <span className="ml-2 text-gray-600">
                    {messageResponse.responseTime ? `${messageResponse.responseTime.toFixed(2)}ms` : 'N/A'}
                  </span>
                </div>
              </div>
              
              {messageResponse.panel_name && (
                <div>
                  <span className="font-medium text-gray-700">Panel:</span>
                  <span className="ml-2 text-gray-600">{messageResponse.panel_name}</span>
                </div>
              )}
              
              {messageResponse.panel_ip && (
                <div>
                  <span className="font-medium text-gray-700">IP:</span>
                  <span className="ml-2 text-gray-600">{messageResponse.panel_ip}</span>
                </div>
              )}
              
              {messageResponse.message && (
                <div>
                  <span className="font-medium text-gray-700">Mensaje enviado:</span>
                  <span className="ml-2 text-gray-600">"{messageResponse.message}"</span>
                </div>
              )}
              
              <div>
                <span className="font-medium text-gray-700">Respuesta del servicio:</span>
                <div className="mt-1 p-2 bg-gray-100 rounded text-xs font-mono text-gray-800">
                  {messageResponse.message || 'Sin respuesta'}
                </div>
              </div>
              
              {messageResponse.errorCode && messageResponse.errorCode !== 0 && (
                <div>
                  <span className="font-medium text-gray-700">Código de error:</span>
                  <span className="ml-2 text-red-600">{messageResponse.errorCode}</span>
                </div>
              )}
            </div>
          )}
        </div>
      )}

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
              onClick={clearMessageResponse}
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

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
              <div className="flex items-center">
                <Info className="h-4 w-4 text-blue-600 mr-2" />
                <span className="text-sm font-medium text-blue-900">Información del Proceso</span>
              </div>
              <p className="text-xs text-blue-700 mt-1">
                El mensaje se enviará usando el servicio C# y se mostrará la respuesta completa del panel, 
                incluyendo tiempo de respuesta y estado de la comunicación.
              </p>
            </div>
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
              onClick={clearMessageResponse}
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