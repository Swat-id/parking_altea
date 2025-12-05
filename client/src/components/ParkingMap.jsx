import { useEffect, useMemo, useState, Component } from 'react'
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { 
  Car, 
  MapPin, 
  TrendingUp, 
  AlertCircle, 
  CheckCircle, 
  Clock,
  X,
  RefreshCw
} from 'lucide-react'

// Error Boundary para capturar errores del mapa sin romper el Dashboard
class MapErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, errorInfo) {
    console.error('Error en el mapa de parkings:', error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div 
          className="flex items-center justify-center bg-gray-100 rounded-lg"
          style={{ height: this.props.height || '400px' }}
        >
          <div className="text-center text-gray-500 p-4">
            <AlertCircle className="h-12 w-12 mx-auto mb-2 text-red-400" />
            <p className="font-medium text-gray-700">Error al cargar el mapa</p>
            <p className="text-sm mt-1">El mapa no está disponible temporalmente</p>
            <button 
              onClick={() => this.setState({ hasError: false, error: null })}
              className="mt-3 inline-flex items-center px-3 py-1.5 text-sm bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
            >
              <RefreshCw className="h-4 w-4 mr-1.5" />
              Reintentar
            </button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

// Componente para ajustar el zoom a los markers
const FitBounds = ({ parkings }) => {
  const map = useMap()
  
  useEffect(() => {
    if (parkings.length > 0) {
      const validCoords = parkings
        .filter(p => p.coords)
        .map(p => [p.coords.lat, p.coords.lng])
      
      if (validCoords.length > 0) {
        const bounds = L.latLngBounds(validCoords)
        map.fitBounds(bounds, { padding: [50, 50] })
      }
    }
  }, [parkings, map])
  
  return null
}

// Crear icono SVG de parking con color dinámico
const createParkingIcon = (status) => {
  const colors = {
    LIBRE: { bg: '#16a34a', border: '#15803d' },           // Verde
    DENSO: { bg: '#eab308', border: '#ca8a04' },           // Amarillo
    COMPLETO: { bg: '#dc2626', border: '#b91c1c' },        // Rojo
    DESCUADRE_NEGATIVO: { bg: '#dc2626', border: '#991b1b' }, // Rojo oscuro (más ocupado que capacidad)
    DESCUADRE_POSITIVO: { bg: '#f97316', border: '#ea580c' }, // Naranja (ocupación negativa)
    DEFAULT: { bg: '#6b7280', border: '#4b5563' }          // Gris
  }
  
  const color = colors[status] || colors.DEFAULT
  
  const svgIcon = `
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 50" width="40" height="50">
      <!-- Pin shape -->
      <path d="M20 0 C8.954 0 0 8.954 0 20 C0 35 20 50 20 50 C20 50 40 35 40 20 C40 8.954 31.046 0 20 0 Z" 
            fill="${color.bg}" stroke="${color.border}" stroke-width="2"/>
      <!-- White circle background for P -->
      <circle cx="20" cy="18" r="12" fill="white"/>
      <!-- P letter -->
      <text x="20" y="24" font-family="Arial, sans-serif" font-size="18" font-weight="bold" 
            fill="${color.bg}" text-anchor="middle">P</text>
    </svg>
  `
  
  return L.divIcon({
    html: svgIcon,
    className: 'parking-marker',
    iconSize: [40, 50],
    iconAnchor: [20, 50],
    popupAnchor: [0, -45]
  })
}

// Parsear coordenadas del formato "lat,lng"
const parseCoordinates = (location) => {
  if (!location) return null
  const parts = location.split(',')
  if (parts.length !== 2) return null
  
  const lat = parseFloat(parts[0])
  const lng = parseFloat(parts[1])
  
  if (isNaN(lat) || isNaN(lng)) return null
  return { lat, lng }
}

// Componente de detalle de parking
const ParkingDetail = ({ parking, onClose }) => {
  const getStatusInfo = (status) => {
    switch (status) {
      case 'LIBRE':
        return { 
          label: 'Libre', 
          color: 'text-green-600 bg-green-100', 
          icon: CheckCircle,
          description: 'Disponibilidad alta'
        }
      case 'DENSO':
        return { 
          label: 'Denso', 
          color: 'text-yellow-600 bg-yellow-100', 
          icon: Clock,
          description: 'Ocupación moderada'
        }
      case 'COMPLETO':
        return { 
          label: 'Completo', 
          color: 'text-red-600 bg-red-100', 
          icon: AlertCircle,
          description: 'Sin disponibilidad'
        }
      case 'DESCUADRE_NEGATIVO':
        return { 
          label: 'Descuadre', 
          color: 'text-red-700 bg-red-100', 
          icon: AlertCircle,
          description: 'Ocupación mayor que capacidad'
        }
      case 'DESCUADRE_POSITIVO':
        return { 
          label: 'Descuadre', 
          color: 'text-orange-600 bg-orange-100', 
          icon: AlertCircle,
          description: 'Ocupación negativa detectada'
        }
      default:
        return { 
          label: status || 'Desconocido', 
          color: 'text-gray-600 bg-gray-100', 
          icon: MapPin,
          description: 'Estado desconocido'
        }
    }
  }
  
  const statusInfo = getStatusInfo(parking.estado)
  const StatusIcon = statusInfo.icon
  const occupancyPercent = parking.total_plazas > 0 
    ? Math.min(100, Math.round((parking.plazas_ocupadas / parking.total_plazas) * 100))
    : 0
  
  return (
    <div className="parking-popup-content">
      <div className="flex items-start justify-between mb-3">
        <h3 className="font-bold text-gray-900 text-base leading-tight pr-2">
          {parking.name}
        </h3>
        <button 
          onClick={onClose}
          className="flex-shrink-0 p-1 hover:bg-gray-100 rounded-full transition-colors"
        >
          <X className="h-4 w-4 text-gray-500" />
        </button>
      </div>
      
      {/* Estado */}
      <div className={`inline-flex items-center px-3 py-1.5 rounded-full text-sm font-medium ${statusInfo.color} mb-3`}>
        <StatusIcon className="h-4 w-4 mr-1.5" />
        <span>{statusInfo.label}</span>
      </div>
      
      {/* Barra de ocupación */}
      <div className="mb-3">
        <div className="flex justify-between text-sm text-gray-600 mb-1">
          <span>Ocupación</span>
          <span className="font-medium">{occupancyPercent}%</span>
        </div>
        <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
          <div 
            className={`h-full transition-all duration-300 rounded-full ${
              occupancyPercent >= 90 ? 'bg-red-500' :
              occupancyPercent >= 60 ? 'bg-yellow-500' : 'bg-green-500'
            }`}
            style={{ width: `${Math.max(0, occupancyPercent)}%` }}
          />
        </div>
      </div>
      
      {/* Estadísticas */}
      <div className="grid grid-cols-2 gap-3 text-sm">
        <div className="bg-gray-50 rounded-lg p-2.5">
          <div className="flex items-center text-gray-500 mb-1">
            <Car className="h-3.5 w-3.5 mr-1" />
            <span className="text-xs">Ocupadas</span>
          </div>
          <p className="font-bold text-gray-900">{parking.plazas_ocupadas || 0}</p>
        </div>
        <div className="bg-gray-50 rounded-lg p-2.5">
          <div className="flex items-center text-gray-500 mb-1">
            <TrendingUp className="h-3.5 w-3.5 mr-1" />
            <span className="text-xs">Libres</span>
          </div>
          <p className="font-bold text-green-600">
            {Math.max(0, parking.plazas_libres || 0)}
          </p>
        </div>
      </div>
      
      {/* Capacidad total */}
      <div className="mt-3 pt-3 border-t border-gray-200">
        <div className="flex justify-between items-center text-sm">
          <span className="text-gray-600">Capacidad total</span>
          <span className="font-semibold text-gray-900">{parking.total_plazas || 0} plazas</span>
        </div>
      </div>
    </div>
  )
}

// Componente interno del mapa
const ParkingMapContent = ({ parkings = [], height = '400px', className = '' }) => {
  const [selectedParking, setSelectedParking] = useState(null)
  
  // Procesar parkings con coordenadas válidas
  const parkingsWithCoords = useMemo(() => {
    if (!Array.isArray(parkings)) return []
    return parkings
      .map(parking => ({
        ...parking,
        coords: parseCoordinates(parking.location)
      }))
      .filter(parking => parking.coords !== null)
  }, [parkings])
  
  // Centro por defecto: Altea
  const defaultCenter = useMemo(() => {
    if (parkingsWithCoords.length > 0) {
      const avgLat = parkingsWithCoords.reduce((sum, p) => sum + p.coords.lat, 0) / parkingsWithCoords.length
      const avgLng = parkingsWithCoords.reduce((sum, p) => sum + p.coords.lng, 0) / parkingsWithCoords.length
      return [avgLat, avgLng]
    }
    return [38.5988, -0.0511] // Centro de Altea
  }, [parkingsWithCoords])
  
  if (parkingsWithCoords.length === 0) {
    return (
      <div 
        className={`flex items-center justify-center bg-gray-100 rounded-lg ${className}`}
        style={{ height }}
      >
        <div className="text-center text-gray-500">
          <MapPin className="h-12 w-12 mx-auto mb-2 opacity-50" />
          <p>No hay parkings con ubicación disponible</p>
        </div>
      </div>
    )
  }
  
  return (
    <div className={`parking-map-container ${className}`} style={{ height }}>
      <MapContainer
        center={defaultCenter}
        zoom={14}
        style={{ height: '100%', width: '100%', borderRadius: '0.5rem' }}
        scrollWheelZoom={true}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        
        <FitBounds parkings={parkingsWithCoords} />
        
        {parkingsWithCoords.map((parking) => (
          <Marker
            key={parking.id}
            position={[parking.coords.lat, parking.coords.lng]}
            icon={createParkingIcon(parking.estado)}
            eventHandlers={{
              click: () => setSelectedParking(parking)
            }}
          >
            <Popup 
              className="parking-popup"
              maxWidth={320}
              minWidth={280}
            >
              <ParkingDetail 
                parking={parking} 
                onClose={() => setSelectedParking(null)}
              />
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  )
}

// Componente principal con Error Boundary
const ParkingMap = ({ parkings = [], height = '400px', className = '' }) => {
  return (
    <MapErrorBoundary height={height}>
      <ParkingMapContent 
        parkings={parkings} 
        height={height} 
        className={className} 
      />
    </MapErrorBoundary>
  )
}

export default ParkingMap

