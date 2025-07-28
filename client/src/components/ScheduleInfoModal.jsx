import React from 'react'
import { X, Calendar, Clock, MessageSquare, Info } from 'lucide-react'

const ScheduleInfoModal = ({ isOpen, onClose, panel, schedule }) => {
  if (!isOpen || !schedule) return null

  const formatTime = (timeString) => {
    if (!timeString) return ''
    try {
      const time = new Date(`2000-01-01T${timeString}`)
      return time.toLocaleTimeString('es-ES', {
        hour: '2-digit',
        minute: '2-digit'
      })
    } catch (error) {
      return timeString
    }
  }

  const formatDate = (dateString) => {
    if (!dateString) return ''
    try {
      const date = new Date(dateString)
      return date.toLocaleDateString('es-ES', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
      })
    } catch (error) {
      return dateString
    }
  }

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-6 border w-96 shadow-lg rounded-md bg-white">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-medium text-gray-900">Información de Programación</h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        <div className="space-y-4">
          {/* Panel Info */}
          <div className="bg-gray-50 p-3 rounded-lg">
            <div className="flex items-center mb-2">
              <MessageSquare className="h-4 w-4 text-blue-600 mr-2" />
              <span className="font-medium text-gray-900">Panel</span>
            </div>
            <p className="text-sm text-gray-600">{panel?.name || 'N/A'}</p>
            <p className="text-xs text-gray-500">{panel?.ip_address || 'N/A'}</p>
          </div>

          {/* Schedule Info */}
          <div className="bg-blue-50 p-3 rounded-lg">
            <div className="flex items-center mb-2">
              <Calendar className="h-4 w-4 text-blue-600 mr-2" />
              <span className="font-medium text-blue-900">Programación Activa</span>
            </div>
            <p className="text-sm font-medium text-blue-800">{schedule.name}</p>
            <p className="text-xs text-blue-600">{schedule.message}</p>
          </div>

          {/* Time Info */}
          <div className="bg-green-50 p-3 rounded-lg">
            <div className="flex items-center mb-2">
              <Clock className="h-4 w-4 text-green-600 mr-2" />
              <span className="font-medium text-green-900">Horario</span>
            </div>
            <div className="text-sm text-green-800">
              <p><strong>Inicio:</strong> {formatTime(schedule.start_time)}</p>
              <p><strong>Fin:</strong> {formatTime(schedule.end_time)}</p>
            </div>
          </div>

          {/* Additional Info */}
          <div className="bg-yellow-50 p-3 rounded-lg">
            <div className="flex items-center mb-2">
              <Info className="h-4 w-4 text-yellow-600 mr-2" />
              <span className="font-medium text-yellow-900">Información Adicional</span>
            </div>
            <div className="text-sm text-yellow-800">
              <p><strong>ID:</strong> {schedule.id}</p>
              <p><strong>Tipo de Mensaje:</strong> Programación</p>
              <p><strong>Estado:</strong> Activa</p>
            </div>
          </div>

          {/* Message Preview */}
          <div className="bg-gray-100 p-3 rounded-lg">
            <p className="text-sm font-medium text-gray-900 mb-1">Vista Previa del Mensaje:</p>
            <div className="bg-white p-2 rounded border text-center">
              <span className="text-sm text-gray-700">{schedule.message}</span>
            </div>
          </div>
        </div>

        <div className="flex justify-end mt-6">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Cerrar
          </button>
        </div>
      </div>
    </div>
  )
}

export default ScheduleInfoModal 