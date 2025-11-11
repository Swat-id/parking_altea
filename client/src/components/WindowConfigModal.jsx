import { useState, useEffect } from 'react'
import { X, Save, Plus, Trash2, AlertCircle } from 'lucide-react'
import windowService from '../services/windowService'
import toast from 'react-hot-toast'
import { useAuth } from '../context/AuthContext'

const WindowConfigModal = ({ 
  isOpen, 
  onClose, 
  parkingId, 
  panelId, 
  windowId, 
  onSuccess 
}) => {
  const { isSuperadmin } = useAuth()
  const [loading, setLoading] = useState(false)
  const [loadingConfig, setLoadingConfig] = useState(false)
  const [rotationEnabled, setRotationEnabled] = useState(true)
  const [refreshTimeSeconds, setRefreshTimeSeconds] = useState(5)
  const [rotationOrder, setRotationOrder] = useState([
    { type: 'parking', percentage: 100, sensor_type: null }
  ])
  const [availableSensorTypes, setAvailableSensorTypes] = useState([])
  const [companyId, setCompanyId] = useState(null)
  const [companies, setCompanies] = useState([])

  useEffect(() => {
    if (isOpen && parkingId && panelId && windowId) {
      loadConfig()
      loadSensorTypes()
      if (isSuperadmin) {
        loadCompanies()
      }
    }
  }, [isOpen, parkingId, panelId, windowId, isSuperadmin])

  const loadConfig = async () => {
    try {
      setLoadingConfig(true)
      const config = await windowService.getWindowConfig(
        parkingId,
        panelId,
        windowId,
        isSuperadmin ? companyId : null
      )

      if (config) {
        setRotationEnabled(config.rotation_enabled ?? true)
        setRefreshTimeSeconds(config.refresh_time_seconds ?? 5)
        setRotationOrder(config.rotation_order || [
          { type: 'parking', percentage: 100, sensor_type: null }
        ])
        if (isSuperadmin) {
          setCompanyId(config.company_id)
        }
      }
    } catch (error) {
      console.error('Error cargando configuración:', error)
    } finally {
      setLoadingConfig(false)
    }
  }

  const loadSensorTypes = async () => {
    try {
      const types = await windowService.getParkingSensorTypes(parkingId)
      setAvailableSensorTypes(types)
    } catch (error) {
      console.error('Error cargando tipos de sensores:', error)
    }
  }

  const loadCompanies = async () => {
    // TODO: Implementar carga de empresas si es necesario
    // Por ahora, dejamos vacío
    setCompanies([])
  }

  const addRotationItem = () => {
    setRotationOrder([
      ...rotationOrder,
      { type: 'parking', percentage: 0, sensor_type: null }
    ])
  }

  const removeRotationItem = (index) => {
    if (rotationOrder.length > 1) {
      const newOrder = rotationOrder.filter((_, i) => i !== index)
      // Recalcular porcentajes para que sumen 100
      const totalPercentage = newOrder.reduce((sum, item) => sum + (item.percentage || 0), 0)
      if (totalPercentage > 0) {
        newOrder.forEach(item => {
          item.percentage = Math.round((item.percentage / totalPercentage) * 100)
        })
      }
      setRotationOrder(newOrder)
    }
  }

  const updateRotationItem = (index, field, value) => {
    const newOrder = [...rotationOrder]
    newOrder[index] = { ...newOrder[index], [field]: value }
    
    // Si cambia el tipo a sensor_group y no hay sensor_type, limpiar
    if (field === 'type' && value === 'parking') {
      newOrder[index].sensor_type = null
    }
    
    setRotationOrder(newOrder)
  }

  const updatePercentage = (index, value) => {
    const numValue = parseInt(value) || 0
    if (numValue < 0 || numValue > 100) return

    const newOrder = [...rotationOrder]
    newOrder[index].percentage = numValue
    
    // Ajustar otros porcentajes para que sumen 100
    const totalPercentage = newOrder.reduce((sum, item) => sum + (item.percentage || 0), 0)
    if (totalPercentage !== 100 && newOrder.length > 1) {
      const diff = 100 - totalPercentage
      // Distribuir la diferencia en el primer elemento que no sea el modificado
      for (let i = 0; i < newOrder.length; i++) {
        if (i !== index && newOrder[i].percentage + diff >= 0) {
          newOrder[i].percentage += diff
          break
        }
      }
    }
    
    setRotationOrder(newOrder)
  }

  const calculateTotalPercentage = () => {
    return rotationOrder.reduce((sum, item) => sum + (item.percentage || 0), 0)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()

    const totalPercentage = calculateTotalPercentage()
    if (Math.abs(totalPercentage - 100) > 0.01) {
      toast.error(`Los porcentajes deben sumar 100%. Actual: ${totalPercentage}%`)
      return
    }

    if (refreshTimeSeconds <= 0) {
      toast.error('El tiempo de refresco debe ser mayor que 0')
      return
    }

    try {
      setLoading(true)
      const config = {
        rotation_enabled: rotationEnabled,
        rotation_order: rotationOrder,
        refresh_time_seconds: refreshTimeSeconds
      }

      if (isSuperadmin && companyId) {
        config.company_id = companyId
      }

      const result = await windowService.updateWindowConfig(
        parkingId,
        panelId,
        windowId,
        config
      )

      if (result.success) {
        toast.success('Configuración guardada exitosamente')
        onSuccess?.()
        onClose()
      } else {
        toast.error(result.error || 'Error al guardar la configuración')
      }
    } catch (error) {
      console.error('Error guardando configuración:', error)
      toast.error(error?.response?.data?.error || 'Error al guardar la configuración')
    } finally {
      setLoading(false)
    }
  }

  if (!isOpen) return null

  const totalPercentage = calculateTotalPercentage()
  const percentageError = Math.abs(totalPercentage - 100) > 0.01

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
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
          {/* Selector de empresa (solo superadmin) */}
          {isSuperadmin && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Empresa (opcional - para aplicar a todos los parkings de la empresa)
              </label>
              <select
                value={companyId || ''}
                onChange={(e) => setCompanyId(e.target.value ? parseInt(e.target.value) : null)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Aplicar solo a este parking</option>
                {companies.map((company) => (
                  <option key={company.id} value={company.id}>
                    {company.name}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Rotación habilitada */}
          <div>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={rotationEnabled}
                onChange={(e) => setRotationEnabled(e.target.checked)}
                className="mr-2"
              />
              <span className="text-sm font-medium text-gray-700">
                Habilitar rotación de contenido
              </span>
            </label>
          </div>

          {/* Tiempo de refresco */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Tiempo de refresco (segundos) <span className="text-red-500">*</span>
            </label>
            <input
              type="number"
              min="1"
              value={refreshTimeSeconds}
              onChange={(e) => setRefreshTimeSeconds(parseInt(e.target.value) || 1)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
            <p className="mt-1 text-sm text-gray-500">
              Tiempo total del ciclo de rotación en segundos
            </p>
          </div>

          {/* Orden de rotación */}
          {rotationEnabled && (
            <div>
              <div className="flex justify-between items-center mb-3">
                <label className="block text-sm font-medium text-gray-700">
                  Orden de Rotación
                </label>
                <button
                  type="button"
                  onClick={addRotationItem}
                  className="text-sm text-blue-600 hover:text-blue-700 flex items-center"
                >
                  <Plus className="h-4 w-4 mr-1" />
                  Agregar elemento
                </button>
              </div>

              {percentageError && (
                <div className="mb-3 p-3 bg-red-50 border border-red-200 rounded-md flex items-start">
                  <AlertCircle className="h-5 w-5 text-red-600 mr-2 mt-0.5" />
                  <span className="text-sm text-red-700">
                    Los porcentajes deben sumar 100%. Actual: {totalPercentage}%
                  </span>
                </div>
              )}

              <div className="space-y-3">
                {rotationOrder.map((item, index) => (
                  <div key={index} className="border border-gray-200 rounded-md p-4">
                    <div className="flex justify-between items-start mb-3">
                      <span className="text-sm font-medium text-gray-700">
                        Elemento {index + 1}
                      </span>
                      {rotationOrder.length > 1 && (
                        <button
                          type="button"
                          onClick={() => removeRotationItem(index)}
                          className="text-red-600 hover:text-red-700"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      )}
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      {/* Tipo */}
                      <div>
                        <label className="block text-xs font-medium text-gray-600 mb-1">
                          Tipo
                        </label>
                        <select
                          value={item.type}
                          onChange={(e) => updateRotationItem(index, 'type', e.target.value)}
                          className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                          <option value="parking">Parking (ocupación general)</option>
                          <option value="sensor_group">Grupo de sensores</option>
                        </select>
                      </div>

                      {/* Tipo de sensor (solo si type === 'sensor_group') */}
                      {item.type === 'sensor_group' && (
                        <div>
                          <label className="block text-xs font-medium text-gray-600 mb-1">
                            Tipo de Sensor
                          </label>
                          <select
                            value={item.sensor_type || ''}
                            onChange={(e) => updateRotationItem(index, 'sensor_type', e.target.value)}
                            className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            required
                          >
                            <option value="">Seleccionar...</option>
                            {availableSensorTypes.map((type) => (
                              <option key={type} value={type}>
                                {type}
                              </option>
                            ))}
                          </select>
                        </div>
                      )}

                      {/* Porcentaje */}
                      <div>
                        <label className="block text-xs font-medium text-gray-600 mb-1">
                          Porcentaje (%)
                        </label>
                        <input
                          type="number"
                          min="0"
                          max="100"
                          value={item.percentage}
                          onChange={(e) => updatePercentage(index, e.target.value)}
                          className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                          required
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              <div className="mt-3 p-3 bg-gray-50 rounded-md">
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium text-gray-700">Total:</span>
                  <span className={`text-sm font-bold ${percentageError ? 'text-red-600' : 'text-green-600'}`}>
                    {totalPercentage}%
                  </span>
                </div>
              </div>
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
              disabled={loading || percentageError}
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

export default WindowConfigModal

