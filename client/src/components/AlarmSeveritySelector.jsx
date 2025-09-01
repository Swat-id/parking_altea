import React from 'react';
import { Form, Row, Col } from 'react-bootstrap';

const AlarmSeveritySelector = ({ 
  severity, 
  thresholdValue, 
  onChange,
  disabled = false 
}) => {
  const handleSeverityChange = (e) => {
    onChange({
      severity: e.target.value,
      thresholdValue: thresholdValue
    });
  };

  const handleThresholdChange = (e) => {
    onChange({
      severity: severity,
      thresholdValue: e.target.value
    });
  };

  const getSeverityDescription = (severity) => {
    const descriptions = {
      'LEVE': 'Primer nivel de alerta - tiempo corto',
      'NORMAL': 'Segundo nivel de alerta - tiempo medio',
      'GRAVE': 'Tercer nivel de alerta - tiempo largo'
    };
    return descriptions[severity] || '';
  };

  const getThresholdLabel = (severity) => {
    const labels = {
      'LEVE': 'Minutos (LEVE)',
      'NORMAL': 'Minutos (NORMAL)',
      'GRAVE': 'Minutos (GRAVE)'
    };
    return labels[severity] || 'Minutos';
  };

  return (
    <Row>
      <Col md={6}>
        <Form.Group className="mb-3">
          <Form.Label>Nivel de Severidad</Form.Label>
          <Form.Select
            value={severity || ''}
            onChange={handleSeverityChange}
            disabled={disabled}
          >
            <option value="">Seleccionar severidad...</option>
            <option value="LEVE">LEVE</option>
            <option value="NORMAL">NORMAL</option>
            <option value="GRAVE">GRAVE</option>
          </Form.Select>
          {severity && (
            <Form.Text className="text-muted">
              {getSeverityDescription(severity)}
            </Form.Text>
          )}
        </Form.Group>
      </Col>
      <Col md={6}>
        <Form.Group className="mb-3">
          <Form.Label>{getThresholdLabel(severity)}</Form.Label>
          <Form.Control
            type="number"
            min="1"
            max="1440"
            value={thresholdValue || ''}
            onChange={handleThresholdChange}
            placeholder="Ej: 5"
            disabled={disabled || !severity}
          />
          <Form.Text className="text-muted">
            Tiempo en minutos antes de generar la alarma
          </Form.Text>
        </Form.Group>
      </Col>
    </Row>
  );
};

export default AlarmSeveritySelector; 