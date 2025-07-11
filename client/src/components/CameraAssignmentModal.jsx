import React, { useState } from 'react'
import { X, Camera, Plus, Trash2 } from 'lucide-react'

const CameraAssignmentModal = ({ isOpen, onClose, onSave, existingCameras = [] }) => {
  const [cameras, setCameras] = useState(existingCameras.length > 0 ? existingCameras : [
    { ip: '', line: 0, name: '' }
  ])

  const addCamera = () => {
    setCameras([...cameras, { ip: '', line: 0, name: '' }])
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

    onSave(validCameras)
    onClose()
  }

  const handleClose = () => {
    setCameras(existingCameras.length > 0 ? existingCameras : [{ ip: '', line: 0, name: '' }])
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

          {cameras.map((camera, index) => (
            <div key={index} className="border border-gray-200 rounded-lg p-4 bg-gray-50">
              <div className="flex justify-between items-center mb-3">
                <h3 className="font-medium text-gray-900">Cámara {index + 1}</h3>
                {cameras.length > 1 && (
                  <button
                    onClick={() => removeCamera(index)}
                    className="text-red-500 hover:text-red-700 transition-colors"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                )}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
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
              </div>
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