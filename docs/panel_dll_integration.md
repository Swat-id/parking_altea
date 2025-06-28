# Integración DLL CP5200 y API de Paneles - Parking Altea

## 🚨 PROBLEMAS CRÍTICOS IDENTIFICADOS

### 1. **Workflow Incorrecto**
**Problema**: Estamos llamando a `SplitScreen` antes de cada envío, pero según el ejemplo del fabricante, `SplitScreen` solo se debe llamar UNA VEZ después de la inicialización.

**Workflow Correcto**:
```
1. InitComm() - Inicializar conexión
2. SplitScreen() - Configurar pantalla (UNA VEZ)
3. SendTagText() - Enviar múltiples mensajes
```

### 2. **Conversión de IP Incorrecta**
**Problema**: Nuestra función `IPToUInt` no hace el byte swapping correcto.

**Conversión Correcta** (según ejemplo del fabricante):
```csharp
private uint GetIP(string strIp)
{
    System.Net.IPAddress ipaddress = System.Net.IPAddress.Parse(strIp);
    uint lIp = (uint)ipaddress.Address;
    lIp = ((lIp & 0xFF000000) >> 24) + ((lIp & 0x00FF0000) >> 8) + 
          ((lIp & 0x0000FF00) << 8) + ((lIp & 0x000000FF) << 24);
    return (lIp);
}
```

### 3. **Parámetros de SendTagText Incorrectos**
**Problema**: Estamos usando parámetros diferentes a los del ejemplo.

**Parámetros Correctos** (según ejemplo):
```csharp
CP5200_Net_SendTagText(m_nCardID, 0, iPtr, icolor, 16, 3, 0, 3, 0);
//                    CardID, Window, Text, Color, Font, Speed, Effect, StayTime, Alignment
```

### 4. **Inicialización por Panel**
**Problema**: Estamos inicializando cada panel individualmente, pero deberíamos mantener una conexión por panel.

## 📋 Resumen Ejecutivo

Este documento describe la implementación completa de la integración con los paneles LED usando la DLL CP5200 del fabricante Rotuloselectronicos.net. El sistema utiliza un servicio C# (.NET 6) que actúa como intermediario entre la aplicación web y los paneles físicos.

## 🏗️ Arquitectura del Sistema

```
Frontend React → Backend Python → Servicio C# → DLL CP5200 → Panel LED
```

### Componentes:
1. **Frontend React**: Interfaz web para enviar mensajes
2. **Backend Python**: API REST que recibe peticiones
3. **Servicio C#**: Intermediario que usa la DLL CP5200
4. **DLL CP5200**: Biblioteca del fabricante para comunicación
5. **Panel LED**: Dispositivo físico de visualización

## 🔧 Configuración del Servicio C#

### Ubicación y Configuración
- **Servicio**: `parking-panel-service.service`
- **Puerto**: 5001
- **Archivos principales**:
  - `PanelService/Controllers/PanelController.cs`
  - `PanelService/Services/PanelCommunicationService.cs`
  - `PanelService/CP5200Wrapper.cs`

### Endpoints Disponibles
```
POST /api/panel/send          - Enviar mensaje a panel específico
POST /api/panel/occupancy     - Enviar información de ocupación
POST /api/panel/broadcast     - Enviar mensaje a todos los paneles
POST /api/panel/test/{ip}     - Probar conectividad de panel
GET  /api/panel/status        - Estado de todos los paneles
GET  /api/panel/colors        - Colores disponibles
```

## 📚 Documentación del Fabricante

### Ubicación de Documentación
- **SDK**: `/docs/Rotuloselectronicos.NET_API+ejemplos/`
- **DLL**: `CP5200.dll` (576KB)
- **Headers**: `CP5200API.h`
- **Ejemplos**: `CPower_CSharp_2010/`

### Funciones Principales de la DLL

#### 1. Inicialización de Red
```csharp
[DllImport("CP5200.dll")]
public static extern int CP5200_Net_Init(uint dwIP, int nIPPort, uint dwIDCode, int nTimeOut);
```

**Parámetros:**
- `dwIP`: IP del panel en formato uint (convertida con byte swapping)
- `nIPPort`: Puerto (por defecto 5200)
- `dwIDCode`: Código de identificación (0xFFFFFFFF)
- `nTimeOut`: Timeout en milisegundos (3000)

#### 2. Configuración de Pantalla
```csharp
[DllImport("CP5200.dll")]
public static extern int CP5200_Net_SplitScreen(int nCardID, int nScrWidth, int nScrHeight, int nWndCnt, int[] pWndRects);
```

**Parámetros:**
- `nCardID`: ID de la tarjeta (1)
- `nScrWidth`: Ancho de pantalla (64)
- `nScrHeight`: Alto de pantalla (32)
- `nWndCnt`: Número de ventanas (1)
- `pWndRects`: Array con coordenadas [0, 0, width, height]

#### 3. Envío de Texto
```csharp
[DllImport("CP5200.dll")]
public static extern int CP5200_Net_SendTagText(int nCardID, int nWndNo, IntPtr pText, int crColor, int nFontSize, int nSpeed, int nEffect, int nStayTime, int nAlignment);
```

**Parámetros CORRECTOS** (según ejemplo del fabricante):
- `nCardID`: ID de la tarjeta (1)
- `nWndNo`: Número de ventana (0)
- `pText`: Puntero al texto (convertido con Marshal.StringToHGlobalAnsi)
- `crColor`: Color en formato específico del SDK (3000 = color por defecto)
- `nFontSize`: Tamaño de fuente (16)
- `nSpeed`: Velocidad de movimiento (3)
- `nEffect`: Efecto visual (0 = sin efecto)
- `nStayTime`: Tiempo de permanencia en segundos (3)
- `nAlignment`: Alineación (0 = izquierda)

## 🎨 Sistema de Colores

### Colores Disponibles (según SDK)
```csharp
public static class PanelColors
{
    public const int Red = 0x0000FF;        // 255 (Decimal)
    public const int Green = 0x00FF00;      // 65280 (Decimal)  
    public const int Blue = 0xFF0000;       // 16711680 (Decimal)
    public const int Yellow = 0x00FFFF;     // 65535 (Decimal)
    public const int Orange = 0x0080FF;     // 33023 (Decimal)
    public const int White = 0xFFFFFF;      // 16777215 (Decimal)
    public const int Default = 3000;        // Color por defecto del ejemplo
}
```

### Estados de Ocupación por Color
- **LLIURE**: Verde (0x00FF00)
- **DENS**: Naranja (0x0080FF)
- **COMPLET**: Rojo (0x0000FF)

## 🔄 Workflow CORRECTO de Envío

### 1. Recepción de Petición
```http
POST /api/panel/send
Content-Type: application/json

{
  "panelIP": "172.20.5.50",
  "message": "Texto a mostrar",
  "color": 3000,
  "fontSize": 16,
  "speed": 3,
  "effect": 0,
  "stayTime": 3,
  "alignment": 0
}
```

### 2. Procesamiento CORRECTO en el Servicio
```csharp
// 1. Convertir IP correctamente (con byte swapping)
var panelIPUInt = GetIP(panelIP); // Usar función del ejemplo

// 2. Inicializar conexión (si no está inicializada)
CP5200Wrapper.CP5200_Net_Init(panelIPUInt, 5200, 0xFFFFFFFF, 3000);

// 3. Configurar pantalla dividida (UNA VEZ por panel)
if (!_splitScreenDone.ContainsKey(panelIP)) {
    int[] windowRect = new int[4] { 0, 0, 64, 32 };
    CP5200Wrapper.CP5200_Net_SplitScreen(1, 64, 32, 1, windowRect);
    _splitScreenDone[panelIP] = true;
}

// 4. Convertir texto a puntero
var textPtr = Marshal.StringToHGlobalAnsi(message);

// 5. Enviar texto con parámetros correctos
var result = CP5200Wrapper.CP5200_Net_SendTagText(
    1, 0, textPtr, color, fontSize, speed, effect, stayTime, alignment
);

// 6. Liberar memoria
Marshal.FreeHGlobal(textPtr);
```

### 3. Respuesta del Servicio
```json
{
  "success": true,
  "message": "Mensaje enviado correctamente",
  "errorCode": 0,
  "responseTime": 75.45,
  "timestamp": "2025-06-28T10:12:58.674Z"
}
```

## 📊 Configuración de Paneles

### IPs de Paneles (Base de Datos)
```sql
SELECT id, name, ip, status FROM panels ORDER BY id;

 id |        name        |      ip      | status 
----+--------------------+--------------+--------
  1 | PANEL C. ESPORTIVA | 172.20.17.50 | ONLINE
  2 | PANEL BASSETA 1    | 172.20.5.50  | ONLINE
  3 | PANEL BASSETA 2    | 172.20.5.51  | ONLINE
  4 | PANEL PITERES      | 172.20.8.50  | ONLINE
  5 | PANEL PALAU        | 172.20.4.50  | ONLINE
  6 | PANEL COCOLISO     | 172.20.4.51  | ONLINE
  7 | BELLES ARTS 2      | 172.20.4.52  | ONLINE
  8 | BELLES ARTS        | 172.20.4.53  | ONLINE
  9 | PANEL RENFE        | 172.20.2.50  | ONLINE
 10 | PANEL ALTEA VELLA  | 172.20.1.50  | ONLINE
```

### Configuración por Defecto
```csharp
public static class DefaultConfig
{
    public const int CardID = 1;
    public const int WindowNo = 0;
    public const int Port = 5200;
    public const int Timeout = 3000;
    public const uint IDCode = 0xFFFFFFFF;
    public const int ScreenWidth = 64;
    public const int ScreenHeight = 32;
}
```

## 🔍 Diagnóstico y Troubleshooting

### Verificación de Conectividad
```bash
# Ping a paneles
ping 172.20.5.50

# Verificar puerto
nc -zv 172.20.5.50 5200

# Logs del servicio
journalctl -u parking-panel-service.service -f
```

### Códigos de Error Comunes
- **-1**: Error de inicialización
- **-2**: Error de conexión TCP
- **-3**: Error de envío de datos
- **-4**: Timeout de respuesta

### Logs del Servicio
```bash
# Ver logs en tiempo real
journalctl -u parking-panel-service.service -f

# Ver últimas 50 líneas
journalctl -u parking-panel-service.service -n 50
```

## 🚀 Comandos de Gestión

### Reiniciar Servicio
```bash
systemctl restart parking-panel-service.service
```

### Verificar Estado
```bash
systemctl status parking-panel-service.service
```

### Recompilar Servicio
```bash
cd /opt/parking_altea/PanelService
dotnet build -c Release
```

## 📝 Notas de Implementación

### Consideraciones Importantes
1. **Inicialización**: Cada panel debe inicializarse antes de enviar mensajes
2. **SplitScreen**: Llamar UNA VEZ después de la inicialización, no antes de cada mensaje
3. **Memoria**: Liberar punteros después de usar
4. **Timeouts**: Configurar timeouts apropiados para la red
5. **Colores**: Usar valores específicos del SDK, no RGB estándar
6. **Conversión de IP**: Usar byte swapping correcto

### Problemas Conocidos
1. **Timeouts de conexión**: Pueden ocurrir en redes lentas
2. **Memoria no liberada**: Causa memory leaks
3. **Inicialización múltiple**: No es necesaria, usar cache
4. **Colores incorrectos**: Usar valores del SDK, no RGB
5. **SplitScreen repetido**: Causa problemas de rendimiento

## 🔮 Próximos Pasos

### Correcciones Inmediatas
1. **Corregir conversión de IP**: Implementar byte swapping correcto
2. **Corregir workflow**: SplitScreen una vez, no antes de cada mensaje
3. **Corregir parámetros**: Usar parámetros exactos del ejemplo
4. **Cache de SplitScreen**: Evitar llamadas repetidas

### Mejoras Pendientes
1. **Pool de conexiones**: Reutilizar conexiones inicializadas
2. **Retry automático**: Reintentar en caso de fallo
3. **Monitoreo**: Métricas de rendimiento y errores
4. **Configuración dinámica**: Cargar configuración desde base de datos

### Optimizaciones
1. **Cache de inicialización**: Evitar reinicializar paneles
2. **Batch de mensajes**: Enviar múltiples mensajes en una conexión
3. **Compresión**: Comprimir mensajes largos
4. **Queue de mensajes**: Cola para mensajes pendientes

---

**Documento creado**: 28 de Junio 2025  
**Versión**: 2.0 (Actualizado con hallazgos críticos)  
**Autor**: Asistente IA  
**Estado**: ✅ Activo - Requiere correcciones inmediatas 