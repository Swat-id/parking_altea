# Configuración de Gmail para Sistema de Alarmas v3.2.0_alarms

## 📧 Configuración SMTP de Gmail

El sistema de alarmas utiliza Gmail como servidor SMTP para enviar notificaciones por email. Esta configuración requiere una clave de aplicación específica para aplicaciones menos seguras.

### 🔧 Configuración Actual

```python
# Configuración por defecto en EmailService
SMTP_HOST = 'smtp.gmail.com'
SMTP_PORT = 587
SMTP_USERNAME = 'info@swat-id.com'
SMTP_PASSWORD = 'pysn fxgf hxzl hevi'  # Clave de aplicación
SMTP_FROM_EMAIL = 'info@swat-id.com'
SMTP_FROM_NAME = 'Sistema de Alarmas Parking Altea'
```

### 📋 Requisitos Previos

1. **Cuenta de Gmail**: `info@swat-id.com`
2. **Verificación en dos pasos habilitada**
3. **Clave de aplicación generada**: `pysn fxgf hxzl hevi`

### 🔐 Configuración de Gmail

#### Paso 1: Habilitar Verificación en Dos Pasos

1. Ir a [Google Account Security](https://myaccount.google.com/security)
2. Activar "Verificación en 2 pasos"
3. Seguir las instrucciones para configurar

#### Paso 2: Generar Clave de Aplicación

1. Ir a [App Passwords](https://myaccount.google.com/apppasswords)
2. Seleccionar aplicación: "Correo"
3. Seleccionar dispositivo: "Windows"
4. Generar clave de aplicación
5. Copiar la clave generada (16 caracteres)

### 🚀 Configuración del Sistema

#### Opción 1: Usar Valores por Defecto

El sistema ya está configurado con los valores por defecto:

```python
# En src/email_service.py
def _load_smtp_config(self) -> Dict[str, Any]:
    return {
        'host': os.getenv('SMTP_HOST', 'smtp.gmail.com'),
        'port': int(os.getenv('SMTP_PORT', '587')),
        'username': os.getenv('SMTP_USERNAME', 'info@swat-id.com'),
        'password': os.getenv('SMTP_PASSWORD', 'pysn fxgf hxzl hevi'),
        'use_tls': os.getenv('SMTP_USE_TLS', 'true').lower() == 'true',
        'use_ssl': os.getenv('SMTP_USE_SSL', 'false').lower() == 'true',
        'from_email': os.getenv('SMTP_FROM_EMAIL', 'info@swat-id.com'),
        'from_name': os.getenv('SMTP_FROM_NAME', 'Sistema de Alarmas Parking Altea')
    }
```

#### Opción 2: Variables de Entorno

Para mayor seguridad, se pueden usar variables de entorno:

```bash
# Configurar variables de entorno
export SMTP_HOST=smtp.gmail.com
export SMTP_PORT=587
export SMTP_USERNAME=info@swat-id.com
export SMTP_PASSWORD=pysn fxgf hxzl hevi
export SMTP_FROM_EMAIL=info@swat-id.com
export SMTP_FROM_NAME='Sistema de Alarmas Parking Altea'
```

### 🧪 Prueba de Configuración

#### Script de Prueba Automático

```bash
# Ejecutar script de prueba
python test_gmail_config.py
```

Este script:
1. Verifica la configuración SMTP
2. Prueba la conexión con Gmail
3. Envía un email de prueba
4. Muestra instrucciones detalladas

#### Prueba Manual

```python
from src.email_service import EmailService

# Crear instancia
email_service = EmailService()

# Probar conexión
if email_service.test_connection():
    print("✅ Conexión exitosa")
    
    # Enviar email de prueba
    test_data = {
        'alarm_id': 1,
        'severity': 'NORMAL',
        'message': 'Prueba de configuración',
        'configuration_name': 'Test',
        'created_at': '2025-07-28T15:00:00Z'
    }
    
    success = email_service.send_alarm_notification('destino@email.com', test_data)
    print(f"Email enviado: {success}")
else:
    print("❌ Error de conexión")
```

### 📧 Plantillas de Email

El sistema incluye plantillas HTML y texto plano para:

#### Email de Alarma
- **Asunto**: `🚨 ALARMA {SEVERIDAD} - {CONFIGURACIÓN}`
- **Contenido**: Detalles de la alarma, equipos afectados, acciones recomendadas
- **Colores**: Naranja (LEVE), Naranja rojizo (NORMAL), Rojo (GRAVE)

#### Email de Resolución
- **Asunto**: `✅ ALARMA RESUELTA - {CONFIGURACIÓN}`
- **Contenido**: Confirmación de resolución, descripción de acciones tomadas
- **Color**: Verde (#28a745)

### 🔍 Solución de Problemas

#### Error de Autenticación

```
SMTPAuthenticationError: (535, b'5.7.8 Username and Password not accepted')
```

**Soluciones**:
1. Verificar que la verificación en dos pasos esté habilitada
2. Generar una nueva clave de aplicación
3. Verificar que la clave no tenga espacios adicionales

#### Error de Conexión

```
SMTPConnectError: (421, b'4.7.0 Try again later')
```

**Soluciones**:
1. Verificar conectividad a internet
2. Verificar que el puerto 587 no esté bloqueado
3. Intentar más tarde (límite de Gmail)

#### Email en Spam

**Soluciones**:
1. Configurar SPF, DKIM y DMARC en el dominio
2. Usar un email corporativo verificado
3. Solicitar al destinatario marcar como "no spam"

### 📊 Monitoreo y Logs

El sistema registra todas las operaciones de email:

```python
# Logs de éxito
logger.info(f"Email enviado exitosamente a {to_email} desde {self.from_email}")

# Logs de error
logger.error(f"Error de autenticación SMTP para {to_email}: {e}")
logger.error("Verificar que la clave de aplicación sea correcta")
```

### 🔄 Actualización de Configuración

Para cambiar la configuración:

1. **Modificar valores por defecto**: Editar `src/email_service.py`
2. **Usar variables de entorno**: Configurar en el sistema
3. **Reiniciar servicios**: Después de cambios

### 📞 Soporte

En caso de problemas:
1. Ejecutar `python test_gmail_config.py`
2. Revisar logs del sistema
3. Verificar configuración de Gmail
4. Contactar administrador del sistema

---

**Nota**: Esta configuración está optimizada para Gmail y utiliza TLS por defecto. Para otros proveedores de email, se pueden modificar los parámetros SMTP. 