import React, { useState, useEffect } from 'react';
import { 
  Container, 
  Row, 
  Col, 
  Card, 
  Button, 
  Badge, 
  Table, 
  Modal, 
  Form, 
  Alert,
  Tabs,
  Tab,
  Spinner
} from 'react-bootstrap';
import { 
  Plus, 
  ExclamationTriangle, 
  ExclamationCircle, 
  ExclamationDiamond,
  Bell,
  BellFill,
  Gear,
  Trash,
  Pencil,
  Eye,
  CheckCircle
} from 'react-bootstrap-icons';
import AlarmStatusCard from '../components/AlarmStatusCard';
import AlarmConfigurationForm from '../components/AlarmConfigurationForm';
import alarmService from '../services/alarmService';

const Alarms = () => {
  const [activeTab, setActiveTab] = useState('configurations');
  const [configurations, setConfigurations] = useState([]);
  const [activeAlarms, setActiveAlarms] = useState([]);
  const [statistics, setStatistics] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Estados para modales
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showResolveModal, setShowResolveModal] = useState(false);
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  
  // Estados para formularios
  const [selectedConfiguration, setSelectedConfiguration] = useState(null);
  const [selectedAlarm, setSelectedAlarm] = useState(null);
  const [alarmType, setAlarmType] = useState('panel');
  const [resolutionDescription, setResolutionDescription] = useState('');
  const [formLoading, setFormLoading] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const [configsData, alarmsData, statsData] = await Promise.all([
        alarmService.getAlarmConfigurations(),
        alarmService.getActiveAlarms(),
        alarmService.getAlarmStatistics()
      ]);
      
      setConfigurations(configsData);
      setActiveAlarms(alarmsData);
      setStatistics(statsData);
    } catch (err) {
      console.error('Error loading alarm data:', err);
      setError('Error al cargar los datos de alarmas');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateConfiguration = async (configData) => {
    setFormLoading(true);
    try {
      await alarmService.createAlarmConfiguration(configData);
      setShowCreateModal(false);
      setAlarmType('panel');
      loadData();
    } catch (err) {
      console.error('Error creating configuration:', err);
      setError('Error al crear la configuración');
    } finally {
      setFormLoading(false);
    }
  };

  const handleUpdateConfiguration = async (configData) => {
    setFormLoading(true);
    try {
      await alarmService.updateAlarmConfiguration(selectedConfiguration.id, configData);
      setShowEditModal(false);
      setSelectedConfiguration(null);
      loadData();
    } catch (err) {
      console.error('Error updating configuration:', err);
      setError('Error al actualizar la configuración');
    } finally {
      setFormLoading(false);
    }
  };

  const handleDeleteConfiguration = async (configId) => {
    if (!window.confirm('¿Está seguro de que desea eliminar esta configuración?')) {
      return;
    }
    
    try {
      await alarmService.deleteAlarmConfiguration(configId);
      loadData();
    } catch (err) {
      console.error('Error deleting configuration:', err);
      setError('Error al eliminar la configuración');
    }
  };

  const handleResolveAlarm = async () => {
    if (!resolutionDescription.trim()) {
      setError('Debe proporcionar una descripción de la resolución');
      return;
    }
    
    setFormLoading(true);
    try {
      await alarmService.resolveAlarm(selectedAlarm.id, {
        resolution_description: resolutionDescription
      });
      setShowResolveModal(false);
      setSelectedAlarm(null);
      setResolutionDescription('');
      loadData();
    } catch (err) {
      console.error('Error resolving alarm:', err);
      setError('Error al resolver la alarma');
    } finally {
      setFormLoading(false);
    }
  };

  const getSeverityIcon = (severity) => {
    const icons = {
      'LEVE': <ExclamationTriangle className="text-warning" />,
      'NORMAL': <ExclamationCircle className="text-info" />,
      'GRAVE': <ExclamationDiamond className="text-danger" />
    };
    return icons[severity] || <ExclamationTriangle />;
  };

  const getStatusBadge = (status) => {
    const variants = {
      'active': 'success',
      'paused': 'warning',
      'resolved': 'secondary'
    };
    return <Badge bg={variants[status] || 'secondary'}>{alarmService.getStatusLabel(status)}</Badge>;
  };

  if (loading) {
    return (
      <Container className="mt-4">
        <div className="text-center">
          <Spinner animation="border" role="status">
            <span className="visually-hidden">Cargando...</span>
          </Spinner>
          <p className="mt-2">Cargando sistema de alarmas...</p>
        </div>
      </Container>
    );
  }

  return (
    <Container className="mt-4">
      <Row className="mb-4">
        <Col>
          <h2>
            <Bell className="me-2" />
            Sistema de Alarmas
          </h2>
          <p className="text-muted">
            Gestión de configuraciones y monitorización de alarmas del sistema
          </p>
        </Col>
        <Col xs="auto">
          <Button 
            variant="primary" 
            onClick={() => setShowCreateModal(true)}
          >
            <Plus className="me-2" />
            Nueva Configuración
          </Button>
        </Col>
      </Row>

      {error && (
        <Alert variant="danger" dismissible onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Estadísticas */}
      <Row className="mb-4">
        <Col md={3}>
          <Card className="text-center">
            <Card.Body>
              <h4 className="text-primary">{statistics.total_configurations || 0}</h4>
              <p className="mb-0">Configuraciones</p>
            </Card.Body>
          </Card>
        </Col>
        <Col md={3}>
          <Card className="text-center">
            <Card.Body>
              <h4 className="text-danger">{statistics.active_alarms || 0}</h4>
              <p className="mb-0">Alarmas Activas</p>
            </Card.Body>
          </Card>
        </Col>
        <Col md={3}>
          <Card className="text-center">
            <Card.Body>
              <h4 className="text-success">{statistics.resolved_alarms || 0}</h4>
              <p className="mb-0">Alarmas Resueltas</p>
            </Card.Body>
          </Card>
        </Col>
        <Col md={3}>
          <Card className="text-center">
            <Card.Body>
              <h4 className="text-info">{statistics.total_alarms || 0}</h4>
              <p className="mb-0">Total Alarmas</p>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Tabs principales */}
      <Tabs activeKey={activeTab} onSelect={(k) => setActiveTab(k)} className="mb-4">
        <Tab eventKey="configurations" title="Configuraciones">
          <Card>
            <Card.Body>
              {configurations.length === 0 ? (
                <div className="text-center py-4">
                  <Bell className="text-muted" size={48} />
                  <p className="mt-2 text-muted">No hay configuraciones de alarmas</p>
                  <Button 
                    variant="primary" 
                    onClick={() => setShowCreateModal(true)}
                  >
                    <Plus className="me-2" />
                    Crear Primera Configuración
                  </Button>
                </div>
              ) : (
                <Table responsive>
                  <thead>
                    <tr>
                      <th>Nombre</th>
                      <th>Tipo</th>
                      <th>Estado</th>
                      <th>Objetivos</th>
                      <th>Umbrales</th>
                      <th>Acciones</th>
                    </tr>
                  </thead>
                  <tbody>
                    {configurations.map(config => (
                      <tr key={config.id}>
                        <td>
                          <div>
                            <strong>{config.name}</strong>
                            {config.description && (
                              <small className="text-muted d-block">
                                {config.description}
                              </small>
                            )}
                          </div>
                        </td>
                        <td>
                          <Badge bg="primary">
                            {alarmService.getAlarmTypeLabel(config.alarm_type)}
                          </Badge>
                        </td>
                        <td>{getStatusBadge(config.status)}</td>
                        <td>
                          <small>
                            {config.targets?.length || 0} objetivo(s)
                          </small>
                        </td>
                        <td>
                          <small>
                            {config.thresholds?.length || 0} umbral(es)
                          </small>
                        </td>
                        <td>
                          <div className="d-flex gap-1">
                            <Button 
                              size="sm" 
                              variant="outline-primary"
                              onClick={() => {
                                setSelectedConfiguration(config);
                                setShowEditModal(true);
                              }}
                            >
                              <Pencil />
                            </Button>
                            <Button 
                              size="sm" 
                              variant="outline-danger"
                              onClick={() => handleDeleteConfiguration(config.id)}
                            >
                              <Trash />
                            </Button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </Table>
              )}
            </Card.Body>
          </Card>
        </Tab>

        <Tab eventKey="active" title="Alarmas Activas">
          <Card>
            <Card.Body>
              {activeAlarms.length === 0 ? (
                <div className="text-center py-4">
                  <CheckCircle className="text-success" size={48} />
                  <p className="mt-2 text-muted">No hay alarmas activas</p>
                </div>
              ) : (
                <div>
                  {activeAlarms.map(alarm => (
                    <AlarmStatusCard
                      key={alarm.id}
                      alarm={alarm}
                      onResolve={(alarm) => {
                        setSelectedAlarm(alarm);
                        setShowResolveModal(true);
                      }}
                      onViewDetails={(alarm) => {
                        setSelectedAlarm(alarm);
                        setShowDetailsModal(true);
                      }}
                    />
                  ))}
                </div>
              )}
            </Card.Body>
          </Card>
        </Tab>
      </Tabs>

      {/* Modal de Crear Configuración */}
      <Modal 
        show={showCreateModal} 
        onHide={() => setShowCreateModal(false)}
        size="lg"
      >
        <Modal.Header closeButton>
          <Modal.Title>Nueva Configuración de Alarma</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form.Group className="mb-3">
            <Form.Label>Tipo de Alarma</Form.Label>
            <Form.Select
              value={alarmType}
              onChange={(e) => setAlarmType(e.target.value)}
            >
              <option value="panel">Panel</option>
              <option value="camera">Cámara</option>
              <option value="parking">Aparcamiento</option>
            </Form.Select>
          </Form.Group>
          
          <AlarmConfigurationForm
            alarmType={alarmType}
            onSubmit={handleCreateConfiguration}
            onCancel={() => setShowCreateModal(false)}
            loading={formLoading}
          />
        </Modal.Body>
      </Modal>

      {/* Modal de Editar Configuración */}
      <Modal 
        show={showEditModal} 
        onHide={() => setShowEditModal(false)}
        size="lg"
      >
        <Modal.Header closeButton>
          <Modal.Title>Editar Configuración de Alarma</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {selectedConfiguration && (
            <AlarmConfigurationForm
              alarmType={selectedConfiguration.alarm_type}
              initialData={selectedConfiguration}
              onSubmit={handleUpdateConfiguration}
              onCancel={() => setShowEditModal(false)}
              loading={formLoading}
            />
          )}
        </Modal.Body>
      </Modal>

      {/* Modal de Resolver Alarma */}
      <Modal 
        show={showResolveModal} 
        onHide={() => setShowResolveModal(false)}
      >
        <Modal.Header closeButton>
          <Modal.Title>Resolver Alarma</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {selectedAlarm && (
            <div>
              <p><strong>Alarma:</strong> {selectedAlarm.configuration_name}</p>
              <p><strong>Mensaje:</strong> {selectedAlarm.message}</p>
              
              <Form.Group className="mb-3">
                <Form.Label>Descripción de la Resolución *</Form.Label>
                <Form.Control
                  as="textarea"
                  rows={3}
                  value={resolutionDescription}
                  onChange={(e) => setResolutionDescription(e.target.value)}
                  placeholder="Describa cómo se resolvió la alarma..."
                />
              </Form.Group>
            </div>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowResolveModal(false)}>
            Cancelar
          </Button>
          <Button 
            variant="success" 
            onClick={handleResolveAlarm}
            disabled={formLoading || !resolutionDescription.trim()}
          >
            {formLoading ? (
              <>
                <Spinner animation="border" size="sm" className="me-2" />
                Resolviendo...
              </>
            ) : (
              'Resolver Alarma'
            )}
          </Button>
        </Modal.Footer>
      </Modal>

      {/* Modal de Detalles de Alarma */}
      <Modal 
        show={showDetailsModal} 
        onHide={() => setShowDetailsModal(false)}
        size="lg"
      >
        <Modal.Header closeButton>
          <Modal.Title>Detalles de la Alarma</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {selectedAlarm && (
            <div>
              <h5>{selectedAlarm.configuration_name}</h5>
              <p className="text-muted">{selectedAlarm.message}</p>
              
              <Row>
                <Col md={6}>
                  <h6>Información General</h6>
                  <p><strong>ID:</strong> {selectedAlarm.id}</p>
                  <p><strong>Tipo:</strong> {alarmService.getAlarmTypeLabel(selectedAlarm.alarm_type)}</p>
                  <p><strong>Severidad:</strong> {alarmService.getSeverityLabel(selectedAlarm.severity)}</p>
                  <p><strong>Estado:</strong> {alarmService.getStatusLabel(selectedAlarm.status)}</p>
                </Col>
                <Col md={6}>
                  <h6>Fechas</h6>
                  <p><strong>Creada:</strong> {new Date(selectedAlarm.created_at).toLocaleString()}</p>
                  {selectedAlarm.resolved_at && (
                    <p><strong>Resuelta:</strong> {new Date(selectedAlarm.resolved_at).toLocaleString()}</p>
                  )}
                </Col>
              </Row>
              
              {selectedAlarm.affected_targets && selectedAlarm.affected_targets.length > 0 && (
                <div className="mt-3">
                  <h6>Objetivos Afectados</h6>
                  <ul>
                    {selectedAlarm.affected_targets.map((target, index) => (
                      <li key={index}>{target.name || `ID: ${target.target_id}`}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </Modal.Body>
      </Modal>
    </Container>
  );
};

export default Alarms; 