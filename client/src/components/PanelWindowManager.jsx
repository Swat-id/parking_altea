import { useState, useEffect } from 'react'
import { Plus, Trash2, Settings, X } from 'lucide-react'
import windowService from '../services/windowService'
import WindowAssignmentModal from './WindowAssignmentModal'
import toast from 'react-hot-toast'

const PanelWindowManager = ({ 
  panelId, 
  parkingId, 
  panelTypeId, 
  windowsCount = 1,
  onWindowsCountChange,
  isEditing = false,
  pendingAssignments = [], // Asignaciones pendientes (para creación de panel)
  onPendingAssignmentsChange = null // Callback para actualizar asignaciones pendientes
}) => {
  const [windows, setWindows] = useState([]) // Array de asignaciones por ventana
  const [windowConfigs, setWindowConfigs] = useState({}) // Configuraciones por ventana {windowId: config}
  const [loading, setLoading] = useState(false)
  const [loadingConfigs, setLoadingConfigs] = useState(false)
  const [showAssignmentModal, setShowAssignmentModal] = useState(false)
  const [selectedWindowId, setSelectedWindowId] = useState(null)
  const [isType3Or4, setIsType3Or4] = useState(false)
  const [panelTypeName, setPanelTypeName] = useState('')

  useEffect(() => {
    // Verificar si es Tipo 3 (2 ventanas) o Tipo 4 (16 ventanas)
    if (panelTypeId) {
      const isType3 = windowsCount === 2 || panelTypeId === 3
      const isType4 = windowsCount === 16 || panelTypeId === 4
      setIsType3Or4(isType3 || isType4)
      
      if (isType3) {
        setPanelTypeName('Tipo 3')
      } else if (isType4) {
        setPanelTypeName('Tipo 4')
      } else {
        setPanelTypeName('')
      }
    }
  }, [panelTypeId, windowsCount])

  useEffect(() => {
    if (panelId && isEditing) {
      console.log(`[PanelWindowManager] useEffect: panelId=${panelId}, isEditing=${isEditing}, windowsCount=${windowsCount}`)
      // Cargar asignaciones y configuraciones
      loadWindowAssignments()
      loadWindowConfigurations()
    } else {
      // Inicializar ventanas vacías para nuevo panel
      initializeWindows()
    }
  }, [panelId, isEditing, windowsCount, panelTypeId, parkingId]) // Añadir parkingId para recargar cuando cambia el parking
  
  // Recargar asignaciones y configuraciones cuando el componente se monta o cuando cambia el panelId
  useEffect(() => {
    if (panelId && isEditing) {
      console.log(`[PanelWindowManager] Recargando asignaciones y configuraciones: panelId=${panelId}`)
      loadWindowAssignments()
      loadWindowConfigurations()
    }
  }, [panelId]) // Solo cuando cambia panelId

  // Efecto separado para actualizar asignaciones pendientes
  useEffect(() => {
    if (!panelId && !isEditing) {
      if (pendingAssignments && pendingAssignments.length > 0) {
        // Agrupar asignaciones pendientes por window_id
        const windowsMap = {}
        for (let i = 0; i < windowsCount; i++) {
          windowsMap[i] = []
        }
        
        pendingAssignments.forEach(assignment => {
          const wid = assignment.window_id
          if (wid >= 0 && wid < windowsCount) {
            windowsMap[wid].push({
              ...assignment,
              parking_name: assignment.parking_name || `Parking ${assignment.parking_id}`
            })
          }
        })
        
        const windowsArray = Object.keys(windowsMap).map(wid => ({
          window_id: parseInt(wid),
          assignments: windowsMap[wid]
        }))
        
        setWindows(windowsArray)
      } else {
        // Si no hay asignaciones pendientes, reinicializar
        initializeWindows()
      }
    }
  }, [pendingAssignments, windowsCount, panelId, isEditing])

  const initializeWindows = () => {
    const initialWindows = []
    for (let i = 0; i < windowsCount; i++) {
      initialWindows.push({
        window_id: i,
        assignments: []
      })
    }
    setWindows(initialWindows)
  }

  const loadWindowAssignments = async () => {
    if (!panelId) return
    
    try {
      setLoading(true)
      console.log(`[PanelWindowManager] Cargando asignaciones para panel ${panelId}, windowsCount: ${windowsCount}`)
      const assignments = await windowService.getWindowAssignments(panelId)
      console.log(`[PanelWindowManager] Asignaciones recibidas:`, assignments)
      
      // Agrupar asignaciones por window_id
      const windowsMap = {}
      for (let i = 0; i < windowsCount; i++) {
        windowsMap[i] = []
      }
      
      assignments.forEach(assignment => {
        const wid = assignment.window_id
        if (wid >= 0 && wid < windowsCount) {
          windowsMap[wid].push(assignment)
        }
      })
      
      const windowsArray = Object.keys(windowsMap).map(wid => ({
        window_id: parseInt(wid),
        assignments: windowsMap[wid]
      }))
      
      console.log(`[PanelWindowManager] Ventanas agrupadas:`, windowsArray)
      setWindows(windowsArray)
    } catch (error) {
      console.error('Error cargando asignaciones de ventanas:', error)
      toast.error('Error al cargar las asignaciones de ventanas')
      // Inicializar ventanas vacías en caso de error
      initializeWindows()
    } finally {
      setLoading(false)
    }
  }

  const loadWindowConfigurations = async () => {
    if (!panelId || !parkingId) return
    
    try {
      setLoadingConfigs(true)
      console.log(`[PanelWindowManager] Cargando configuraciones para panel ${panelId}, parking ${parkingId}`)
      
      const configs = {}
      // Cargar configuraciones para cada ventana
      for (let windowId = 0; windowId < windowsCount; windowId++) {
        try {
          const config = await windowService.getWindowConfig(parkingId, panelId, windowId)
          if (config) {
            configs[windowId] = config
            console.log(`[PanelWindowManager] Configuración cargada para ventana ${windowId}:`, config)
          }
        } catch (error) {
          // Si no existe configuración, no es error (puede no estar configurada)
          if (error.response?.status !== 404) {
            console.warn(`[PanelWindowManager] Error cargando configuración para ventana ${windowId}:`, error)
          }
        }
      }
      
      setWindowConfigs(configs)
      console.log(`[PanelWindowManager] Configuraciones cargadas:`, configs)
    } catch (error) {
      console.error('Error cargando configuraciones de ventanas:', error)
      // No mostrar error al usuario, las configuraciones son opcionales
    } finally {
      setLoadingConfigs(false)
    }
  }

  const handleAddAssignment = (windowId) => {
    setSelectedWindowId(windowId)
    setShowAssignmentModal(true)
  }

  const handleRemoveAssignment = async (windowId, assignment) => {
    if (!window.confirm('¿Estás seguro de que quieres eliminar esta asignación?')) {
      return
    }

    if (panelId && isEditing) {
      // Eliminar de la base de datos
      try {
        await windowService.unassignParkingFromWindow(
          panelId,
          windowId,
          assignment.parking_id,
          assignment.sensor_type
        )
        toast.success('Asignación eliminada')
        loadWindowAssignments()
      } catch (error) {
        console.error('Error eliminando asignación:', error)
        toast.error('Error al eliminar la asignación')
      }
    } else {
      // Eliminar de asignaciones pendientes
      if (onPendingAssignmentsChange) {
        const updated = pendingAssignments.filter(a => 
          !(a.window_id === windowId && 
            a.parking_id === assignment.parking_id && 
            (a.sensor_type || null) === (assignment.sensor_type || null))
        )
        onPendingAssignmentsChange(updated)
        toast.success('Asignación eliminada')
      }
    }
  }

  const handleAssignmentSuccess = (newAssignment) => {
    if (panelId && isEditing) {
      loadWindowAssignments()
      loadWindowConfigurations() // Recargar también configuraciones
      setShowAssignmentModal(false)
      setSelectedWindowId(null)
    } else if (onPendingAssignmentsChange && newAssignment) {
      // Agregar a asignaciones pendientes
      const updated = [...(pendingAssignments || []), newAssignment]
      onPendingAssignmentsChange(updated)
      setShowAssignmentModal(false)
      setSelectedWindowId(null)
      // La visualización se actualizará automáticamente por el useEffect
    } else {
      setShowAssignmentModal(false)
      setSelectedWindowId(null)
    }
  }

  const getAssignmentLabel = (assignment) => {
    if (assignment.sensor_type) {
      const prefix = assignment.texto_fijo_previo || assignment.sensor_type
      return `${prefix} (${assignment.parking_name || `Parking ${assignment.parking_id}`})`
    }
    return `Parking: ${assignment.parking_name || `Parking ${assignment.parking_id}`}`
  }

  if (!isType3Or4) {
    return null // No mostrar para paneles que no son Tipo 3 o Tipo 4
  }

  // Determinar el número máximo de ventanas según el tipo
  const maxWindows = windowsCount === 2 ? 2 : 16

  return (
    <div className="mt-6 border-t pt-6">
      <div className="flex items-center justify-between mb-4">
        <h4 className="text-lg font-semibold text-gray-900">
          Configuración de Ventanas ({panelTypeName})
        </h4>
        {windowsCount === 16 && (
          <div className="flex items-center space-x-2">
            <label className="text-sm text-gray-700">Número de ventanas:</label>
            <select
              value={windowsCount}
              onChange={(e) => onWindowsCountChange?.(parseInt(e.target.value))}
              className="px-2 py-1 border border-gray-300 rounded-md text-sm"
              disabled={isEditing}
            >
              {Array.from({ length: 16 }, (_, i) => i + 1).map(num => (
                <option key={num} value={num}>{num}</option>
              ))}
            </select>
          </div>
        )}
      </div>

      {(loading || loadingConfigs) ? (
        <div className="text-center py-4 text-gray-500">
          Cargando {loading ? 'asignaciones' : ''} {loading && loadingConfigs ? 'y ' : ''} {loadingConfigs ? 'configuraciones' : ''}...
        </div>
      ) : (
        <div className="space-y-4">
          {windows.map((window) => {
            const windowConfig = windowConfigs[window.window_id]
            return (
              <div key={window.window_id} className="border rounded-lg p-4 bg-gray-50">
                <div className="flex items-center justify-between mb-3">
                  <h5 className="font-medium text-gray-900">
                    Ventana {window.window_id}
                    {windowConfig && (
                      <span className="ml-2 text-xs text-gray-500">
                        (Configurada: {windowConfig.rotation_enabled ? 'Rotación activa' : 'Sin rotación'})
                      </span>
                    )}
                  </h5>
                  <button
                    type="button"
                    onClick={() => handleAddAssignment(window.window_id)}
                    className="flex items-center px-3 py-1 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700"
                  >
                    <Plus className="h-4 w-4 mr-1" />
                    Agregar
                  </button>
                </div>

                {window.assignments.length === 0 ? (
                  <p className="text-sm text-gray-500 italic">
                    No hay asignaciones para esta ventana
                  </p>
                ) : (
                  <div className="space-y-2">
                    {window.assignments.map((assignment, idx) => (
                      <div
                        key={idx}
                        className="flex items-center justify-between bg-white p-2 rounded border"
                      >
                        <span className="text-sm text-gray-700">
                          {getAssignmentLabel(assignment)}
                        </span>
                        <button
                          type="button"
                          onClick={() => handleRemoveAssignment(window.window_id, assignment)}
                          className="text-red-600 hover:text-red-800"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
                
                {/* Mostrar información de configuración si existe (solo para Tipo 4) */}
                {windowConfig && panelTypeId === 4 && (
                  <div className="mt-3 pt-3 border-t border-gray-200">
                    <p className="text-xs text-gray-600">
                      <strong>Configuración:</strong> {windowConfig.rotation_enabled ? 'Rotación activa' : 'Sin rotación'} | 
                      Refresco: {windowConfig.refresh_time_seconds}s | 
                      Elementos: {windowConfig.rotation_order?.length || 0}
                    </p>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}

      {showAssignmentModal && selectedWindowId !== null && (
        <WindowAssignmentModal
          isOpen={showAssignmentModal}
          onClose={() => {
            setShowAssignmentModal(false)
            setSelectedWindowId(null)
          }}
          panelId={panelId} // Puede ser null si se está creando
          windowId={selectedWindowId}
          onSuccess={handleAssignmentSuccess}
          isCreating={!panelId && !isEditing} // Indica si se está creando el panel
          parkingId={parkingId} // Parking del panel (para Tipo 3)
          panelTypeId={panelTypeId} // Tipo de panel
        />
      )}

      {!panelId && !isEditing && pendingAssignments.length > 0 && (
        <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-md">
          <p className="text-sm text-green-800">
            <strong>✓ {pendingAssignments.length} asignación(es) configurada(s).</strong> 
            {' '}Se guardarán automáticamente al crear el panel.
          </p>
        </div>
      )}
    </div>
  )
}

export default PanelWindowManager

