# Guía de Desarrollo del Servicio PanelSender

## Descripción General

El servicio PanelSender es un sistema de control de paneles LED que permite enviar texto y contenido a múltiples pantallas LED de forma simultánea. El servicio se ejecuta como un proceso en segundo plano en un servidor Ubuntu y expone una API REST para recibir comandos de control.

## Arquitectura del Sistema

### Componentes Principales
1. **Servicio Java**: Controlador de paneles LED (protocol.jar)
2. **API REST**: Interfaz HTTP para recibir comandos
3. **Base de Datos**: PostgreSQL para almacenar configuración y logs
4. **Frontend**: React Vite para interfaz de usuario

### Flujo de Comunicación
```
Frontend → API REST → Servicio Java → Paneles LED
```

## Especificación Técnica del Servicio

### 1. Configuración del Servicio

#### Estructura de Directorios
```
/opt/panelsender/
├── service/
│   ├── panel-controller.jar
│   ├── protocol.jar
│   ├── config/
│   │   ├── application.properties
│   │   └── panels.json
│   ├── logs/
│   └── scripts/
│       ├── start.sh
│       ├── stop.sh
│       └── restart.sh
├── api/
│   ├── server.js
│   ├── package.json
│   └── routes/
└── frontend/
    ├── dist/
    └── src/
```

#### Configuración de Paneles (panels.json)
```json
{
  "panels": [
    {
      "id": "panel_0",
      "ip": "192.168.1.221",
      "port": 5200,
      "description": "Panel Principal",
      "enabled": true,
      "windows": [
        {
          "id": 0,
          "coordinates": [0, 0, 32, 16],
          "description": "Ventana Izquierda"
        },
        {
          "id": 1,
          "coordinates": [32, 0, 32, 16],
          "description": "Ventana Derecha"
        }
      ]
    },
    {
      "id": "panel_1",
      "ip": "192.168.1.222",
      "port": 5200,
      "description": "Panel Secundario",
      "enabled": true,
      "windows": [
        {
          "id": 0,
          "coordinates": [0, 0, 32, 16],
          "description": "Ventana Izquierda"
        },
        {
          "id": 1,
          "coordinates": [32, 0, 32, 16],
          "description": "Ventana Derecha"
        }
      ]
    }
  ],
  "defaults": {
    "color": 1,
    "fontSize": 2,
    "speed": 100,
    "effect": 1,
    "stayTime": 50,
    "alignmentH": 0,
    "alignmentV": 0
  }
}
```

### 2. API REST Specification

#### Endpoint Base
```
POST /api/v1/panels/send
```

#### Request Body Schema
```json
{
  "panels": [
    {
      "ip": "192.168.1.221",
      "windows": [
        {
          "id": 0,
          "text": "Texto Izquierda",
          "color": 1,
          "fontSize": 2,
          "speed": 100,
          "effect": 1,
          "stayTime": 50,
          "alignmentH": 0,
          "alignmentV": 0
        },
        {
          "id": 1,
          "text": "Texto Derecha",
          "color": 2,
          "fontSize": 3,
          "speed": 150,
          "effect": 2,
          "stayTime": 100,
          "alignmentH": 1,
          "alignmentV": 1
        }
      ]
    },
    {
      "ip": "192.168.1.222",
      "windows": [
        {
          "id": 0,
          "text": "Panel 2 Izq",
          "color": 1,
          "fontSize": 2,
          "speed": 100,
          "effect": 1,
          "stayTime": 50,
          "alignmentH": 0,
          "alignmentV": 0
        }
      ]
    }
  ],
  "options": {
    "sequential": false,
    "timeout": 30000,
    "retryAttempts": 3
  }
}
```

#### Response Schema
```json
{
  "success": true,
  "message": "Comandos enviados correctamente",
  "data": {
    "totalPanels": 2,
    "totalWindows": 3,
    "results": [
      {
        "ip": "192.168.1.221",
        "success": true,
        "windows": [
          {
            "id": 0,
            "success": true,
            "message": "Texto enviado correctamente"
          },
          {
            "id": 1,
            "success": true,
            "message": "Texto enviado correctamente"
          }
        ]
      },
      {
        "ip": "192.168.1.222",
        "success": true,
        "windows": [
          {
            "id": 0,
            "success": true,
            "message": "Texto enviado correctamente"
          }
        ]
      }
    ]
  },
  "timestamp": "2025-07-03T16:30:00Z"
}
```

#### Parámetros de Texto

| Parámetro | Tipo | Descripción | Valores |
|-----------|------|-------------|---------|
| `color` | int | Color del texto | 1=Rojo, 2=Verde, 3=Azul, 4=Amarillo, 5=Magenta, 6=Cian, 7=Blanco |
| `fontSize` | int | Tamaño de fuente | 1=8px, 2=16px, 3=24px, 4=32px |
| `speed` | int | Velocidad de scroll (ms) | 50-500 |
| `effect` | int | Efecto de visualización | 1=Scroll, 2=Static, 3=Blink |
| `stayTime` | int | Tiempo de permanencia (ms) | 10-1000 |
| `alignmentH` | int | Alineación horizontal | 0=Izquierda, 1=Centro, 2=Derecha |
| `alignmentV` | int | Alineación vertical | 0=Arriba, 1=Centro, 2=Abajo |

### 3. Implementación del Servicio Java

#### Clase Principal: PanelService
```java
public class PanelService {
    private static PanelService instance;
    private Map<String, PanelController> panelControllers;
    private PanelConfiguration config;
    private Logger logger;
    
    public static PanelService getInstance() {
        if (instance == null) {
            instance = new PanelService();
        }
        return instance;
    }
    
    public void initialize() {
        // Cargar configuración
        // Inicializar controladores
        // Configurar logging
    }
    
    public SendResult sendToPanels(SendRequest request) {
        // Procesar request
        // Enviar a paneles
        // Retornar resultados
    }
    
    public void shutdown() {
        // Cerrar conexiones
        // Limpiar recursos
    }
}
```

#### Clase: SendRequest
```java
public class SendRequest {
    private List<PanelRequest> panels;
    private SendOptions options;
    
    // Getters y setters
}

public class PanelRequest {
    private String ip;
    private List<WindowRequest> windows;
    
    // Getters y setters
}

public class WindowRequest {
    private int id;
    private String text;
    private int color;
    private int fontSize;
    private int speed;
    private int effect;
    private int stayTime;
    private int alignmentH;
    private int alignmentV;
    
    // Getters y setters
}
```

#### Clase: SendResult
```java
public class SendResult {
    private boolean success;
    private String message;
    private List<PanelResult> results;
    private long timestamp;
    
    // Getters y setters
}

public class PanelResult {
    private String ip;
    private boolean success;
    private List<WindowResult> windows;
    private String errorMessage;
    
    // Getters y setters
}

public class WindowResult {
    private int id;
    private boolean success;
    private String message;
    private String errorMessage;
    
    // Getters y setters
}
```

### 4. Implementación del Servidor NodeJS

#### Estructura del Servidor
```javascript
// server.js
const express = require('express');
const { spawn } = require('child_process');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json());

// Middleware de logging
app.use((req, res, next) => {
    console.log(`${new Date().toISOString()} - ${req.method} ${req.path}`);
    next();
});

// Endpoint principal
app.post('/api/v1/panels/send', async (req, res) => {
    try {
        const result = await sendToPanels(req.body);
        res.json(result);
    } catch (error) {
        res.status(500).json({
            success: false,
            message: error.message,
            timestamp: new Date().toISOString()
        });
    }
});

// Endpoint de estado
app.get('/api/v1/status', (req, res) => {
    res.json({
        status: 'running',
        timestamp: new Date().toISOString(),
        version: '1.0.0'
    });
});

app.listen(PORT, () => {
    console.log(`PanelSender API running on port ${PORT}`);
});
```

#### Función de Envío
```javascript
async function sendToPanels(request) {
    return new Promise((resolve, reject) => {
        const javaProcess = spawn('java', [
            '-cp', '/opt/panelsender/service/*',
            'com.panelsender.PanelService'
        ], {
            cwd: '/opt/panelsender/service'
        });
        
        let output = '';
        let errorOutput = '';
        
        javaProcess.stdout.on('data', (data) => {
            output += data.toString();
        });
        
        javaProcess.stderr.on('data', (data) => {
            errorOutput += data.toString();
        });
        
        javaProcess.on('close', (code) => {
            if (code === 0) {
                try {
                    const result = JSON.parse(output);
                    resolve(result);
                } catch (error) {
                    reject(new Error('Invalid response from Java service'));
                }
            } else {
                reject(new Error(`Java service failed: ${errorOutput}`));
            }
        });
        
        // Enviar request como JSON
        javaProcess.stdin.write(JSON.stringify(request));
        javaProcess.stdin.end();
    });
}
```

### 5. Scripts de Despliegue

#### Script de Inicio (start.sh)
```bash
#!/bin/bash

# PanelSender Service Startup Script
# Ubicación: /opt/panelsender/scripts/start.sh

SERVICE_DIR="/opt/panelsender"
LOG_DIR="$SERVICE_DIR/logs"
PID_FILE="$SERVICE_DIR/service.pid"

# Crear directorios si no existen
mkdir -p $LOG_DIR

# Verificar si el servicio ya está ejecutándose
if [ -f $PID_FILE ]; then
    PID=$(cat $PID_FILE)
    if ps -p $PID > /dev/null 2>&1; then
        echo "PanelSender service is already running (PID: $PID)"
        exit 1
    else
        rm -f $PID_FILE
    fi
fi

# Iniciar servicio Java
echo "Starting PanelSender Java service..."
cd $SERVICE_DIR/service
nohup java -cp ".:protocol.jar:panel-controller.jar" \
    -Djava.library.path=. \
    -Dlogback.configurationFile=logback.xml \
    com.panelsender.PanelService > $LOG_DIR/java-service.log 2>&1 &
JAVA_PID=$!

# Iniciar API NodeJS
echo "Starting PanelSender API..."
cd $SERVICE_DIR/api
nohup node server.js > $LOG_DIR/api.log 2>&1 &
API_PID=$!

# Guardar PIDs
echo $JAVA_PID > $PID_FILE
echo $API_PID >> $PID_FILE

echo "PanelSender service started successfully"
echo "Java Service PID: $JAVA_PID"
echo "API Service PID: $API_PID"
echo "Logs: $LOG_DIR"
```

#### Script de Parada (stop.sh)
```bash
#!/bin/bash

# PanelSender Service Stop Script
# Ubicación: /opt/panelsender/scripts/stop.sh

SERVICE_DIR="/opt/panelsender"
PID_FILE="$SERVICE_DIR/service.pid"

if [ -f $PID_FILE ]; then
    echo "Stopping PanelSender service..."
    
    while read -r PID; do
        if ps -p $PID > /dev/null 2>&1; then
            echo "Stopping process $PID..."
            kill $PID
            
            # Esperar hasta 10 segundos
            for i in {1..10}; do
                if ! ps -p $PID > /dev/null 2>&1; then
                    break
                fi
                sleep 1
            done
            
            # Forzar parada si es necesario
            if ps -p $PID > /dev/null 2>&1; then
                echo "Force killing process $PID..."
                kill -9 $PID
            fi
        fi
    done < $PID_FILE
    
    rm -f $PID_FILE
    echo "PanelSender service stopped"
else
    echo "PanelSender service is not running"
fi
```

#### Script de Reinicio (restart.sh)
```bash
#!/bin/bash

# PanelSender Service Restart Script
# Ubicación: /opt/panelsender/scripts/restart.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_DIR="$(dirname "$SCRIPT_DIR")"

echo "Restarting PanelSender service..."

# Parar servicio
$SCRIPT_DIR/stop.sh

# Esperar un momento
sleep 2

# Iniciar servicio
$SCRIPT_DIR/start.sh

echo "PanelSender service restarted"
```

### 6. Configuración de Sistema (systemd)

#### Archivo de Servicio (/etc/systemd/system/panelsender.service)
```ini
[Unit]
Description=PanelSender LED Panel Control Service
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=forking
User=panelsender
Group=panelsender
WorkingDirectory=/opt/panelsender
ExecStart=/opt/panelsender/scripts/start.sh
ExecStop=/opt/panelsender/scripts/stop.sh
ExecReload=/opt/panelsender/scripts/restart.sh
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### 7. Configuración de Base de Datos

#### Esquema PostgreSQL
```sql
-- Crear base de datos
CREATE DATABASE panelsender;

-- Crear usuario
CREATE USER panelsender WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE panelsender TO panelsender;

-- Conectar a la base de datos
\c panelsender

-- Tabla de paneles
CREATE TABLE panels (
    id SERIAL PRIMARY KEY,
    panel_id VARCHAR(50) UNIQUE NOT NULL,
    ip_address INET NOT NULL,
    port INTEGER DEFAULT 5200,
    description TEXT,
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de ventanas
CREATE TABLE windows (
    id SERIAL PRIMARY KEY,
    panel_id VARCHAR(50) REFERENCES panels(panel_id),
    window_id INTEGER NOT NULL,
    coordinates INTEGER[] NOT NULL, -- [left, top, right, bottom]
    description TEXT,
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de comandos enviados
CREATE TABLE commands (
    id SERIAL PRIMARY KEY,
    panel_id VARCHAR(50) REFERENCES panels(panel_id),
    window_id INTEGER,
    text_content TEXT NOT NULL,
    color INTEGER DEFAULT 1,
    font_size INTEGER DEFAULT 2,
    speed INTEGER DEFAULT 100,
    effect INTEGER DEFAULT 1,
    stay_time INTEGER DEFAULT 50,
    alignment_h INTEGER DEFAULT 0,
    alignment_v INTEGER DEFAULT 0,
    success BOOLEAN,
    error_message TEXT,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de logs del sistema
CREATE TABLE system_logs (
    id SERIAL PRIMARY KEY,
    level VARCHAR(10) NOT NULL,
    message TEXT NOT NULL,
    details JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para optimización
CREATE INDEX idx_commands_panel_id ON commands(panel_id);
CREATE INDEX idx_commands_sent_at ON commands(sent_at);
CREATE INDEX idx_system_logs_level ON system_logs(level);
CREATE INDEX idx_system_logs_created_at ON system_logs(created_at);
```

### 8. Configuración de Logging

#### Logback Configuration (logback.xml)
```xml
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
    <property name="LOG_DIR" value="/opt/panelsender/logs"/>
    
    <!-- Console Appender -->
    <appender name="CONSOLE" class="ch.qos.logback.core.ConsoleAppender">
        <encoder>
            <pattern>%d{yyyy-MM-dd HH:mm:ss.SSS} [%thread] %-5level %logger{36} - %msg%n</pattern>
        </encoder>
    </appender>
    
    <!-- File Appender -->
    <appender name="FILE" class="ch.qos.logback.core.rolling.RollingFileAppender">
        <file>${LOG_DIR}/panelsender.log</file>
        <rollingPolicy class="ch.qos.logback.core.rolling.TimeBasedRollingPolicy">
            <fileNamePattern>${LOG_DIR}/panelsender.%d{yyyy-MM-dd}.log</fileNamePattern>
            <maxHistory>30</maxHistory>
        </rollingPolicy>
        <encoder>
            <pattern>%d{yyyy-MM-dd HH:mm:ss.SSS} [%thread] %-5level %logger{36} - %msg%n</pattern>
        </encoder>
    </appender>
    
    <!-- API Calls Appender -->
    <appender name="API_FILE" class="ch.qos.logback.core.rolling.RollingFileAppender">
        <file>${LOG_DIR}/api-calls.log</file>
        <rollingPolicy class="ch.qos.logback.core.rolling.TimeBasedRollingPolicy">
            <fileNamePattern>${LOG_DIR}/api-calls.%d{yyyy-MM-dd}.log</fileNamePattern>
            <maxHistory>30</maxHistory>
        </rollingPolicy>
        <encoder>
            <pattern>%d{yyyy-MM-dd HH:mm:ss.SSS} - %msg%n</pattern>
        </encoder>
    </appender>
    
    <!-- Logger específico para API calls -->
    <logger name="com.panelsender.api" level="INFO" additivity="false">
        <appender-ref ref="API_FILE"/>
        <appender-ref ref="CONSOLE"/>
    </logger>
    
    <!-- Root Logger -->
    <root level="INFO">
        <appender-ref ref="CONSOLE"/>
        <appender-ref ref="FILE"/>
    </root>
</configuration>
```

### 9. Instalación en Ubuntu

#### Script de Instalación (install.sh)
```bash
#!/bin/bash

# PanelSender Installation Script for Ubuntu
# Ejecutar como root: sudo ./install.sh

set -e

echo "Installing PanelSender Service..."

# Actualizar sistema
apt-get update
apt-get upgrade -y

# Instalar dependencias
apt-get install -y \
    openjdk-11-jdk \
    nodejs \
    npm \
    postgresql \
    postgresql-contrib \
    nginx \
    curl \
    wget \
    unzip

# Crear usuario del servicio
useradd -r -s /bin/false panelsender

# Crear directorios
mkdir -p /opt/panelsender/{service,api,frontend,logs,scripts,config}
chown -R panelsender:panelsender /opt/panelsender

# Copiar archivos del servicio
cp panel-controller.jar /opt/panelsender/service/
cp protocol.jar /opt/panelsender/service/
cp -r config/* /opt/panelsender/config/

# Instalar dependencias NodeJS
cd /opt/panelsender/api
npm install

# Configurar base de datos
sudo -u postgres psql -c "CREATE DATABASE panelsender;"
sudo -u postgres psql -c "CREATE USER panelsender WITH PASSWORD 'secure_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE panelsender TO panelsender;"

# Copiar scripts
cp scripts/* /opt/panelsender/scripts/
chmod +x /opt/panelsender/scripts/*.sh

# Configurar systemd
cp systemd/panelsender.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable panelsender

# Configurar nginx
cp nginx/panelsender.conf /etc/nginx/sites-available/panelsender
ln -s /etc/nginx/sites-available/panelsender /etc/nginx/sites-enabled/
systemctl restart nginx

# Configurar firewall
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 3000/tcp

echo "PanelSender installation completed!"
echo "To start the service: sudo systemctl start panelsender"
echo "To check status: sudo systemctl status panelsender"
```

### 10. Configuración de Nginx

#### Archivo de Configuración (/etc/nginx/sites-available/panelsender)
```nginx
server {
    listen 80;
    server_name panelsender.local;
    
    # Redirigir a HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name panelsender.local;
    
    # SSL Configuration
    ssl_certificate /etc/ssl/certs/panelsender.crt;
    ssl_certificate_key /etc/ssl/private/panelsender.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";
    
    # API Proxy
    location /api/ {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
    
    # Frontend
    location / {
        root /opt/panelsender/frontend/dist;
        try_files $uri $uri/ /index.html;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
    
    # Health check
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
```

### 11. Monitoreo y Mantenimiento

#### Script de Monitoreo (monitor.sh)
```bash
#!/bin/bash

# PanelSender Monitoring Script
# Ubicación: /opt/panelsender/scripts/monitor.sh

SERVICE_DIR="/opt/panelsender"
LOG_DIR="$SERVICE_DIR/logs"
PID_FILE="$SERVICE_DIR/service.pid"

echo "=== PanelSender Service Monitor ==="
echo "Timestamp: $(date)"
echo

# Verificar procesos
if [ -f $PID_FILE ]; then
    echo "Service PIDs:"
    while read -r PID; do
        if ps -p $PID > /dev/null 2>&1; then
            echo "  PID $PID: RUNNING"
        else
            echo "  PID $PID: STOPPED"
        fi
    done < $PID_FILE
else
    echo "Service PID file not found"
fi

echo

# Verificar puertos
echo "Port Status:"
if netstat -tlnp | grep :3000 > /dev/null; then
    echo "  Port 3000 (API): LISTENING"
else
    echo "  Port 3000 (API): NOT LISTENING"
fi

if netstat -tlnp | grep :80 > /dev/null; then
    echo "  Port 80 (HTTP): LISTENING"
else
    echo "  Port 80 (HTTP): NOT LISTENING"
fi

echo

# Verificar logs recientes
echo "Recent Log Entries:"
tail -n 5 $LOG_DIR/panelsender.log

echo

# Verificar espacio en disco
echo "Disk Usage:"
df -h $SERVICE_DIR

echo

# Verificar memoria
echo "Memory Usage:"
free -h
```

#### Cron Job para Monitoreo
```bash
# Agregar al crontab del usuario root
# */5 * * * * /opt/panelsender/scripts/monitor.sh >> /opt/panelsender/logs/monitor.log 2>&1
```

### 12. Testing y Validación

#### Script de Pruebas (test.sh)
```bash
#!/bin/bash

# PanelSender Test Script
# Ubicación: /opt/panelsender/scripts/test.sh

API_URL="http://localhost:3000/api/v1"

echo "Testing PanelSender API..."

# Test 1: Health Check
echo "1. Testing health endpoint..."
curl -s "$API_URL/status" | jq '.'

# Test 2: Send to single panel
echo "2. Testing single panel send..."
curl -s -X POST "$API_URL/panels/send" \
  -H "Content-Type: application/json" \
  -d '{
    "panels": [
      {
        "ip": "192.168.1.221",
        "windows": [
          {
            "id": 0,
            "text": "TEST",
            "color": 1,
            "fontSize": 2,
            "speed": 100,
            "effect": 1,
            "stayTime": 50,
            "alignmentH": 0,
            "alignmentV": 0
          }
        ]
      }
    ]
  }' | jq '.'

# Test 3: Send to multiple panels
echo "3. Testing multiple panels send..."
curl -s -X POST "$API_URL/panels/send" \
  -H "Content-Type: application/json" \
  -d '{
    "panels": [
      {
        "ip": "192.168.1.221",
        "windows": [
          {
            "id": 0,
            "text": "LEFT",
            "color": 1,
            "fontSize": 2,
            "speed": 100,
            "effect": 1,
            "stayTime": 50,
            "alignmentH": 0,
            "alignmentV": 0
          },
          {
            "id": 1,
            "text": "RIGHT",
            "color": 2,
            "fontSize": 2,
            "speed": 100,
            "effect": 1,
            "stayTime": 50,
            "alignmentH": 0,
            "alignmentV": 0
          }
        ]
      },
      {
        "ip": "192.168.1.222",
        "windows": [
          {
            "id": 0,
            "text": "PANEL2",
            "color": 3,
            "fontSize": 2,
            "speed": 100,
            "effect": 1,
            "stayTime": 50,
            "alignmentH": 0,
            "alignmentV": 0
          }
        ]
      }
    ]
  }' | jq '.'

echo "Testing completed!"
```

### 13. Consideraciones de Seguridad

1. **Firewall**: Configurar ufw para permitir solo puertos necesarios
2. **SSL/TLS**: Usar certificados válidos para HTTPS
3. **Autenticación**: Implementar JWT para la API
4. **Rate Limiting**: Limitar requests por IP
5. **Logging**: Registrar todos los accesos y errores
6. **Backups**: Respaldar configuración y logs regularmente

### 14. Troubleshooting

#### Problemas Comunes

1. **Servicio no inicia**:
   ```bash
   sudo systemctl status panelsender
   sudo journalctl -u panelsender -f
   ```

2. **API no responde**:
   ```bash
   curl http://localhost:3000/api/v1/status
   netstat -tlnp | grep :3000
   ```

3. **Paneles no responden**:
   ```bash
   ping 192.168.1.221
   telnet 192.168.1.221 5200
   ```

4. **Logs de error**:
   ```bash
   tail -f /opt/panelsender/logs/panelsender.log
   tail -f /opt/panelsender/logs/api.log
   ```

Esta documentación proporciona una guía completa para desarrollar e implementar el servicio PanelSender en un servidor Ubuntu. Cada sección incluye ejemplos de código, configuraciones y scripts necesarios para el despliegue en producción. 