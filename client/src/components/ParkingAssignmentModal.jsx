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
      const response = await fetch('/api/parkings')
      const data = await response.json()
      setAllParkings(data || [])
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
      const userParkings = response.user?.parkings || []
      setSelectedParkings(userParkings.map(p => p.id))
    } catch (err) {
      console.error('Error loading user parkings:', err)
      // Si falla la carga, usar los parkings pasados como prop
      if (currentParkings && currentParkings.length > 0) {
        setSelectedParkings(currentParkings)
      }
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

  // Manejar selección de parkings
  const handleParkingToggle = (parkingId) => {
    setSelectedParkings(prev => {
      if (prev.includes(parkingId)) {
        return prev.filter(id => id !== parkingId)
      } else {
        return [...prev, parkingId]
      }
    })
  }

  // Filtrar parkings por búsqueda
  const filteredParkings = allParkings.filter(parking =>
    parking.name.toLowerCase().includes(searchTerm.toLowerCase())
  )

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
        <div className="mt-3">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            Asignar Parkings a {userName}
          </h3>
          
          {error && (
            <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          )}

          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Buscar Parkings
            </label>
            <input
              type="text"
              placeholder="Buscar por nombre..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {loading ? (
            <div className="text-center py-4">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
              <p className="mt-2 text-gray-600">Cargando parkings...</p>
            </div>
          ) : (
            <div className="max-h-64 overflow-y-auto border border-gray-200 rounded-md p-2">
              {filteredParkings.map(parking => (
                <label key={parking.id} className="flex items-center p-2 hover:bg-gray-50 rounded">
                  <input
                    type="checkbox"
                    checked={selectedParkings.includes(parking.id)}
                    onChange={() => handleParkingToggle(parking.id)}
                    className="mr-3 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <div>
                    <div className="text-sm font-medium text-gray-900">
                      {parking.name}
                    </div>
                    <div className="text-xs text-gray-500">
                      {parking.total_plazas} plazas • {parking.estado}
                    </div>
                  </div>
                </label>
              ))}
              
              {filteredParkings.length === 0 && (
                <div className="text-center py-4 text-gray-500">
                  No se encontraron parkings
                </div>
              )}
            </div>
          )}

          <div className="mt-4 text-sm text-gray-600">
            <p>Parkings seleccionados: {selectedParkings.length}</p>
          </div>

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
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {saving ? 'Guardando...' : 'Guardar'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ParkingAssignmentModal 