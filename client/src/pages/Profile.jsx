import { useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { useQuery } from 'react-query'
import { authService } from '../services/authService'
import { 
  User, 
  Mail, 
  Calendar, 
  Shield, 
  Eye, 
  EyeOff,
  Save,
  CheckCircle,
  AlertCircle,
  Clock
} from 'lucide-react'
import toast from 'react-hot-toast'

const Profile = () => {
  const { user, updatePassword } = useAuth()
  const [showCurrentPassword, setShowCurrentPassword] = useState(false)
  const [showNewPassword, setShowNewPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [isChangingPassword, setIsChangingPassword] = useState(false)
  
  const [passwordForm, setPasswordForm] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  })

  // Obtener permisos del usuario
  const { data: permissions } = useQuery(
    'permissions',
    authService.getPermissions,
    {
      enabled: !!user
    }
  )

  const handlePasswordChange = async (e) => {
    e.preventDefault()
    
    if (passwordForm.newPassword !== passwordForm.confirmPassword) {
      toast.error('Las contraseñas no coinciden')
      return
    }

    if (passwordForm.newPassword.length < 8) {
      toast.error('La nueva contraseña debe tener al menos 8 caracteres')
      return
    }

    setIsChangingPassword(true)
    
    try {
      const result = await updatePassword(passwordForm.currentPassword, passwordForm.newPassword)
      if (result.success) {
        setPasswordForm({
          currentPassword: '',
          newPassword: '',
          confirmPassword: ''
        })
      }
    } catch (error) {
      console.error('Error changing password:', error)
    } finally {
      setIsChangingPassword(false)
    }
  }

  const getPasswordStrength = (password) => {
    if (!password) return { strength: 0, color: 'bg-gray-200', text: '' }
    
    let strength = 0
    if (password.length >= 8) strength++
    if (/[a-z]/.test(password)) strength++
    if (/[A-Z]/.test(password)) strength++
    if (/[0-9]/.test(password)) strength++
    if (/[^A-Za-z0-9]/.test(password)) strength++

    switch (strength) {
      case 0:
      case 1:
        return { strength, color: 'bg-red-500', text: 'Muy débil' }
      case 2:
        return { strength, color: 'bg-orange-500', text: 'Débil' }
      case 3:
        return { strength, color: 'bg-yellow-500', text: 'Media' }
      case 4:
        return { strength, color: 'bg-blue-500', text: 'Fuerte' }
      case 5:
        return { strength, color: 'bg-green-500', text: 'Muy fuerte' }
      default:
        return { strength, color: 'bg-gray-200', text: '' }
    }
  }

  const passwordStrength = getPasswordStrength(passwordForm.newPassword)

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
        <div className="card">
          <div className="flex items-center mb-6">
            <div className="h-16 w-16 rounded-full bg-primary-100 flex items-center justify-center">
              <User className="h-8 w-8 text-primary-600" />
            </div>
            <div className="ml-4">
              <h2 className="text-lg font-medium text-gray-900">{user?.name}</h2>
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
                <p className="text-sm text-gray-500">Administrador</p>
              </div>
            </div>
          </div>
        </div>

        {/* Permisos */}
        <div className="card">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Permisos de Acceso</h2>
          
          {permissions ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                <div className="flex items-center">
                  <CheckCircle className="h-5 w-5 text-green-600 mr-2" />
                  <span className="text-sm font-medium text-green-900">Parkings</span>
                </div>
                <span className="text-sm text-green-600">{permissions.parkings || 0} asignados</span>
              </div>

              <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
                <div className="flex items-center">
                  <CheckCircle className="h-5 w-5 text-blue-600 mr-2" />
                  <span className="text-sm font-medium text-blue-900">Paneles</span>
                </div>
                <span className="text-sm text-blue-600">{permissions.panels || 0} asignados</span>
              </div>

              <div className="flex items-center justify-between p-3 bg-purple-50 rounded-lg">
                <div className="flex items-center">
                  <CheckCircle className="h-5 w-5 text-purple-600 mr-2" />
                  <span className="text-sm font-medium text-purple-900">Cámaras</span>
                </div>
                <span className="text-sm text-purple-600">{permissions.cameras || 0} asignadas</span>
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-center py-8">
              <Clock className="h-8 w-8 text-gray-400" />
              <p className="ml-2 text-sm text-gray-500">Cargando permisos...</p>
            </div>
          )}
        </div>
      </div>

      {/* Cambio de contraseña */}
      <div className="card">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Cambiar Contraseña</h2>
        
        <form onSubmit={handlePasswordChange} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Contraseña Actual
            </label>
            <div className="relative">
              <input
                type={showCurrentPassword ? 'text' : 'password'}
                value={passwordForm.currentPassword}
                onChange={(e) => setPasswordForm({
                  ...passwordForm,
                  currentPassword: e.target.value
                })}
                className="input-field pr-10"
                required
              />
              <button
                type="button"
                onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                className="absolute inset-y-0 right-0 pr-3 flex items-center"
              >
                {showCurrentPassword ? (
                  <EyeOff className="h-5 w-5 text-gray-400" />
                ) : (
                  <Eye className="h-5 w-5 text-gray-400" />
                )}
              </button>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Nueva Contraseña
            </label>
            <div className="relative">
              <input
                type={showNewPassword ? 'text' : 'password'}
                value={passwordForm.newPassword}
                onChange={(e) => setPasswordForm({
                  ...passwordForm,
                  newPassword: e.target.value
                })}
                className="input-field pr-10"
                required
              />
              <button
                type="button"
                onClick={() => setShowNewPassword(!showNewPassword)}
                className="absolute inset-y-0 right-0 pr-3 flex items-center"
              >
                {showNewPassword ? (
                  <EyeOff className="h-5 w-5 text-gray-400" />
                ) : (
                  <Eye className="h-5 w-5 text-gray-400" />
                )}
              </button>
            </div>
            
            {/* Indicador de fortaleza de contraseña */}
            {passwordForm.newPassword && (
              <div className="mt-2">
                <div className="flex items-center justify-between text-xs text-gray-500 mb-1">
                  <span>Fortaleza de la contraseña</span>
                  <span className={passwordStrength.text === 'Muy fuerte' ? 'text-green-600' : 
                                  passwordStrength.text === 'Fuerte' ? 'text-blue-600' :
                                  passwordStrength.text === 'Media' ? 'text-yellow-600' :
                                  passwordStrength.text === 'Débil' ? 'text-orange-600' : 'text-red-600'}>
                    {passwordStrength.text}
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full transition-all duration-300 ${passwordStrength.color}`}
                    style={{ width: `${(passwordStrength.strength / 5) * 100}%` }}
                  />
                </div>
              </div>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Confirmar Nueva Contraseña
            </label>
            <div className="relative">
              <input
                type={showConfirmPassword ? 'text' : 'password'}
                value={passwordForm.confirmPassword}
                onChange={(e) => setPasswordForm({
                  ...passwordForm,
                  confirmPassword: e.target.value
                })}
                className={`input-field pr-10 ${
                  passwordForm.confirmPassword && passwordForm.newPassword !== passwordForm.confirmPassword
                    ? 'border-red-300 focus:border-red-500 focus:ring-red-500'
                    : ''
                }`}
                required
              />
              <button
                type="button"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                className="absolute inset-y-0 right-0 pr-3 flex items-center"
              >
                {showConfirmPassword ? (
                  <EyeOff className="h-5 w-5 text-gray-400" />
                ) : (
                  <Eye className="h-5 w-5 text-gray-400" />
                )}
              </button>
            </div>
            
            {passwordForm.confirmPassword && passwordForm.newPassword !== passwordForm.confirmPassword && (
              <p className="mt-1 text-sm text-red-600">
                Las contraseñas no coinciden
              </p>
            )}
          </div>

          <div className="flex space-x-3 pt-4">
            <button
              type="submit"
              disabled={isChangingPassword || passwordForm.newPassword !== passwordForm.confirmPassword}
              className="btn-primary flex items-center"
            >
              <Save className="h-4 w-4 mr-2" />
              {isChangingPassword ? 'Cambiando...' : 'Cambiar Contraseña'}
            </button>
            <button
              type="button"
              onClick={() => setPasswordForm({
                currentPassword: '',
                newPassword: '',
                confirmPassword: ''
              })}
              className="btn-secondary"
            >
              Cancelar
            </button>
          </div>
        </form>
      </div>

      {/* Información de seguridad */}
      <div className="card">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Información de Seguridad</h2>
        
        <div className="space-y-4">
          <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <div className="flex items-center">
              <Shield className="h-5 w-5 text-gray-400 mr-3" />
              <div>
                <p className="text-sm font-medium text-gray-900">Autenticación JWT</p>
                <p className="text-sm text-gray-500">Tokens seguros con expiración de 24 horas</p>
              </div>
            </div>
            <CheckCircle className="h-5 w-5 text-green-600" />
          </div>

          <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <div className="flex items-center">
              <AlertCircle className="h-5 w-5 text-gray-400 mr-3" />
              <div>
                <p className="text-sm font-medium text-gray-900">Control de Acceso</p>
                <p className="text-sm text-gray-500">Permisos granulares por recursos</p>
              </div>
            </div>
            <CheckCircle className="h-5 w-5 text-green-600" />
          </div>

          <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <div className="flex items-center">
              <Clock className="h-5 w-5 text-gray-400 mr-3" />
              <div>
                <p className="text-sm font-medium text-gray-900">Sesión Activa</p>
                <p className="text-sm text-gray-500">Última actividad: {new Date().toLocaleString('es-ES')}</p>
              </div>
            </div>
            <CheckCircle className="h-5 w-5 text-green-600" />
          </div>
        </div>
      </div>
    </div>
  )
}

export default Profile 