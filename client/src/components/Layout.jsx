import React, { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { 
  Home, 
  Car, 
  Monitor, 
  BarChart3, 
  User, 
  Menu, 
  X,
  Building2,
  Camera,
  Calendar,
  ShieldCheck,
  Users,
  LogOut
} from 'lucide-react'

const Layout = ({ children }) => {
  const { user, isSuperadmin, logout } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  // Navegación base
  const navigation = [
    { name: 'Dashboard', href: '/dashboard', current: location.pathname === '/dashboard', icon: Home },
    { name: 'Parkings', href: '/parkings', current: location.pathname === '/parkings', icon: Car },
    { name: 'Paneles', href: '/panels', current: location.pathname === '/panels', icon: Monitor },
    { name: 'Programaciones', href: '/schedules', current: location.pathname === '/schedules', icon: Calendar },
    { name: 'Estadísticas', href: '/statistics', current: location.pathname === '/statistics', icon: BarChart3 },
    { name: 'Camera Logs', href: '/camera-logs', current: location.pathname === '/camera-logs', icon: Camera },
    { name: 'Perfil', href: '/profile', current: location.pathname === '/profile', icon: User },
  ]

  // Opciones de administración solo para superadmin
  const adminNavigation = [
    { name: 'Dashboard Admin', href: '/admin', current: location.pathname === '/admin', icon: ShieldCheck },
    { name: 'Gestión Usuarios', href: '/admin/users', current: location.pathname === '/admin/users', icon: Users },
  ]

  // Combinar navegación según rol
  const fullNavigation = isSuperadmin
    ? [...navigation.slice(0, 1), ...adminNavigation, ...navigation.slice(1)]
    : navigation

  return (
    <div className="min-h-screen bg-gray-100">
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex">
              <div className="flex-shrink-0 flex items-center">
                <h1 className="text-xl font-semibold text-gray-900">
                  Parking Altea
                </h1>
              </div>
              <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
                {fullNavigation.map((item) => (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={`${
                      item.current
                        ? 'border-indigo-500 text-gray-900'
                        : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                    } whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm transition-colors duration-200`}
                  >
                    {item.icon && <item.icon className="inline-block h-4 w-4 mr-1 align-text-bottom" />}
                    {item.name}
                  </Link>
                ))}
              </div>
            </div>
            {/* Usuario en desktop */}
            <div className="hidden sm:ml-6 sm:flex sm:items-center">
              <div className="ml-3 relative">
                <div className="flex items-center space-x-4">
                  <span className="text-sm text-gray-700">
                    {user?.name}
                  </span>
                  <span className="text-xs text-gray-400">{user?.role}</span>
                  <button
                    onClick={handleLogout}
                    className="flex items-center px-3 py-1 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-md transition-colors"
                  >
                    <LogOut className="h-4 w-4 mr-1" />
                    Cerrar Sesión
                  </button>
                </div>
              </div>
            </div>
            {/* Botón menú móvil */}
            <div className="flex items-center sm:hidden">
              <button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-indigo-500"
              >
                {mobileMenuOpen ? (
                  <X className="h-6 w-6" />
                ) : (
                  <Menu className="h-6 w-6" />
                )}
              </button>
            </div>
          </div>
        </div>
        {/* Menú móvil */}
        {mobileMenuOpen && (
          <div className="sm:hidden">
            <div className="pt-2 pb-3 space-y-1 bg-white border-t border-gray-200">
              {fullNavigation.map((item) => {
                const Icon = item.icon
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    onClick={() => setMobileMenuOpen(false)}
                    className={`$${
                      item.current
                        ? 'bg-indigo-50 border-indigo-500 text-indigo-700'
                        : 'border-transparent text-gray-500 hover:bg-gray-50 hover:border-gray-300 hover:text-gray-700'
                    } block pl-3 pr-4 py-2 border-l-4 text-base font-medium transition-colors duration-200`}
                  >
                    <div className="flex items-center">
                      <Icon className="h-5 w-5 mr-3" />
                      {item.name}
                    </div>
                  </Link>
                )
              })}
              <div className="pt-4 pb-3 border-t border-gray-200">
                <div className="flex items-center px-4">
                  <div className="flex-shrink-0">
                    <div className="h-8 w-8 rounded-full bg-indigo-100 flex items-center justify-center">
                      <User className="h-5 w-5 text-indigo-600" />
                    </div>
                  </div>
                  <div className="ml-3 flex-1">
                    <div className="text-base font-medium text-gray-800">
                      {user?.name}
                    </div>
                    <div className="text-xs text-gray-400">{user?.role}</div>
                  </div>
                  <button
                    onClick={handleLogout}
                    className="flex items-center px-3 py-1 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-md transition-colors"
                  >
                    <LogOut className="h-4 w-4 mr-1" />
                    Salir
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </nav>
      <main className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
        {children}
      </main>
    </div>
  )
}

export default Layout 