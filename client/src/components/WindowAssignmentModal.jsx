import { useState, useEffect } from 'react'
import { X, Save, AlertCircle, Info } from 'lucide-react'
import windowService from '../services/windowService'
import parkingService from '../services/parkingService'
import toast from 'react-hot-toast'

const WindowAssignmentModal = ({ 
  isOpen, 
  onClose, 
  panelId, 
  windowId, 
  onSuccess, 
  isCreating = false,
  parkingId = null, // Parking del panel (para Tipo 3)
  panelTypeId = null // Tipo de panel (para determinar si es Tipo 3)
}) => {
  const [parkings, setParkings] = useState([])
  const [selectedParkingId, setSelectedParkingId] = useState(null)
  const [sensorTypes, setSensorTypes] = useState([])
  const [selectedSensorType, setSelectedSensorType] = useState(null)
  
  // Nuevo: Tipo de contenido a mostrar
  const [contentType, setContentType] = useState('numeric') // 'numeric', 'status', 'pmr', 'sensor_group'
  
  // Nuevo: Idioma para el texto de estado
  const [statusLanguage, setStatusLanguage] = useState('valenciano') // 'valenciano', 'castellano'
  
  const [textoFijoPrevio, setTextoFijoPrevio] = useState('')
  const [color, setColor] = useState(2) // Color por defecto: Verde (2)
  const [loading, setLoading] = useState(false)
  const [loadingParkings, setLoadingParkings] = useState(false)
  const [loadingSensorTypes, setLoadingSensorTypes] = useState(false)
  
  // Determinar si es Tipo 3
  const isType3 = panelTypeId === 3 || (windowId !== undefined && windowId < 2 && parkingId !== null)
  const isType4 = panelTypeId === 4

  // Textos de estado según idioma
  const statusTexts = {
    valenciano: { libre: 'LLIURE', denso: 'DENS', completo: 'COMPLET' },
    castellano: { libre: 'LIBRE', denso: 'DENSO', completo: 'COMPLETO' }
  }

  useEffect(() => {
    if (isOpen) {
      loadParkings()
      
      // Si es Tipo 3 y tiene parkingId, usar ese parking directamente
      if (isType3 && parkingId) {
        setSelectedParkingId(parkingId)
      }
    } else {
      // Reset al cerrar
      resetForm()
    }
  }, [isOpen, parkingId, windowId, isType3])

  useEffect(() => {
    if (selectedParkingId && contentType === 'sensor_group') {
      loadSensorTypes(selectedParkingId)
    } else if (contentType !== 'sensor_group') {
      setSensorTypes([])
      setSelectedSensorType(null)
    }
  }, [selectedParkingId, contentType])

  const resetForm = () => {
    setSelectedParkingId(null)
    setContentType('numeric')
    setStatusLanguage('valenciano')
    setSelectedSensorType(null)
    setTextoFijoPrevio('')
    setColor(2)
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

  const loadSensorTypes = async (parkingId) => {
    try {
      setLoadingSensorTypes(true)
      const types = await windowService.getParkingSensorTypes(parkingId)
      setSensorTypes(types)
    } catch (error) {
      console.error('Error cargando tipos de sensores:', error)
      toast.error('Error al cargar los tipos de sensores')
    } finally {
      setLoadingSensorTypes(false)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    e.stopPropagation() // Evitar propagación al form padre

    if (!selectedParkingId) {
      toast.error('Debes seleccionar un parking')
      return
    }

    if (contentType === 'sensor_group' && !selectedSensorType) {
      toast.error('Debes seleccionar un tipo de sensor')
      return
    }

    // Construir la asignación
    const parking = parkings.find(p => p.id === selectedParkingId)
    
    // Determinar el tipo de sensor y texto según el tipo de contenido
    let sensorType = null
    let textoFijo = null
    let assignmentColor = null

    switch (contentType) {
      case 'numeric':
        // Plazas libres numéricas - sin sensor_type especial
        sensorType = null
        textoFijo = null
        assignmentColor = null
        break
      case 'status':
        // Mostrar texto de estado (LIBRE/DENSO/COMPLETO)
        sensorType = '__STATUS__'
        textoFijo = statusLanguage // Guardar el idioma seleccionado
        assignmentColor = null // El color se determina dinámicamente según el estado
        break
      case 'pmr':
        // Plazas PMR
        sensorType = 'PMR'
        textoFijo = isType3 ? null : 'PMR'
        assignmentColor = color
        break
      case 'sensor_group':
        sensorType = selectedSensorType
        textoFijo = isType3 ? null : (textoFijoPrevio || null)
        assignmentColor = color
        break
    }

    // Si se está creando el panel (sin panelId), devolver la asignación al callback
    if (isCreating || !panelId) {
      const newAssignment = {
        window_id: windowId,
        parking_id: selectedParkingId,
        parking_name: parking?.name || `Parking ${selectedParkingId}`,
        sensor_type: sensorType,
        content_type: contentType,
        status_language: contentType === 'status' ? statusLanguage : null,
        texto_fijo_previo: textoFijo,
        color: assignmentColor
      }
      
      toast.success('Asignación agregada')
      // Primero actualizar las asignaciones pendientes, luego cerrar
      onSuccess?.(newAssignment)
      resetForm()
      // El cierre del modal lo maneja handleAssignmentSuccess en PanelWindowManager
      return
    }

    // Si el panel ya existe, guardar en la base de datos
    try {
      setLoading(true)
      const result = await windowService.assignParkingToWindow(
        panelId,
        windowId,
        selectedParkingId,
        sensorType,
        textoFijo,
        assignmentColor
      )

      if (result.success) {
        toast.success('Asignación creada exitosamente')
        onSuccess?.()
        if (!isType3 || !parkingId) {
          setSelectedParkingId(null)
        }
        resetForm()
        setTimeout(() => {
          onClose()
        }, 500)
      } else {
        toast.error(result.error || 'Error al crear la asignación')
      }
    } catch (error) {
      console.error('Error asignando parking a ventana:', error)
      toast.error(error?.response?.data?.error || 'Error al crear la asignación')
    } finally {
      setLoading(false)
    }
  }

  if (!isOpen) return null

  return (
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[60]"
      onClick={(e) => {
        e.stopPropagation()
        if (e.target === e.currentTarget) {
          onClose()
        }
      }}
    >
      <div 
        className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex justify-between items-center p-6 border-b">
          <h2 className="text-xl font-bold text-gray-900">
            Configurar Ventana {windowId}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          
          {/* Selección de parking */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Parking <span className="text-red-500">*</span>
            </label>
            {isType3 && parkingId ? (
              <>
                <div className="px-3 py-2 border border-gray-300 rounded-md bg-gray-50 text-gray-700">
                  {parkings.find(p => p.id === parkingId)?.name || `Parking ${parkingId}`}
                </div>
                <p className="mt-1 text-xs text-gray-500">
                  Para paneles Tipo 3, el parking está vinculado al panel
                </p>
              </>
            ) : (
              <>
                {loadingParkings ? (
                  <div className="text-sm text-gray-500">Cargando parkings...</div>
                ) : (
                  <select
                    value={selectedParkingId || ''}
                    onChange={(e) => setSelectedParkingId(parseInt(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  >
                    <option value="">Seleccionar parking...</option>
                    {parkings.map((parking) => (
                      <option key={parking.id} value={parking.id}>
                        {parking.name}
                      </option>
                    ))}
                  </select>
                )}
              </>
            )}
          </div>

          {/* Tipo de contenido a mostrar */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              ¿Qué mostrar en esta ventana?
            </label>
            <div className="space-y-3">
              <label className="flex items-start p-3 border rounded-lg cursor-pointer hover:bg-gray-50 transition-colors">
                <input
                  type="radio"
                  value="numeric"
                  checked={contentType === 'numeric'}
                  onChange={(e) => setContentType(e.target.value)}
                  className="mt-1 mr-3"
                />
                <div>
                  <span className="font-medium text-gray-900">Plazas libres (número)</span>
                  <p className="text-sm text-gray-500">Muestra el número de plazas libres del parking (ej: "45")</p>
                </div>
              </label>
              
              <label className="flex items-start p-3 border rounded-lg cursor-pointer hover:bg-gray-50 transition-colors">
                <input
                  type="radio"
                  value="status"
                  checked={contentType === 'status'}
                  onChange={(e) => setContentType(e.target.value)}
                  className="mt-1 mr-3"
                />
                <div>
                  <span className="font-medium text-gray-900">Estado (texto)</span>
                  <p className="text-sm text-gray-500">Muestra el estado del parking (LIBRE, DENSO, COMPLETO)</p>
                </div>
              </label>
              
              <label className="flex items-start p-3 border rounded-lg cursor-pointer hover:bg-gray-50 transition-colors">
                <input
                  type="radio"
                  value="pmr"
                  checked={contentType === 'pmr'}
                  onChange={(e) => setContentType(e.target.value)}
                  className="mt-1 mr-3"
                />
                <div>
                  <span className="font-medium text-gray-900">Plazas PMR (minusválidos)</span>
                  <p className="text-sm text-gray-500">Muestra las plazas libres de movilidad reducida</p>
                </div>
              </label>
              
              <label className="flex items-start p-3 border rounded-lg cursor-pointer hover:bg-gray-50 transition-colors">
                <input
                  type="radio"
                  value="sensor_group"
                  checked={contentType === 'sensor_group'}
                  onChange={(e) => setContentType(e.target.value)}
                  className="mt-1 mr-3"
                />
                <div>
                  <span className="font-medium text-gray-900">Grupo de sensores específico</span>
                  <p className="text-sm text-gray-500">Eléctrico, Caravanas, u otro tipo de sensor configurado</p>
                </div>
              </label>
            </div>
          </div>

          {/* Selector de idioma (solo si contentType === 'status') */}
          {contentType === 'status' && (
            <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Idioma del texto de estado
              </label>
              <div className="grid grid-cols-2 gap-4">
                <label className={`flex flex-col items-center p-4 border-2 rounded-lg cursor-pointer transition-colors ${
                  statusLanguage === 'valenciano' ? 'border-blue-500 bg-blue-100' : 'border-gray-200 hover:bg-gray-50'
                }`}>
                  <input
                    type="radio"
                    value="valenciano"
                    checked={statusLanguage === 'valenciano'}
                    onChange={(e) => setStatusLanguage(e.target.value)}
                    className="sr-only"
                  />
                  <span className="font-medium text-gray-900 mb-2">Valenciano</span>
                  <div className="text-xs text-gray-600 space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="w-3 h-3 rounded-full bg-green-500"></span>
                      <span>LLIURE</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="w-3 h-3 rounded-full bg-yellow-500"></span>
                      <span>DENS</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="w-3 h-3 rounded-full bg-red-500"></span>
                      <span>COMPLET</span>
                    </div>
                  </div>
                </label>
                
                <label className={`flex flex-col items-center p-4 border-2 rounded-lg cursor-pointer transition-colors ${
                  statusLanguage === 'castellano' ? 'border-blue-500 bg-blue-100' : 'border-gray-200 hover:bg-gray-50'
                }`}>
                  <input
                    type="radio"
                    value="castellano"
                    checked={statusLanguage === 'castellano'}
                    onChange={(e) => setStatusLanguage(e.target.value)}
                    className="sr-only"
                  />
                  <span className="font-medium text-gray-900 mb-2">Castellano</span>
                  <div className="text-xs text-gray-600 space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="w-3 h-3 rounded-full bg-green-500"></span>
                      <span>LIBRE</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="w-3 h-3 rounded-full bg-yellow-500"></span>
                      <span>DENSO</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="w-3 h-3 rounded-full bg-red-500"></span>
                      <span>COMPLETO</span>
                    </div>
                  </div>
                </label>
              </div>
              <div className="mt-3 flex items-start text-xs text-blue-700">
                <Info className="h-4 w-4 mr-1 flex-shrink-0 mt-0.5" />
                <span>El color se ajustará automáticamente según el estado del parking</span>
              </div>
            </div>
          )}

          {/* Opciones para PMR */}
          {contentType === 'pmr' && !isType3 && (
            <div className="p-4 bg-purple-50 border border-purple-200 rounded-lg">
              <div className="flex items-start mb-3">
                <Info className="h-5 w-5 text-purple-600 mr-2 flex-shrink-0" />
                <p className="text-sm text-purple-800">
                  Se mostrará el número de plazas PMR libres con el prefijo "PMR"
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Color del texto
                </label>
                <select
                  value={color}
                  onChange={(e) => setColor(parseInt(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value={1}>Rojo</option>
                  <option value={2}>Verde</option>
                  <option value={3}>Amarillo/Naranja</option>
                  <option value={4}>Azul</option>
                  <option value={5}>Morado</option>
                  <option value={6}>Cian</option>
                  <option value={7}>Blanco</option>
                </select>
              </div>
            </div>
          )}

          {/* Selección de tipo de sensor (solo si contentType === 'sensor_group') */}
          {contentType === 'sensor_group' && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Tipo de Sensor <span className="text-red-500">*</span>
                </label>
                {loadingSensorTypes ? (
                  <div className="text-sm text-gray-500">Cargando tipos de sensores...</div>
                ) : sensorTypes.length === 0 ? (
                  <div className="text-sm text-yellow-600 bg-yellow-50 p-3 rounded-md flex items-start">
                    <AlertCircle className="h-5 w-5 mr-2 mt-0.5" />
                    <span>
                      El parking seleccionado no tiene sensores configurados. 
                      Primero debes agregar sensores al parking.
                    </span>
                  </div>
                ) : (
                  <select
                    value={selectedSensorType || ''}
                    onChange={(e) => setSelectedSensorType(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  >
                    <option value="">Seleccionar tipo de sensor...</option>
                    {sensorTypes.map((type) => (
                      <option key={type} value={type}>
                        {type}
                      </option>
                    ))}
                  </select>
                )}
              </div>

              {selectedSensorType && (
                <>
                  {/* Texto fijo previo - SOLO para Tipo 4, NO para Tipo 3 */}
                  {!isType3 && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Texto fijo previo (opcional)
                      </label>
                      <input
                        type="text"
                        value={textoFijoPrevio}
                        onChange={(e) => setTextoFijoPrevio(e.target.value)}
                        placeholder="Ej: ELÉCTRICO, CARAVANAS..."
                        maxLength={50}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                      <p className="mt-1 text-xs text-gray-500">
                        Texto que aparecerá antes del número de plazas libres
                      </p>
                    </div>
                  )}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Color del texto
                    </label>
                    <select
                      value={color}
                      onChange={(e) => setColor(parseInt(e.target.value))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value={1}>Rojo</option>
                      <option value={2}>Verde</option>
                      <option value={3}>Amarillo/Naranja</option>
                      <option value={4}>Azul</option>
                      <option value={5}>Morado</option>
                      <option value={6}>Cian</option>
                      <option value={7}>Blanco</option>
                    </select>
                  </div>
                </>
              )}
            </div>
          )}

          {/* Resumen de la configuración */}
          <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg">
            <h4 className="text-sm font-medium text-gray-700 mb-2">Resumen</h4>
            <div className="text-sm text-gray-600">
              <p><strong>Parking:</strong> {selectedParkingId ? (parkings.find(p => p.id === selectedParkingId)?.name || `ID ${selectedParkingId}`) : 'No seleccionado'}</p>
              <p><strong>Contenido:</strong> {
                contentType === 'numeric' ? 'Número de plazas libres' :
                contentType === 'status' ? `Estado en ${statusLanguage === 'valenciano' ? 'Valenciano' : 'Castellano'}` :
                contentType === 'pmr' ? 'Plazas PMR' :
                contentType === 'sensor_group' ? `Grupo: ${selectedSensorType || 'No seleccionado'}` : ''
              }</p>
            </div>
          </div>

          {/* Botones */}
          <div className="flex justify-end space-x-3 pt-4 border-t">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={loading || !selectedParkingId || (contentType === 'sensor_group' && (!selectedSensorType || sensorTypes.length === 0))}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Guardando...
                </>
              ) : (
                <>
                  <Save className="h-4 w-4 mr-2" />
                  Guardar
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default WindowAssignmentModal
