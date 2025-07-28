import React from 'react';
import { 
  AlertTriangle, 
  AlertCircle, 
  AlertOctagon,
  Clock,
  CheckCircle,
  XCircle,
  Eye
} from 'lucide-react';
import alarmService from '../services/alarmService';

const AlarmStatusCard = ({ alarm, onResolve, onViewDetails }) => {
  const getSeverityIcon = (severity) => {
    const icons = {
      'LEVE': <AlertTriangle className="text-yellow-500" size={20} />,
      'NORMAL': <AlertCircle className="text-blue-500" size={20} />,
      'GRAVE': <AlertOctagon className="text-red-500" size={20} />
    };
    return icons[severity] || <AlertTriangle className="text-yellow-500" size={20} />;
  };

  const getSeverityColor = (severity) => {
    const colors = {
      'LEVE': 'bg-yellow-100 text-yellow-800',
      'NORMAL': 'bg-blue-100 text-blue-800',
      'GRAVE': 'bg-red-100 text-red-800'
    };
    return colors[severity] || 'bg-gray-100 text-gray-800';
  };

  const getStatusIcon = (status) => {
    const icons = {
      'active': <Clock className="text-red-500" size={16} />,
      'resolved': <CheckCircle className="text-green-500" size={16} />,
      'paused': <XCircle className="text-yellow-500" size={16} />
    };
    return icons[status] || <Clock className="text-gray-500" size={16} />;
  };

  const getStatusColor = (status) => {
    const colors = {
      'active': 'bg-red-100 text-red-800',
      'resolved': 'bg-green-100 text-green-800',
      'paused': 'bg-yellow-100 text-yellow-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
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
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex justify-between items-center">
          <div className="flex items-center space-x-3">
            {getSeverityIcon(alarm.severity)}
            <span className="font-semibold text-gray-900">{alarm.configuration_name}</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getSeverityColor(alarm.severity)}`}>
              {alarmService.getSeverityLabel(alarm.severity)}
            </span>
            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(alarm.status)}`}>
              {getStatusIcon(alarm.status)}
              <span className="ml-1">{alarmService.getStatusLabel(alarm.status)}</span>
            </span>
          </div>
        </div>
      </div>
      
      <div className="px-6 py-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="md:col-span-2 space-y-3">
            <div>
              <p className="text-sm text-gray-600">
                <span className="font-medium text-gray-900">Mensaje:</span> {alarm.message}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600">
                <span className="font-medium text-gray-900">Objetivos afectados:</span> {getAffectedTargetsText(alarm.affected_targets)}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600">
                <span className="font-medium text-gray-900">Tipo:</span> {alarmService.getAlarmTypeLabel(alarm.alarm_type)}
              </p>
            </div>
          </div>
          
          <div className="text-right space-y-2">
            <div>
              <p className="text-xs text-gray-500 font-medium">Creada</p>
              <p className="text-sm text-gray-900">{formatDate(alarm.created_at)}</p>
            </div>
            {alarm.resolved_at && (
              <div>
                <p className="text-xs text-gray-500 font-medium">Resuelta</p>
                <p className="text-sm text-gray-900">{formatDate(alarm.resolved_at)}</p>
              </div>
            )}
          </div>
        </div>
      </div>
      
      <div className="px-6 py-3 bg-gray-50 border-t border-gray-200 rounded-b-lg">
        <div className="flex justify-between items-center">
          <div>
            <p className="text-xs text-gray-500">
              ID: {alarm.id} | Configuración: {alarm.alarm_configuration_id}
            </p>
          </div>
          <div className="flex space-x-2">
            {onViewDetails && (
              <button
                onClick={() => onViewDetails(alarm)}
                className="inline-flex items-center px-3 py-1.5 border border-gray-300 shadow-sm text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                <Eye className="h-3 w-3 mr-1" />
                Ver Detalles
              </button>
            )}
            {alarm.status === 'active' && onResolve && (
              <button
                onClick={() => onResolve(alarm)}
                className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
              >
                <CheckCircle className="h-3 w-3 mr-1" />
                Resolver
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AlarmStatusCard; 