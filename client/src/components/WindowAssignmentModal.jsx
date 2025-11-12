import { useState, useEffect } from 'react'
import { X, Save, AlertCircle } from 'lucide-react'
import windowService from '../services/windowService'
import panelService from '../services/panelService'
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
  const [displayType, setDisplayType] = useState('parking') // 'parking' o 'sensor_group'
  const [textoFijoPrevio, setTextoFijoPrevio] = useState('')
  const [color, setColor] = useState(2) // Color por defecto: Verde (2)
  const [loading, setLoading] = useState(false)
  const [loadingParkings, setLoadingParkings] = useState(false)
  const [loadingSensorTypes, setLoadingSensorTypes] = useState(false)
  
  // Determinar si es Tipo 3
  const isType3 = panelTypeId === 3 || (windowId !== undefined && windowId < 2 && parkingId !== null)

  useEffect(() => {
    if (isOpen) {
      // Siempre cargar parkings para poder mostrar nombres
      loadParkings()
      
      // Si es Tipo 3 y tiene parkingId, usar ese parking directamente
      if (isType3 && parkingId) {
        setSelectedParkingId(parkingId)
        // Para Tipo 3, permitir seleccionar cualquier tipo de asignación
        // No pre-configurar displayType, dejar que el usuario elija
        // Solo cargar tipos de sensores si el usuario selecciona sensor_group
      }
    } else {
      // Reset al cerrar
      setSelectedParkingId(null)
      setDisplayType('parking')
      setSelectedSensorType(null)
      setTextoFijoPrevio('')
      setColor(2)
    }
  }, [isOpen, parkingId, windowId, isType3])

  useEffect(() => {
    if (selectedParkingId && displayType === 'sensor_group') {
      loadSensorTypes(selectedParkingId)
    } else {
      setSensorTypes([])
      setSelectedSensorType(null)
    }
  }, [selectedParkingId, displayType])

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

    if (!selectedParkingId) {
      toast.error('Debes seleccionar un parking')
      return
    }

    if (displayType === 'sensor_group' && !selectedSensorType) {
      toast.error('Debes seleccionar un tipo de sensor')
      return
    }

    // Si se está creando el panel (sin panelId), devolver la asignación al callback
    if (isCreating || !panelId) {
      const parking = parkings.find(p => p.id === selectedParkingId)
      // Para Tipo 3, NO incluir texto_fijo_previo (solo valores numéricos)
      const textoFijo = isType3 ? null : (displayType === 'sensor_group' && textoFijoPrevio ? textoFijoPrevio : null)
      const newAssignment = {
        window_id: windowId,
        parking_id: selectedParkingId,
        parking_name: parking?.name || `Parking ${selectedParkingId}`,
        sensor_type: displayType === 'sensor_group' ? selectedSensorType : null,
        texto_fijo_previo: textoFijo,
        color: displayType === 'sensor_group' ? color : null
      }
      
      toast.success('Asignación agregada')
      onSuccess?.(newAssignment)
      onClose()
      // Reset form
      setSelectedParkingId(null)
      setSelectedSensorType(null)
      setDisplayType('parking')
      setTextoFijoPrevio('')
      setColor(2) // Reset a verde
      return
    }

        // Si el panel ya existe, guardar en la base de datos
    try {
      setLoading(true)
      // Para Tipo 3, NO enviar texto_fijo_previo (solo valores numéricos)
      const textoFijo = isType3 ? null : (displayType === 'sensor_group' && textoFijoPrevio ? textoFijoPrevio : null)
      const result = await windowService.assignParkingToWindow(
        panelId,
        windowId,
        selectedParkingId,
        displayType === 'sensor_group' ? selectedSensorType : null,
        textoFijo,
        displayType === 'sensor_group' ? color : null
      )

      if (result.success) {
        toast.success('Asignación creada exitosamente')
        // NO cerrar el modal aquí, solo llamar onSuccess para que recargue las asignaciones
        onSuccess?.()
        // Reset form pero mantener parkingId si es Tipo 3
        if (!isType3 || !parkingId) {
          setSelectedParkingId(null)
        }
        setSelectedSensorType(null)
        if (!isType3) {
          setDisplayType('parking')
        }
        setTextoFijoPrevio('')
        setColor(2) // Reset a verde
        // Cerrar el modal después de un pequeño delay para que el usuario vea el mensaje
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
        // Prevenir que el clic en el overlay cierre el modal padre
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
            Asignar Parking/Sensor a Ventana {windowId}
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
          {/* Tipo de asignación - Permitir seleccionar cualquier tipo para Tipo 3 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Tipo de asignación
            </label>
            <div className="space-y-2">
              <label className="flex items-center">
                <input
                  type="radio"
                  value="parking"
                  checked={displayType === 'parking'}
                  onChange={(e) => setDisplayType(e.target.value)}
                  className="mr-2"
                />
                <span>Ocupación general del parking (Plazas libres totales)</span>
              </label>
              <label className="flex items-center">
                <input
                  type="radio"
                  value="sensor_group"
                  checked={displayType === 'sensor_group'}
                  onChange={(e) => setDisplayType(e.target.value)}
                  className="mr-2"
                />
                <span>Grupo de sensores (PMR, Eléctrico, Caravanas, etc.)</span>
              </label>
            </div>
            {isType3 && (
              <p className="mt-1 text-xs text-gray-500">
                Para paneles Tipo 3, solo se mostrarán valores numéricos (sin texto previo)
              </p>
            )}
          </div>

          {/* Selección de parking - Para Tipo 3, mostrar solo el parking del panel */}
          {isType3 && parkingId ? (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Parking
              </label>
              <div className="px-3 py-2 border border-gray-300 rounded-md bg-gray-50 text-gray-700">
                {parkings.find(p => p.id === parkingId)?.name || `Parking ${parkingId}`}
              </div>
              <p className="mt-1 text-xs text-gray-500">
                Para paneles Tipo 3, el parking está vinculado al panel
              </p>
            </div>
          ) : (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Parking <span className="text-red-500">*</span>
              </label>
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
                      {parking.name} {parking.location ? `(${parking.location})` : ''}
                    </option>
                  ))}
                </select>
              )}
            </div>
          )}

          {/* Selección de tipo de sensor (solo si displayType === 'sensor_group') */}
          {displayType === 'sensor_group' && (
            <>
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

              {/* Color (solo si displayType === 'sensor_group') - Para Tipo 3, NO mostrar texto previo */}
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
                        placeholder="Ej: PMR, ELÉCTRICO, CARAVANAS..."
                        maxLength={50}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                      <p className="mt-1 text-xs text-gray-500">
                        Texto que aparecerá antes del número de plazas libres (ej: "PMR: 5/10 libres")
                      </p>
                    </div>
                  )}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Color
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
                    <p className="mt-1 text-xs text-gray-500">
                      Color del texto para este tipo de sensor
                    </p>
                  </div>
                </>
              )}
            </>
          )}

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
              disabled={loading || (displayType === 'sensor_group' && sensorTypes.length === 0)}
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

