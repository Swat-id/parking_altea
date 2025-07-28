import React, { useState, useEffect } from 'react';
import { Plus, X, Save, ArrowLeft } from 'lucide-react';
import AlarmSeveritySelector from './AlarmSeveritySelector';
import alarmService from '../services/alarmService';
import panelService from '../services/panelService';
import cameraService from '../services/cameraService';
import parkingService from '../services/parkingService';

const AlarmConfigurationForm = ({ 
  alarmType, 
  configuration = null,
  onSubmit,
  onCancel,
  loading = false,
  setAlarmType
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
    { severity: 'LEVE', threshold_value: '', threshold_type: 'disconnection_time' },
    { severity: 'NORMAL', threshold_value: '', threshold_type: 'disconnection_time' },
    { severity: 'GRAVE', threshold_value: '', threshold_type: 'disconnection_time' }
  ]);
  const [errors, setErrors] = useState({});
  const [loadingTargets, setLoadingTargets] = useState(false);

  useEffect(() => {
    if (configuration) {
      setFormData({
        name: configuration.name || '',
        description: configuration.description || '',
        alarm_type: configuration.alarm_type || alarmType || 'panel',
        status: configuration.status || 'active',
        targets: configuration.targets || [],
        thresholds: configuration.thresholds || []
      });
      
      if (configuration.targets) {
        setSelectedTargets(configuration.targets.map(t => t.target_id));
      }
      
      if (configuration.thresholds) {
        setThresholds(configuration.thresholds);
      }
    } else {
      // Reset form data for new configuration
      setFormData({
        name: '',
        description: '',
        alarm_type: alarmType || 'panel',
        status: 'active',
        targets: [],
        thresholds: []
      });
      setSelectedTargets([]);
      setThresholds([
        { severity: 'LEVE', threshold_value: '', threshold_type: 'disconnection_time' },
        { severity: 'NORMAL', threshold_value: '', threshold_type: 'disconnection_time' },
        { severity: 'GRAVE', threshold_value: '', threshold_type: 'disconnection_time' }
      ]);
    }
    loadAvailableTargets();
  }, [configuration, alarmType, formData.alarm_type]);

  const loadAvailableTargets = async () => {
    setLoadingTargets(true);
    setErrors(prev => ({ ...prev, targets: null }));
    
    try {
      let targets = [];
      
      switch (formData.alarm_type) {
        case 'panel':
          const panels = await panelService.getUserPanels();
          targets = (panels || []).map(panel => ({
            id: panel.id,
            name: panel.name || `Panel ${panel.id}`,
            type: 'panel'
          }));
          break;
        case 'camera':
          const cameras = await cameraService.getUserCameras();
          targets = (cameras || []).map(camera => ({
            id: camera.id,
            name: camera.name || `Cámara ${camera.id}`,
            type: 'camera'
          }));
          break;
        case 'parking':
          const parkings = await parkingService.getUserParkings();
          targets = (parkings || []).map(parking => ({
            id: parking.id,
            name: parking.name || `Parking ${parking.id}`,
            type: 'parking'
          }));
          break;
        default:
          break;
      }
      
      setAvailableTargets(targets);
    } catch (error) {
      console.error('Error loading targets:', error);
      setErrors(prev => ({ ...prev, targets: 'Error al cargar los objetivos disponibles' }));
      setAvailableTargets([]);
    } finally {
      setLoadingTargets(false);
    }
  };

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
    
    if (field === 'alarm_type') {
      setSelectedTargets([]);
      setFormData(prev => ({
        ...prev,
        targets: []
      }));
    }
    
    // Limpiar error del campo
    if (errors[field]) {
      setErrors(prev => ({
        ...prev,
        [field]: null
      }));
    }
  };

  const handleTargetToggle = (targetId) => {
    const newSelected = selectedTargets.includes(targetId)
      ? selectedTargets.filter(id => id !== targetId)
      : [...selectedTargets, targetId];
    
    setSelectedTargets(newSelected);
    setFormData(prev => ({
      ...prev,
      targets: newSelected.map(id => ({ target_id: id }))
    }));
  };

  const handleThresholdChange = (index, data) => {
    const newThresholds = [...thresholds];
    newThresholds[index] = { ...newThresholds[index], ...data };
    setThresholds(newThresholds);
  };

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.name.trim()) {
      newErrors.name = 'El nombre es requerido';
    }
    
    if (!formData.description.trim()) {
      newErrors.description = 'La descripción es requerida';
    }
    
    if (selectedTargets.length === 0) {
      newErrors.targets = 'Debe seleccionar al menos un objetivo';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }
    
    // Determinar el tipo de umbral según el tipo de alarma
    const getThresholdType = (alarmType) => {
      switch (alarmType) {
        case 'panel':
        case 'camera':
          return 'disconnection_time';
        case 'parking':
          return 'occupancy_high';
        default:
          return 'disconnection_time';
      }
    };
    
    const thresholdType = getThresholdType(formData.alarm_type);
    
    const submitData = {
      ...formData,
      targets: selectedTargets, // Array de IDs directamente
      thresholds: thresholds
        .filter(t => t.threshold_value)
        .map(t => ({
          ...t,
          threshold_type: thresholdType
        }))
    };
    
    onSubmit(submitData);
  };

  const getTargetTypeLabel = (type) => {
    const labels = {
      'panel': 'Panel',
      'camera': 'Cámara',
      'parking': 'Aparcamiento'
    };
    return labels[type] || type;
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Tipo de Alarma */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Tipo de Alarma
        </label>
        <select
          value={formData.alarm_type}
          onChange={(e) => handleInputChange('alarm_type', e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="panel">Panel</option>
          <option value="camera">Cámara</option>
          <option value="parking">Aparcamiento</option>
        </select>
      </div>

      {/* Nombre */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Nombre de la Configuración *
        </label>
        <input
          type="text"
          value={formData.name}
          onChange={(e) => handleInputChange('name', e.target.value)}
          className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
            errors.name ? 'border-red-300' : 'border-gray-300'
          }`}
          placeholder="Ej: Panel sin conexión"
        />
        {errors.name && (
          <p className="mt-1 text-sm text-red-600">{errors.name}</p>
        )}
      </div>

      {/* Descripción */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Descripción *
        </label>
        <textarea
          value={formData.description}
          onChange={(e) => handleInputChange('description', e.target.value)}
          rows={3}
          className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
            errors.description ? 'border-red-300' : 'border-gray-300'
          }`}
          placeholder="Describe la configuración de la alarma..."
        />
        {errors.description && (
          <p className="mt-1 text-sm text-red-600">{errors.description}</p>
        )}
      </div>

      {/* Estado */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Estado
        </label>
        <select
          value={formData.status}
          onChange={(e) => handleInputChange('status', e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="active">Activa</option>
          <option value="paused">Pausada</option>
        </select>
      </div>

      {/* Objetivos */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Objetivos a Monitorear *
        </label>
        {loadingTargets ? (
          <div className="text-center py-4">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-2 text-sm text-gray-600">Cargando objetivos...</p>
          </div>
        ) : (
          <div className="space-y-2">
            {availableTargets.length === 0 ? (
              <p className="text-sm text-gray-500">No hay objetivos disponibles para este tipo de alarma</p>
            ) : (
              availableTargets.map(target => (
                <label key={target.id} className="flex items-center space-x-3 p-3 border border-gray-200 rounded-md hover:bg-gray-50">
                  <input
                    type="checkbox"
                    checked={selectedTargets.includes(target.id)}
                    onChange={() => handleTargetToggle(target.id)}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <div>
                    <span className="text-sm font-medium text-gray-900">{target.name}</span>
                    <span className="ml-2 text-xs text-gray-500">({getTargetTypeLabel(target.type)})</span>
                  </div>
                </label>
              ))
            )}
          </div>
        )}
        {errors.targets && (
          <p className="mt-1 text-sm text-red-600">{errors.targets}</p>
        )}
      </div>

      {/* Umbrales */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Umbrales de Alarma
        </label>
        <div className="mb-3 p-3 bg-blue-50 border border-blue-200 rounded-md">
          <p className="text-sm text-blue-800">
            <strong>Información sobre los umbrales:</strong>
          </p>
          <ul className="text-sm text-blue-700 mt-1 space-y-1">
            <li>• <strong>Paneles:</strong> Tiempo de desconexión en <strong>minutos</strong></li>
            <li>• <strong>Cámaras:</strong> Tiempo de desconexión en <strong>minutos</strong></li>
            <li>• <strong>Aparcamientos:</strong> Porcentaje de ocupación (0-100)</li>
          </ul>
        </div>
        <div className="space-y-3">
          {thresholds.map((threshold, index) => (
            <div key={threshold.severity} className="flex items-center space-x-3">
              <div className="w-24">
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                  threshold.severity === 'LEVE' ? 'bg-yellow-100 text-yellow-800' :
                  threshold.severity === 'NORMAL' ? 'bg-blue-100 text-blue-800' :
                  'bg-red-100 text-red-800'
                }`}>
                  {alarmService.getSeverityLabel(threshold.severity)}
                </span>
              </div>
              <div className="flex-1 flex items-center space-x-2">
                <input
                  type="number"
                  min="0"
                  value={threshold.threshold_value}
                  onChange={(e) => handleThresholdChange(index, { threshold_value: e.target.value })}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder={formData.alarm_type === 'parking' ? '0-100' : '0'}
                />
                <span className="text-sm text-gray-500 whitespace-nowrap">
                  {formData.alarm_type === 'parking' ? '%' : 'min'}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Botones */}
      <div className="flex justify-end space-x-3 pt-6 border-t border-gray-200">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          Cancelar
        </button>
        <button
          type="submit"
          disabled={loading}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
        >
          {loading ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              Guardando...
            </>
          ) : (
            <>
              <Save className="h-4 w-4 mr-2" />
              Guardar Configuración
            </>
          )}
        </button>
      </div>
    </form>
  );
};

export default AlarmConfigurationForm; 