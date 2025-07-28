import React, { useState, useEffect } from 'react';
import { 
  Container, 
  Row, 
  Col, 
  Card, 
  Form, 
  Button, 
  Table, 
  Badge, 
  Modal,
  Alert,
  Spinner,
  Pagination
} from 'react-bootstrap';
import { 
  ClockHistory, 
  Filter, 
  Search, 
  Eye,
  Calendar,
  ExclamationTriangle,
  ExclamationCircle,
  ExclamationDiamond
} from 'react-bootstrap-icons';
import AlarmStatusCard from '../components/AlarmStatusCard';
import alarmService from '../services/alarmService';

const AlarmHistory = () => {
  const [alarms, setAlarms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [selectedAlarm, setSelectedAlarm] = useState(null);
  
  // Estados para filtros
  const [filters, setFilters] = useState({
    severity: '',
    status: '',
    alarm_type: '',
    start_date: '',
    end_date: '',
    limit: 50
  });
  
  // Estados para paginación
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalAlarms, setTotalAlarms] = useState(0);

  useEffect(() => {
    loadAlarmHistory();
  }, [filters, currentPage]);

  const loadAlarmHistory = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const historyData = await alarmService.getAlarmHistory({
        ...filters,
        page: currentPage
      });
      
      setAlarms(historyData.alarms || historyData);
      setTotalAlarms(historyData.total || historyData.length);
      setTotalPages(historyData.pages || 1);
    } catch (err) {
      console.error('Error loading alarm history:', err);
      setError('Error al cargar el histórico de alarmas');
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (field, value) => {
    setFilters(prev => ({
      ...prev,
      [field]: value
    }));
    setCurrentPage(1); // Reset to first page when filters change
  };

  const handleClearFilters = () => {
    setFilters({
      severity: '',
      status: '',
      alarm_type: '',
      start_date: '',
      end_date: '',
      limit: 50
    });
    setCurrentPage(1);
  };

  const handleViewDetails = (alarm) => {
    setSelectedAlarm(alarm);
    setShowDetailsModal(true);
  };

  const getSeverityIcon = (severity) => {
    const icons = {
      'LEVE': <ExclamationTriangle className="text-warning" />,
      'NORMAL': <ExclamationCircle className="text-info" />,
      'GRAVE': <ExclamationDiamond className="text-danger" />
    };
    return icons[severity] || <ExclamationTriangle />;
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString('es-ES', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getStatusBadge = (status) => {
    const variants = {
      'active': 'danger',
      'resolved': 'success',
      'paused': 'warning'
    };
    return <Badge bg={variants[status] || 'secondary'}>{alarmService.getStatusLabel(status)}</Badge>;
  };

  const renderPagination = () => {
    if (totalPages <= 1) return null;

    const pages = [];
    const maxVisiblePages = 5;
    let startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2));
    let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);

    if (endPage - startPage + 1 < maxVisiblePages) {
      startPage = Math.max(1, endPage - maxVisiblePages + 1);
    }

    // Previous button
    pages.push(
      <Pagination.Prev
        key="prev"
        disabled={currentPage === 1}
        onClick={() => setCurrentPage(currentPage - 1)}
      />
    );

    // First page
    if (startPage > 1) {
      pages.push(
        <Pagination.Item
          key={1}
          active={currentPage === 1}
          onClick={() => setCurrentPage(1)}
        >
          1
        </Pagination.Item>
      );
      if (startPage > 2) {
        pages.push(<Pagination.Ellipsis key="ellipsis1" />);
      }
    }

    // Visible pages
    for (let i = startPage; i <= endPage; i++) {
      pages.push(
        <Pagination.Item
          key={i}
          active={currentPage === i}
          onClick={() => setCurrentPage(i)}
        >
          {i}
        </Pagination.Item>
      );
    }

    // Last page
    if (endPage < totalPages) {
      if (endPage < totalPages - 1) {
        pages.push(<Pagination.Ellipsis key="ellipsis2" />);
      }
      pages.push(
        <Pagination.Item
          key={totalPages}
          active={currentPage === totalPages}
          onClick={() => setCurrentPage(totalPages)}
        >
          {totalPages}
        </Pagination.Item>
      );
    }

    // Next button
    pages.push(
      <Pagination.Next
        key="next"
        disabled={currentPage === totalPages}
        onClick={() => setCurrentPage(currentPage + 1)}
      />
    );

    return <Pagination className="justify-content-center">{pages}</Pagination>;
  };

  if (loading && alarms.length === 0) {
    return (
      <Container className="mt-4">
        <div className="text-center">
          <Spinner animation="border" role="status">
            <span className="visually-hidden">Cargando...</span>
          </Spinner>
          <p className="mt-2">Cargando histórico de alarmas...</p>
        </div>
      </Container>
    );
  }

  return (
    <Container className="mt-4">
      <Row className="mb-4">
        <Col>
          <h2>
            <ClockHistory className="me-2" />
            Histórico de Alarmas
          </h2>
          <p className="text-muted">
            Historial completo de alarmas generadas y resueltas
          </p>
        </Col>
      </Row>

      {error && (
        <Alert variant="danger" dismissible onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Filtros */}
      <Card className="mb-4">
        <Card.Header>
          <h5 className="mb-0">
            <Filter className="me-2" />
            Filtros de Búsqueda
          </h5>
        </Card.Header>
        <Card.Body>
          <Row>
            <Col md={3}>
              <Form.Group className="mb-3">
                <Form.Label>Severidad</Form.Label>
                <Form.Select
                  value={filters.severity}
                  onChange={(e) => handleFilterChange('severity', e.target.value)}
                >
                  <option value="">Todas las severidades</option>
                  <option value="LEVE">Leve</option>
                  <option value="NORMAL">Normal</option>
                  <option value="GRAVE">Grave</option>
                </Form.Select>
              </Form.Group>
            </Col>
            <Col md={3}>
              <Form.Group className="mb-3">
                <Form.Label>Estado</Form.Label>
                <Form.Select
                  value={filters.status}
                  onChange={(e) => handleFilterChange('status', e.target.value)}
                >
                  <option value="">Todos los estados</option>
                  <option value="active">Activa</option>
                  <option value="resolved">Resuelta</option>
                  <option value="paused">Pausada</option>
                </Form.Select>
              </Form.Group>
            </Col>
            <Col md={3}>
              <Form.Group className="mb-3">
                <Form.Label>Tipo de Alarma</Form.Label>
                <Form.Select
                  value={filters.alarm_type}
                  onChange={(e) => handleFilterChange('alarm_type', e.target.value)}
                >
                  <option value="">Todos los tipos</option>
                  <option value="panel">Panel</option>
                  <option value="camera">Cámara</option>
                  <option value="parking">Aparcamiento</option>
                </Form.Select>
              </Form.Group>
            </Col>
            <Col md={3}>
              <Form.Group className="mb-3">
                <Form.Label>Límite de resultados</Form.Label>
                <Form.Select
                  value={filters.limit}
                  onChange={(e) => handleFilterChange('limit', e.target.value)}
                >
                  <option value={25}>25 resultados</option>
                  <option value={50}>50 resultados</option>
                  <option value={100}>100 resultados</option>
                </Form.Select>
              </Form.Group>
            </Col>
          </Row>
          
          <Row>
            <Col md={4}>
              <Form.Group className="mb-3">
                <Form.Label>Fecha de Inicio</Form.Label>
                <Form.Control
                  type="date"
                  value={filters.start_date}
                  onChange={(e) => handleFilterChange('start_date', e.target.value)}
                />
              </Form.Group>
            </Col>
            <Col md={4}>
              <Form.Group className="mb-3">
                <Form.Label>Fecha de Fin</Form.Label>
                <Form.Control
                  type="date"
                  value={filters.end_date}
                  onChange={(e) => handleFilterChange('end_date', e.target.value)}
                />
              </Form.Group>
            </Col>
            <Col md={4} className="d-flex align-items-end">
              <div className="d-flex gap-2 w-100">
                <Button 
                  variant="outline-secondary" 
                  onClick={handleClearFilters}
                  className="flex-fill"
                >
                  Limpiar Filtros
                </Button>
                <Button 
                  variant="primary" 
                  onClick={loadAlarmHistory}
                  className="flex-fill"
                >
                  <Search className="me-2" />
                  Buscar
                </Button>
              </div>
            </Col>
          </Row>
        </Card.Body>
      </Card>

      {/* Resultados */}
      <Card>
        <Card.Header className="d-flex justify-content-between align-items-center">
          <h5 className="mb-0">Resultados ({totalAlarms} alarmas)</h5>
          {loading && <Spinner animation="border" size="sm" />}
        </Card.Header>
        <Card.Body>
          {alarms.length === 0 ? (
            <div className="text-center py-4">
              <ClockHistory className="text-muted" size={48} />
              <p className="mt-2 text-muted">No se encontraron alarmas con los filtros aplicados</p>
            </div>
          ) : (
            <div>
              {alarms.map(alarm => (
                <AlarmStatusCard
                  key={alarm.id}
                  alarm={alarm}
                  onViewDetails={handleViewDetails}
                />
              ))}
              
              {renderPagination()}
            </div>
          )}
        </Card.Body>
      </Card>

      {/* Modal de Detalles */}
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
                  <p><strong>Creada:</strong> {formatDate(selectedAlarm.created_at)}</p>
                  {selectedAlarm.resolved_at && (
                    <p><strong>Resuelta:</strong> {formatDate(selectedAlarm.resolved_at)}</p>
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
              
              {selectedAlarm.resolution_description && (
                <div className="mt-3">
                  <h6>Descripción de la Resolución</h6>
                  <p className="text-muted">{selectedAlarm.resolution_description}</p>
                </div>
              )}
            </div>
          )}
        </Modal.Body>
      </Modal>
    </Container>
  );
};

export default AlarmHistory; 