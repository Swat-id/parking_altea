import React, { useState, useEffect } from 'react'
import { Clock, User, Car, Monitor, Calendar, Activity } from 'lucide-react'

const UserActivityLog = ({ userId }) => {
  const [activities, setActivities] = useState([])
  const [loading, setLoading] = useState(true)

  // Simular datos de actividad (en un caso real vendría de la API)
  useEffect(() => {
    const mockActivities = [
      {
        id: 1,
        type: 'login',
        description: 'Inicio de sesión',
        timestamp: new Date(Date.now() - 1000 * 60 * 30), // 30 minutos atrás
        icon: User,
        color: 'text-blue-600',
        bgColor: 'bg-blue-50'
      },
      {
        id: 2,
        type: 'parking_access',
        description: 'Acceso al parking Centro Comercial',
        timestamp: new Date(Date.now() - 1000 * 60 * 60 * 2), // 2 horas atrás
        icon: Car,
        color: 'text-green-600',
        bgColor: 'bg-green-50'
      },
      {
        id: 3,
        type: 'panel_update',
        description: 'Actualización de panel LED',
        timestamp: new Date(Date.now() - 1000 * 60 * 60 * 4), // 4 horas atrás
        icon: Monitor,
        color: 'text-purple-600',
        bgColor: 'bg-purple-50'
      },
      {
        id: 4,
        type: 'schedule_created',
        description: 'Creación de programación semanal',
        timestamp: new Date(Date.now() - 1000 * 60 * 60 * 24), // 1 día atrás
        icon: Calendar,
        color: 'text-orange-600',
        bgColor: 'bg-orange-50'
      },
      {
        id: 5,
        type: 'password_change',
        description: 'Cambio de contraseña',
        timestamp: new Date(Date.now() - 1000 * 60 * 60 * 24 * 3), // 3 días atrás
        icon: Activity,
        color: 'text-red-600',
        bgColor: 'bg-red-50'
      }
    ]

    // Simular carga
    setTimeout(() => {
      setActivities(mockActivities)
      setLoading(false)
    }, 1000)
  }, [userId])

  const formatTimestamp = (timestamp) => {
    const now = new Date()
    const diff = now - timestamp
    const minutes = Math.floor(diff / (1000 * 60))
    const hours = Math.floor(diff / (1000 * 60 * 60))
    const days = Math.floor(diff / (1000 * 60 * 60 * 24))

    if (minutes < 60) {
      return `Hace ${minutes} minutos`
    } else if (hours < 24) {
      return `Hace ${hours} horas`
    } else {
      return `Hace ${days} días`
    }
  }

  const getActivityIcon = (type) => {
    switch (type) {
      case 'login':
        return User
      case 'parking_access':
        return Car
      case 'panel_update':
        return Monitor
      case 'schedule_created':
        return Calendar
      case 'password_change':
        return Activity
      default:
        return Clock
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <p className="ml-2 text-sm text-gray-500">Cargando historial...</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium text-gray-900">Historial de Actividad</h3>
        <span className="text-sm text-gray-500">{activities.length} actividades</span>
      </div>
      
      <div className="space-y-3">
        {activities.map((activity) => {
          const Icon = activity.icon
          return (
            <div key={activity.id} className="flex items-start space-x-3 p-3 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors">
              <div className={`flex-shrink-0 w-8 h-8 rounded-full ${activity.bgColor} flex items-center justify-center`}>
                <Icon className={`h-4 w-4 ${activity.color}`} />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900">{activity.description}</p>
                <p className="text-xs text-gray-500">{formatTimestamp(activity.timestamp)}</p>
              </div>
            </div>
          )
        })}
      </div>

      {activities.length === 0 && (
        <div className="text-center py-8">
          <Clock className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500">No hay actividad reciente</p>
        </div>
      )}
    </div>
  )
}

export default UserActivityLog 