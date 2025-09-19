import { 
  X,
  CheckCircle,
  AlertCircle,
  Info,
  Settings,
  Battery,
  BatteryLow
} from 'lucide-react'
import sensorService from '../services/sensorService'

// Modal de edición
export const EditSensorModal = ({ 
  show, 
  sensor, 
  editingForm, 
  setEditingForm, 
  onClose, 
  onUpdate, 
  isLoading, 
  parkings 
}) => {
  if (!show || !sensor) return null

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
        <div className="mt-3">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Editar Sensor</h3>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Número de Serie *
              </label>
              <input
                type="text"
                value={editingForm.serial_number}
                onChange={(e) => setEditingForm(prev => ({ ...prev, serial_number: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Nombre *
              </label>
              <input
                type="text"
                value={editingForm.name}
                onChange={(e) => setEditingForm(prev => ({ ...prev, name: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Tipo de Sensor
              </label>
              <select
                value={editingForm.sensor_type}
                onChange={(e) => setEditingForm(prev => ({ ...prev, sensor_type: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {sensorService.getSensorTypes().map(type => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Parking
              </label>
              <select
                value={editingForm.parking_id}
                onChange={(e) => setEditingForm(prev => ({ ...prev, parking_id: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Sin asignar</option>
                {parkings.map(parking => (
                  <option key={parking.id} value={parking.id}>
                    {parking.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Descripción
              </label>
              <textarea
                value={editingForm.description}
                onChange={(e) => setEditingForm(prev => ({ ...prev, description: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                rows="3"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Coordenadas (lat,lng)
              </label>
              <input
                type="text"
                value={editingForm.location_coordinates}
                onChange={(e) => setEditingForm(prev => ({ ...prev, location_coordinates: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={editingForm.is_active}
                  onChange={(e) => setEditingForm(prev => ({ ...prev, is_active: e.target.checked }))}
                  className="mr-2"
                />
                <span className="text-sm font-medium text-gray-700">Sensor activo</span>
              </label>
            </div>
          </div>

          <div className="flex justify-end space-x-3 mt-6">
            <button
              onClick={onClose}
              className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
            >
              Cancelar
            </button>
            <button
              onClick={onUpdate}
              disabled={isLoading}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {isLoading ? 'Actualizando...' : 'Actualizar'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

// Modal de actualización de estado
export const StatusUpdateModal = ({ 
  show, 
  sensor, 
  statusForm, 
  setStatusForm, 
  onClose, 
  onUpdate, 
  isLoading 
}) => {
  if (!show || !sensor) return null

  const getStatusIcon = (status) => {
    switch (status) {
      case 'free':
        return <CheckCircle className="h-5 w-5 text-green-500" />
      case 'busy':
        return <AlertCircle className="h-5 w-5 text-red-500" />
      case 'error':
        return <AlertCircle className="h-5 w-5 text-yellow-500" />
      case 'unknown':
        return <Info className="h-5 w-5 text-gray-500" />
      default:
        return <Settings className="h-5 w-5 text-purple-500" />
    }
  }

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
        <div className="mt-3">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            Actualizar Estado - {sensor.name}
          </h3>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Estado *
              </label>
              <select
                value={statusForm.status}
                onChange={(e) => setStatusForm(prev => ({ ...prev, status: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {sensorService.getSensorStatuses().map(status => (
                  <option key={status.value} value={status.value}>
                    {status.icon} {status.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Capacidad de Batería (%)
              </label>
              <input
                type="number"
                min="0"
                max="100"
                value={statusForm.battery_capacity}
                onChange={(e) => setStatusForm(prev => ({ ...prev, battery_capacity: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="0-100"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Voltaje de Batería (V)
              </label>
              <input
                type="number"
                step="0.1"
                min="0"
                max="5"
                value={statusForm.battery_voltage}
                onChange={(e) => setStatusForm(prev => ({ ...prev, battery_voltage: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Ej: 3.7"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Temperatura (°C)
              </label>
              <input
                type="number"
                step="0.1"
                value={statusForm.temperature}
                onChange={(e) => setStatusForm(prev => ({ ...prev, temperature: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Ej: 25.5"
              />
            </div>
          </div>

          <div className="flex justify-end space-x-3 mt-6">
            <button
              onClick={onClose}
              className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
            >
              Cancelar
            </button>
            <button
              onClick={onUpdate}
              disabled={isLoading}
              className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
            >
              {isLoading ? 'Actualizando...' : 'Actualizar Estado'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

// Modal de detalles
export const SensorDetailModal = ({ show, sensor, onClose }) => {
  if (!show || !sensor) return null

  const getStatusIcon = (status) => {
    switch (status) {
      case 'free':
        return <CheckCircle className="h-5 w-5 text-green-500" />
      case 'busy':
        return <AlertCircle className="h-5 w-5 text-red-500" />
      case 'error':
        return <AlertCircle className="h-5 w-5 text-yellow-500" />
      case 'unknown':
        return <Info className="h-5 w-5 text-gray-500" />
      default:
        return <Settings className="h-5 w-5 text-purple-500" />
    }
  }

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-2/3 max-w-4xl shadow-lg rounded-md bg-white">
        <div className="mt-3">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-medium text-gray-900">
              Detalles del Sensor - {sensor.name}
            </h3>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <X className="h-6 w-6" />
            </button>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Información básica */}
            <div className="space-y-4">
              <h4 className="font-medium text-gray-900">Información Básica</h4>
              <div className="bg-gray-50 p-4 rounded-lg space-y-2">
                <p><strong>Serial:</strong> {sensor.serial_number}</p>
                <p><strong>Nombre:</strong> {sensor.name}</p>
                <p><strong>Tipo:</strong> {sensorService.formatSensorType(sensor.sensor_type)}</p>
                <p><strong>Parking:</strong> {sensor.parking_name || 'Sin asignar'}</p>
                <p><strong>Fabricante:</strong> {sensor.manufacturer}</p>
                <p><strong>Estado:</strong> {sensor.is_active ? 'Activo' : 'Inactivo'}</p>
                {sensor.description && (
                  <p><strong>Descripción:</strong> {sensor.description}</p>
                )}
                {sensor.location_coordinates && (
                  <p><strong>Coordenadas:</strong> {sensor.location_coordinates}</p>
                )}
              </div>
            </div>

            {/* Estado actual */}
            <div className="space-y-4">
              <h4 className="font-medium text-gray-900">Estado Actual</h4>
              <div className="bg-gray-50 p-4 rounded-lg space-y-2">
                <div className="flex items-center">
                  {getStatusIcon(sensor.current_status)}
                  <span className="ml-2">{sensorService.formatSensorStatus(sensor.current_status)}</span>
                </div>
                {sensor.battery_info && (
                  <>
                    <div className="flex items-center">
                      {sensor.battery_info.is_low ? (
                        <BatteryLow className="h-4 w-4 text-red-500 mr-2" />
                      ) : (
                        <Battery className="h-4 w-4 text-green-500 mr-2" />
                      )}
                      <span><strong>Batería:</strong> {sensor.battery_info.capacity}%</span>
                    </div>
                    {sensor.battery_info.voltage && (
                      <p><strong>Voltaje:</strong> {sensor.battery_info.voltage}V</p>
                    )}
                  </>
                )}
                <p><strong>Última actualización:</strong> {
                  sensor.last_update ? 
                  new Date(sensor.last_update).toLocaleString() : 
                  'Nunca'
                }</p>
                <p><strong>Creado:</strong> {
                  sensor.created_at ? 
                  new Date(sensor.created_at).toLocaleString() : 
                  'N/A'
                }</p>
              </div>
            </div>

            {/* Historial reciente */}
            {sensor.recent_history && sensor.recent_history.length > 0 && (
              <div className="md:col-span-2">
                <h4 className="font-medium text-gray-900 mb-4">Historial Reciente (24h)</h4>
                <div className="bg-gray-50 p-4 rounded-lg max-h-60 overflow-y-auto">
                  <div className="space-y-2">
                    {sensor.recent_history.slice(0, 10).map((record, index) => (
                      <div key={index} className="flex justify-between items-center text-sm border-b border-gray-200 pb-2">
                        <div className="flex items-center">
                          {getStatusIcon(record.status)}
                          <span className="ml-2">{sensorService.formatSensorStatus(record.status)}</span>
                          {record.battery_capacity && (
                            <span className="ml-2 text-gray-500">
                              (Batería: {record.battery_capacity}%)
                            </span>
                          )}
                        </div>
                        <div className="text-gray-500">
                          {new Date(record.timestamp).toLocaleString()}
                        </div>
                      </div>
                    ))}
                    {sensor.recent_history.length === 0 && (
                      <p className="text-gray-500 text-center py-4">No hay historial disponible</p>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
