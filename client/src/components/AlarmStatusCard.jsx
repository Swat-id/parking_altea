import React from 'react';
import { Card, Badge, Button, Row, Col } from 'react-bootstrap';
import { 
  ExclamationTriangleFill, 
  ExclamationCircleFill, 
  ExclamationDiamondFill,
  Clock,
  CheckCircle,
  XCircle
} from 'react-bootstrap-icons';
import alarmService from '../services/alarmService';

const AlarmStatusCard = ({ alarm, onResolve, onViewDetails }) => {
  const getSeverityIcon = (severity) => {
    const icons = {
      'LEVE': <ExclamationTriangleFill className="text-warning" />,
      'NORMAL': <ExclamationCircleFill className="text-info" />,
      'GRAVE': <ExclamationDiamondFill className="text-danger" />
    };
    return icons[severity] || <ExclamationTriangleFill />;
  };

  const getSeverityColor = (severity) => {
    return alarmService.getSeverityColor(severity);
  };

  const getStatusIcon = (status) => {
    const icons = {
      'active': <Clock className="text-danger" />,
      'resolved': <CheckCircle className="text-success" />,
      'paused': <XCircle className="text-warning" />
    };
    return icons[status] || <Clock />;
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

  const getAffectedTargetsText = (affectedTargets) => {
    if (!affectedTargets || affectedTargets.length === 0) {
      return 'Sin objetivos afectados';
    }
    
    const targets = affectedTargets.map(target => target.name || target.target_id);
    return targets.join(', ');
  };

  return (
    <Card className="mb-3 shadow-sm">
      <Card.Header className="d-flex justify-content-between align-items-center">
        <div className="d-flex align-items-center">
          {getSeverityIcon(alarm.severity)}
          <span className="ms-2 fw-bold">{alarm.configuration_name}</span>
        </div>
        <div className="d-flex align-items-center gap-2">
          <Badge bg={getSeverityColor(alarm.severity)}>
            {alarmService.getSeverityLabel(alarm.severity)}
          </Badge>
          {getStatusIcon(alarm.status)}
        </div>
      </Card.Header>
      
      <Card.Body>
        <Row>
          <Col md={8}>
            <p className="mb-2">
              <strong>Mensaje:</strong> {alarm.message}
            </p>
            <p className="mb-2">
              <strong>Objetivos afectados:</strong> {getAffectedTargetsText(alarm.affected_targets)}
            </p>
            <p className="mb-2">
              <strong>Tipo:</strong> {alarmService.getAlarmTypeLabel(alarm.alarm_type)}
            </p>
          </Col>
          <Col md={4}>
            <div className="text-end">
              <p className="mb-1">
                <small className="text-muted">
                  <strong>Creada:</strong><br />
                  {formatDate(alarm.created_at)}
                </small>
              </p>
              {alarm.resolved_at && (
                <p className="mb-1">
                  <small className="text-muted">
                    <strong>Resuelta:</strong><br />
                    {formatDate(alarm.resolved_at)}
                  </small>
                </p>
              )}
            </div>
          </Col>
        </Row>
      </Card.Body>
      
      <Card.Footer className="d-flex justify-content-between align-items-center">
        <div>
          <small className="text-muted">
            ID: {alarm.id} | Configuración: {alarm.alarm_configuration_id}
          </small>
        </div>
        <div className="d-flex gap-2">
          {onViewDetails && (
            <Button 
              variant="outline-primary" 
              size="sm"
              onClick={() => onViewDetails(alarm)}
            >
              Ver Detalles
            </Button>
          )}
          {alarm.status === 'active' && onResolve && (
            <Button 
              variant="success" 
              size="sm"
              onClick={() => onResolve(alarm)}
            >
              Resolver
            </Button>
          )}
        </div>
      </Card.Footer>
    </Card>
  );
};

export default AlarmStatusCard; 