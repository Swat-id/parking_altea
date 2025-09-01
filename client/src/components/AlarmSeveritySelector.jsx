import React from 'react';

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
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div className="mb-3">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Nivel de Severidad
        </label>
        <select
          value={severity || ''}
          onChange={handleSeverityChange}
          disabled={disabled}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
        >
          <option value="">Seleccionar severidad...</option>
          <option value="LEVE">LEVE</option>
          <option value="NORMAL">NORMAL</option>
          <option value="GRAVE">GRAVE</option>
        </select>
        {severity && (
          <p className="mt-1 text-sm text-gray-500">
            {getSeverityDescription(severity)}
          </p>
        )}
      </div>
      <div className="mb-3">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          {getThresholdLabel(severity)}
        </label>
        <input
          type="number"
          min="1"
          max="1440"
          value={thresholdValue || ''}
          onChange={handleThresholdChange}
          placeholder="Ej: 5"
          disabled={disabled || !severity}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
        />
        <p className="mt-1 text-sm text-gray-500">
          Tiempo en minutos antes de generar la alarma
        </p>
      </div>
    </div>
  );
};

export default AlarmSeveritySelector; 