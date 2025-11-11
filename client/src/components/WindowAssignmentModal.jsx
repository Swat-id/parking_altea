import { useState, useEffect } from 'react'
import { X, Save, AlertCircle } from 'lucide-react'
import windowService from '../services/windowService'
import panelService from '../services/panelService'
import parkingService from '../services/parkingService'
import toast from 'react-hot-toast'

const WindowAssignmentModal = ({ isOpen, onClose, panelId, windowId, onSuccess }) => {
  const [parkings, setParkings] = useState([])
  const [selectedParkingId, setSelectedParkingId] = useState(null)
  const [sensorTypes, setSensorTypes] = useState([])
  const [selectedSensorType, setSelectedSensorType] = useState(null)
  const [displayType, setDisplayType] = useState('parking') // 'parking' o 'sensor_group'
  const [loading, setLoading] = useState(false)
  const [loadingParkings, setLoadingParkings] = useState(false)
  const [loadingSensorTypes, setLoadingSensorTypes] = useState(false)

  useEffect(() => {
    if (isOpen && panelId) {
      loadParkings()
    }
  }, [isOpen, panelId])

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

    try {
      setLoading(true)
      const result = await windowService.assignParkingToWindow(
        panelId,
        windowId,
        selectedParkingId,
        displayType === 'sensor_group' ? selectedSensorType : null
      )

      if (result.success) {
        toast.success('Asignación creada exitosamente')
        onSuccess?.()
        onClose()
        // Reset form
        setSelectedParkingId(null)
        setSelectedSensorType(null)
        setDisplayType('parking')
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
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
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
          {/* Tipo de asignación */}
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
                <span>Ocupación general del parking</span>
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
          </div>

          {/* Selección de parking */}
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

          {/* Selección de tipo de sensor (solo si displayType === 'sensor_group') */}
          {displayType === 'sensor_group' && (
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

