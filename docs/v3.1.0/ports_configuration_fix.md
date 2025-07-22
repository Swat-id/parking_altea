# Corrección de Configuración de Puertos - 22 de Julio 2025

## Problema Identificado

El error `ECONNRESET` al crear programaciones se debía a una configuración incorrecta de puertos en el frontend.

## Configuración Correcta de Puertos

### Arquitectura del Sistema

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Nginx Proxy   │    │   API Backend   │
│   Puerto 5789   │───▶│   Puerto 5789   │───▶│   Puerto 6001   │
│   (React)       │    │   (Proxy)       │    │   (Gunicorn)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Panel Service │
                       │   Puerto 8888   │
                       │   (panelSender) │
                       └─────────────────┘
```

### Puertos y Servicios

| Puerto | Servicio | Descripción |
|--------|----------|-------------|
| **5789** | **Nginx** | Frontend + Proxy reverso para API |
| **6001** | **API Backend** | Servicio principal de la API (gunicorn) |
| **6400** | **Camera Service** | Endpoint para recepción de datos de cámaras |
| **8888** | **Panel Service** | Servicio de comunicación con paneles (panelSender) |

## Cambios Realizados

### 1. Corrección del Frontend (`client/src/pages/Schedules.jsx`)

**Antes:**
```javascript
const API_BASE_URL = 'http://157.180.91.63:8888/api'
```

**Después:**
```javascript
const API_BASE_URL = 'http://157.180.91.63:5789'
```

### 2. Corrección de URLs en las Consultas

Todas las URLs ahora incluyen `/api` correctamente:

```javascript
// Obtener parkings
() => fetch(`${API_BASE_URL}/api/parkings`).then(res => res.json())

// Obtener programaciones
() => fetch(`${API_BASE_URL}/api/schedules?${params}`).then(res => res.json())

// Crear programación
() => fetch(`${API_BASE_URL}/api/schedules`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(data)
}).then(res => res.json())
```

### 3. Configuración de Nginx

La configuración de nginx en `/etc/nginx/sites-available/parking_altea` está correcta:

```nginx
server {
    listen 5789;
    server_name localhost;

    root /var/www/parking_altea;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://localhost:6001/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Flujo de Comunicación Corregido

### Frontend → API Backend
1. Frontend (puerto 5789) hace petición a `/api/schedules`
2. Nginx recibe la petición en puerto 5789
3. Nginx hace proxy a `http://localhost:6001/api/schedules`
4. API Backend (puerto 6001) procesa la petición

### API Backend → Panel Service
1. API Backend necesita enviar mensajes a paneles
2. API Backend hace petición a `http://localhost:8888/api/v1/panels/send`
3. Panel Service (puerto 8888) recibe y procesa la petición

## Verificación

### Script de Prueba Creado
- `test/test_correct_ports_configuration.py` - Verifica la configuración de puertos

### Endpoints Verificados
- ✅ `http://157.180.91.63:5789/api/parkings` - Frontend → API
- ✅ `http://157.180.91.63:5789/api/schedules` - Frontend → API
- ✅ `http://157.180.91.63:6001/api/parkings` - API directa
- ✅ `http://157.180.91.63:8888/` - Panel Service

## Resultado

- ✅ **Error ECONNRESET resuelto**: El frontend ahora accede correctamente al API a través del proxy de nginx
- ✅ **Dropdown de parkings funcionando**: Las consultas a `/api/parkings` funcionan correctamente
- ✅ **Creación de programaciones funcionando**: Las peticiones POST a `/api/schedules` funcionan correctamente
- ✅ **Servicio de paneles preservado**: El puerto 8888 sigue disponible para el servicio de paneles

## Notas Importantes

1. **No modificar el puerto 8888**: Este puerto está reservado para el servicio de comunicación con paneles
2. **Usar siempre el puerto 5789**: El frontend debe acceder siempre al puerto 5789 donde nginx hace proxy
3. **Incluir `/api` en las URLs**: Todas las peticiones del frontend deben incluir `/api` en la ruta

---
**Fecha de Corrección**: 22 de Julio 2025  
**Estado**: ✅ Completado y Verificado 