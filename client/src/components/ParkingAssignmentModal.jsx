import React, { useState, useEffect } from 'react'
import { authService } from '../services/authService'

const ParkingAssignmentModal = ({ 
  isOpen, 
  onClose, 
  userId, 
  userName, 
  currentParkings = [],
  onAssignmentComplete 
}) => {
  const [allParkings, setAllParkings] = useState([])
  const [selectedParkings, setSelectedParkings] = useState([])
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)
  const [searchTerm, setSearchTerm] = useState('')

  // Cargar todos los parkings disponibles
  const loadParkings = async () => {
    try {
      setLoading(true)
      // Usar el endpoint de parkings existente
      const response = await fetch('/api/parkings')
      const data = await response.json()
      setAllParkings(data.parkings || [])
    } catch (err) {
      setError('Error al cargar parkings: ' + err.message)
    } finally {
      setLoading(false)
    }
  }

  // Cargar parkings del usuario
  const loadUserParkings = async () => {
    try {
      const response = await authService.getUserDetails(userId)
      const userParkings = response.parkings || []
      setSelectedParkings(userParkings.map(p => p.id))
    } catch (err) {
      setError('Error al cargar parkings del usuario: ' + err.message)
    }
  }

  useEffect(() => {
    if (isOpen && userId) {
      loadParkings()
      loadUserParkings()
    }
  }, [isOpen, userId])

  // Asignar parkings
  const handleAssignParkings = async () => {
    try {
      setSaving(true)
      setError(null)
      
      await authService.assignUserResources(userId, {
        parking_ids: selectedParkings
      })
      
      onAssignmentComplete()
      onClose()
    } catch (err) {
      setError('Error al asignar parkings: ' + (err.response?.data?.message || err.message))
    } finally {
      setSaving(false)
    }
  }

  // Toggle selección de parking
  const toggleParkingSelection = (parkingId) => {
    setSelectedParkings(prev => 
      prev.includes(parkingId)
        ? prev.filter(id => id !== parkingId)
        : [...prev, parkingId]
    )
  }

  // Seleccionar todos
  const selectAll = () => {
    const filteredParkings = allParkings.filter(parking =>
      parking.name.toLowerCase().includes(searchTerm.toLowerCase())
    )
    setSelectedParkings(filteredParkings.map(p => p.id))
  }

  // Deseleccionar todos
  const deselectAll = () => {
    setSelectedParkings([])
  }

  // Filtrar parkings
  const filteredParkings = allParkings.filter(parking =>
    parking.name.toLowerCase().includes(searchTerm.toLowerCase())
  )

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-10 mx-auto p-5 border w-11/12 max-w-4xl shadow-lg rounded-md bg-white">
        <div className="mt-3">
          {/* Header */}
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-lg font-medium text-gray-900">
              Asignar Parkings - {userName}
            </h3>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Mensaje de error */}
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
              {error}
            </div>
          )}

          {/* Búsqueda y controles */}
          <div className="mb-6">
            <div className="flex flex-col sm:flex-row gap-4">
              <div className="flex-1">
                <input
                  type="text"
                  placeholder="Buscar parkings..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div className="flex gap-2">
                <button
                  onClick={selectAll}
                  className="px-3 py-2 text-sm bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200"
                >
                  Seleccionar Todos
                </button>
                <button
                  onClick={deselectAll}
                  className="px-3 py-2 text-sm bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
                >
                  Deseleccionar Todos
                </button>
              </div>
            </div>
          </div>

          {/* Lista de parkings */}
          <div className="max-h-96 overflow-y-auto border border-gray-200 rounded-md">
            {loading ? (
              <div className="p-8 text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                <p className="mt-2 text-gray-600">Cargando parkings...</p>
              </div>
            ) : filteredParkings.length === 0 ? (
              <div className="p-8 text-center text-gray-500">
                No se encontraron parkings
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 p-4">
                {filteredParkings.map((parking) => (
                  <div
                    key={parking.id}
                    className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                      selectedParkings.includes(parking.id)
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                    onClick={() => toggleParkingSelection(parking.id)}
                  >
                    <div className="flex items-start space-x-3">
                      <input
                        type="checkbox"
                        checked={selectedParkings.includes(parking.id)}
                        onChange={() => toggleParkingSelection(parking.id)}
                        className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      />
                      <div className="flex-1 min-w-0">
                        <h4 className="text-sm font-medium text-gray-900 truncate">
                          {parking.name}
                        </h4>
                        <p className="text-sm text-gray-500 truncate">
                          {parking.address || 'Sin dirección'}
                        </p>
                        <div className="mt-2 flex items-center space-x-4 text-xs text-gray-500">
                          <span>Plazas: {parking.total_spaces || 0}</span>
                          <span>Ocupadas: {parking.occupied_spaces || 0}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Resumen */}
          <div className="mt-4 p-4 bg-gray-50 rounded-md">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">
                {selectedParkings.length} de {allParkings.length} parkings seleccionados
              </span>
              <span className="text-sm font-medium text-gray-900">
                {filteredParkings.length} parkings mostrados
              </span>
            </div>
          </div>

          {/* Acciones */}
          <div className="flex justify-end space-x-3 mt-6">
            <button
              onClick={onClose}
              className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
              disabled={saving}
            >
              Cancelar
            </button>
            <button
              onClick={handleAssignParkings}
              disabled={saving}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {saving ? (
                <div className="flex items-center space-x-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  <span>Guardando...</span>
                </div>
              ) : (
                'Guardar Asignación'
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ParkingAssignmentModal 