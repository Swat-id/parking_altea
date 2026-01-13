import { useState, useEffect } from 'react'
import { Plus, Trash2, ChevronDown, ChevronUp, Check, X } from 'lucide-react'
import windowService from '../services/windowService'
import parkingService from '../services/parkingService'
import toast from 'react-hot-toast'

const PanelWindowManager = ({ 
  panelId, 
  parkingId, 
  panelTypeId, 
  windowsCount = 1,
  onWindowsCountChange,
  isEditing = false,
  pendingAssignments = [],
  onPendingAssignmentsChange = null
}) => {
  const [windows, setWindows] = useState([])
  const [windowConfigs, setWindowConfigs] = useState({})
  const [loading, setLoading] = useState(false)
  const [loadingConfigs, setLoadingConfigs] = useState(false)
  const [isType3Or4, setIsType3Or4] = useState(false)
  const [panelTypeName, setPanelTypeName] = useState('')
  
  // Estado para el formulario inline de cada ventana
  const [expandedWindow, setExpandedWindow] = useState(null)
  const [parkings, setParkings] = useState([])
  const [loadingParkings, setLoadingParkings] = useState(false)
  const [sensorTypes, setSensorTypes] = useState([])
  const [loadingSensorTypes, setLoadingSensorTypes] = useState(false)
  
  // Estado del formulario inline
  const [inlineForm, setInlineForm] = useState({
    parking_id: null,
    content_type: 'numeric',
    status_language: 'valenciano',
    sensor_type: null,
    texto_fijo_previo: '',
    color: 2
  })

  // Determinar si es Tipo 3
  const isType3 = panelTypeId === 3 || (windowsCount === 2 && panelTypeId)
  const isType4 = panelTypeId === 4

  useEffect(() => {
    if (panelTypeId) {
      const type3 = windowsCount === 2 || panelTypeId === 3
      const type4 = windowsCount === 16 || panelTypeId === 4
      setIsType3Or4(type3 || type4)
      
      if (type3) {
        setPanelTypeName('Tipo 3')
      } else if (type4) {
        setPanelTypeName('Tipo 4')
      } else {
        setPanelTypeName('')
      }
    }
  }, [panelTypeId, windowsCount])

  useEffect(() => {
    if (panelId && isEditing) {
      loadWindowAssignments()
      loadWindowConfigurations()
    } else {
      initializeWindows()
    }
  }, [panelId, isEditing, windowsCount, panelTypeId, parkingId])

  useEffect(() => {
    if (!panelId && !isEditing) {
      if (pendingAssignments && pendingAssignments.length > 0) {
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
        initializeWindows()
      }
    }
  }, [pendingAssignments, windowsCount, panelId, isEditing])

  // Cargar parkings cuando se expande una ventana
  useEffect(() => {
    if (expandedWindow !== null && parkings.length === 0) {
      loadParkings()
    }
  }, [expandedWindow])

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

  const loadParkings = async () => {
    try {
      setLoadingParkings(true)
      const data = await parkingService.getParkings()
      setParkings(data || [])
    } catch (error) {
      console.error('Error cargando parkings:', error)
      toast.error('Error al cargar los parkings')
    } finally {
      setLoadingParkings(false)
    }
  }

  const loadSensorTypes = async (selectedParkingId) => {
    if (!selectedParkingId) return
    try {
      setLoadingSensorTypes(true)
      const types = await windowService.getParkingSensorTypes(selectedParkingId)
      setSensorTypes(types || [])
    } catch (error) {
      console.error('Error cargando tipos de sensores:', error)
      setSensorTypes([])
    } finally {
      setLoadingSensorTypes(false)
    }
  }

  const loadWindowAssignments = async () => {
    if (!panelId) return
    
    try {
      setLoading(true)
      const assignments = await windowService.getWindowAssignments(panelId)
      
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
      initializeWindows()
    } finally {
      setLoading(false)
    }
  }

  const loadWindowConfigurations = async () => {
    if (!panelId || !parkingId) return
    
    try {
      setLoadingConfigs(true)
      const configs = {}
      for (let windowId = 0; windowId < windowsCount; windowId++) {
        try {
          const config = await windowService.getWindowConfig(parkingId, panelId, windowId)
          if (config) {
            configs[windowId] = config
          }
        } catch (error) {
          if (error.response?.status !== 404) {
            console.warn(`Error cargando configuración para ventana ${windowId}:`, error)
          }
        }
      }
      setWindowConfigs(configs)
    } catch (error) {
      console.error('Error cargando configuraciones de ventanas:', error)
    } finally {
      setLoadingConfigs(false)
    }
  }

  const handleExpandWindow = (windowId) => {
    if (expandedWindow === windowId) {
      setExpandedWindow(null)
      resetInlineForm()
    } else {
      setExpandedWindow(windowId)
      resetInlineForm()
      // Si es Tipo 3 y hay parkingId, preseleccionarlo
      if (isType3 && parkingId) {
        setInlineForm(prev => ({ ...prev, parking_id: parkingId }))
      }
    }
  }

  const resetInlineForm = () => {
    setInlineForm({
      parking_id: isType3 && parkingId ? parkingId : null,
      content_type: 'numeric',
      status_language: 'valenciano',
      sensor_type: null,
      texto_fijo_previo: '',
      color: 2
    })
    setSensorTypes([])
  }

  const handleParkingChange = (parkingIdValue) => {
    const pid = parseInt(parkingIdValue)
    setInlineForm(prev => ({ ...prev, parking_id: pid, sensor_type: null }))
    if (inlineForm.content_type === 'sensor_group') {
      loadSensorTypes(pid)
    }
  }

  const handleContentTypeChange = (contentType) => {
    setInlineForm(prev => ({ ...prev, content_type: contentType, sensor_type: null }))
    if (contentType === 'sensor_group' && inlineForm.parking_id) {
      loadSensorTypes(inlineForm.parking_id)
    }
  }

  const handleSaveAssignment = async (windowId) => {
    if (!inlineForm.parking_id) {
      toast.error('Debes seleccionar un parking')
      return
    }

    if (inlineForm.content_type === 'sensor_group' && !inlineForm.sensor_type) {
      toast.error('Debes seleccionar un tipo de sensor')
      return
    }

    const parking = parkings.find(p => p.id === inlineForm.parking_id)
    
    // Determinar el tipo de sensor y texto según el tipo de contenido
    let sensorType = null
    let textoFijo = null
    let assignmentColor = null

    switch (inlineForm.content_type) {
      case 'numeric':
        sensorType = null
        textoFijo = null
        assignmentColor = null
        break
      case 'status':
        sensorType = '__STATUS__'
        textoFijo = inlineForm.status_language
        assignmentColor = null
        break
      case 'pmr':
        sensorType = 'PMR'
        textoFijo = isType3 ? null : 'PMR'
        assignmentColor = inlineForm.color
        break
      case 'sensor_group':
        sensorType = inlineForm.sensor_type
        textoFijo = isType3 ? null : (inlineForm.texto_fijo_previo || null)
        assignmentColor = inlineForm.color
        break
    }

    const newAssignment = {
      window_id: windowId,
      parking_id: inlineForm.parking_id,
      parking_name: parking?.name || `Parking ${inlineForm.parking_id}`,
      sensor_type: sensorType,
      content_type: inlineForm.content_type,
      status_language: inlineForm.content_type === 'status' ? inlineForm.status_language : null,
      texto_fijo_previo: textoFijo,
      color: assignmentColor
    }

    if (panelId && isEditing) {
      // Si el panel ya existe, guardar en la base de datos
      try {
        const result = await windowService.assignParkingToWindow(
          panelId,
          windowId,
          inlineForm.parking_id,
          sensorType,
          textoFijo,
          assignmentColor
        )

        if (result.success) {
          toast.success('Asignación guardada')
          loadWindowAssignments()
          setExpandedWindow(null)
          resetInlineForm()
        } else {
          toast.error(result.error || 'Error al guardar la asignación')
        }
      } catch (error) {
        console.error('Error guardando asignación:', error)
        toast.error(error?.response?.data?.error || 'Error al guardar la asignación')
      }
    } else if (onPendingAssignmentsChange) {
      // Agregar a asignaciones pendientes
      const updated = [...(pendingAssignments || []), newAssignment]
      onPendingAssignmentsChange(updated)
      toast.success('Asignación agregada')
      setExpandedWindow(null)
      resetInlineForm()
    }
  }

  const handleRemoveAssignment = async (windowId, assignment) => {
    if (!window.confirm('¿Estás seguro de que quieres eliminar esta asignación?')) {
      return
    }

    if (panelId && isEditing) {
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
    } else if (onPendingAssignmentsChange) {
      const updated = pendingAssignments.filter(a => 
        !(a.window_id === windowId && 
          a.parking_id === assignment.parking_id && 
          (a.sensor_type || null) === (assignment.sensor_type || null))
      )
      onPendingAssignmentsChange(updated)
      toast.success('Asignación eliminada')
    }
  }

  const getAssignmentLabel = (assignment) => {
    const parkingName = assignment.parking_name || `Parking ${assignment.parking_id}`
    
    if (assignment.content_type) {
      switch (assignment.content_type) {
        case 'numeric':
          return `📊 Plazas libres - ${parkingName}`
        case 'status':
          const lang = assignment.status_language === 'castellano' ? 'Castellano' : 'Valenciano'
          return `📝 Estado (${lang}) - ${parkingName}`
        case 'pmr':
          return `♿ Plazas PMR - ${parkingName}`
        case 'sensor_group':
          const prefix = assignment.texto_fijo_previo || assignment.sensor_type
          return `🔌 ${prefix} - ${parkingName}`
        default:
          break
      }
    }
    
    if (assignment.sensor_type === '__STATUS__') {
      const lang = assignment.texto_fijo_previo === 'castellano' ? 'Castellano' : 'Valenciano'
      return `📝 Estado (${lang}) - ${parkingName}`
    }
    
    if (assignment.sensor_type === 'PMR') {
      return `♿ Plazas PMR - ${parkingName}`
    }
    
    if (assignment.sensor_type) {
      const prefix = assignment.texto_fijo_previo || assignment.sensor_type
      return `🔌 ${prefix} - ${parkingName}`
    }
    
    return `📊 Plazas libres - ${parkingName}`
  }

  if (!isType3Or4) {
    return null
  }

  return (
    <div className="mt-6 border-t pt-6">
      <div className="flex items-center justify-between mb-4">
        <h4 className="text-lg font-semibold text-gray-900">
          Configuración de Ventanas ({panelTypeName})
        </h4>
        {panelTypeId === 4 && (
          <div className="flex items-center space-x-2">
            <label className="text-sm text-gray-700">Ventanas:</label>
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
          Cargando configuración...
        </div>
      ) : (
        <div className="space-y-3">
          {windows.map((windowItem) => {
            const windowConfig = windowConfigs[windowItem.window_id]
            const isExpanded = expandedWindow === windowItem.window_id
            
            return (
              <div key={windowItem.window_id} className="border rounded-lg bg-gray-50 overflow-hidden">
                {/* Header de la ventana */}
                <div className="flex items-center justify-between p-3 bg-gray-100">
                  <h5 className="font-medium text-gray-900">
                    Ventana {windowItem.window_id}
                    {windowItem.assignments.length > 0 && (
                      <span className="ml-2 text-xs text-green-600">
                        ({windowItem.assignments.length} asignación{windowItem.assignments.length > 1 ? 'es' : ''})
                      </span>
                    )}
                  </h5>
                  <button
                    type="button"
                    onClick={() => handleExpandWindow(windowItem.window_id)}
                    className="flex items-center px-3 py-1 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700"
                  >
                    <Plus className="h-4 w-4 mr-1" />
                    Agregar
                    {isExpanded ? <ChevronUp className="h-4 w-4 ml-1" /> : <ChevronDown className="h-4 w-4 ml-1" />}
                  </button>
                </div>

                {/* Asignaciones existentes */}
                {windowItem.assignments.length > 0 && (
                  <div className="p-3 space-y-2 border-t">
                    {windowItem.assignments.map((assignment, idx) => (
                      <div
                        key={idx}
                        className="flex items-center justify-between bg-white p-2 rounded border"
                      >
                        <span className="text-sm text-gray-700">
                          {getAssignmentLabel(assignment)}
                        </span>
                        <button
                          type="button"
                          onClick={() => handleRemoveAssignment(windowItem.window_id, assignment)}
                          className="text-red-600 hover:text-red-800 p-1"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}

                {/* Formulario inline expandible */}
                {isExpanded && (
                  <div className="p-4 border-t bg-white space-y-4">
                    {/* Selector de parking */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Parking
                      </label>
                      {isType3 && parkingId ? (
                        <div className="px-3 py-2 border border-gray-300 rounded-md bg-gray-50 text-gray-700 text-sm">
                          {parkings.find(p => p.id === parkingId)?.name || `Parking ${parkingId}`}
                        </div>
                      ) : (
                        <select
                          value={inlineForm.parking_id || ''}
                          onChange={(e) => handleParkingChange(e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-blue-500 focus:border-blue-500"
                        >
                          <option value="">Seleccionar parking...</option>
                          {parkings.map((p) => (
                            <option key={p.id} value={p.id}>{p.name}</option>
                          ))}
                        </select>
                      )}
                    </div>

                    {/* Tipo de contenido */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        ¿Qué mostrar?
                      </label>
                      <div className="grid grid-cols-2 gap-2">
                        {[
                          { value: 'numeric', label: '📊 Plazas libres', desc: 'Número' },
                          { value: 'status', label: '📝 Estado', desc: 'LIBRE/DENSO/COMPLETO' },
                          { value: 'pmr', label: '♿ Plazas PMR', desc: 'Minusválidos' },
                          { value: 'sensor_group', label: '🔌 Sensores', desc: 'Grupo específico' }
                        ].map((option) => (
                          <label
                            key={option.value}
                            className={`flex flex-col p-2 border rounded-md cursor-pointer text-sm transition-colors ${
                              inlineForm.content_type === option.value
                                ? 'border-blue-500 bg-blue-50'
                                : 'border-gray-200 hover:bg-gray-50'
                            }`}
                          >
                            <input
                              type="radio"
                              value={option.value}
                              checked={inlineForm.content_type === option.value}
                              onChange={(e) => handleContentTypeChange(e.target.value)}
                              className="sr-only"
                            />
                            <span className="font-medium">{option.label}</span>
                            <span className="text-xs text-gray-500">{option.desc}</span>
                          </label>
                        ))}
                      </div>
                    </div>

                    {/* Opciones según tipo de contenido */}
                    {inlineForm.content_type === 'status' && (
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Idioma
                        </label>
                        <div className="flex gap-3">
                          {[
                            { value: 'valenciano', label: 'Valenciano', texts: 'LLIURE, DENS, COMPLET' },
                            { value: 'castellano', label: 'Castellano', texts: 'LIBRE, DENSO, COMPLETO' }
                          ].map((lang) => (
                            <label
                              key={lang.value}
                              className={`flex-1 p-3 border rounded-md cursor-pointer text-center transition-colors ${
                                inlineForm.status_language === lang.value
                                  ? 'border-blue-500 bg-blue-50'
                                  : 'border-gray-200 hover:bg-gray-50'
                              }`}
                            >
                              <input
                                type="radio"
                                value={lang.value}
                                checked={inlineForm.status_language === lang.value}
                                onChange={(e) => setInlineForm(prev => ({ ...prev, status_language: e.target.value }))}
                                className="sr-only"
                              />
                              <span className="block font-medium text-sm">{lang.label}</span>
                              <span className="block text-xs text-gray-500 mt-1">{lang.texts}</span>
                            </label>
                          ))}
                        </div>
                      </div>
                    )}

                    {(inlineForm.content_type === 'pmr' || inlineForm.content_type === 'sensor_group') && (
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Color
                        </label>
                        <select
                          value={inlineForm.color}
                          onChange={(e) => setInlineForm(prev => ({ ...prev, color: parseInt(e.target.value) }))}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                        >
                          <option value={1}>🔴 Rojo</option>
                          <option value={2}>🟢 Verde</option>
                          <option value={3}>🟡 Amarillo</option>
                          <option value={4}>🔵 Azul</option>
                          <option value={5}>🟣 Morado</option>
                          <option value={6}>🩵 Cian</option>
                          <option value={7}>⚪ Blanco</option>
                        </select>
                      </div>
                    )}

                    {inlineForm.content_type === 'sensor_group' && (
                      <>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Tipo de sensor
                          </label>
                          {loadingSensorTypes ? (
                            <div className="text-sm text-gray-500">Cargando...</div>
                          ) : sensorTypes.length === 0 ? (
                            <div className="text-sm text-yellow-600 bg-yellow-50 p-2 rounded">
                              No hay sensores configurados en este parking
                            </div>
                          ) : (
                            <select
                              value={inlineForm.sensor_type || ''}
                              onChange={(e) => setInlineForm(prev => ({ ...prev, sensor_type: e.target.value }))}
                              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                            >
                              <option value="">Seleccionar...</option>
                              {sensorTypes.map((type) => (
                                <option key={type} value={type}>{type}</option>
                              ))}
                            </select>
                          )}
                        </div>
                        {!isType3 && (
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                              Texto previo (opcional)
                            </label>
                            <input
                              type="text"
                              value={inlineForm.texto_fijo_previo}
                              onChange={(e) => setInlineForm(prev => ({ ...prev, texto_fijo_previo: e.target.value }))}
                              placeholder="Ej: ELÉCTRICO"
                              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                            />
                          </div>
                        )}
                      </>
                    )}

                    {/* Botones de acción */}
                    <div className="flex justify-end gap-2 pt-2 border-t">
                      <button
                        type="button"
                        onClick={() => {
                          setExpandedWindow(null)
                          resetInlineForm()
                        }}
                        className="px-3 py-1.5 text-sm text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
                      >
                        <X className="h-4 w-4 inline mr-1" />
                        Cancelar
                      </button>
                      <button
                        type="button"
                        onClick={() => handleSaveAssignment(windowItem.window_id)}
                        disabled={!inlineForm.parking_id || (inlineForm.content_type === 'sensor_group' && !inlineForm.sensor_type)}
                        className="px-3 py-1.5 text-sm bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        <Check className="h-4 w-4 inline mr-1" />
                        Guardar
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )
          })}
        </div>
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
