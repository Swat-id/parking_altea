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
  const [loading, setLoading] = useState(false)
  const [showAssignmentModal, setShowAssignmentModal] = useState(false)
  const [selectedWindowId, setSelectedWindowId] = useState(null)
  const [isType4, setIsType4] = useState(false)

  useEffect(() => {
    // Verificar si es Tipo 4 (soporta 16 ventanas)
    if (panelTypeId) {
      // Asumimos que Tipo 4 tiene windows_count = 16
      // Esto se puede verificar con una consulta a panelTypes si es necesario
      setIsType4(windowsCount === 16 || panelTypeId === 4)
    }
  }, [panelTypeId, windowsCount])

  useEffect(() => {
    if (panelId && isEditing) {
      loadWindowAssignments()
    } else {
      // Inicializar ventanas vacías para nuevo panel
      initializeWindows()
    }
  }, [panelId, isEditing, windowsCount])

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
      const assignments = await windowService.getWindowAssignments(panelId)
      
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
      
      setWindows(windowsArray)
    } catch (error) {
      console.error('Error cargando asignaciones de ventanas:', error)
      toast.error('Error al cargar las asignaciones de ventanas')
    } finally {
      setLoading(false)
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

  if (!isType4) {
    return null // No mostrar para paneles que no son Tipo 4
  }

  return (
    <div className="mt-6 border-t pt-6">
      <div className="flex items-center justify-between mb-4">
        <h4 className="text-lg font-semibold text-gray-900">
          Configuración de Ventanas (Tipo 4)
        </h4>
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
      </div>

      {loading ? (
        <div className="text-center py-4 text-gray-500">Cargando asignaciones...</div>
      ) : (
        <div className="space-y-4">
          {windows.map((window) => (
            <div key={window.window_id} className="border rounded-lg p-4 bg-gray-50">
              <div className="flex items-center justify-between mb-3">
                <h5 className="font-medium text-gray-900">
                  Ventana {window.window_id}
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
            </div>
          ))}
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

