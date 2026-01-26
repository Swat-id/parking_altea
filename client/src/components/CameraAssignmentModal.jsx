import React, { useState, useEffect, useMemo } from 'react'
import { X, Camera, Plus, Trash2, Eye, BarChart3 } from 'lucide-react'

const CameraAssignmentModal = ({ isOpen, onClose, onSave, existingCameras = [] }) => {
  const [cameras, setCameras] = useState(existingCameras.length > 0 ? existingCameras : [
    { ip: '', line: 0, name: '', camera_type: 'counting', monitored_spots_count: 0 }
  ])

  // Actualizar cámaras cuando cambien las existentes
  useEffect(() => {
    if (existingCameras.length > 0) {
      // Asegurar que todas las cámaras tienen los nuevos campos
      const camerasWithDefaults = existingCameras.map(cam => ({
        ...cam,
        camera_type: cam.camera_type || 'counting',
        monitored_spots_count: cam.monitored_spots_count || 0
      }))
      setCameras(camerasWithDefaults)
    }
  }, [existingCameras])

  // Calcular total de plazas monitorizadas
  const totalMonitoredSpots = useMemo(() => {
    return cameras
      .filter(cam => cam.camera_type === 'spot_detection')
      .reduce((sum, cam) => sum + (parseInt(cam.monitored_spots_count) || 0), 0)
  }, [cameras])

  const addCamera = () => {
    setCameras([...cameras, { ip: '', line: 0, name: '', camera_type: 'counting', monitored_spots_count: 0 }])
  }

  const removeCamera = (index) => {
    if (cameras.length > 1) {
      setCameras(cameras.filter((_, i) => i !== index))
    }
  }

  const updateCamera = (index, field, value) => {
    const updatedCameras = [...cameras]
    updatedCameras[index] = { ...updatedCameras[index], [field]: value }
    setCameras(updatedCameras)
  }

  const handleSave = () => {
    // Validar que al menos una cámara tenga IP
    const validCameras = cameras.filter(camera => camera.ip.trim() !== '')
    
    if (validCameras.length === 0) {
      alert('Debe añadir al menos una cámara con IP válida')
      return
    }

    // Validar que no haya IPs duplicadas
    const ips = validCameras.map(c => c.ip.trim())
    const uniqueIps = [...new Set(ips)]
    
    if (ips.length !== uniqueIps.length) {
      alert('No puede haber IPs duplicadas')
      return
    }

    // Validar que las cámaras de detección tengan plazas definidas
    const spotDetectionCameras = validCameras.filter(c => c.camera_type === 'spot_detection')
    const invalidSpotCameras = spotDetectionCameras.filter(c => !c.monitored_spots_count || c.monitored_spots_count <= 0)
    
    if (invalidSpotCameras.length > 0) {
      alert('Las cámaras de detección por plaza deben tener un número de plazas monitorizadas mayor que 0')
      return
    }

    // Calcular el total de plazas monitorizadas para devolver al padre
    const totalSpots = spotDetectionCameras.reduce((sum, cam) => sum + (parseInt(cam.monitored_spots_count) || 0), 0)

    onSave(validCameras, totalSpots)
    onClose()
  }

  const handleClose = () => {
    const defaultCameras = existingCameras.length > 0 
      ? existingCameras.map(cam => ({
          ...cam,
          camera_type: cam.camera_type || 'counting',
          monitored_spots_count: cam.monitored_spots_count || 0
        }))
      : [{ ip: '', line: 0, name: '', camera_type: 'counting', monitored_spots_count: 0 }]
    setCameras(defaultCameras)
    onClose()
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold text-gray-900 flex items-center">
            <Camera className="h-5 w-5 mr-2" />
            Asignar Cámaras al Parking
          </h2>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        <div className="space-y-4">
          <p className="text-sm text-gray-600">
            Configure las cámaras que monitorearán este parking. Una misma cámara puede asignarse a varios parkings.
          </p>

          {/* Resumen de plazas monitorizadas */}
          {totalMonitoredSpots > 0 && (
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-3 flex items-center">
              <Eye className="h-5 w-5 text-purple-600 mr-2" />
              <span className="text-sm text-purple-800">
                <strong>{totalMonitoredSpots}</strong> plazas monitorizadas por detección individual
              </span>
            </div>
          )}

          {cameras.map((camera, index) => (
            <div key={index} className={`border rounded-lg p-4 ${
              camera.camera_type === 'spot_detection' 
                ? 'border-purple-300 bg-purple-50' 
                : 'border-gray-200 bg-gray-50'
            }`}>
              <div className="flex justify-between items-center mb-3">
                <div className="flex items-center">
                  {camera.camera_type === 'spot_detection' ? (
                    <Eye className="h-4 w-4 text-purple-600 mr-2" />
                  ) : (
                    <BarChart3 className="h-4 w-4 text-blue-600 mr-2" />
                  )}
                  <h3 className="font-medium text-gray-900">Cámara {index + 1}</h3>
                  <span className={`ml-2 text-xs px-2 py-1 rounded-full ${
                    camera.camera_type === 'spot_detection'
                      ? 'bg-purple-100 text-purple-700'
                      : 'bg-blue-100 text-blue-700'
                  }`}>
                    {camera.camera_type === 'spot_detection' ? 'Detección por Plaza' : 'Conteo'}
                  </span>
                </div>
                {cameras.length > 1 && (
                  <button
                    onClick={() => removeCamera(index)}
                    className="text-red-500 hover:text-red-700 transition-colors"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                )}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    IP de la Cámara *
                  </label>
                  <input
                    type="text"
                    value={camera.ip}
                    onChange={(e) => updateCamera(index, 'ip', e.target.value)}
                    placeholder="192.168.1.100"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Línea
                  </label>
                  <input
                    type="number"
                    value={camera.line}
                    onChange={(e) => updateCamera(index, 'line', parseInt(e.target.value) || 0)}
                    min="0"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Nombre (Opcional)
                  </label>
                  <input
                    type="text"
                    value={camera.name}
                    onChange={(e) => updateCamera(index, 'name', e.target.value)}
                    placeholder="Entrada Principal"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Tipo de Cámara
                  </label>
                  <select
                    value={camera.camera_type || 'counting'}
                    onChange={(e) => updateCamera(index, 'camera_type', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="counting">Conteo (Entradas/Salidas)</option>
                    <option value="spot_detection">Detección por Plaza</option>
                  </select>
                </div>
              </div>

              {/* Campo adicional para cámaras de detección por plaza */}
              {camera.camera_type === 'spot_detection' && (
                <div className="mt-4 pt-4 border-t border-purple-200">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-purple-700 mb-1">
                        Plazas Monitorizadas por esta Cámara
                      </label>
                      <input
                        type="number"
                        value={camera.monitored_spots_count || 0}
                        onChange={(e) => updateCamera(index, 'monitored_spots_count', parseInt(e.target.value) || 0)}
                        min="0"
                        placeholder="Ej: 40"
                        className="w-full px-3 py-2 border border-purple-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent bg-white"
                      />
                      <p className="mt-1 text-xs text-purple-600">
                        Número de plazas individuales que monitoriza esta cámara
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))}

          <button
            onClick={addCamera}
            className="w-full flex items-center justify-center px-4 py-2 border-2 border-dashed border-gray-300 rounded-lg text-gray-600 hover:border-gray-400 hover:text-gray-700 transition-colors"
          >
            <Plus className="h-4 w-4 mr-2" />
            Añadir Otra Cámara
          </button>
        </div>

        <div className="flex justify-end space-x-3 mt-6 pt-4 border-t border-gray-200">
          <button
            onClick={handleClose}
            className="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors"
          >
            Cancelar
          </button>
          <button
            onClick={handleSave}
            className="px-4 py-2 bg-blue-600 text-white hover:bg-blue-700 rounded-md transition-colors"
          >
            Guardar Cámaras
          </button>
        </div>
      </div>
    </div>
  )
}

export default CameraAssignmentModal 