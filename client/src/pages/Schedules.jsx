import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import { 
  Calendar, 
  Clock, 
  MessageSquare, 
  Settings, 
  Plus, 
  Edit, 
  Trash2, 
  Play, 
  Pause, 
  Eye,
  EyeOff,
  CheckCircle,
  XCircle,
  AlertCircle,
  CalendarDays,
  Palette,
  Type,
  Zap,
  Filter,
  Search,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  PlayCircle
} from 'lucide-react'
import toast from 'react-hot-toast'
import api from '../services/api'

const API_BASE_URL = 'http://157.180.91.63:5789'

const Schedules = () => {
  const queryClient = useQueryClient()
  const [showForm, setShowForm] = useState(false)
  const [editingSchedule, setEditingSchedule] = useState(null)
  const [selectedParking, setSelectedParking] = useState('')
  const [filterActive, setFilterActive] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [expandedSchedule, setExpandedSchedule] = useState(null)

  // Form state
  const [formData, setFormData] = useState({
    parking_id: '',
    name: '',
    description: '',
    start_date: '',
    end_date: '',
    start_time: '',
    end_time: '',
    monday: false,
    tuesday: false,
    wednesday: false,
    thursday: false,
    friday: false,
    saturday: false,
    sunday: false,
    message: '',
    color: 2,
    font_size: 2,
    effect: 'static',
    priority: 1,
    is_active: true
  })

  // Obtener parkings
  const { data: parkings = [] } = useQuery(
    'parkings',
    () => fetch(`${API_BASE_URL}/api/parkings`).then(res => res.json())
  )

  // Obtener programaciones
  const { data: schedulesData = { schedules: [] }, isLoading, refetch } = useQuery(
    ['schedules', selectedParking, filterActive],
    () => {
      const params = new URLSearchParams()
      if (selectedParking) params.append('parking_id', selectedParking)
      if (filterActive !== null) params.append('active_only', filterActive.toString())
      return fetch(`${API_BASE_URL}/api/schedules?${params}`).then(res => res.json())
    },
    {
      refetchInterval: 30000, // Refrescar cada 30 segundos
    }
  )

  // Mutaciones
  const createScheduleMutation = useMutation(
    (data) => fetch(`${API_BASE_URL}/api/schedules`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(res => res.json()),
    {
      onSuccess: (data) => {
        if (data.success) {
          toast.success('Programación creada exitosamente')
          setShowForm(false)
          resetForm()
          queryClient.invalidateQueries('schedules')
        } else {
          toast.error(data.error || 'Error al crear la programación')
        }
      },
      onError: () => {
        toast.error('Error al crear la programación')
      }
    }
  )

  const updateScheduleMutation = useMutation(
    ({ id, data }) => fetch(`${API_BASE_URL}/api/schedules/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(res => res.json()),
    {
      onSuccess: (data) => {
        if (data.success) {
          let message = 'Programación actualizada exitosamente'
          
          if (data.auto_executed) {
            message += ` y ejecutada automáticamente (${data.panels_affected} paneles afectados)`
          } else if (data.execution_error) {
            message += ', pero falló la ejecución automática'
          }
          
          toast.success(message)
          setShowForm(false)
          setEditingSchedule(null)
          resetForm()
          queryClient.invalidateQueries('schedules')
        } else {
          toast.error(data.error || 'Error al actualizar la programación')
        }
      },
      onError: () => {
        toast.error('Error al actualizar la programación')
      }
    }
  )

  const deleteScheduleMutation = useMutation(
    (id) => fetch(`${API_BASE_URL}/api/schedules/${id}`, { method: 'DELETE' }).then(res => res.json()),
    {
      onSuccess: (data) => {
        if (data.success) {
          toast.success('Programación eliminada exitosamente')
          queryClient.invalidateQueries('schedules')
        } else {
          toast.error(data.error || 'Error al eliminar la programación')
        }
      },
      onError: () => {
        toast.error('Error al eliminar la programación')
      }
    }
  )

  const toggleScheduleMutation = useMutation(
    (id) => fetch(`${API_BASE_URL}/api/schedules/${id}/toggle`, { method: 'POST' }).then(res => res.json()),
    {
      onSuccess: (data) => {
        if (data.success) {
          const status = data.is_active ? 'activada' : 'desactivada'
          toast.success(`Programación ${status} exitosamente`)
          queryClient.invalidateQueries('schedules')
        } else {
          toast.error(data.error || 'Error al cambiar el estado de la programación')
        }
      },
      onError: () => {
        toast.error('Error al cambiar el estado de la programación')
      }
    }
  )

  const executeScheduleMutation = useMutation(
    (id) => api.post(`/schedules/${id}/execute`).then(res => res.data),
    {
      onSuccess: (data) => {
        if (data.success) {
          toast.success(`Programación ejecutada exitosamente (${data.panels_affected} paneles afectados)`)
        } else {
          toast.error(data.error || 'Error al ejecutar la programación')
        }
      },
      onError: () => {
        toast.error('Error al ejecutar la programación')
      }
    }
  )

  const executeAllSchedulesMutation = useMutation(
    () => api.post('/schedules/execute-all').then(res => res.data),
    {
      onSuccess: (data) => {
        if (data.success) {
          const message = data.schedules_executed > 0 
            ? `${data.schedules_executed} programaciones ejecutadas exitosamente (${data.total_panels_affected} paneles afectados)`
            : data.message || 'No hay programaciones activas para ejecutar'
          
          if (data.schedules_failed > 0) {
            toast.success(`${message}. ${data.schedules_failed} programaciones fallaron.`)
          } else {
            toast.success(message)
          }
        } else {
          toast.error(data.error || 'Error al ejecutar las programaciones')
        }
      },
      onError: () => {
        toast.error('Error al ejecutar las programaciones')
      }
    }
  )

  // Funciones auxiliares
  const resetForm = () => {
    setFormData({
      parking_id: '',
      name: '',
      description: '',
      start_date: '',
      end_date: '',
      start_time: '',
      end_time: '',
      monday: false,
      tuesday: false,
      wednesday: false,
      thursday: false,
      friday: false,
      saturday: false,
      sunday: false,
      message: '',
      color: 2,
      font_size: 2,
      effect: 'static',
      priority: 1,
      is_active: true
    })
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    
    if (editingSchedule) {
      updateScheduleMutation.mutate({ id: editingSchedule.id, data: formData })
    } else {
      createScheduleMutation.mutate(formData)
    }
  }

  const handleEdit = (schedule) => {
    setEditingSchedule(schedule)
    setFormData({
      parking_id: schedule.parking_id,
      name: schedule.name,
      description: schedule.description || '',
      start_date: schedule.start_date.split('T')[0],
      end_date: schedule.end_date.split('T')[0],
      start_time: schedule.start_time,
      end_time: schedule.end_time,
      monday: schedule.monday,
      tuesday: schedule.tuesday,
      wednesday: schedule.wednesday,
      thursday: schedule.thursday,
      friday: schedule.friday,
      saturday: schedule.saturday,
      sunday: schedule.sunday,
      message: schedule.message,
      color: schedule.color,
      font_size: schedule.font_size,
      effect: schedule.effect,
      priority: schedule.priority,
      is_active: schedule.is_active
    })
    setShowForm(true)
  }

  const handleDelete = (id) => {
    if (window.confirm('¿Estás seguro de que quieres eliminar esta programación?')) {
      deleteScheduleMutation.mutate(id)
    }
  }

  const handleToggle = (id) => {
    toggleScheduleMutation.mutate(id)
  }

  const handleExecute = (id) => {
    executeScheduleMutation.mutate(id)
  }

  const handleExecuteAll = () => {
    if (window.confirm('¿Estás seguro de que quieres ejecutar todas las programaciones activas?')) {
      executeAllSchedulesMutation.mutate()
    }
  }

  const getColorName = (colorCode) => {
    const colors = {
      1: 'Rojo',
      2: 'Verde', 
      3: 'Amarillo',
      4: 'Azul',
      5: 'Magenta',
      6: 'Cian',
      7: 'Blanco'
    }
    return colors[colorCode] || 'Verde'
  }

  const getEffectName = (effect) => {
    const effects = {
      'static': 'Estático',
      'scroll_left': 'Desplazamiento izquierda',
      'scroll_right': 'Desplazamiento derecha',
      'center': 'Centrado'
    }
    return effects[effect] || 'Estático'
  }

  const getPriorityName = (priority) => {
    const priorities = {
      1: 'Baja',
      2: 'Media-Baja',
      3: 'Media',
      4: 'Media-Alta',
      5: 'Alta'
    }
    return priorities[priority] || 'Baja'
  }

  const getWeekdays = (schedule) => {
    const days = []
    if (schedule.monday) days.push('Lun')
    if (schedule.tuesday) days.push('Mar')
    if (schedule.wednesday) days.push('Mié')
    if (schedule.thursday) days.push('Jue')
    if (schedule.friday) days.push('Vie')
    if (schedule.saturday) days.push('Sáb')
    if (schedule.sunday) days.push('Dom')
    return days.join(', ')
  }

  // Filtrar programaciones
  const filteredSchedules = schedulesData.schedules.filter(schedule => {
    const matchesSearch = schedule.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         schedule.message.toLowerCase().includes(searchTerm.toLowerCase())
    return matchesSearch
  })

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Programaciones de Paneles</h1>
          <p className="text-gray-600 mt-2">Gestiona las programaciones automáticas de los paneles electrónicos</p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={handleExecuteAll}
            disabled={executeAllSchedulesMutation.isLoading}
            className="bg-green-600 hover:bg-green-700 disabled:bg-green-400 text-white px-4 py-2 rounded-lg flex items-center gap-2"
          >
            <PlayCircle className="h-5 w-5" />
            {executeAllSchedulesMutation.isLoading ? 'Ejecutando...' : 'Ejecutar Todas las Programaciones'}
          </button>
          <button
            onClick={() => {
              setShowForm(true)
              setEditingSchedule(null)
              resetForm()
            }}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center gap-2"
          >
            <Plus className="h-5 w-5" />
            Nueva Programación
          </button>
        </div>
      </div>

      {/* Filtros */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Parking</label>
            <select
              value={selectedParking}
              onChange={(e) => setSelectedParking(e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Todos los parkings</option>
              {parkings.map(parking => (
                <option key={parking.id} value={parking.id}>{parking.name}</option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Estado</label>
            <select
              value={filterActive}
              onChange={(e) => setFilterActive(e.target.value === 'true')}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value={true}>Solo activas</option>
              <option value={false}>Solo inactivas</option>
              <option value={null}>Todas</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Buscar</label>
            <div className="relative">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Buscar por nombre o mensaje..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
          
          <div className="flex items-end">
            <button
              onClick={() => refetch()}
              className="w-full bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2 rounded-md flex items-center justify-center gap-2"
            >
              <RefreshCw className="h-4 w-4" />
              Actualizar
            </button>
          </div>
        </div>
      </div>

      {/* Lista de programaciones */}
      <div className="bg-white rounded-lg shadow-md">
        {isLoading ? (
          <div className="p-8 text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-2 text-gray-600">Cargando programaciones...</p>
          </div>
        ) : filteredSchedules.length === 0 ? (
          <div className="p-8 text-center">
            <Calendar className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600">No se encontraron programaciones</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {filteredSchedules.map(schedule => (
              <div key={schedule.id} className="p-6">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-lg font-semibold text-gray-900">{schedule.name}</h3>
                      <div className="flex items-center gap-2">
                        <div className={`w-3 h-3 rounded-full ${
                          schedule.is_active ? 'bg-green-500' : 'bg-gray-400'
                        }`}></div>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          schedule.is_active 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-gray-100 text-gray-800'
                        }`}>
                          {schedule.is_active ? '🟢 Activa' : '⚫ Inactiva'}
                        </span>
                      </div>
                      <span className="px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        Prioridad: {getPriorityName(schedule.priority)}
                      </span>
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-gray-600">
                      <div>
                        <span className="font-medium">Parking:</span> {parkings.find(p => p.id === schedule.parking_id)?.name || 'N/A'}
                      </div>
                      <div>
                        <span className="font-medium">Horario:</span> {schedule.start_time} - {schedule.end_time}
                      </div>
                      <div>
                        <span className="font-medium">Días:</span> {getWeekdays(schedule)}
                      </div>
                    </div>
                    
                    <div className="mt-2 text-sm text-gray-600">
                      <span className="font-medium">Mensaje:</span> {schedule.message}
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setExpandedSchedule(expandedSchedule === schedule.id ? null : schedule.id)}
                      className="p-2 text-gray-400 hover:text-gray-600"
                    >
                      {expandedSchedule === schedule.id ? <ChevronUp className="h-5 w-5" /> : <ChevronDown className="h-5 w-5" />}
                    </button>
                    
                    <button
                      onClick={() => handleExecute(schedule.id)}
                      className="p-2 text-blue-600 hover:text-blue-800"
                      title="Ejecutar ahora"
                    >
                      <Play className="h-5 w-5" />
                    </button>
                    
                    <button
                      onClick={() => handleToggle(schedule.id)}
                      className={`p-2 ${
                        schedule.is_active 
                          ? 'text-green-600 hover:text-green-800 bg-green-50' 
                          : 'text-gray-600 hover:text-gray-800 bg-gray-50'
                      } rounded-md`}
                      title={schedule.is_active ? 'Desactivar' : 'Activar'}
                    >
                      {schedule.is_active ? <Pause className="h-5 w-5" /> : <Play className="h-5 w-5" />}
                    </button>
                    
                    <button
                      onClick={() => handleEdit(schedule)}
                      className="p-2 text-green-600 hover:text-green-800"
                      title="Editar"
                    >
                      <Edit className="h-5 w-5" />
                    </button>
                    
                    <button
                      onClick={() => handleDelete(schedule.id)}
                      className="p-2 text-red-600 hover:text-red-800"
                      title="Eliminar"
                    >
                      <Trash2 className="h-5 w-5" />
                    </button>
                  </div>
                </div>
                
                {/* Detalles expandidos */}
                {expandedSchedule === schedule.id && (
                  <div className="mt-4 pt-4 border-t border-gray-200">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="font-medium">Descripción:</span> {schedule.description || 'Sin descripción'}
                      </div>
                      <div>
                        <span className="font-medium">Período:</span> {schedule.start_date.split('T')[0]} - {schedule.end_date.split('T')[0]}
                      </div>
                      <div>
                        <span className="font-medium">Color:</span> {getColorName(schedule.color)}
                      </div>
                      <div>
                        <span className="font-medium">Tamaño fuente:</span> {schedule.font_size}
                      </div>
                      <div>
                        <span className="font-medium">Efecto:</span> {getEffectName(schedule.effect)}
                      </div>
                      <div>
                        <span className="font-medium">Creada:</span> {new Date(schedule.created_at).toLocaleString()}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Modal de formulario */}
      {showForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-xl font-semibold text-gray-900">
                {editingSchedule ? 'Editar Programación' : 'Nueva Programación'}
              </h2>
            </div>
            
            <form onSubmit={handleSubmit} className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Información básica */}
                <div className="md:col-span-2">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Información Básica</h3>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Parking *</label>
                  <select
                    required
                    value={formData.parking_id}
                    onChange={(e) => setFormData({...formData, parking_id: e.target.value})}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">Seleccionar parking</option>
                    {parkings.map(parking => (
                      <option key={parking.id} value={parking.id}>{parking.name}</option>
                    ))}
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Nombre *</label>
                  <input
                    type="text"
                    required
                    value={formData.name}
                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Nombre de la programación"
                  />
                </div>
                
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-2">Descripción</label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData({...formData, description: e.target.value})}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    rows="3"
                    placeholder="Descripción opcional"
                  />
                </div>
                
                {/* Fechas y horarios */}
                <div className="md:col-span-2">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Fechas y Horarios</h3>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Fecha de inicio *</label>
                  <input
                    type="date"
                    required
                    value={formData.start_date}
                    onChange={(e) => setFormData({...formData, start_date: e.target.value})}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Fecha de fin *</label>
                  <input
                    type="date"
                    required
                    value={formData.end_date}
                    onChange={(e) => setFormData({...formData, end_date: e.target.value})}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Hora de inicio *</label>
                  <input
                    type="time"
                    required
                    value={formData.start_time}
                    onChange={(e) => setFormData({...formData, start_time: e.target.value})}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Hora de fin *</label>
                  <input
                    type="time"
                    required
                    value={formData.end_time}
                    onChange={(e) => setFormData({...formData, end_time: e.target.value})}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                
                {/* Días de la semana */}
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-2">Días de la semana</label>
                  <div className="grid grid-cols-7 gap-2">
                    {[
                      { key: 'monday', label: 'Lun' },
                      { key: 'tuesday', label: 'Mar' },
                      { key: 'wednesday', label: 'Mié' },
                      { key: 'thursday', label: 'Jue' },
                      { key: 'friday', label: 'Vie' },
                      { key: 'saturday', label: 'Sáb' },
                      { key: 'sunday', label: 'Dom' }
                    ].map(day => (
                      <label key={day.key} className="flex items-center justify-center p-2 border border-gray-300 rounded-md cursor-pointer hover:bg-gray-50">
                        <input
                          type="checkbox"
                          checked={formData[day.key]}
                          onChange={(e) => setFormData({...formData, [day.key]: e.target.checked})}
                          className="mr-2"
                        />
                        {day.label}
                      </label>
                    ))}
                  </div>
                </div>
                
                {/* Configuración del mensaje */}
                <div className="md:col-span-2">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Configuración del Mensaje</h3>
                </div>
                
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-2">Mensaje *</label>
                  <textarea
                    required
                    value={formData.message}
                    onChange={(e) => setFormData({...formData, message: e.target.value})}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    rows="3"
                    placeholder="Texto a mostrar en los paneles"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Color</label>
                  <select
                    value={formData.color}
                    onChange={(e) => setFormData({...formData, color: parseInt(e.target.value)})}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value={1}>Rojo</option>
                    <option value={2}>Verde</option>
                    <option value={3}>Amarillo</option>
                    <option value={4}>Azul</option>
                    <option value={5}>Magenta</option>
                    <option value={6}>Cian</option>
                    <option value={7}>Blanco</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Tamaño de fuente</label>
                  <select
                    value={formData.font_size}
                    onChange={(e) => setFormData({...formData, font_size: parseInt(e.target.value)})}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value={1}>Pequeño</option>
                    <option value={2}>Mediano</option>
                    <option value={3}>Grande</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Efecto</label>
                  <select
                    value={formData.effect}
                    onChange={(e) => setFormData({...formData, effect: e.target.value})}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="static">Estático</option>
                    <option value="scroll_left">Desplazamiento izquierda</option>
                    <option value="scroll_right">Desplazamiento derecha</option>
                    <option value="center">Centrado</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Prioridad</label>
                  <select
                    value={formData.priority}
                    onChange={(e) => setFormData({...formData, priority: parseInt(e.target.value)})}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value={1}>Baja</option>
                    <option value={2}>Media-Baja</option>
                    <option value={3}>Media</option>
                    <option value={4}>Media-Alta</option>
                    <option value={5}>Alta</option>
                  </select>
                </div>
                
                <div className="md:col-span-2">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={formData.is_active}
                      onChange={(e) => setFormData({...formData, is_active: e.target.checked})}
                      className="mr-2"
                    />
                    <span className="text-sm font-medium text-gray-700">Programación activa</span>
                  </label>
                </div>
              </div>
              
              <div className="flex justify-end gap-4 mt-6 pt-6 border-t border-gray-200">
                <button
                  type="button"
                  onClick={() => {
                    setShowForm(false)
                    setEditingSchedule(null)
                    resetForm()
                  }}
                  className="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={createScheduleMutation.isLoading || updateScheduleMutation.isLoading}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md disabled:opacity-50"
                >
                  {createScheduleMutation.isLoading || updateScheduleMutation.isLoading ? 'Guardando...' : 'Guardar'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default Schedules 