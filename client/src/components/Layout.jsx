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
  const [sidebarOpen, setSidebarOpen] = useState(false)

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
      {/* Sidebar para desktop */}
      <div className="hidden md:flex md:w-64 md:flex-col md:fixed md:inset-y-0">
        <div className="flex-1 flex flex-col min-h-0 bg-white border-r border-gray-200">
          {/* Logo y título */}
          <div className="flex items-center h-16 flex-shrink-0 px-4 bg-white border-b border-gray-200">
            <img
              className="h-8 w-auto mr-3"
              src="/logo_swatid.png"
              alt="SWAT-ID Logo"
            />
            <h1 className="text-lg font-semibold text-gray-900">
              Parking Altea
            </h1>
          </div>
          
          {/* Navegación */}
          <div className="flex-1 flex flex-col overflow-y-auto">
            <nav className="flex-1 px-2 py-4 space-y-1">
              {fullNavigation.map((item) => {
                const Icon = item.icon
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={`${
                      item.current
                        ? 'bg-indigo-50 border-indigo-500 text-indigo-700'
                        : 'border-transparent text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                    } group flex items-center px-2 py-2 text-sm font-medium border-l-4 transition-colors duration-200`}
                  >
                    <Icon className="mr-3 h-5 w-5" />
                    {item.name}
                  </Link>
                )
              })}
            </nav>
          </div>
          
          {/* Usuario en sidebar */}
          <div className="flex-shrink-0 flex border-t border-gray-200 p-4">
            <div className="flex items-center w-full">
              <div className="flex-shrink-0">
                <div className="h-8 w-8 rounded-full bg-indigo-100 flex items-center justify-center">
                  <User className="h-5 w-5 text-indigo-600" />
                </div>
              </div>
              <div className="ml-3 flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">
                  {user?.name}
                </p>
                <p className="text-xs text-gray-500 truncate">
                  {user?.role}
                </p>
              </div>
              <button
                onClick={handleLogout}
                className="flex-shrink-0 p-1 text-gray-400 hover:text-gray-600 transition-colors"
                title="Cerrar Sesión"
              >
                <LogOut className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Contenido principal */}
      <div className="md:pl-64 flex flex-col flex-1">
        {/* Header móvil */}
        <div className="md:hidden bg-white border-b border-gray-200">
          <div className="flex items-center justify-between h-16 px-4">
            <div className="flex items-center">
              <img
                className="h-8 w-auto mr-3"
                src="/logo_swatid.png"
                alt="SWAT-ID Logo"
              />
              <h1 className="text-lg font-semibold text-gray-900">
                Parking Altea
              </h1>
            </div>
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-indigo-500"
            >
              {sidebarOpen ? (
                <X className="h-6 w-6" />
              ) : (
                <Menu className="h-6 w-6" />
              )}
            </button>
          </div>
        </div>

        {/* Sidebar móvil */}
        {sidebarOpen && (
          <div className="md:hidden fixed inset-0 z-40">
            <div className="fixed inset-0 bg-gray-600 bg-opacity-75" onClick={() => setSidebarOpen(false)} />
            <div className="relative flex-1 flex flex-col max-w-xs w-full bg-white">
              <div className="absolute top-0 right-0 -mr-12 pt-2">
                <button
                  onClick={() => setSidebarOpen(false)}
                  className="ml-1 flex items-center justify-center h-10 w-10 rounded-full focus:outline-none focus:ring-2 focus:ring-inset focus:ring-white"
                >
                  <X className="h-6 w-6 text-white" />
                </button>
              </div>
              
              {/* Navegación móvil */}
              <div className="flex-1 h-0 pt-5 pb-4 overflow-y-auto">
                <nav className="mt-5 px-2 space-y-1">
                  {fullNavigation.map((item) => {
                    const Icon = item.icon
                    return (
                      <Link
                        key={item.name}
                        to={item.href}
                        onClick={() => setSidebarOpen(false)}
                        className={`${
                          item.current
                            ? 'bg-indigo-50 border-indigo-500 text-indigo-700'
                            : 'border-transparent text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                        } group flex items-center px-2 py-2 text-base font-medium border-l-4 transition-colors duration-200`}
                      >
                        <Icon className="mr-4 h-6 w-6" />
                        {item.name}
                      </Link>
                    )
                  })}
                </nav>
              </div>
              
              {/* Usuario móvil */}
              <div className="flex-shrink-0 flex border-t border-gray-200 p-4">
                <div className="flex items-center w-full">
                  <div className="flex-shrink-0">
                    <div className="h-8 w-8 rounded-full bg-indigo-100 flex items-center justify-center">
                      <User className="h-5 w-5 text-indigo-600" />
                    </div>
                  </div>
                  <div className="ml-3 flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {user?.name}
                    </p>
                    <p className="text-xs text-gray-500 truncate">
                      {user?.role}
                    </p>
                  </div>
                  <button
                    onClick={handleLogout}
                    className="flex-shrink-0 p-1 text-gray-400 hover:text-gray-600 transition-colors"
                    title="Cerrar Sesión"
                  >
                    <LogOut className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Contenido principal */}
        <main className="flex-1">
          <div className="py-6">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 md:px-8">
              {children}
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}

export default Layout 