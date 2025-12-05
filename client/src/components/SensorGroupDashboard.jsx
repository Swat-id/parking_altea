/**
 * Dashboard de Sensores Agrupados con Control de Permisos
 * v4.2.0 - Componente para mostrar sensores agrupados por parking y tipo
 * Migrado a Tailwind CSS
 */

import React, { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import sensorGroupService from '../services/sensorGroupService'
import { AlertCircle, Activity, CheckCircle, XCircle, Clock } from 'lucide-react'

// Componente Badge reutilizable
const Badge = ({ children, variant = 'secondary', className = '' }) => {
  const variants = {
    primary: 'bg-primary-600 text-white',
    secondary: 'bg-gray-500 text-white',
    success: 'bg-green-500 text-white',
    warning: 'bg-yellow-500 text-white',
    danger: 'bg-red-500 text-white',
    info: 'bg-blue-500 text-white'
  }
  
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${variants[variant]} ${className}`}>
      {children}
    </span>
  )
}

// Componente Card reutilizable
const Card = ({ children, className = '' }) => (
  <div className={`bg-white rounded-lg shadow-sm border border-gray-200 ${className}`}>
    {children}
  </div>
)

const CardHeader = ({ children, className = '' }) => (
  <div className={`px-4 py-3 border-b border-gray-200 ${className}`}>
    {children}
  </div>
)

const CardBody = ({ children, className = '' }) => (
  <div className={`p-4 ${className}`}>
    {children}
  </div>
)

// Componente Alert reutilizable
const Alert = ({ children, variant = 'info', className = '' }) => {
  const variants = {
    info: 'bg-blue-50 border-blue-200 text-blue-800',
    success: 'bg-green-50 border-green-200 text-green-800',
    warning: 'bg-yellow-50 border-yellow-200 text-yellow-800',
    danger: 'bg-red-50 border-red-200 text-red-800'
  }
  
  return (
    <div className={`px-4 py-3 rounded-lg border ${variants[variant]} ${className}`}>
      {children}
    </div>
  )
}

const SensorGroupDashboard = () => {
  const { user } = useAuth()
  const [dashboardData, setDashboardData] = useState(null)
  const [userSummary, setUserSummary] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState('overview')

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    try {
      setLoading(true)
      setError(null)

      const [dashboard, summary] = await Promise.all([
        sensorGroupService.getUserDashboard(),
        sensorGroupService.getUserSummary()
      ])

      setDashboardData(dashboard)
      setUserSummary(summary)
    } catch (err) {
      console.error('Error cargando dashboard:', err)
      setError('Error cargando datos del dashboard')
    } finally {
      setLoading(false)
    }
  }

  const getAlertVariant = (severity) => {
    switch (severity) {
      case 'high': return 'danger'
      case 'medium': return 'warning'
      case 'low': return 'info'
      default: return 'info'
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center h-48">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (error) {
    return <Alert variant="danger">{error}</Alert>
  }

  if (!dashboardData || !userSummary) {
    return <Alert variant="info">No hay datos disponibles</Alert>
  }

  const { summary, parkings, alerts, statistics, user_info } = dashboardData
  const { user_parkings } = userSummary

  return (
    <div className="sensor-group-dashboard space-y-6">
      {/* Header con información del usuario */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-xl font-bold text-gray-900">Dashboard de Sensores</h2>
          <p className="text-sm text-gray-500">
            Usuario: <strong>{user_info.user_name}</strong> | 
            Parkings asignados: <strong>{user_info.accessible_parkings}</strong>
          </p>
        </div>
        <Badge variant="primary" className="text-sm">
          <Clock className="h-3 w-3 mr-1" />
          {new Date(dashboardData.timestamp).toLocaleString()}
        </Badge>
      </div>

      {/* Alertas */}
      {alerts && alerts.length > 0 && (
        <div className="space-y-2">
          <h5 className="text-sm font-medium text-gray-700">Alertas y Notificaciones</h5>
          {alerts.map((alert, index) => (
            <Alert key={index} variant={getAlertVariant(alert.severity)} className="flex justify-between items-center">
              <span>{alert.message}</span>
              <Badge variant={getAlertVariant(alert.severity)}>{alert.count}</Badge>
            </Alert>
          ))}
        </div>
      )}

      {/* Resumen Global */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="text-center">
          <CardBody>
            <Activity className="h-6 w-6 text-primary-600 mx-auto mb-2" />
            <h3 className="text-2xl font-bold text-primary-600">{summary.total_sensors}</h3>
            <p className="text-sm text-gray-500">Total Sensores</p>
          </CardBody>
        </Card>
        <Card className="text-center">
          <CardBody>
            <CheckCircle className="h-6 w-6 text-green-600 mx-auto mb-2" />
            <h3 className="text-2xl font-bold text-green-600">{summary.total_free}</h3>
            <p className="text-sm text-gray-500">Libres</p>
          </CardBody>
        </Card>
        <Card className="text-center">
          <CardBody>
            <Clock className="h-6 w-6 text-yellow-600 mx-auto mb-2" />
            <h3 className="text-2xl font-bold text-yellow-600">{summary.total_busy}</h3>
            <p className="text-sm text-gray-500">Ocupados</p>
          </CardBody>
        </Card>
        <Card className="text-center">
          <CardBody>
            <XCircle className="h-6 w-6 text-red-600 mx-auto mb-2" />
            <h3 className="text-2xl font-bold text-red-600">{summary.total_error}</h3>
            <p className="text-sm text-gray-500">Con Error</p>
          </CardBody>
        </Card>
      </div>

      {/* Métricas Globales */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card className="text-center">
          <CardBody>
            <h4 className="text-xl font-bold text-blue-600">{summary.occupancy_rate}%</h4>
            <p className="text-sm text-gray-500">Tasa de Ocupación</p>
          </CardBody>
        </Card>
        <Card className="text-center">
          <CardBody>
            <h4 className="text-xl font-bold text-green-600">{summary.health_score}%</h4>
            <p className="text-sm text-gray-500">Estado de Salud</p>
          </CardBody>
        </Card>
      </div>

      {/* Tabs para diferentes vistas */}
      <div className="border-b border-gray-200">
        <nav className="flex gap-4">
          <button
            onClick={() => setActiveTab('overview')}
            className={`py-2 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'overview'
                ? 'border-primary-600 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Resumen
          </button>
          <button
            onClick={() => setActiveTab('detailed')}
            className={`py-2 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'detailed'
                ? 'border-primary-600 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Vista Detallada
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Tabla Resumen por Parking */}
          <Card className="lg:col-span-2">
            <CardHeader>
              <h5 className="font-medium text-gray-900">Resumen por Parking</h5>
            </CardHeader>
            <CardBody className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead>
                  <tr>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Parking</th>
                    <th className="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase">Total</th>
                    <th className="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase">Libres</th>
                    <th className="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase">Ocupados</th>
                    <th className="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase">Error</th>
                    <th className="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase">Ocupación</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {parkings.map(parking => (
                    <tr key={parking.parking_id} className="hover:bg-gray-50">
                      <td className="px-3 py-2 text-sm text-gray-900">{parking.parking_name}</td>
                      <td className="px-3 py-2 text-center text-sm">{parking.total_sensors}</td>
                      <td className="px-3 py-2 text-center">
                        <Badge variant="success">{parking.free}</Badge>
                      </td>
                      <td className="px-3 py-2 text-center">
                        <Badge variant="warning">{parking.busy}</Badge>
                      </td>
                      <td className="px-3 py-2 text-center">
                        <Badge variant="danger">{parking.error}</Badge>
                      </td>
                      <td className="px-3 py-2 text-center">
                        <Badge variant={parking.occupancy_rate > 70 ? 'danger' : parking.occupancy_rate > 40 ? 'warning' : 'success'}>
                          {parking.occupancy_rate}%
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CardBody>
          </Card>

          {/* Estadísticas */}
          <Card>
            <CardHeader>
              <h5 className="font-medium text-gray-900">Estadísticas</h5>
            </CardHeader>
            <CardBody className="space-y-4">
              {statistics.sensor_types && Object.keys(statistics.sensor_types).length > 0 && (
                <div>
                  <h6 className="text-sm font-medium text-gray-700 mb-2">Por Tipo de Sensor</h6>
                  {Object.entries(statistics.sensor_types).map(([type, data]) => (
                    <div key={type} className="flex justify-between items-center mb-2">
                      <span className="text-sm text-gray-600">{type}</span>
                      <div className="flex gap-1">
                        <Badge variant="secondary">{data.total}</Badge>
                        <Badge variant="warning">{data.busy}</Badge>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {statistics.most_occupied_parking && (
                <div>
                  <h6 className="text-sm font-medium text-gray-700 mb-1">Más Ocupado</h6>
                  <p className="text-sm text-gray-900 font-medium">{statistics.most_occupied_parking.name}</p>
                  <Badge variant="warning">{statistics.most_occupied_parking.occupancy_rate}%</Badge>
                </div>
              )}

              {statistics.least_occupied_parking && (
                <div>
                  <h6 className="text-sm font-medium text-gray-700 mb-1">Menos Ocupado</h6>
                  <p className="text-sm text-gray-900 font-medium">{statistics.least_occupied_parking.name}</p>
                  <Badge variant="success">{statistics.least_occupied_parking.occupancy_rate}%</Badge>
                </div>
              )}
            </CardBody>
          </Card>
        </div>
      )}

      {activeTab === 'detailed' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {user_parkings.map(parking => (
            <Card key={parking.parking_id}>
              <CardHeader>
                <h6 className="font-medium text-gray-900">{parking.parking_name}</h6>
              </CardHeader>
              <CardBody className="space-y-3">
                {Object.entries(parking.sensor_types).map(([sensorType, typeData]) => (
                  <div key={sensorType}>
                    <div className="flex justify-between items-center mb-1">
                      <strong className="text-sm text-gray-700">{sensorType}</strong>
                      <Badge variant="secondary">{typeData.total}</Badge>
                    </div>
                    <div className="flex justify-between text-xs">
                      <span className="flex items-center gap-1">
                        <Badge variant="success">{typeData.free}</Badge>
                        Libres
                      </span>
                      <span className="flex items-center gap-1">
                        <Badge variant="warning">{typeData.busy}</Badge>
                        Ocupados
                      </span>
                      <span className="flex items-center gap-1">
                        <Badge variant="danger">{typeData.error}</Badge>
                        Error
                      </span>
                    </div>
                  </div>
                ))}
              </CardBody>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}

export default SensorGroupDashboard
