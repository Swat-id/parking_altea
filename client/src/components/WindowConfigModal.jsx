import { useState, useEffect, useRef } from 'react'
import { X, Save, Plus, Trash2, AlertCircle } from 'lucide-react'
import windowService from '../services/windowService'
import { authService } from '../services/authService'
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
  const { isSuperadmin, user } = useAuth()
  const [loading, setLoading] = useState(false)
  const [loadingConfig, setLoadingConfig] = useState(false)
  const [rotationEnabled, setRotationEnabled] = useState(true)
  const [refreshTimeSeconds, setRefreshTimeSeconds] = useState(5)
  const [rotationOrder, setRotationOrder] = useState([
    { type: 'parking', percentage: 100, sensor_type: null, texto_fijo_previo: null, color: null }
  ])
  const [parkingStatusConfig, setParkingStatusConfig] = useState({
    LLIURE: { color: 2, text: 'LLIURE' },
    DENS: { color: 3, text: 'DENS' },
    COMPLET: { color: 1, text: 'COMPLET' }
  })
  const [availableSensorTypes, setAvailableSensorTypes] = useState([])
  const [companyId, setCompanyId] = useState(null)
  const [companies, setCompanies] = useState([])
  const isInitialLoad = useRef(true)
  
  // Obtener company_id por defecto del usuario actual (si no es superadmin o no se especifica)
  const getDefaultCompanyId = () => {
    if (isSuperadmin && companyId) {
      return companyId
    }
    // Para usuarios regulares, usar su propio ID como company_id
    return user?.id || null
  }

  useEffect(() => {
    if (isOpen && parkingId !== null && parkingId !== undefined && windowId !== undefined) {
      // Resetear estado cuando se abre el modal
      isInitialLoad.current = true
      setRotationEnabled(true)
      setRefreshTimeSeconds(30)
      setRotationOrder([
        { type: 'parking', percentage: 100, sensor_type: null, texto_fijo_previo: null, color: null }
      ])
      setParkingStatusConfig({
        LLIURE: { color: 2, text: 'LLIURE' },
        DENS: { color: 3, text: 'DENS' },
        COMPLET: { color: 1, text: 'COMPLET' }
      })
      if (!isSuperadmin) {
        setCompanyId(null) // Solo resetear si no es superadmin
      }
      
      // Cargar configuración (puede ser preparatoria si no hay panelId)
      loadConfig()
      loadSensorTypes()
      if (isSuperadmin) {
        loadCompanies()
      }
      
      // Marcar que la carga inicial ha terminado después de un breve delay
      setTimeout(() => {
        isInitialLoad.current = false
      }, 500)
    }
  }, [isOpen, parkingId, panelId, windowId, isSuperadmin])

  // Recargar configuración cuando cambie la empresa seleccionada (solo superadmin)
  useEffect(() => {
    if (isOpen && isSuperadmin && !isInitialLoad.current && companyId !== null && companyId !== undefined && parkingId !== null && parkingId !== undefined && windowId !== undefined) {
      // Solo recargar si el modal ya estaba abierto y no es la carga inicial
      loadConfig()
    }
  }, [companyId])

  const loadConfig = async () => {
    try {
      setLoadingConfig(true)
      // Usar panelId o 0 si no hay panelId (para configuraciones preparatorias)
      const effectivePanelId = panelId || 0
      const effectiveCompanyId = isSuperadmin && companyId ? companyId : null
      
      const config = await windowService.getWindowConfig(
        parkingId,
        effectivePanelId,
        windowId,
        effectiveCompanyId
      )

      if (config) {
        // Configuración encontrada, cargar datos
        setRotationEnabled(config.rotation_enabled ?? true)
        setRefreshTimeSeconds(config.refresh_time_seconds ?? 30)
        setRotationOrder(config.rotation_order || [
          { type: 'parking', percentage: 100, sensor_type: null, texto_fijo_previo: null, color: null }
        ])
        if (config.parking_status_config) {
          setParkingStatusConfig(config.parking_status_config)
        }
        if (isSuperadmin && config.company_id) {
          setCompanyId(config.company_id)
        }
      } else {
        // No hay configuración, usar valores por defecto (ya están establecidos en el useEffect)
        console.log('No se encontró configuración, usando valores por defecto')
      }
    } catch (error) {
      console.error('Error cargando configuración:', error)
      // En caso de error, mantener valores por defecto
      toast.error('Error al cargar la configuración. Se usarán valores por defecto.')
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
    try {
      const response = await authService.getAllUsers()
      // Convertir usuarios a formato de empresas (cada usuario es una empresa)
      const companiesList = (response.users || []).map(user => ({
        id: user.id,
        name: user.name || user.email
      }))
      setCompanies(companiesList)
    } catch (error) {
      console.error('Error cargando empresas:', error)
      toast.error('Error al cargar la lista de empresas')
      setCompanies([])
    }
  }

  const addRotationItem = () => {
    setRotationOrder([
      ...rotationOrder,
      { type: 'parking', percentage: 0, sensor_type: null, texto_fijo_previo: null, color: null }
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
    // Si se cambia el tipo a sensor_group, agregar campo texto_fijo_previo si no existe
    if (field === 'type' && value === 'sensor_group') {
      const updated = [...rotationOrder]
      updated[index] = {
        ...updated[index],
        [field]: value,
        texto_fijo_previo: updated[index].texto_fijo_previo || '',
        color: updated[index].color || 2  // Verde por defecto
      }
      setRotationOrder(updated)
      return
    }
    const newOrder = [...rotationOrder]
    newOrder[index] = { ...newOrder[index], [field]: value }
    
    // Si cambia el tipo a parking, limpiar campos de sensor
    if (field === 'type' && value === 'parking') {
      newOrder[index].sensor_type = null
      newOrder[index].texto_fijo_previo = null
      newOrder[index].color = null
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
        refresh_time_seconds: refreshTimeSeconds,
        parking_status_config: parkingStatusConfig
      }

      if (isSuperadmin && companyId) {
        config.company_id = companyId
      }

      // Si no hay panelId, usar 0 para crear configuración preparatoria
      // La configuración se asociará automáticamente cuando se cree el panel Tipo 4
      const effectivePanelId = panelId || 0
      
      // Asegurar que company_id esté en la configuración
      if (!config.company_id) {
        config.company_id = getDefaultCompanyId()
      }
      
      const result = await windowService.updateWindowConfig(
        parkingId,
        effectivePanelId,
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
          <div>
            <h2 className="text-xl font-bold text-gray-900">
              Configurar Ventana {windowId}
            </h2>
            {!panelId && (
              <p className="text-sm text-blue-600 mt-1">
                ⓘ Configuración preparatoria: Esta configuración se aplicará cuando se cree un panel Tipo 4 en este parking.
              </p>
            )}
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        {/* Form */}
        {loadingConfig ? (
          <div className="p-6 flex items-center justify-center">
            <div className="text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
              <p className="text-sm text-gray-600">Cargando configuración...</p>
            </div>
          </div>
        ) : (
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Selector de empresa (solo superadmin) */}
          {isSuperadmin && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Empresa <span className="text-gray-500 font-normal">(opcional - para aplicar a todos los parkings de la empresa)</span>
              </label>
              <select
                value={companyId || ''}
                onChange={(e) => {
                  const newCompanyId = e.target.value ? parseInt(e.target.value) : null
                  setCompanyId(newCompanyId)
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={loadingConfig}
              >
                <option value="">Aplicar solo a este parking</option>
                {companies.length > 0 ? (
                  companies.map((company) => (
                    <option key={company.id} value={company.id}>
                      {company.name}
                    </option>
                  ))
                ) : (
                  <option value="" disabled>Cargando empresas...</option>
                )}
              </select>
              <p className="mt-1 text-xs text-gray-500">
                Si seleccionas una empresa, la configuración se aplicará a todos los parkings de esa empresa.
                Si no seleccionas ninguna, la configuración será solo para este parking específico.
              </p>
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
              min="30"
              step="30"
              value={refreshTimeSeconds}
              onChange={(e) => {
                const value = parseInt(e.target.value) || 30
                // Asegurar que sea múltiplo de 30
                const rounded = Math.max(30, Math.round(value / 30) * 30)
                setRefreshTimeSeconds(rounded)
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
            <p className="mt-1 text-sm text-gray-500">
              Tiempo total del ciclo de rotación en segundos (debe ser múltiplo de 30)
            </p>
            <p className="mt-1 text-xs text-gray-400">
              El contenido se rotará en bloques de 30 segundos. Ejemplo: 120 segundos = 4 bloques de 30s
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

                    <div className={`grid grid-cols-1 gap-4 ${item.type === 'sensor_group' ? 'md:grid-cols-4' : 'md:grid-cols-2'}`}>
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
                        <>
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
                          <div>
                            <label className="block text-xs font-medium text-gray-600 mb-1">
                              Texto fijo previo
                            </label>
                            <input
                              type="text"
                              value={item.texto_fijo_previo || ''}
                              onChange={(e) => updateRotationItem(index, 'texto_fijo_previo', e.target.value)}
                              placeholder="Ej: PMR, ELÉCTRICO..."
                              maxLength={50}
                              className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                            <p className="mt-1 text-xs text-gray-500">
                              Texto antes del número
                            </p>
                          </div>
                          <div>
                            <label className="block text-xs font-medium text-gray-600 mb-1">
                              Color
                            </label>
                            <select
                              value={item.color || 2}
                              onChange={(e) => updateRotationItem(index, 'color', parseInt(e.target.value))}
                              className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
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

          {/* Configuración de colores y textos para estados de parking */}
          <div className="border-t pt-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Configuración de Estados de Parking
            </h3>
            <p className="text-sm text-gray-600 mb-4">
              Define los colores y textos para cada estado del parking (LLIURE, DENS, COMPLET)
            </p>
            
            <div className="space-y-4">
              {['LLIURE', 'DENS', 'COMPLET'].map((status) => (
                <div key={status} className="border rounded-md p-4 bg-gray-50">
                  <h4 className="font-medium text-gray-900 mb-3">{status}</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-medium text-gray-600 mb-1">
                        Color
                      </label>
                      <select
                        value={parkingStatusConfig[status]?.color || (status === 'LLIURE' ? 2 : status === 'DENS' ? 3 : 1)}
                        onChange={(e) => {
                          setParkingStatusConfig({
                            ...parkingStatusConfig,
                            [status]: {
                              ...parkingStatusConfig[status],
                              color: parseInt(e.target.value)
                            }
                          })
                        }}
                        className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
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
                    <div>
                      <label className="block text-xs font-medium text-gray-600 mb-1">
                        Texto a mostrar
                      </label>
                      <input
                        type="text"
                        value={parkingStatusConfig[status]?.text || status}
                        onChange={(e) => {
                          setParkingStatusConfig({
                            ...parkingStatusConfig,
                            [status]: {
                              ...parkingStatusConfig[status],
                              text: e.target.value
                            }
                          })
                        }}
                        placeholder={status}
                        maxLength={50}
                        className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                  </div>
                </div>
              ))}
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
        )}
      </div>
    </div>
  )
}

export default WindowConfigModal

