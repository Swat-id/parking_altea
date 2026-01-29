import { useState, useEffect } from 'react'
import { useQuery } from 'react-query'
import parkingService from '../services/parkingService'
import { 
  X, 
  Camera, 
  Car, 
  CheckCircle, 
  XCircle,
  RefreshCw,
  ChevronDown,
  ChevronRight,
  Wifi,
  WifiOff,
  MapPin
} from 'lucide-react'

/**
 * Modal para mostrar el detalle de plazas monitorizadas de un parking.
 * Agrupa las plazas por cámara y área, mostrando el estado actual de cada una.
 */
const SpotMonitoringModal = ({ isOpen, onClose, parkingId, parkingName }) => {
  const [expandedCameras, setExpandedCameras] = useState({})
  const [expandedAreas, setExpandedAreas] = useState({})

  // Query para obtener datos de plazas monitorizadas
  const { 
    data: spotData, 
    isLoading, 
    error, 
    refetch,
    isFetching 
  } = useQuery(
    ['monitored-spots', parkingId],
    () => parkingService.getMonitoredSpots(parkingId),
    {
      enabled: isOpen && !!parkingId,
      refetchInterval: 30000, // Refrescar cada 30 segundos
      staleTime: 10000,
    }
  )

  // Expandir todas las cámaras por defecto al cargar
  useEffect(() => {
    if (spotData?.detection_cameras) {
      const expanded = {}
      spotData.detection_cameras.forEach(cam => {
        expanded[cam.camera_id] = true
      })
      setExpandedCameras(expanded)
    }
  }, [spotData])

  if (!isOpen) return null

  const toggleCamera = (cameraId) => {
    setExpandedCameras(prev => ({
      ...prev,
      [cameraId]: !prev[cameraId]
    }))
  }

  const toggleArea = (cameraId, areaName) => {
    const key = `${cameraId}-${areaName}`
    setExpandedAreas(prev => ({
      ...prev,
      [key]: !prev[key]
    }))
  }

  const getSpotColor = (isOccupied) => {
    return isOccupied 
      ? 'bg-red-500 text-white' 
      : 'bg-green-500 text-white'
  }

  const formatDateTime = (isoString) => {
    if (!isoString) return 'N/A'
    const date = new Date(isoString)
    return date.toLocaleString('es-ES', {
      day: '2-digit',
      month: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="bg-gradient-to-r from-purple-600 to-indigo-600 px-6 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="bg-white/20 rounded-lg p-2">
              <Car className="h-6 w-6 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">
                Plazas Monitorizadas
              </h2>
              <p className="text-purple-100 text-sm">
                {parkingName || spotData?.parking_name || 'Parking'}
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => refetch()}
              disabled={isFetching}
              className="p-2 hover:bg-white/20 rounded-lg transition-colors"
              title="Actualizar datos"
            >
              <RefreshCw className={`h-5 w-5 text-white ${isFetching ? 'animate-spin' : ''}`} />
            </button>
            <button
              onClick={onClose}
              className="p-2 hover:bg-white/20 rounded-lg transition-colors"
            >
              <X className="h-5 w-5 text-white" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {isLoading ? (
            <div className="flex items-center justify-center h-64">
              <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto"></div>
                <p className="mt-4 text-gray-600">Cargando plazas...</p>
              </div>
            </div>
          ) : error ? (
            <div className="flex items-center justify-center h-64">
              <div className="text-center">
                <XCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
                <p className="text-red-600">Error al cargar las plazas</p>
                <button
                  onClick={() => refetch()}
                  className="mt-4 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
                >
                  Reintentar
                </button>
              </div>
            </div>
          ) : !spotData?.detection_cameras?.length ? (
            <div className="flex items-center justify-center h-64">
              <div className="text-center">
                <Camera className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600">No hay cámaras de detección configuradas</p>
                <p className="text-sm text-gray-500 mt-2">
                  Este parking no tiene monitorización plaza a plaza habilitada
                </p>
              </div>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Resumen general */}
              <div className="bg-gradient-to-r from-slate-50 to-slate-100 rounded-xl p-4 border border-slate-200">
                <h3 className="text-sm font-semibold text-slate-600 uppercase tracking-wide mb-3">
                  Resumen General
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-white rounded-lg p-3 shadow-sm">
                    <p className="text-xs text-gray-500">Total Plazas Monitorizadas</p>
                    <p className="text-2xl font-bold text-slate-800">
                      {spotData.summary.total_spots}
                    </p>
                  </div>
                  <div className="bg-white rounded-lg p-3 shadow-sm">
                    <p className="text-xs text-gray-500">Ocupadas</p>
                    <p className="text-2xl font-bold text-red-600">
                      {spotData.summary.occupied}
                    </p>
                  </div>
                  <div className="bg-white rounded-lg p-3 shadow-sm">
                    <p className="text-xs text-gray-500">Libres</p>
                    <p className="text-2xl font-bold text-green-600">
                      {spotData.summary.free}
                    </p>
                  </div>
                  <div className="bg-white rounded-lg p-3 shadow-sm">
                    <p className="text-xs text-gray-500">Ocupación Detectada</p>
                    <p className="text-2xl font-bold text-purple-600">
                      {spotData.summary.occupancy_percentage}%
                    </p>
                  </div>
                </div>
                
                {/* Comparación con conteo de accesos */}
                <div className="mt-4 pt-4 border-t border-slate-200">
                  <div className="flex items-center justify-between text-sm">
                    <div>
                      <span className="text-gray-500">Ocupación por conteo (accesos): </span>
                      <span className="font-semibold">
                        {spotData.current_occupancy} / {spotData.max_capacity}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-500">Última sincronización: </span>
                      <span className="font-semibold">
                        {formatDateTime(spotData.last_spot_sync)}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Lista de cámaras */}
              <div className="space-y-4">
                <h3 className="text-sm font-semibold text-slate-600 uppercase tracking-wide">
                  Detalle por Cámara ({spotData.detection_cameras.length})
                </h3>
                
                {spotData.detection_cameras.map((camera) => (
                  <div 
                    key={camera.camera_id}
                    className="border border-gray-200 rounded-xl overflow-hidden"
                  >
                    {/* Header de cámara */}
                    <button
                      onClick={() => toggleCamera(camera.camera_id)}
                      className="w-full px-4 py-3 bg-gray-50 hover:bg-gray-100 flex items-center justify-between transition-colors"
                    >
                      <div className="flex items-center space-x-3">
                        {expandedCameras[camera.camera_id] ? (
                          <ChevronDown className="h-5 w-5 text-gray-400" />
                        ) : (
                          <ChevronRight className="h-5 w-5 text-gray-400" />
                        )}
                        <Camera className="h-5 w-5 text-purple-600" />
                        <div className="text-left">
                          <p className="font-medium text-gray-900">{camera.camera_name}</p>
                          <p className="text-xs text-gray-500">{camera.camera_ip}</p>
                        </div>
                        <div className={`flex items-center space-x-1 px-2 py-0.5 rounded-full text-xs ${
                          camera.status === 'ONLINE' 
                            ? 'bg-green-100 text-green-700' 
                            : 'bg-red-100 text-red-700'
                        }`}>
                          {camera.status === 'ONLINE' ? (
                            <Wifi className="h-3 w-3" />
                          ) : (
                            <WifiOff className="h-3 w-3" />
                          )}
                          <span>{camera.status}</span>
                        </div>
                      </div>
                      <div className="flex items-center space-x-4 text-sm">
                        <div className="flex items-center space-x-2">
                          <span className="text-red-600 font-semibold">{camera.occupied}</span>
                          <span className="text-gray-400">/</span>
                          <span className="text-green-600 font-semibold">{camera.free}</span>
                          <span className="text-gray-400">/</span>
                          <span className="text-gray-600">{camera.total_spots_detected}</span>
                        </div>
                      </div>
                    </button>

                    {/* Contenido expandido de la cámara */}
                    {expandedCameras[camera.camera_id] && (
                      <div className="p-4 space-y-4">
                        {camera.areas.length === 0 ? (
                          <p className="text-gray-500 text-sm italic">
                            No hay plazas registradas para esta cámara
                          </p>
                        ) : (
                          camera.areas.map((area) => {
                            const areaKey = `${camera.camera_id}-${area.name}`
                            const isAreaExpanded = expandedAreas[areaKey] !== false

                            return (
                              <div key={areaKey} className="border border-gray-100 rounded-lg">
                                {/* Header de área */}
                                <button
                                  onClick={() => toggleArea(camera.camera_id, area.name)}
                                  className="w-full px-3 py-2 bg-slate-50 hover:bg-slate-100 flex items-center justify-between transition-colors rounded-t-lg"
                                >
                                  <div className="flex items-center space-x-2">
                                    {isAreaExpanded ? (
                                      <ChevronDown className="h-4 w-4 text-gray-400" />
                                    ) : (
                                      <ChevronRight className="h-4 w-4 text-gray-400" />
                                    )}
                                    <MapPin className="h-4 w-4 text-indigo-500" />
                                    <span className="font-medium text-gray-800">
                                      Área {area.name}
                                    </span>
                                  </div>
                                  <div className="flex items-center space-x-2 text-xs">
                                    <span className="px-2 py-0.5 bg-red-100 text-red-700 rounded">
                                      {area.occupied} ocupadas
                                    </span>
                                    <span className="px-2 py-0.5 bg-green-100 text-green-700 rounded">
                                      {area.free} libres
                                    </span>
                                  </div>
                                </button>

                                {/* Grid de plazas */}
                                {isAreaExpanded && (
                                  <div className="p-3">
                                    <div className="grid grid-cols-6 sm:grid-cols-8 md:grid-cols-10 lg:grid-cols-12 gap-2">
                                      {area.spots.map((spot) => (
                                        <div
                                          key={spot.id}
                                          className={`
                                            relative group cursor-default
                                            aspect-square rounded-lg flex items-center justify-center
                                            font-bold text-sm shadow-sm transition-transform hover:scale-110
                                            ${getSpotColor(spot.is_occupied)}
                                          `}
                                          title={`Plaza ${spot.spot_identifier}\nEstado: ${spot.is_occupied ? 'Ocupada' : 'Libre'}\nÚltimo cambio: ${formatDateTime(spot.last_status_change)}`}
                                        >
                                          <span className="text-xs sm:text-sm">
                                            {spot.spot_number}
                                          </span>
                                          
                                          {/* Tooltip on hover */}
                                          <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 bg-gray-900 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-10">
                                            {spot.spot_identifier}: {spot.is_occupied ? 'Ocupada' : 'Libre'}
                                          </div>
                                        </div>
                                      ))}
                                    </div>
                                  </div>
                                )}
                              </div>
                            )
                          })
                        )}
                        
                        {/* Info de última actualización */}
                        <div className="text-xs text-gray-500 flex items-center justify-between pt-2 border-t border-gray-100">
                          <span>Última mensaje: {formatDateTime(camera.last_message)}</span>
                          <span>Plazas configuradas: {camera.monitored_spots_count}</span>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>

              {/* Leyenda */}
              <div className="flex items-center justify-center space-x-6 text-sm pt-4 border-t border-gray-200">
                <div className="flex items-center space-x-2">
                  <div className="w-6 h-6 rounded bg-green-500 flex items-center justify-center">
                    <CheckCircle className="h-4 w-4 text-white" />
                  </div>
                  <span className="text-gray-600">Plaza Libre</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-6 h-6 rounded bg-red-500 flex items-center justify-center">
                    <XCircle className="h-4 w-4 text-white" />
                  </div>
                  <span className="text-gray-600">Plaza Ocupada</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-gray-200 px-6 py-3 bg-gray-50 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
          >
            Cerrar
          </button>
        </div>
      </div>
    </div>
  )
}

export default SpotMonitoringModal
