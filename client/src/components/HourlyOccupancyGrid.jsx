import React, { useState } from 'react'
import { Clock, Activity, TrendingUp, Info } from 'lucide-react'

const HourlyOccupancyGrid = ({ hourlyStats, parkingName }) => {
  const [activeTab, setActiveTab] = useState('occupancy')
  const [selectedHour, setSelectedHour] = useState(null)

  // Función para obtener el color basado en el porcentaje de ocupación
  const getOccupancyColor = (percentage) => {
    if (percentage === 0) return 'bg-gray-100'
    if (percentage <= 20) return 'bg-green-100'
    if (percentage <= 40) return 'bg-green-300'
    if (percentage <= 60) return 'bg-yellow-300'
    if (percentage <= 80) return 'bg-orange-400'
    if (percentage <= 100) return 'bg-red-400'
    return 'bg-red-600' // Más del 100%
  }

  // Función para obtener el color basado en la intensidad de tráfico
  const getTrafficColor = (intensity) => {
    const maxIntensity = Math.max(...hourlyStats.map(stat => stat.traffic_intensity || 0))
    if (maxIntensity === 0) return 'bg-gray-100'
    
    const percentage = (intensity / maxIntensity) * 100
    if (percentage === 0) return 'bg-gray-100'
    if (percentage <= 20) return 'bg-blue-100'
    if (percentage <= 40) return 'bg-blue-300'
    if (percentage <= 60) return 'bg-blue-400'
    if (percentage <= 80) return 'bg-blue-500'
    return 'bg-blue-600'
  }

  // Función para obtener el texto del color
  const getTextColor = (percentage, isTraffic = false) => {
    if (isTraffic) {
      const maxIntensity = Math.max(...hourlyStats.map(stat => stat.traffic_intensity || 0))
      const intensityPercentage = maxIntensity > 0 ? (percentage / maxIntensity) * 100 : 0
      return intensityPercentage > 60 ? 'text-white' : 'text-gray-800'
    }
    return percentage > 60 ? 'text-white' : 'text-gray-800'
  }

  const renderOccupancyGrid = () => (
    <div className="grid grid-cols-1 gap-2">
      <div className="text-sm text-gray-600 mb-4">
        <div className="flex items-center justify-between">
          <span>Ocupación por horas (promedio)</span>
          <div className="flex items-center space-x-2 text-xs">
            <div className="flex items-center space-x-1">
              <div className="w-3 h-3 bg-gray-100 border"></div>
              <span>0%</span>
            </div>
            <div className="flex items-center space-x-1">
              <div className="w-3 h-3 bg-green-300 border"></div>
              <span>20-40%</span>
            </div>
            <div className="flex items-center space-x-1">
              <div className="w-3 h-3 bg-yellow-300 border"></div>
              <span>40-60%</span>
            </div>
            <div className="flex items-center space-x-1">
              <div className="w-3 h-3 bg-orange-400 border"></div>
              <span>60-80%</span>
            </div>
            <div className="flex items-center space-x-1">
              <div className="w-3 h-3 bg-red-400 border"></div>
              <span>80-100%</span>
            </div>
            <div className="flex items-center space-x-1">
              <div className="w-3 h-3 bg-red-600 border"></div>
              <span>>100%</span>
            </div>
          </div>
        </div>
      </div>
      
      {hourlyStats.map((stat) => (
        <div
          key={stat.hour}
          className={`
            p-4 rounded-lg border-2 cursor-pointer transition-all duration-200
            ${getOccupancyColor(stat.occupancy_percentage || 0)}
            ${selectedHour === stat.hour ? 'border-blue-500 ring-2 ring-blue-200' : 'border-gray-200'}
            hover:border-blue-300 hover:shadow-md
          `}
          onClick={() => setSelectedHour(selectedHour === stat.hour ? null : stat.hour)}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Clock className="w-5 h-5 text-gray-600" />
              <span className={`font-semibold ${getTextColor(stat.occupancy_percentage || 0)}`}>
                {stat.hour_label}
              </span>
            </div>
            <div className={`text-right ${getTextColor(stat.occupancy_percentage || 0)}`}>
              <div className="text-lg font-bold">
                {stat.occupancy_percentage || 0}%
              </div>
              <div className="text-sm opacity-75">
                {stat.message_count || 0} msgs
              </div>
            </div>
          </div>
          
          {selectedHour === stat.hour && (
            <div className="mt-3 pt-3 border-t border-gray-300 grid grid-cols-3 gap-4 text-sm">
              <div>
                <div className="font-medium text-green-600">Entradas</div>
                <div className="text-lg">{stat.total_vehicles_in || 0}</div>
              </div>
              <div>
                <div className="font-medium text-red-600">Salidas</div>
                <div className="text-lg">{stat.total_vehicles_out || 0}</div>
              </div>
              <div>
                <div className="font-medium text-blue-600">Cambio neto</div>
                <div className="text-lg">{stat.net_change || 0}</div>
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  )

  const renderTrafficGrid = () => (
    <div className="grid grid-cols-1 gap-2">
      <div className="text-sm text-gray-600 mb-4">
        <div className="flex items-center justify-between">
          <span>Intensidad de tráfico por horas (entradas + salidas)</span>
          <div className="flex items-center space-x-2 text-xs">
            <div className="flex items-center space-x-1">
              <div className="w-3 h-3 bg-gray-100 border"></div>
              <span>Sin tráfico</span>
            </div>
            <div className="flex items-center space-x-1">
              <div className="w-3 h-3 bg-blue-300 border"></div>
              <span>Bajo</span>
            </div>
            <div className="flex items-center space-x-1">
              <div className="w-3 h-3 bg-blue-500 border"></div>
              <span>Alto</span>
            </div>
            <div className="flex items-center space-x-1">
              <div className="w-3 h-3 bg-blue-600 border"></div>
              <span>Muy alto</span>
            </div>
          </div>
        </div>
      </div>
      
      {hourlyStats.map((stat) => (
        <div
          key={stat.hour}
          className={`
            p-4 rounded-lg border-2 cursor-pointer transition-all duration-200
            ${getTrafficColor(stat.traffic_intensity || 0)}
            ${selectedHour === stat.hour ? 'border-blue-500 ring-2 ring-blue-200' : 'border-gray-200'}
            hover:border-blue-300 hover:shadow-md
          `}
          onClick={() => setSelectedHour(selectedHour === stat.hour ? null : stat.hour)}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Activity className="w-5 h-5 text-gray-600" />
              <span className={`font-semibold ${getTextColor(stat.traffic_intensity || 0, true)}`}>
                {stat.hour_label}
              </span>
            </div>
            <div className={`text-right ${getTextColor(stat.traffic_intensity || 0, true)}`}>
              <div className="text-lg font-bold">
                {stat.traffic_intensity || 0}
              </div>
              <div className="text-sm opacity-75">
                vehículos
              </div>
            </div>
          </div>
          
          {selectedHour === stat.hour && (
            <div className="mt-3 pt-3 border-t border-gray-300 grid grid-cols-3 gap-4 text-sm">
              <div>
                <div className="font-medium text-green-600">Entradas</div>
                <div className="text-lg">{stat.total_vehicles_in || 0}</div>
              </div>
              <div>
                <div className="font-medium text-red-600">Salidas</div>
                <div className="text-lg">{stat.total_vehicles_out || 0}</div>
              </div>
              <div>
                <div className="font-medium text-gray-600">Ocupación</div>
                <div className="text-lg">{stat.occupancy_percentage || 0}%</div>
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  )

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900">
          Análisis por Horas - {parkingName}
        </h3>
        <div className="flex items-center space-x-1 bg-gray-100 rounded-lg p-1">
          <button
            onClick={() => setActiveTab('occupancy')}
            className={`px-3 py-1 rounded-md text-sm font-medium transition-colors ${
              activeTab === 'occupancy'
                ? 'bg-white text-blue-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <TrendingUp className="w-4 h-4 inline mr-1" />
            Ocupación
          </button>
          <button
            onClick={() => setActiveTab('traffic')}
            className={`px-3 py-1 rounded-md text-sm font-medium transition-colors ${
              activeTab === 'traffic'
                ? 'bg-white text-blue-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <Activity className="w-4 h-4 inline mr-1" />
            Tráfico
          </button>
        </div>
      </div>

      <div className="mb-4 p-3 bg-blue-50 rounded-lg">
        <div className="flex items-start space-x-2">
          <Info className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
          <div className="text-sm text-blue-800">
            <p className="font-medium mb-1">Cómo interpretar la visualización:</p>
            <ul className="space-y-1 text-xs">
              <li>• <strong>Ocupación:</strong> Colores desde blanco (0%) hasta rojo intenso (>100%)</li>
              <li>• <strong>Tráfico:</strong> Intensidad de azul según el volumen de entradas + salidas</li>
              <li>• <strong>Interacción:</strong> Haz clic en cualquier hora para ver detalles</li>
            </ul>
          </div>
        </div>
      </div>

      <div className="max-h-96 overflow-y-auto">
        {activeTab === 'occupancy' ? renderOccupancyGrid() : renderTrafficGrid()}
      </div>

      {hourlyStats.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          <Clock className="w-12 h-12 mx-auto mb-2 opacity-50" />
          <p>No hay datos de estadísticas por horas disponibles</p>
        </div>
      )}
    </div>
  )
}

export default HourlyOccupancyGrid
