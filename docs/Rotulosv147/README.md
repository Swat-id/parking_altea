# PanelSender - Sistema de Control de Paneles LED

## Descripción del Proyecto

PanelSender es un sistema para controlar paneles LED mediante comunicación de red. El proyecto permite enviar texto y contenido a múltiples pantallas LED de forma simultánea.

## Arquitectura del Proyecto

### Estructura de Directorios
```
PanelSender/
├── client/          # Frontend React Vite
├── server/          # Backend NodeJS
├── docs/            # Documentación del proyecto
└── protocol.jar     # Librería Java para control de paneles
```

### Configuración de Paneles

#### IPs de los Paneles de Prueba
- Panel 1: 192.168.1.221
- Panel 2: 192.168.1.222  
- Panel 3: 192.168.1.223
- Panel 4: 192.168.1.224

#### Configuración de Ventanas
Cada panel tiene 2 ventanas de 32x16 píxeles:
- Ventana 0: Coordenadas (0,0)
- Ventana 1: Coordenadas (32,0)

## Protocolo de Comunicación

### Configuración de Red
- **Puerto de comunicación**: 5200
- **ID Code**: 255.255.255.255 (común para todas las pantallas)

### Proceso de Envío de Programas
1. Invocar `initNetwork` para inicializar parámetros de comunicación de red
2. Llamar `setListener` para establecer listener y escuchar estado de comunicación
3. Llamar `splitScreen` para dividir ventanas
4. Llamar `sendXXX` para enviar programas (en este caso `sendText`)

### Secuencia de Envío
Para el patrón solicitado:
```
000 111 222 333
444 555 666 777
```

Cada número se enviará a la ventana 0 de cada panel correspondiente con texto rojo.

## Tecnologías Utilizadas

- **Frontend**: React Vite
- **Backend**: NodeJS puro
- **Base de Datos**: PostgreSQL (snake_case)
- **Control de Paneles**: Java (protocol.jar)
- **Usuario por defecto**: superadmin@swat-id.com / admin123!

## Desarrollo

### Rama de Desarrollo
- Rama actual: `feature/panel-communication`

### Rutas
- Se utilizan rutas relativas en todo el proyecto
- No se emplean rutas absolutas

## Documentación del Fabricante

La documentación completa del fabricante se encuentra en:
`docs/Control Card Development API-1.4.7.docx`

## Controlador Java

El controlador Java está listo para pruebas y se encuentra en el directorio `java-panel-controller/`.

### Características Implementadas
- ✅ Protocolo de comunicación del fabricante (API real implementada)
- ✅ Gestión de múltiples paneles simultáneamente
- ✅ Envío de texto con color rojo usando sendTextRGB
- ✅ Interfaz interactiva para pruebas
- ✅ Manejo robusto de errores
- ✅ Carga dinámica de librería protocol.jar
- ✅ Modo real/simulación automático
- ✅ Reflection API para compatibilidad

### Ejecución de Pruebas
```bash
# Pruebas básicas
cd java-panel-controller
run-test.bat

# Pruebas interactivas
run-interactive.bat

# Pruebas de librería
test-library.bat

# Con librería real
run-with-protocol.bat
```

Para más detalles, consultar:
- `docs/Java-Controller-Guide.md` - Guía técnica completa
- `java-panel-controller/README.md` - Documentación específica del controlador 