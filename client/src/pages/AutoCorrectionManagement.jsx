import React, { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import { 
  Settings, 
  RefreshCw, 
  CheckCircle, 
  XCircle, 
  Clock, 
  TrendingUp, 
  TrendingDown,
  AlertTriangle,
  BarChart3,
  PlayCircle,
  PauseCircle,
  Calendar,
  ChevronDown,
  ChevronUp,
  Zap,
  Database,
  Info,
  ArrowRight,
  Target,
  Activity,
  FileText
} from 'lucide-react'
import api from '../services/api'
import { useAuth } from '../context/AuthContext'

const WEEKDAY_NAMES = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
const WEEKDAY_NAMES_SHORT = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']

export default function AutoCorrectionManagement() {
  const { user } = useAuth()
  const queryClient = useQueryClient()
  
  const [selectedParking, setSelectedParking] = useState(null)
  const [expandedParking, setExpandedParking] = useState(null)
  const [bulkSelection, setBulkSelection] = useState([])
  const [bulkAction, setBulkAction] = useState({ enabled: true, hour: 6, minute: 0 })
  const [showBulkModal, setShowBulkModal] = useState(false)
  const [showHistoryModal, setShowHistoryModal] = useState(false)
  const [showStatsModal, setShowStatsModal] = useState(false)
  const [statsParking, setStatsParking] = useState(null)
  const [bootstrapDays, setBootstrapDays] = useState(365)
  const [showBootstrapModal, setShowBootstrapModal] = useState(false)
  
  // Verificar si es superadmin
  if (user?.role !== 'superadmin') {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <XCircle className="h-16 w-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-800 mb-2">Acceso Denegado</h2>
          <p className="text-gray-600">Esta página solo está disponible para superadministradores.</p>
        </div>
      </div>
    )
  }
  
  // Query para obtener configuraciones
  const { data: configsData, isLoading, error, refetch } = useQuery({
    queryKey: ['correction-configs'],
    queryFn: async () => {
      const response = await api.get('/api/auto-correction/configs')
      return response.data
    }
  })
  
  // Query para historial
  const { data: historyData, isLoading: historyLoading } = useQuery({
    queryKey: ['auto-corrections-history'],
    queryFn: async () => {
      const response = await api.get('/api/auto-corrections/history?days=30')
      return response.data
    },
    enabled: showHistoryModal
  })
  
  // Query para estadísticas detalladas de un parking (sugerencia de corrección)
  const { data: statsData, isLoading: statsLoading } = useQuery({
    queryKey: ['parking-correction-stats', statsParking],
    queryFn: async () => {
      const response = await api.get(`/api/auto-correction/${statsParking}/suggest`)
      return response.data
    },
    enabled: showStatsModal && statsParking !== null
  })
  
  // Función para abrir modal de estadísticas
  const openStatsModal = (parkingId) => {
    setStatsParking(parkingId)
    setShowStatsModal(true)
  }
  
  // Mutación para actualizar configuración individual
  const updateConfigMutation = useMutation({
    mutationFn: async ({ parkingId, config }) => {
      const response = await api.put(`/api/parkings/${parkingId}/correction-config`, config)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['correction-configs'] })
    },
    onError: (error) => {
      console.error('Error actualizando configuración:', error)
    }
  })
  
  // Mutación para actualización masiva
  const bulkUpdateMutation = useMutation({
    mutationFn: async (data) => {
      const response = await api.put('/api/correction-configs/bulk-update', data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['correction-configs'] })
      setShowBulkModal(false)
      setBulkSelection([])
    }
  })
  
  // Mutación para aplicar corrección manualmente
  const applyCorrectionMutation = useMutation({
    mutationFn: async (parkingId) => {
      const response = await api.post(`/api/auto-correction/${parkingId}/apply`, { force: true })
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['correction-configs'] })
      queryClient.invalidateQueries({ queryKey: ['auto-corrections-history'] })
    }
  })
  
  // Mutación para ejecutar bootstrap
  const bootstrapMutation = useMutation({
    mutationFn: async ({ parkingId, days }) => {
      const response = await api.post('/api/run-bootstrap', { parking_id: parkingId, days })
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['correction-configs'] })
      setShowBootstrapModal(false)
    }
  })
  
  const toggleEnabled = (parkingId, currentEnabled) => {
    updateConfigMutation.mutate({
      parkingId,
      config: { auto_correction_enabled: !currentEnabled }
    })
  }
  
  const updateCorrectionTime = (parkingId, hour, minute) => {
    updateConfigMutation.mutate({
      parkingId,
      config: { correction_hour: hour, correction_minute: minute }
    })
  }
  
  const toggleBulkSelection = (parkingId) => {
    setBulkSelection(prev => 
      prev.includes(parkingId)
        ? prev.filter(id => id !== parkingId)
        : [...prev, parkingId]
    )
  }
  
  const selectAllParkings = () => {
    if (bulkSelection.length === configsData?.configs?.length) {
      setBulkSelection([])
    } else {
      setBulkSelection(configsData?.configs?.map(c => c.parking_id) || [])
    }
  }
  
  const handleBulkUpdate = () => {
    bulkUpdateMutation.mutate({
      parking_ids: bulkSelection,
      auto_correction_enabled: bulkAction.enabled,
      correction_hour: bulkAction.hour,
      correction_minute: bulkAction.minute
    })
  }
  
  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.7) return 'text-green-600 bg-green-100'
    if (confidence >= 0.4) return 'text-yellow-600 bg-yellow-100'
    return 'text-red-600 bg-red-100'
  }
  
  const getDriftIndicator = (drift) => {
    if (drift > 0.5) return { icon: TrendingUp, color: 'text-red-500', label: 'Alta deriva' }
    if (drift < -0.5) return { icon: TrendingDown, color: 'text-blue-500', label: 'Deriva negativa' }
    return { icon: TrendingUp, color: 'text-gray-400', label: 'Estable' }
  }
  
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <RefreshCw className="h-8 w-8 text-blue-500 animate-spin" />
      </div>
    )
  }
  
  if (error) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <AlertTriangle className="h-16 w-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-800 mb-2">Error</h2>
          <p className="text-gray-600">{error.message}</p>
        </div>
      </div>
    )
  }
  
  const configs = configsData?.configs || []
  const enabledCount = configs.filter(c => c.auto_correction_enabled === true).length
  const highConfidenceCount = configs.filter(c => (c.confidence_level || 0) >= 0.7).length
  
  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <div className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white py-8 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold flex items-center gap-3">
                <Zap className="h-8 w-8" />
                Gestión de Corrección Automática
              </h1>
              <p className="mt-2 text-indigo-200">
                Configura las correcciones automáticas de ocupación basadas en patrones históricos
              </p>
            </div>
            <div className="flex gap-3">
              <button
                onClick={() => {
                  if (window.confirm('¿Activar corrección automática para TODOS los parkings?')) {
                    bulkUpdateMutation.mutate({
                      parking_ids: configs.map(c => c.parking_id),
                      auto_correction_enabled: true
                    })
                  }
                }}
                className="flex items-center gap-2 px-4 py-2 bg-green-500 hover:bg-green-600 rounded-lg transition"
                title="Activar para todos"
              >
                <PlayCircle className="h-5 w-5" />
                Activar Todos
              </button>
              <button
                onClick={() => {
                  if (window.confirm('¿Desactivar corrección automática para TODOS los parkings?')) {
                    bulkUpdateMutation.mutate({
                      parking_ids: configs.map(c => c.parking_id),
                      auto_correction_enabled: false
                    })
                  }
                }}
                className="flex items-center gap-2 px-4 py-2 bg-red-500 hover:bg-red-600 rounded-lg transition"
                title="Desactivar para todos"
              >
                <PauseCircle className="h-5 w-5" />
                Desactivar Todos
              </button>
              <button
                onClick={() => setShowBootstrapModal(true)}
                className="flex items-center gap-2 px-4 py-2 bg-white/20 hover:bg-white/30 rounded-lg transition"
              >
                <Database className="h-5 w-5" />
                Bootstrap
              </button>
              <button
                onClick={() => setShowHistoryModal(true)}
                className="flex items-center gap-2 px-4 py-2 bg-white/20 hover:bg-white/30 rounded-lg transition"
              >
                <BarChart3 className="h-5 w-5" />
                Historial
              </button>
              <button
                onClick={() => refetch()}
                className="flex items-center gap-2 px-4 py-2 bg-white/20 hover:bg-white/30 rounded-lg transition"
              >
                <RefreshCw className="h-5 w-5" />
                Actualizar
              </button>
            </div>
          </div>
          
          {/* Estadísticas rápidas */}
          <div className="mt-6 grid grid-cols-4 gap-4">
            <div className="bg-white/10 rounded-lg p-4">
              <div className="text-3xl font-bold">{configs.length}</div>
              <div className="text-indigo-200">Total Parkings</div>
            </div>
            <div className="bg-white/10 rounded-lg p-4">
              <div className="text-3xl font-bold">{enabledCount}</div>
              <div className="text-indigo-200">Corrección Activa</div>
            </div>
            <div className="bg-white/10 rounded-lg p-4">
              <div className="text-3xl font-bold">{highConfidenceCount}</div>
              <div className="text-indigo-200">Alta Confianza (≥70%)</div>
            </div>
            <div className="bg-white/10 rounded-lg p-4">
              <div className="text-3xl font-bold">06:00</div>
              <div className="text-indigo-200">Hora por Defecto</div>
            </div>
          </div>
        </div>
      </div>
      
      {/* Contenido principal */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Acciones masivas */}
        {bulkSelection.length > 0 && (
          <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-4 mb-6 flex items-center justify-between">
            <span className="text-indigo-700 font-medium">
              {bulkSelection.length} parking(s) seleccionado(s)
            </span>
            <div className="flex gap-3">
              <button
                onClick={() => setShowBulkModal(true)}
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition"
              >
                Configurar seleccionados
              </button>
              <button
                onClick={() => setBulkSelection([])}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition"
              >
                Limpiar selección
              </button>
            </div>
          </div>
        )}
        
        {/* Lista de parkings */}
        <div className="bg-white rounded-xl shadow-lg overflow-hidden">
          <div className="p-4 border-b bg-gray-50 flex items-center justify-between">
            <div className="flex items-center gap-4">
              <input
                type="checkbox"
                checked={bulkSelection.length === configs.length && configs.length > 0}
                onChange={selectAllParkings}
                className="h-4 w-4 text-indigo-600 rounded"
              />
              <span className="font-medium text-gray-700">Seleccionar todos</span>
            </div>
            <div className="text-sm text-gray-500">
              {configs.length} parkings configurados
            </div>
          </div>
          
          <div className="divide-y">
            {configs.map((config) => {
              const drift = getDriftIndicator(config.avg_hourly_drift)
              const DriftIcon = drift.icon
              const isExpanded = expandedParking === config.parking_id
              
              return (
                <div key={config.parking_id} className="hover:bg-gray-50">
                  {/* Fila principal */}
                  <div className="p-4 flex items-center gap-4">
                    <input
                      type="checkbox"
                      checked={bulkSelection.includes(config.parking_id)}
                      onChange={() => toggleBulkSelection(config.parking_id)}
                      className="h-4 w-4 text-indigo-600 rounded"
                    />
                    
                    {/* Estado habilitado/deshabilitado */}
                    <button
                      onClick={() => toggleEnabled(config.parking_id, config.auto_correction_enabled)}
                      className={`p-2 rounded-full transition ${
                        config.auto_correction_enabled
                          ? 'bg-green-100 text-green-600 hover:bg-green-200'
                          : 'bg-gray-100 text-gray-400 hover:bg-gray-200'
                      }`}
                      title={config.auto_correction_enabled ? 'Desactivar' : 'Activar'}
                    >
                      {config.auto_correction_enabled ? (
                        <PlayCircle className="h-5 w-5" />
                      ) : (
                        <PauseCircle className="h-5 w-5" />
                      )}
                    </button>
                    
                    {/* Info del parking */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <h3 className="font-medium text-gray-900 truncate">{config.parking_name}</h3>
                        {config.no_config && (
                          <span className="text-xs px-2 py-0.5 bg-orange-100 text-orange-600 rounded">
                            Sin datos
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-4 text-sm text-gray-500 mt-1">
                        <span className="flex items-center gap-1">
                          <Clock className="h-4 w-4" />
                          {String(config.correction_hour).padStart(2, '0')}:{String(config.correction_minute).padStart(2, '0')}
                        </span>
                        <span className="flex items-center gap-1">
                          Ocupación: {config.current_occupancy}/{config.max_capacity}
                        </span>
                        <span className={`px-2 py-0.5 rounded text-xs ${
                          config.status === 'LIBRE' ? 'bg-green-100 text-green-700' :
                          config.status === 'DENSO' ? 'bg-yellow-100 text-yellow-700' :
                          'bg-red-100 text-red-700'
                        }`}>
                          {config.status}
                        </span>
                      </div>
                    </div>
                    
                    {/* Métricas */}
                    <div className="flex items-center gap-6">
                      {/* Confianza */}
                      <div className="text-center">
                        <div className={`inline-flex items-center px-2 py-1 rounded ${getConfidenceColor(config.confidence_level)}`}>
                          {Math.round((config.confidence_level || 0) * 100)}%
                        </div>
                        <div className="text-xs text-gray-500 mt-1">Confianza</div>
                      </div>
                      
                      {/* Drift diario */}
                      <div className="text-center">
                        <div className={`flex items-center gap-1 ${drift.color}`}>
                          <DriftIcon className="h-4 w-4" />
                          <span className="font-medium">{(config.avg_daily_drift || 0).toFixed(1)}</span>
                        </div>
                        <div className="text-xs text-gray-500 mt-1">Drift/día</div>
                      </div>
                      
                      {/* Corrección sugerida */}
                      <div className="text-center">
                        <div className={`font-medium ${
                          config.suggested_correction > 0 ? 'text-red-600' :
                          config.suggested_correction < 0 ? 'text-blue-600' :
                          'text-gray-600'
                        }`}>
                          {config.suggested_correction > 0 ? '+' : ''}{config.suggested_correction || 0}
                        </div>
                        <div className="text-xs text-gray-500 mt-1">Sugerencia</div>
                      </div>
                      
                      {/* Muestras */}
                      <div className="text-center">
                        <div className="font-medium text-gray-700">{config.sample_count || 0}</div>
                        <div className="text-xs text-gray-500 mt-1">Muestras</div>
                      </div>
                    </div>
                    
                    {/* Acciones */}
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => openStatsModal(config.parking_id)}
                        className="p-2 text-green-600 hover:bg-green-100 rounded-lg transition"
                        title="Ver estadísticas detalladas"
                      >
                        <BarChart3 className="h-5 w-5" />
                      </button>
                      
                      <button
                        onClick={() => applyCorrectionMutation.mutate(config.parking_id)}
                        disabled={applyCorrectionMutation.isPending || !config.auto_correction_enabled}
                        className="p-2 text-indigo-600 hover:bg-indigo-100 rounded-lg transition disabled:opacity-50"
                        title="Aplicar corrección ahora"
                      >
                        <Zap className="h-5 w-5" />
                      </button>
                      
                      <button
                        onClick={() => setExpandedParking(isExpanded ? null : config.parking_id)}
                        className="p-2 text-gray-400 hover:bg-gray-100 rounded-lg transition"
                      >
                        {isExpanded ? (
                          <ChevronUp className="h-5 w-5" />
                        ) : (
                          <ChevronDown className="h-5 w-5" />
                        )}
                      </button>
                    </div>
                  </div>
                  
                  {/* Panel expandido */}
                  {isExpanded && (
                    <div className="px-4 pb-4 pt-2 bg-gray-50 border-t">
                      <div className="grid grid-cols-3 gap-6">
                        {/* Configuración de hora */}
                        <div className="bg-white rounded-lg p-4 shadow-sm">
                          <h4 className="font-medium text-gray-700 mb-3 flex items-center gap-2">
                            <Clock className="h-4 w-4" />
                            Hora de Corrección
                          </h4>
                          <div className="flex items-center gap-2">
                            <select
                              value={config.correction_hour}
                              onChange={(e) => updateCorrectionTime(config.parking_id, parseInt(e.target.value), config.correction_minute)}
                              className="px-3 py-2 border rounded-lg"
                            >
                              {Array.from({ length: 24 }, (_, i) => (
                                <option key={i} value={i}>{String(i).padStart(2, '0')}</option>
                              ))}
                            </select>
                            <span>:</span>
                            <select
                              value={config.correction_minute}
                              onChange={(e) => updateCorrectionTime(config.parking_id, config.correction_hour, parseInt(e.target.value))}
                              className="px-3 py-2 border rounded-lg"
                            >
                              {[0, 15, 30, 45].map(m => (
                                <option key={m} value={m}>{String(m).padStart(2, '0')}</option>
                              ))}
                            </select>
                          </div>
                          {config.last_auto_correction_at && (
                            <p className="text-sm text-gray-500 mt-2">
                              Última corrección: {new Date(config.last_auto_correction_at).toLocaleString()}
                              {config.last_auto_correction_amount && (
                                <span className={config.last_auto_correction_amount > 0 ? 'text-red-600' : 'text-blue-600'}>
                                  {' '}({config.last_auto_correction_amount > 0 ? '+' : ''}{config.last_auto_correction_amount})
                                </span>
                              )}
                            </p>
                          )}
                        </div>
                        
                        {/* Ratio y Transacciones por día */}
                        <div className="bg-white rounded-lg p-4 shadow-sm">
                          <h4 className="font-medium text-gray-700 mb-3 flex items-center gap-2">
                            <Calendar className="h-4 w-4" />
                            Métricas por Día de Semana
                          </h4>
                          <div className="grid grid-cols-7 gap-1 text-center text-xs">
                            {WEEKDAY_NAMES.map((name, idx) => {
                              const ratio = config.avg_correction_ratio_by_weekday?.[String(idx)] || 1.0
                              const trans = config.avg_transactions_by_weekday?.[String(idx)] || 0
                              const expectedOcc = config.expected_occupancy_by_weekday?.[String(idx)] || 0
                              return (
                                <div 
                                  key={idx}
                                  className={`py-2 px-1 rounded ${
                                    ratio < 0.7 ? 'bg-red-100 text-red-700' :
                                    ratio < 0.9 ? 'bg-yellow-100 text-yellow-700' :
                                    'bg-green-100 text-green-700'
                                  }`}
                                  title={`${name}: Ratio=${ratio.toFixed(2)}, Trans=${Math.round(trans)}, Occ.Esp=${Math.round(expectedOcc)}`}
                                >
                                  <div className="font-medium">{name.substring(0, 2)}</div>
                                  <div className="text-[10px]">{ratio.toFixed(2)}</div>
                                  <div className="text-[9px] text-gray-500">{Math.round(trans)}</div>
                                </div>
                              )
                            })}
                          </div>
                          <div className="mt-2 text-[10px] text-gray-500 flex justify-between">
                            <span>Ratio &lt;0.7: sobreestima mucho</span>
                            <span>Trans: transacciones promedio</span>
                          </div>
                        </div>
                        
                        {/* Información adicional - Algoritmo v4.5.1 */}
                        <div className="bg-white rounded-lg p-4 shadow-sm">
                          <h4 className="font-medium text-gray-700 mb-3 flex items-center gap-2">
                            <BarChart3 className="h-4 w-4" />
                            Métricas v4.5.1
                          </h4>
                          <div className="space-y-2 text-sm">
                            <div className="flex justify-between">
                              <span className="text-gray-500">Error/transacción:</span>
                              <span className="font-medium">{(config.avg_error_per_transaction || 0).toFixed(4)}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-500">Transacciones/día:</span>
                              <span className="font-medium">{Math.round(config.avg_transactions_per_day || 0)}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-500">Última corrección:</span>
                              <span className="font-medium">
                                {config.last_correction_at 
                                  ? new Date(config.last_correction_at).toLocaleDateString() 
                                  : 'Nunca'}
                              </span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-500">Último cálculo:</span>
                              <span className="font-medium">
                                {config.last_calculation_at 
                                  ? new Date(config.last_calculation_at).toLocaleDateString() 
                                  : 'Nunca'}
                              </span>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      </div>
      
      {/* Modal de configuración masiva */}
      {showBulkModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-md p-6">
            <h3 className="text-xl font-bold mb-4">Configuración Masiva</h3>
            <p className="text-gray-600 mb-4">
              Aplicar configuración a {bulkSelection.length} parking(s) seleccionado(s)
            </p>
            
            <div className="space-y-4">
              <label className="flex items-center gap-3">
                <input
                  type="checkbox"
                  checked={bulkAction.enabled}
                  onChange={(e) => setBulkAction({ ...bulkAction, enabled: e.target.checked })}
                  className="h-4 w-4 text-indigo-600 rounded"
                />
                <span>Corrección automática habilitada</span>
              </label>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Hora de corrección
                </label>
                <div className="flex items-center gap-2">
                  <select
                    value={bulkAction.hour}
                    onChange={(e) => setBulkAction({ ...bulkAction, hour: parseInt(e.target.value) })}
                    className="px-3 py-2 border rounded-lg"
                  >
                    {Array.from({ length: 24 }, (_, i) => (
                      <option key={i} value={i}>{String(i).padStart(2, '0')}</option>
                    ))}
                  </select>
                  <span>:</span>
                  <select
                    value={bulkAction.minute}
                    onChange={(e) => setBulkAction({ ...bulkAction, minute: parseInt(e.target.value) })}
                    className="px-3 py-2 border rounded-lg"
                  >
                    {[0, 15, 30, 45].map(m => (
                      <option key={m} value={m}>{String(m).padStart(2, '0')}</option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
            
            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => setShowBulkModal(false)}
                className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg"
              >
                Cancelar
              </button>
              <button
                onClick={handleBulkUpdate}
                disabled={bulkUpdateMutation.isPending}
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
              >
                {bulkUpdateMutation.isPending ? 'Aplicando...' : 'Aplicar'}
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* Modal de historial */}
      {showHistoryModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-4xl max-h-[80vh] overflow-hidden">
            <div className="p-6 border-b flex items-center justify-between">
              <h3 className="text-xl font-bold">Historial de Correcciones Automáticas</h3>
              <button
                onClick={() => setShowHistoryModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <XCircle className="h-6 w-6" />
              </button>
            </div>
            
            <div className="overflow-auto max-h-[60vh]">
              {historyLoading ? (
                <div className="p-6 text-center">
                  <RefreshCw className="h-8 w-8 text-blue-500 animate-spin mx-auto" />
                </div>
              ) : historyData?.history?.length === 0 ? (
                <div className="p-6 text-center text-gray-500">
                  No hay historial de correcciones automáticas
                </div>
              ) : (
                <table className="w-full">
                  <thead className="bg-gray-50 sticky top-0">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Fecha</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Parking</th>
                      <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Antes</th>
                      <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Después</th>
                      <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Corrección</th>
                      <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Confianza</th>
                      <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Validado</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {historyData?.history?.map((h) => (
                      <tr key={h.id} className="hover:bg-gray-50">
                        <td className="px-4 py-3 text-sm">
                          {new Date(h.applied_at).toLocaleString()}
                        </td>
                        <td className="px-4 py-3 text-sm font-medium">{h.parking_name}</td>
                        <td className="px-4 py-3 text-sm text-center">{h.occupancy_before}</td>
                        <td className="px-4 py-3 text-sm text-center">{h.occupancy_after}</td>
                        <td className={`px-4 py-3 text-sm text-center font-medium ${
                          h.correction_amount > 0 ? 'text-red-600' : 'text-blue-600'
                        }`}>
                          {h.correction_amount > 0 ? '+' : ''}{h.correction_amount}
                          {h.was_limited && (
                            <span className="ml-1 text-xs text-orange-500" title="Se aplicó límite">⚠️</span>
                          )}
                        </td>
                        <td className="px-4 py-3 text-sm text-center">
                          <span className={`px-2 py-0.5 rounded ${getConfidenceColor(h.confidence_at_time)}`}>
                            {Math.round((h.confidence_at_time || 0) * 100)}%
                          </span>
                        </td>
                        <td className="px-4 py-3 text-center">
                          {h.validated ? (
                            <span className="flex items-center justify-center gap-1 text-green-600">
                              <CheckCircle className="h-4 w-4" />
                              {h.prediction_error !== null && (
                                <span className="text-xs">
                                  ({h.prediction_error > 0 ? '+' : ''}{h.prediction_error})
                                </span>
                              )}
                            </span>
                          ) : (
                            <span className="text-gray-400">Pendiente</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        </div>
      )}
      
      {/* Modal de Bootstrap */}
      {showBootstrapModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-md p-6">
            <h3 className="text-xl font-bold mb-2 flex items-center gap-2">
              <Database className="h-6 w-6 text-indigo-600" />
              Ejecutar Bootstrap
            </h3>
            <p className="text-gray-600 mb-4">
              Analiza el historial de ajustes manuales para calcular los parámetros iniciales del algoritmo de corrección.
            </p>
            
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 mb-4">
              <p className="text-amber-700 text-sm">
                <AlertTriangle className="h-4 w-4 inline mr-1" />
                Este proceso puede tardar varios minutos dependiendo del volumen de datos.
              </p>
            </div>
            
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Período de análisis (días)
              </label>
              <input
                type="number"
                value={bootstrapDays}
                onChange={(e) => setBootstrapDays(parseInt(e.target.value) || 365)}
                min="30"
                max="730"
                className="w-full px-3 py-2 border rounded-lg"
              />
              <p className="text-xs text-gray-500 mt-1">
                Se recomienda analizar al menos 365 días para obtener patrones significativos
              </p>
            </div>
            
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setShowBootstrapModal(false)}
                className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg"
              >
                Cancelar
              </button>
              <button
                onClick={() => bootstrapMutation.mutate({ days: bootstrapDays })}
                disabled={bootstrapMutation.isPending}
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
              >
                {bootstrapMutation.isPending ? (
                  <span className="flex items-center gap-2">
                    <RefreshCw className="h-4 w-4 animate-spin" />
                    Procesando...
                  </span>
                ) : (
                  'Ejecutar Bootstrap'
                )}
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* Modal de Sugerencia de Corrección */}
      {showStatsModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 overflow-auto py-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-3xl max-h-[90vh] overflow-hidden">
            <div className="p-6 border-b flex items-center justify-between bg-gradient-to-r from-indigo-600 to-purple-600 text-white">
              <div>
                <h3 className="text-xl font-bold flex items-center gap-2">
                  <Activity className="h-6 w-6" />
                  Sugerencia de Corrección v4.5.1
                </h3>
                {statsData && (
                  <p className="text-indigo-200">{statsData.parking_name} - {statsData.weekday_name}</p>
                )}
              </div>
              <button
                onClick={() => { setShowStatsModal(false); setStatsParking(null); }}
                className="text-white/80 hover:text-white"
              >
                <XCircle className="h-6 w-6" />
              </button>
            </div>
            
            <div className="overflow-auto max-h-[calc(90vh-80px)] p-6">
              {statsLoading ? (
                <div className="flex items-center justify-center py-12">
                  <RefreshCw className="h-8 w-8 text-indigo-500 animate-spin" />
                </div>
              ) : statsData ? (
                <div className="space-y-6">
                  {/* Resumen de corrección sugerida */}
                  <div className="bg-gradient-to-r from-indigo-50 to-purple-50 border border-indigo-200 rounded-lg p-6">
                    <div className="grid grid-cols-3 gap-6 text-center">
                      <div>
                        <div className="text-3xl font-bold text-gray-700">
                          {statsData.current_occupancy}
                        </div>
                        <div className="text-sm text-gray-500">Ocupación Actual</div>
                      </div>
                      <div>
                        <div className={`text-3xl font-bold ${
                          statsData.suggested_correction > 0 ? 'text-red-600' :
                          statsData.suggested_correction < 0 ? 'text-blue-600' :
                          'text-gray-600'
                        }`}>
                          {statsData.suggested_correction > 0 ? '+' : ''}{statsData.suggested_correction}
                        </div>
                        <div className="text-sm text-gray-500">Corrección Sugerida</div>
                      </div>
                      <div>
                        <div className="text-3xl font-bold text-green-600">
                          {statsData.estimated_real_occupancy}
                        </div>
                        <div className="text-sm text-gray-500">Ocupación Estimada</div>
                      </div>
                    </div>
                    <div className="mt-4 text-center text-sm text-gray-600">
                      Método: <span className="font-medium">{statsData.method}</span> | 
                      Capacidad: <span className="font-medium">{statsData.max_capacity}</span>
                    </div>
                    {statsData.explanation && (
                      <div className="mt-2 text-center text-xs text-indigo-600 bg-indigo-100 rounded px-3 py-1">
                        {statsData.explanation}
                      </div>
                    )}
                  </div>
                  
                  {/* Métricas del algoritmo */}
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-gray-50 rounded-lg p-4">
                      <h4 className="font-medium text-gray-700 mb-3 flex items-center gap-2">
                        <Target className="h-4 w-4" />
                        Métricas de Ratio
                      </h4>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-gray-500">Ratio de corrección:</span>
                          <span className={`font-medium ${
                            statsData.metrics?.correction_ratio < 0.7 ? 'text-red-600' :
                            statsData.metrics?.correction_ratio < 0.9 ? 'text-yellow-600' :
                            'text-green-600'
                          }`}>
                            {statsData.metrics?.correction_ratio?.toFixed(3)}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-500">Desviación estándar:</span>
                          <span className="font-medium">{statsData.metrics?.ratio_std?.toFixed(3)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-500">Muestras ratio:</span>
                          <span className="font-medium">{statsData.metrics?.ratio_samples}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-500">Ocupación esperada:</span>
                          <span className="font-medium">{statsData.metrics?.expected_occupancy?.toFixed(1)}</span>
                        </div>
                      </div>
                    </div>
                    
                    <div className="bg-gray-50 rounded-lg p-4">
                      <h4 className="font-medium text-gray-700 mb-3 flex items-center gap-2">
                        <Activity className="h-4 w-4" />
                        Métricas de Transacciones
                      </h4>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-gray-500">Transacciones hoy:</span>
                          <span className="font-medium">{statsData.transactions_count || 0}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-500">Promedio histórico:</span>
                          <span className="font-medium">{Math.round(statsData.metrics?.avg_transactions_historical || 0)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-500">Factor ajuste:</span>
                          <span className={`font-medium ${
                            statsData.metrics?.transaction_factor < 0.5 ? 'text-blue-600' :
                            statsData.metrics?.transaction_factor > 1.5 ? 'text-red-600' :
                            'text-green-600'
                          }`}>
                            {statsData.metrics?.transaction_factor?.toFixed(3)}x
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-500">Error/transacción:</span>
                          <span className="font-medium">{statsData.metrics?.error_per_transaction?.toFixed(4)}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  {/* Confianza */}
                  <div className="bg-white border rounded-lg p-4">
                    <h4 className="font-medium text-gray-700 mb-3 flex items-center gap-2">
                      <CheckCircle className="h-4 w-4" />
                      Confianza del Algoritmo
                    </h4>
                    <div className="flex items-center gap-4">
                      <div className={`text-2xl font-bold px-4 py-2 rounded ${getConfidenceColor(statsData.confidence?.overall)}`}>
                        {Math.round((statsData.confidence?.overall || 0) * 100)}%
                      </div>
                      <div className="text-sm text-gray-600">
                        {statsData.confidence?.has_enough_data ? (
                          <span className="text-green-600 flex items-center gap-1">
                            <CheckCircle className="h-4 w-4" />
                            Datos suficientes para corrección fiable
                          </span>
                        ) : (
                          <span className="text-amber-600 flex items-center gap-1">
                            <AlertTriangle className="h-4 w-4" />
                            Datos insuficientes, usar con precaución
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="mt-3 text-xs text-gray-500">
                      Última corrección hace {statsData.hours_since_last?.toFixed(1)} horas
                    </div>
                  </div>
                  
                  {/* Botón aplicar */}
                  <div className="flex justify-end gap-3">
                    <button
                      onClick={() => { setShowStatsModal(false); setStatsParking(null); }}
                      className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg"
                    >
                      Cerrar
                    </button>
                    <button
                      onClick={() => {
                        applyCorrectionMutation.mutate(statsParking)
                        setShowStatsModal(false)
                        setStatsParking(null)
                      }}
                      disabled={applyCorrectionMutation.isPending || !statsData.confidence?.has_enough_data}
                      className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 flex items-center gap-2"
                    >
                      <Zap className="h-4 w-4" />
                      Aplicar Corrección ({statsData.suggested_correction > 0 ? '+' : ''}{statsData.suggested_correction})
                    </button>
                  </div>
                </div>
              ) : (
                <div className="text-center py-12 text-gray-500">
                  No se pudieron cargar los datos
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
