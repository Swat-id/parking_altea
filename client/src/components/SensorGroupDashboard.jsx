/**
 * Dashboard de Sensores Agrupados con Control de Permisos
 * v4.2.0 - Componente para mostrar sensores agrupados por parking y tipo
 */

import React, { useState, useEffect } from 'react'
import { Card, Row, Col, Badge, Alert, Spinner, Table, Tabs, Tab } from 'react-bootstrap'
import { useAuth } from '../context/AuthContext'
import sensorGroupService from '../services/sensorGroupService'

const SensorGroupDashboard = () => {
  const { user, hasParkingAccess } = useAuth()
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

      // Cargar dashboard personalizado y resumen del usuario en paralelo
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

  const getStatusBadgeVariant = (status) => {
    switch (status) {
      case 'free': return 'success'
      case 'busy': return 'warning'
      case 'error': return 'danger'
      default: return 'secondary'
    }
  }

  const getAlertVariant = (severity) => {
    switch (severity) {
      case 'high': return 'danger'
      case 'medium': return 'warning'
      case 'low': return 'info'
      default: return 'secondary'
    }
  }

  if (loading) {
    return (
      <div className="d-flex justify-content-center align-items-center" style={{ height: '200px' }}>
        <Spinner animation="border" role="status">
          <span className="visually-hidden">Cargando...</span>
        </Spinner>
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
  const { user_parkings, global_totals } = userSummary

  return (
    <div className="sensor-group-dashboard">
      {/* Header con información del usuario */}
      <div className="d-flex justify-content-between align-items-center mb-4">
        <div>
          <h2>Dashboard de Sensores</h2>
          <p className="text-muted mb-0">
            Usuario: <strong>{user_info.user_name}</strong> | 
            Parkings asignados: <strong>{user_info.accessible_parkings}</strong>
          </p>
        </div>
        <Badge bg="primary" className="fs-6">
          Última actualización: {new Date(dashboardData.timestamp).toLocaleString()}
        </Badge>
      </div>

      {/* Alertas */}
      {alerts && alerts.length > 0 && (
        <Row className="mb-4">
          <Col>
            <h5>Alertas y Notificaciones</h5>
            {alerts.map((alert, index) => (
              <Alert key={index} variant={getAlertVariant(alert.severity)} className="d-flex justify-content-between align-items-center">
                <span>{alert.message}</span>
                <Badge bg={getAlertVariant(alert.severity)}>{alert.count}</Badge>
              </Alert>
            ))}
          </Col>
        </Row>
      )}

      {/* Resumen Global */}
      <Row className="mb-4">
        <Col md={3}>
          <Card className="text-center">
            <Card.Body>
              <h3 className="text-primary">{summary.total_sensors}</h3>
              <p className="mb-0">Total Sensores</p>
            </Card.Body>
          </Card>
        </Col>
        <Col md={3}>
          <Card className="text-center">
            <Card.Body>
              <h3 className="text-success">{summary.total_free}</h3>
              <p className="mb-0">Libres</p>
            </Card.Body>
          </Card>
        </Col>
        <Col md={3}>
          <Card className="text-center">
            <Card.Body>
              <h3 className="text-warning">{summary.total_busy}</h3>
              <p className="mb-0">Ocupados</p>
            </Card.Body>
          </Card>
        </Col>
        <Col md={3}>
          <Card className="text-center">
            <Card.Body>
              <h3 className="text-danger">{summary.total_error}</h3>
              <p className="mb-0">Con Error</p>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Métricas Globales */}
      <Row className="mb-4">
        <Col md={6}>
          <Card>
            <Card.Body className="text-center">
              <h4 className="text-info">{summary.occupancy_rate}%</h4>
              <p className="mb-0">Tasa de Ocupación</p>
            </Card.Body>
          </Card>
        </Col>
        <Col md={6}>
          <Card>
            <Card.Body className="text-center">
              <h4 className="text-success">{summary.health_score}%</h4>
              <p className="mb-0">Estado de Salud</p>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Tabs para diferentes vistas */}
      <Tabs activeKey={activeTab} onSelect={setActiveTab} className="mb-3">
        <Tab eventKey="overview" title="Resumen">
          <Row>
            <Col md={8}>
              <Card>
                <Card.Header>
                  <h5>Resumen por Parking</h5>
                </Card.Header>
                <Card.Body>
                  <Table responsive striped>
                    <thead>
                      <tr>
                        <th>Parking</th>
                        <th>Total</th>
                        <th>Libres</th>
                        <th>Ocupados</th>
                        <th>Error</th>
                        <th>Ocupación</th>
                      </tr>
                    </thead>
                    <tbody>
                      {parkings.map(parking => (
                        <tr key={parking.parking_id}>
                          <td>{parking.parking_name}</td>
                          <td>{parking.total_sensors}</td>
                          <td>
                            <Badge bg="success">{parking.free}</Badge>
                          </td>
                          <td>
                            <Badge bg="warning">{parking.busy}</Badge>
                          </td>
                          <td>
                            <Badge bg="danger">{parking.error}</Badge>
                          </td>
                          <td>
                            <Badge bg={parking.occupancy_rate > 70 ? 'danger' : parking.occupancy_rate > 40 ? 'warning' : 'success'}>
                              {parking.occupancy_rate}%
                            </Badge>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </Table>
                </Card.Body>
              </Card>
            </Col>
            <Col md={4}>
              <Card>
                <Card.Header>
                  <h5>Estadísticas</h5>
                </Card.Header>
                <Card.Body>
                  {/* Tipos de Sensor */}
                  {statistics.sensor_types && Object.keys(statistics.sensor_types).length > 0 && (
                    <div className="mb-3">
                      <h6>Por Tipo de Sensor</h6>
                      {Object.entries(statistics.sensor_types).map(([type, data]) => (
                        <div key={type} className="d-flex justify-content-between align-items-center mb-2">
                          <span>{type}</span>
                          <div>
                            <Badge bg="secondary" className="me-1">{data.total}</Badge>
                            <Badge bg="warning">{data.busy}</Badge>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Parking más ocupado */}
                  {statistics.most_occupied_parking && (
                    <div className="mb-3">
                      <h6>Más Ocupado</h6>
                      <p className="mb-1">
                        <strong>{statistics.most_occupied_parking.name}</strong>
                      </p>
                      <Badge bg="warning">
                        {statistics.most_occupied_parking.occupancy_rate}%
                      </Badge>
                    </div>
                  )}

                  {/* Parking menos ocupado */}
                  {statistics.least_occupied_parking && (
                    <div>
                      <h6>Menos Ocupado</h6>
                      <p className="mb-1">
                        <strong>{statistics.least_occupied_parking.name}</strong>
                      </p>
                      <Badge bg="success">
                        {statistics.least_occupied_parking.occupancy_rate}%
                      </Badge>
                    </div>
                  )}
                </Card.Body>
              </Card>
            </Col>
          </Row>
        </Tab>

        <Tab eventKey="detailed" title="Vista Detallada">
          <Row>
            {user_parkings.map(parking => (
              <Col md={6} lg={4} key={parking.parking_id} className="mb-3">
                <Card>
                  <Card.Header>
                    <h6>{parking.parking_name}</h6>
                  </Card.Header>
                  <Card.Body>
                    {Object.entries(parking.sensor_types).map(([sensorType, typeData]) => (
                      <div key={sensorType} className="mb-3">
                        <div className="d-flex justify-content-between align-items-center mb-2">
                          <strong>{sensorType}</strong>
                          <Badge bg="secondary">{typeData.total}</Badge>
                        </div>
                        <div className="d-flex justify-content-between">
                          <span>
                            <Badge bg="success" className="me-1">{typeData.free}</Badge>
                            Libres
                          </span>
                          <span>
                            <Badge bg="warning" className="me-1">{typeData.busy}</Badge>
                            Ocupados
                          </span>
                          <span>
                            <Badge bg="danger" className="me-1">{typeData.error}</Badge>
                            Error
                          </span>
                        </div>
                      </div>
                    ))}
                  </Card.Body>
                </Card>
              </Col>
            ))}
          </Row>
        </Tab>
      </Tabs>
    </div>
  )
}

export default SensorGroupDashboard
