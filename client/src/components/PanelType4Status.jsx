import { useState, useEffect } from 'react'
import { Clock, RefreshCw, ChevronDown, ChevronUp, Info } from 'lucide-react'
import windowService from '../services/windowService'
import toast from 'react-hot-toast'

const PanelType4Status = ({ panelId, windowsCount = 16 }) => {
  const [expanded, setExpanded] = useState(false)
  const [loading, setLoading] = useState(false)
  const [windowStatuses, setWindowStatuses] = useState({})
  const [nextChanges, setNextChanges] = useState({})

  useEffect(() => {
    if (expanded && panelId) {
      loadWindowStatuses()
    }
  }, [expanded, panelId])

  const loadWindowStatuses = async () => {
    setLoading(true)
    try {
      const statuses = {}
      const changes = {}

      // Cargar estado y próximos cambios para cada ventana
      for (let windowId = 0; windowId < windowsCount; windowId++) {
        try {
          const [contentResult, changesResult] = await Promise.all([
            windowService.getWindowContent(panelId, windowId).catch(() => null),
            windowService.getWindowNextChanges(panelId, windowId).catch(() => null)
          ])

          if (contentResult?.success) {
            statuses[windowId] = {
              hasContent: true,
              message: contentResult.message,
              contentType: contentResult.content?.type,
              sensorType: contentResult.content?.sensor_type,
              textoFijoPrevio: contentResult.content?.texto_fijo_previo
            }
          } else {
            statuses[windowId] = {
              hasContent: false,
              message: 'Sin contenido configurado'
            }
          }

          if (changesResult?.success && changesResult.changes?.length > 0) {
            changes[windowId] = changesResult.changes.slice(0, 5) // Primeros 5 cambios
          }
        } catch (error) {
          console.error(`Error cargando estado de ventana ${windowId}:`, error)
        }
      }

      setWindowStatuses(statuses)
      setNextChanges(changes)
    } catch (error) {
      console.error('Error cargando estados de ventanas:', error)
      toast.error('Error al cargar el estado de las ventanas')
    } finally {
      setLoading(false)
    }
  }

  const handleRefresh = () => {
    loadWindowStatuses()
  }

  const formatTime = (timeString) => {
    const date = new Date(timeString)
    return date.toLocaleTimeString('es-ES', { 
      hour: '2-digit', 
      minute: '2-digit',
      second: '2-digit'
    })
  }

  const getContentLabel = (status) => {
    if (!status.hasContent) return 'Sin contenido'
    
    if (status.contentType === 'parking') {
      return 'Parking general'
    } else if (status.contentType === 'sensor_group') {
      const prefix = status.textoFijoPrevio || status.sensorType || 'Sensor'
      return prefix
    }
    return 'Desconocido'
  }

  return (
    <div className="mt-2 border rounded-lg bg-gray-50">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between p-3 text-left hover:bg-gray-100 transition-colors"
      >
        <div className="flex items-center space-x-2">
          <Info className="h-4 w-4 text-blue-600" />
          <span className="text-sm font-medium text-gray-900">
            Estado y Próximos Cambios (Tipo 4)
          </span>
        </div>
        <div className="flex items-center space-x-2">
          {loading && (
            <RefreshCw className="h-4 w-4 text-gray-400 animate-spin" />
          )}
          {expanded ? (
            <ChevronUp className="h-4 w-4 text-gray-500" />
          ) : (
            <ChevronDown className="h-4 w-4 text-gray-500" />
          )}
        </div>
      </button>

      {expanded && (
        <div className="p-4 border-t bg-white">
          <div className="flex justify-end mb-3">
            <button
              onClick={handleRefresh}
              disabled={loading}
              className="flex items-center px-3 py-1 text-sm text-blue-600 hover:text-blue-700 disabled:opacity-50"
            >
              <RefreshCw className={`h-4 w-4 mr-1 ${loading ? 'animate-spin' : ''}`} />
              Actualizar
            </button>
          </div>

          {loading ? (
            <div className="text-center py-4 text-gray-500">Cargando estados...</div>
          ) : (
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {Array.from({ length: windowsCount }, (_, i) => i).map((windowId) => {
                const status = windowStatuses[windowId] || { hasContent: false }
                const changes = nextChanges[windowId] || []

                return (
                  <div key={windowId} className="border rounded-md p-3 bg-gray-50">
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <h5 className="font-medium text-sm text-gray-900">
                          Ventana {windowId}
                        </h5>
                        <p className="text-xs text-gray-600 mt-1">
                          {status.hasContent ? (
                            <>
                              <span className="font-medium">{getContentLabel(status)}</span>
                              {status.message && (
                                <span className="ml-2 text-gray-500">
                                  - {status.message}
                                </span>
                              )}
                            </>
                          ) : (
                            <span className="text-gray-400">Sin contenido configurado</span>
                          )}
                        </p>
                      </div>
                      <span
                        className={`px-2 py-1 text-xs rounded-full ${
                          status.hasContent
                            ? 'bg-green-100 text-green-800'
                            : 'bg-gray-100 text-gray-600'
                        }`}
                      >
                        {status.hasContent ? 'Activa' : 'Inactiva'}
                      </span>
                    </div>

                    {changes.length > 0 && (
                      <div className="mt-2 pt-2 border-t">
                        <div className="flex items-center text-xs text-gray-600 mb-1">
                          <Clock className="h-3 w-3 mr-1" />
                          Próximos cambios:
                        </div>
                        <div className="space-y-1">
                          {changes.map((change, idx) => (
                            <div
                              key={idx}
                              className="text-xs text-gray-600 flex items-center justify-between"
                            >
                              <span>
                                {formatTime(change.time)} -{' '}
                                {change.texto_fijo_previo || change.sensor_type || change.content_type}
                                {' '}
                                ({change.percentage}%, {Math.round(change.duration_seconds)}s)
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default PanelType4Status

