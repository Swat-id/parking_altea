# Parking Altea - Frontend

Frontend React para el sistema de gestión de aparcamientos de Altea.

## 🚀 Características

- **Autenticación JWT** con persistencia de sesión
- **Dashboard interactivo** con estadísticas en tiempo real
- **Gestión de parkings** con edición de ocupación y configuración
- **Comunicación con paneles** electrónicos
- **Estadísticas y análisis** de ocupación
- **Interfaz responsive** para móvil y desktop
- **Sistema de notificaciones** en tiempo real

## 🛠️ Tecnologías

- **React 18.2.0** - Framework de UI
- **Vite 5.0.0** - Build tool y dev server
- **React Router 6.20.1** - Navegación
- **React Query 3.39.3** - Gestión de estado y caché
- **Axios 1.6.2** - Cliente HTTP
- **Tailwind CSS 3.3.5** - Framework de estilos
- **Lucide React** - Iconografía
- **React Hook Form** - Gestión de formularios
- **React Hot Toast** - Notificaciones

## 📦 Instalación

1. **Clonar el repositorio**
```bash
git clone https://github.com/Swat-id/parking_altea.git
cd parking_altea/client
```

2. **Instalar dependencias**
```bash
npm install
```

3. **Configurar variables de entorno**
```bash
# Crear archivo .env basado en .env.example
cp .env.example .env
```

4. **Iniciar servidor de desarrollo**
```bash
npm run dev
```

El frontend estará disponible en `http://localhost:3000`

## 🔧 Scripts Disponibles

```bash
# Desarrollo
npm run dev          # Inicia servidor de desarrollo
npm run build        # Construye para producción
npm run preview      # Previsualiza build de producción

# Pruebas
npm run test         # Ejecuta pruebas unitarias
npm run test:ui      # Interfaz visual para pruebas

# Linting
npm run lint         # Verifica código con ESLint
```

## 🏗️ Estructura del Proyecto

```
src/
├── components/          # Componentes reutilizables
│   └── Layout.jsx      # Layout principal con navegación
├── pages/              # Páginas de la aplicación
│   ├── Login.jsx       # Página de autenticación
│   ├── Dashboard.jsx   # Dashboard principal
│   ├── Parkings.jsx    # Listado de parkings
│   ├── ParkingDetail.jsx # Detalle y edición de parking
│   ├── Panels.jsx      # Gestión de paneles
│   ├── Statistics.jsx  # Estadísticas y gráficos
│   └── Profile.jsx     # Perfil de usuario
├── services/           # Servicios de API
│   ├── api.js         # Configuración base de Axios
│   ├── authService.js # Servicios de autenticación
│   ├── parkingService.js # Servicios de parkings
│   └── panelService.js # Servicios de paneles
├── context/           # Contextos de React
│   └── AuthContext.jsx # Contexto de autenticación
├── hooks/             # Hooks personalizados
├── utils/             # Utilidades
└── test/              # Configuración de pruebas
```

## 🔐 Autenticación

### Usuarios de Prueba
- **Toni Alos**: `atea.dti@altea.es` / `altea2025!`
- **Iván Martí**: `gerenciapstd@altea.es` / `altea2025!`

### Flujo de Autenticación
1. Usuario ingresa credenciales en `/login`
2. Sistema valida con API y obtiene token JWT
3. Token se almacena en localStorage
4. Usuario es redirigido al dashboard
5. Todas las peticiones incluyen token automáticamente

## 📱 Páginas Principales

### Dashboard (`/dashboard`)
- Resumen general del sistema
- Estadísticas de ocupación
- Estado de parkings
- Acceso rápido a funcionalidades

### Parkings (`/parkings`)
- Listado de todos los parkings
- Filtros por estado y búsqueda
- Acceso a detalles individuales

### Detalle de Parking (`/parking/:id`)
- Información completa del parking
- Edición de ocupación
- Configuración de umbrales
- Envío de mensajes a paneles

### Paneles (`/panels`)
- Listado de paneles electrónicos
- Estado de conectividad
- Envío de mensajes de prueba
- Configuración de parámetros

### Estadísticas (`/statistics`)
- Gráficos de ocupación por tiempo
- Análisis de tendencias
- Exportación de datos
- Resumen por parking

### Perfil (`/profile`)
- Información del usuario
- Cambio de contraseña
- Permisos de acceso
- Configuración de seguridad

## 🔌 Configuración de API

El frontend se conecta automáticamente al backend en:
- **Desarrollo**: `http://localhost:6001` (proxy configurado)
- **Producción**: `http://157.180.91.63:6001`

### Endpoints Principales
- `POST /auth/login` - Autenticación
- `GET /user/parkings` - Parkings del usuario
- `GET /parkings` - Todos los parkings
- `POST /parking/{id}/occupancy` - Actualizar ocupación
- `GET /panels` - Lista de paneles
- `POST /panel/{id}/message` - Enviar mensaje

## 🎨 Sistema de Diseño

### Colores
- **Primary**: Azul (#3b82f6)
- **Success**: Verde (#10b981)
- **Warning**: Amarillo (#f59e0b)
- **Error**: Rojo (#ef4444)

### Estados de Parking
- **LIBRE**: Verde
- **DENSO**: Amarillo
- **COMPLETO**: Rojo

### Componentes
- Botones con variantes: primary, secondary, danger
- Cards con sombras y bordes
- Formularios con validación
- Notificaciones toast

## 🧪 Pruebas

### Configuración
- **Vitest** para pruebas unitarias
- **Testing Library** para pruebas de componentes
- **jsdom** para entorno de DOM

### Ejecutar Pruebas
```bash
npm run test           # Ejecuta todas las pruebas
npm run test:ui        # Interfaz visual
npm run test -- --coverage  # Con cobertura
```

### Estructura de Pruebas
```
src/
├── __tests__/         # Pruebas organizadas por funcionalidad
├── test/              # Configuración y utilidades
└── components/        # Pruebas junto a componentes
```

## 🚀 Despliegue

### Build de Producción
```bash
npm run build
```

### Servir Build
```bash
npm run preview
```

### Configuración de Servidor
El build genera archivos estáticos que pueden servirse desde cualquier servidor web:
- Nginx
- Apache
- CDN
- Servicios cloud (Vercel, Netlify, etc.)

## 🔧 Configuración Avanzada

### Variables de Entorno
```bash
VITE_API_URL=http://157.180.91.63:6001
VITE_DEV_MODE=true
VITE_ENABLE_MOCK_DATA=false
```

### Proxy de Desarrollo
Configurado en `vite.config.js` para redirigir `/api` al backend.

### Optimizaciones
- Lazy loading de componentes
- Code splitting automático
- Compresión de assets
- Caché de consultas con React Query

## 📞 Soporte

- **Desarrollador**: Francisco
- **Email**: info@swat-id.com
- **Proyecto**: Parking Altea v2.2
- **Documentación**: `/docs/`

## 📝 Notas de Desarrollo

### Convenciones
- **Componentes**: PascalCase
- **Archivos**: kebab-case
- **Variables**: camelCase
- **Constantes**: UPPER_SNAKE_CASE

### Mejores Prácticas
- Usar React Query para gestión de estado
- Implementar error boundaries
- Validar formularios con React Hook Form
- Usar TypeScript para proyectos futuros
- Implementar pruebas unitarias

---

**Versión**: 1.0.0  
**Última actualización**: 26/06/2025 