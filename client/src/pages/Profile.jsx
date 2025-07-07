import { useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { useQuery } from 'react-query'
import { authService } from '../services/authService'
import ChangePasswordModal from '../components/ChangePasswordModal'
import UserActivityLog from '../components/UserActivityLog'
import { 
  User, 
  Mail, 
  Calendar, 
  Shield, 
  CheckCircle,
  Clock,
  Key
} from 'lucide-react'
import toast from 'react-hot-toast'

const Profile = () => {
  const { user } = useAuth()
  const [showChangePasswordModal, setShowChangePasswordModal] = useState(false)

  // Obtener permisos del usuario
  const { data: permissions } = useQuery(
    'permissions',
    authService.getPermissions,
    {
      enabled: !!user
    }
  )

  // Obtener parkings del usuario
  const { data: userParkings } = useQuery(
    'userParkings',
    authService.getUserParkings,
    {
      enabled: !!user
    }
  )

  const handlePasswordChangeSuccess = () => {
    toast.success('Contraseña cambiada exitosamente')
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Perfil de Usuario</h1>
        <p className="mt-1 text-sm text-gray-500">
          Gestiona tu información personal y configuración de cuenta
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Información del usuario */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center mb-6">
            <div className="h-16 w-16 rounded-full bg-blue-100 flex items-center justify-center">
              <User className="h-8 w-8 text-blue-600" />
            </div>
            <div className="ml-4">
              <h2 className="text-lg font-medium text-gray-900">{user?.name || 'Sin nombre'}</h2>
              <p className="text-sm text-gray-500">{user?.email}</p>
            </div>
          </div>

          <div className="space-y-4">
            <div className="flex items-center">
              <Mail className="h-5 w-5 text-gray-400 mr-3" />
              <div>
                <p className="text-sm font-medium text-gray-900">Email</p>
                <p className="text-sm text-gray-500">{user?.email}</p>
              </div>
            </div>

            <div className="flex items-center">
              <Calendar className="h-5 w-5 text-gray-400 mr-3" />
              <div>
                <p className="text-sm font-medium text-gray-900">Miembro desde</p>
                <p className="text-sm text-gray-500">
                  {user?.created_at ? new Date(user.created_at).toLocaleDateString('es-ES') : 'N/A'}
                </p>
              </div>
            </div>

            <div className="flex items-center">
              <Shield className="h-5 w-5 text-gray-400 mr-3" />
              <div>
                <p className="text-sm font-medium text-gray-900">Rol</p>
                <p className="text-sm text-gray-500 capitalize">{user?.role || 'Usuario'}</p>
              </div>
            </div>

            <div className="flex items-center">
              <div className="h-5 w-5 text-gray-400 mr-3 flex items-center justify-center">
                <div className={`w-2 h-2 rounded-full ${user?.is_active ? 'bg-green-500' : 'bg-red-500'}`}></div>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-900">Estado</p>
                <p className="text-sm text-gray-500">{user?.is_active ? 'Activo' : 'Inactivo'}</p>
              </div>
            </div>
          </div>

          {/* Botón de cambio de contraseña */}
          <div className="mt-6 pt-6 border-t border-gray-200">
            <button
              onClick={() => setShowChangePasswordModal(true)}
              className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <Key className="h-4 w-4 mr-2" />
              Cambiar Contraseña
            </button>
          </div>
        </div>

        {/* Permisos y recursos */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Permisos de Acceso</h2>
          
          {permissions ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                <div className="flex items-center">
                  <CheckCircle className="h-5 w-5 text-green-600 mr-2" />
                  <span className="text-sm font-medium text-green-900">Parkings</span>
                </div>
                <span className="text-sm text-green-600">
                  {permissions.permissions?.parking_ids?.length || 0} asignados
                </span>
              </div>

              <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
                <div className="flex items-center">
                  <CheckCircle className="h-5 w-5 text-blue-600 mr-2" />
                  <span className="text-sm font-medium text-blue-900">Paneles</span>
                </div>
                <span className="text-sm text-blue-600">
                  {permissions.permissions?.panel_ids?.length || 0} asignados
                </span>
              </div>

              <div className="flex items-center justify-between p-3 bg-purple-50 rounded-lg">
                <div className="flex items-center">
                  <CheckCircle className="h-5 w-5 text-purple-600 mr-2" />
                  <span className="text-sm font-medium text-purple-900">Accesos</span>
                </div>
                <span className="text-sm text-purple-600">
                  {permissions.permissions?.access_ids?.length || 0} asignados
                </span>
              </div>

              {user?.role === 'superadmin' && (
                <div className="flex items-center justify-between p-3 bg-orange-50 rounded-lg">
                  <div className="flex items-center">
                    <Shield className="h-5 w-5 text-orange-600 mr-2" />
                    <span className="text-sm font-medium text-orange-900">Superadmin</span>
                  </div>
                  <span className="text-sm text-orange-600">Acceso completo</span>
                </div>
              )}
            </div>
          ) : (
            <div className="flex items-center justify-center py-8">
              <Clock className="h-8 w-8 text-gray-400" />
              <p className="ml-2 text-sm text-gray-500">Cargando permisos...</p>
            </div>
          )}
        </div>
      </div>

      {/* Parkings asignados */}
      {userParkings && userParkings.parkings && userParkings.parkings.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Parkings Asignados</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {userParkings.parkings.map((parking) => (
              <div key={parking.id} className="border border-gray-200 rounded-lg p-4">
                <h3 className="font-medium text-gray-900 mb-2">{parking.name}</h3>
                <p className="text-sm text-gray-500 mb-2">{parking.address}</p>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Plazas: {parking.total_spaces}</span>
                  <span className="text-gray-600">Ocupadas: {parking.occupied_spaces}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Historial de actividad */}
      <div className="bg-white rounded-lg shadow p-6">
        <UserActivityLog userId={user?.id} />
      </div>

      {/* Modal de cambio de contraseña */}
      <ChangePasswordModal
        isOpen={showChangePasswordModal}
        onClose={() => setShowChangePasswordModal(false)}
        onSuccess={handlePasswordChangeSuccess}
      />
    </div>
  )
}

export default Profile 