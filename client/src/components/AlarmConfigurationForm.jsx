import React, { useState, useEffect } from 'react';
import { Form, Button, Card, Row, Col, Alert, Badge } from 'react-bootstrap';
import { Plus, X, Save, ArrowLeft } from 'react-bootstrap-icons';
import AlarmSeveritySelector from './AlarmSeveritySelector';
import alarmService from '../services/alarmService';
import panelService from '../services/panelService';
import cameraService from '../services/cameraService';
import parkingService from '../services/parkingService';

const AlarmConfigurationForm = ({ 
  alarmType, 
  initialData = null,
  onSubmit,
  onCancel,
  loading = false 
}) => {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    alarm_type: alarmType || 'panel',
    status: 'active',
    targets: [],
    thresholds: []
  });

  const [availableTargets, setAvailableTargets] = useState([]);
  const [selectedTargets, setSelectedTargets] = useState([]);
  const [thresholds, setThresholds] = useState([
    { severity: 'LEVE', threshold_value: '' },
    { severity: 'NORMAL', threshold_value: '' },
    { severity: 'GRAVE', threshold_value: '' }
  ]);
  const [errors, setErrors] = useState({});
  const [loadingTargets, setLoadingTargets] = useState(false);

  useEffect(() => {
    if (initialData) {
      setFormData({
        name: initialData.name || '',
        description: initialData.description || '',
        alarm_type: initialData.alarm_type || alarmType || 'panel',
        status: initialData.status || 'active',
        targets: initialData.targets || [],
        thresholds: initialData.thresholds || []
      });
      
      if (initialData.targets) {
        setSelectedTargets(initialData.targets.map(t => t.target_id));
      }
      
      if (initialData.thresholds) {
        setThresholds(initialData.thresholds);
      }
    }
    loadAvailableTargets();
  }, [initialData, alarmType]);

  const loadAvailableTargets = async () => {
    setLoadingTargets(true);
    try {
      let targets = [];
      
      switch (formData.alarm_type) {
        case 'panel':
          const panels = await panelService.getUserPanels();
          targets = panels.map(panel => ({
            id: panel.id,
            name: panel.name,
            type: 'panel'
          }));
          break;
        case 'camera':
          const cameras = await cameraService.getUserCameras();
          targets = cameras.map(camera => ({
            id: camera.id,
            name: camera.name,
            type: 'camera'
          }));
          break;
        case 'parking':
          const parkings = await parkingService.getUserParkings();
          targets = parkings.map(parking => ({
            id: parking.id,
            name: parking.name,
            type: 'parking'
          }));
          break;
        default:
          break;
      }
      
      setAvailableTargets(targets);
    } catch (error) {
      console.error('Error loading targets:', error);
      setErrors({ targets: 'Error al cargar los objetivos disponibles' });
    } finally {
      setLoadingTargets(false);
    }
  };

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
    
    if (errors[field]) {
      setErrors(prev => ({
        ...prev,
        [field]: null
      }));
    }
  };

  const handleTargetToggle = (targetId) => {
    setSelectedTargets(prev => {
      if (prev.includes(targetId)) {
        return prev.filter(id => id !== targetId);
      } else {
        return [...prev, targetId];
      }
    });
  };

  const handleThresholdChange = (index, data) => {
    const newThresholds = [...thresholds];
    newThresholds[index] = {
      ...newThresholds[index],
      ...data
    };
    setThresholds(newThresholds);
  };

  const validateForm = () => {
    const newErrors = {};

    if (!formData.name.trim()) {
      newErrors.name = 'El nombre es obligatorio';
    }

    if (selectedTargets.length === 0) {
      newErrors.targets = 'Debe seleccionar al menos un objetivo';
    }

    const validThresholds = thresholds.filter(t => t.severity && t.threshold_value);
    if (validThresholds.length === 0) {
      newErrors.thresholds = 'Debe configurar al menos un umbral';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    const submitData = {
      ...formData,
      targets: selectedTargets.map(targetId => ({
        target_type: formData.alarm_type,
        target_id: targetId
      })),
      thresholds: thresholds.filter(t => t.severity && t.threshold_value)
    };

    onSubmit(submitData);
  };

  const getTargetTypeLabel = (type) => {
    return alarmService.getAlarmTypeLabel(type);
  };

  return (
    <Card className="shadow">
      <Card.Header className="d-flex justify-content-between align-items-center">
        <h5 className="mb-0">
          {initialData ? 'Editar' : 'Crear'} Configuración de Alarma
        </h5>
        <Badge bg="primary">
          {getTargetTypeLabel(formData.alarm_type)}
        </Badge>
      </Card.Header>
      
      <Card.Body>
        <Form onSubmit={handleSubmit}>
          <Row>
            <Col md={6}>
              <Form.Group className="mb-3">
                <Form.Label>Nombre de la Alarma *</Form.Label>
                <Form.Control
                  type="text"
                  value={formData.name}
                  onChange={(e) => handleInputChange('name', e.target.value)}
                  placeholder="Ej: Alarma de desconexión de paneles"
                  isInvalid={!!errors.name}
                />
                <Form.Control.Feedback type="invalid">
                  {errors.name}
                </Form.Control.Feedback>
              </Form.Group>
            </Col>
            <Col md={6}>
              <Form.Group className="mb-3">
                <Form.Label>Estado</Form.Label>
                <Form.Select
                  value={formData.status}
                  onChange={(e) => handleInputChange('status', e.target.value)}
                >
                  <option value="active">Activa</option>
                  <option value="paused">Pausada</option>
                </Form.Select>
              </Form.Group>
            </Col>
          </Row>

          <Form.Group className="mb-3">
            <Form.Label>Descripción</Form.Label>
            <Form.Control
              as="textarea"
              rows={3}
              value={formData.description}
              onChange={(e) => handleInputChange('description', e.target.value)}
              placeholder="Descripción opcional de la alarma..."
            />
          </Form.Group>

          <hr />

          <h6>Objetivos a Monitorizar *</h6>
          {loadingTargets ? (
            <Alert variant="info">Cargando objetivos disponibles...</Alert>
          ) : (
            <div className="mb-3">
              {availableTargets.length === 0 ? (
                <Alert variant="warning">
                  No hay {getTargetTypeLabel(formData.alarm_type).toLowerCase()}s disponibles
                </Alert>
              ) : (
                <Row>
                  {availableTargets.map(target => (
                    <Col md={4} key={target.id} className="mb-2">
                      <Form.Check
                        type="checkbox"
                        id={`target-${target.id}`}
                        label={target.name}
                        checked={selectedTargets.includes(target.id)}
                        onChange={() => handleTargetToggle(target.id)}
                      />
                    </Col>
                  ))}
                </Row>
              )}
              {errors.targets && (
                <Alert variant="danger" className="mt-2">
                  {errors.targets}
                </Alert>
              )}
            </div>
          )}

          <hr />

          <h6>Configuración de Umbrales *</h6>
          {thresholds.map((threshold, index) => (
            <div key={index} className="mb-3 p-3 border rounded">
              <h6 className="mb-3">Umbral {index + 1}</h6>
              <AlarmSeveritySelector
                severity={threshold.severity}
                thresholdValue={threshold.threshold_value}
                onChange={(data) => handleThresholdChange(index, data)}
                disabled={loading}
              />
            </div>
          ))}
          {errors.thresholds && (
            <Alert variant="danger">
              {errors.thresholds}
            </Alert>
          )}

          <div className="d-flex justify-content-between mt-4">
            <Button 
              variant="outline-secondary" 
              onClick={onCancel}
              disabled={loading}
            >
              <ArrowLeft className="me-2" />
              Cancelar
            </Button>
            <Button 
              type="submit" 
              variant="primary"
              disabled={loading}
            >
              {loading ? (
                <>
                  <span className="spinner-border spinner-border-sm me-2" />
                  Guardando...
                </>
              ) : (
                <>
                  <Save className="me-2" />
                  {initialData ? 'Actualizar' : 'Crear'} Configuración
                </>
              )}
            </Button>
          </div>
        </Form>
      </Card.Body>
    </Card>
  );
};

export default AlarmConfigurationForm; 