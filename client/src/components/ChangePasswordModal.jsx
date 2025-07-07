import React, { useState } from 'react'
import { authService } from '../services/authService'

const ChangePasswordModal = ({ isOpen, onClose, onSuccess }) => {
  const [formData, setFormData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    // Validaciones
    if (formData.newPassword !== formData.confirmPassword) {
      setError('Las contraseñas nuevas no coinciden')
      return
    }

    if (formData.newPassword.length < 6) {
      setError('La nueva contraseña debe tener al menos 6 caracteres')
      return
    }

    if (formData.currentPassword === formData.newPassword) {
      setError('La nueva contraseña debe ser diferente a la actual')
      return
    }

    try {
      setLoading(true)
      setError(null)
      
      await authService.updatePassword(formData.currentPassword, formData.newPassword)
      
      setSuccess(true)
      setFormData({ currentPassword: '', newPassword: '', confirmPassword: '' })
      
      // Cerrar modal después de 2 segundos
      setTimeout(() => {
        onClose()
        setSuccess(false)
        if (onSuccess) onSuccess()
      }, 2000)
      
    } catch (err) {
      setError('Error al cambiar contraseña: ' + (err.response?.data?.message || err.message))
    } finally {
      setLoading(false)
    }
  }

  const handleClose = () => {
    if (!loading) {
      setFormData({ currentPassword: '', newPassword: '', confirmPassword: '' })
      setError(null)
      setSuccess(false)
      onClose()
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
        <div className="mt-3">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            Cambiar Contraseña
          </h3>
          
          {success ? (
            <div className="text-center">
              <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100 mb-4">
                <svg className="h-6 w-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                ¡Contraseña Cambiada!
              </h3>
              <p className="text-sm text-gray-500">
                Tu contraseña ha sido actualizada exitosamente.
              </p>
            </div>
          ) : (
            <form onSubmit={handleSubmit}>
              {/* Mensaje de error */}
              {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
                  {error}
                </div>
              )}

              {/* Contraseña actual */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Contraseña Actual
                </label>
                <input
                  type="password"
                  value={formData.currentPassword}
                  onChange={(e) => setFormData({...formData, currentPassword: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                  disabled={loading}
                />
              </div>

              {/* Nueva contraseña */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Nueva Contraseña
                </label>
                <input
                  type="password"
                  value={formData.newPassword}
                  onChange={(e) => setFormData({...formData, newPassword: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                  disabled={loading}
                  minLength={6}
                />
                <p className="text-xs text-gray-500 mt-1">
                  Mínimo 6 caracteres
                </p>
              </div>

              {/* Confirmar nueva contraseña */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Confirmar Nueva Contraseña
                </label>
                <input
                  type="password"
                  value={formData.confirmPassword}
                  onChange={(e) => setFormData({...formData, confirmPassword: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                  disabled={loading}
                />
                {formData.confirmPassword && formData.newPassword !== formData.confirmPassword && (
                  <p className="text-xs text-red-500 mt-1">
                    Las contraseñas no coinciden
                  </p>
                )}
              </div>

              {/* Botones */}
              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={handleClose}
                  disabled={loading}
                  className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? (
                    <div className="flex items-center space-x-2">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                      <span>Cambiando...</span>
                    </div>
                  ) : (
                    'Cambiar Contraseña'
                  )}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  )
}

export default ChangePasswordModal 