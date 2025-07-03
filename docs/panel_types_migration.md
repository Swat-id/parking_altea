# Migración de Tipos de Paneles - Documentación

## Descripción General

Esta migración actualiza el sistema Parking Altea para soportar tres tipos diferentes de paneles LED, cada uno con su propio protocolo y configuración específica.

## Tipos de Paneles Soportados

### Panel Tipo 1: Protocolo Antiguo
- **Fabricante**: Rotulos Electrónicos
- **Configuración**: 1 ventana, 1 línea 64x16
- **Protocolo**: Antiguo (Panel Service v1)
- **Endpoint**: `http://localhost:3000/api/panels/send`
- **Características**:
  - Una sola ventana que ocupa todo el panel
  - Texto simple con colores básicos
  - Efectos limitados (static, scroll)

### Panel Tipo 2: Protocolo Nuevo - 1 Ventana
- **Fabricante**: Rotulos Electrónicos
- **Configuración**: 1 ventana, 1 línea 64x16
- **Protocolo**: Nuevo (Panel Service v2)
- **Endpoint**: `http://localhost:5657/api/v1/panels/send`
- **Características**:
  - Una ventana que ocupa todo el panel
  - Texto con efectos avanzados
  - Colores RGB completos
  - Animaciones y transiciones

### Panel Tipo 3: Protocolo Nuevo - 2 Ventanas
- **Fabricante**: Rotulos Electrónicos
- **Configuración**: 2 ventanas, 32x16 cada una
- **Protocolo**: Nuevo (Panel Service v2)
- **Endpoint**: `http://localhost:5657/api/v1/panels/send`
- **Características**:
  - Dos ventanas independientes
  - Cada ventana puede mostrar contenido diferente
  - Configuración flexible de coordenadas
  - Efectos avanzados por ventana

## Cambios en la Base de Datos

### Nuevas Tablas

#### 1. Tabla `manufacturers`
```sql
CREATE TABLE manufacturers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    website VARCHAR(255),
    contact_email VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### 2. Tabla `panel_types`
```sql
CREATE TABLE panel_types (
    id SERIAL PRIMARY KEY,
    manufacturer_id INTEGER NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    protocol_type VARCHAR(50) NOT NULL, -- 'old', 'new'
    windows_count INTEGER NOT NULL DEFAULT 1,
    window_width INTEGER NOT NULL,
    window_height INTEGER NOT NULL,
    total_width INTEGER NOT NULL,
    total_height INTEGER NOT NULL,
    port INTEGER NOT NULL DEFAULT 5200,
    service_endpoint VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    FOREIGN KEY (manufacturer_id) REFERENCES manufacturers(id)
);
```

### Modificaciones en Tabla Existente

#### Tabla `panels` - Nuevos Campos
```sql
ALTER TABLE panels 
ADD COLUMN panel_type_id INTEGER,
ADD COLUMN port INTEGER DEFAULT 5200,
ADD COLUMN window_config JSONB,
ADD COLUMN protocol_version VARCHAR(20) DEFAULT 'old',
ADD COLUMN service_endpoint VARCHAR(255),
ADD COLUMN is_active BOOLEAN DEFAULT TRUE,
ADD COLUMN last_protocol_check TIMESTAMP WITH TIME ZONE,
ADD COLUMN protocol_status VARCHAR(20) DEFAULT 'unknown';
```

### Índices Creados
```sql
CREATE INDEX idx_panels_panel_type_id ON panels(panel_type_id);
CREATE INDEX idx_panels_protocol_version ON panels(protocol_version);
CREATE INDEX idx_panels_is_active ON panels(is_active);
CREATE INDEX idx_panel_types_manufacturer_id ON panel_types(manufacturer_id);
CREATE INDEX idx_panel_types_protocol_type ON panel_types(protocol_type);
CREATE INDEX idx_panel_types_is_active ON panel_types(is_active);
```

## Datos Iniciales

### Fabricante
```sql
INSERT INTO manufacturers (name, description, website, contact_email)
VALUES (
    'Rotulos Electrónicos',
    'Fabricante especializado en paneles LED para sistemas de parking y señalización',
    'https://www.rotuloselectronicos.com',
    'info@rotuloselectronicos.com'
);
```

### Tipos de Paneles
```sql
-- Panel Tipo 1: Protocolo Antiguo
INSERT INTO panel_types (
    manufacturer_id, name, description, protocol_type, 
    windows_count, window_width, window_height, 
    total_width, total_height, port, service_endpoint
) VALUES (
    1, 'Panel Tipo 1 - Protocolo Antiguo',
    'Panel Rotulos Electrónicos con 1 ventana, 1 línea 64x16, protocolo antiguo',
    'old', 1, 64, 16, 64, 16, 5200,
    'http://localhost:3000/api/panels/send'
);

-- Panel Tipo 2: Protocolo Nuevo 1 Ventana
INSERT INTO panel_types (
    manufacturer_id, name, description, protocol_type, 
    windows_count, window_width, window_height, 
    total_width, total_height, port, service_endpoint
) VALUES (
    1, 'Panel Tipo 2 - Protocolo Nuevo 1 Ventana',
    'Panel Rotulos Electrónicos con 1 ventana, 1 línea 64x16, protocolo nuevo',
    'new', 1, 64, 16, 64, 16, 5200,
    'http://localhost:5657/api/v1/panels/send'
);

-- Panel Tipo 3: Protocolo Nuevo 2 Ventanas
INSERT INTO panel_types (
    manufacturer_id, name, description, protocol_type, 
    windows_count, window_width, window_height, 
    total_width, total_height, port, service_endpoint
) VALUES (
    1, 'Panel Tipo 3 - Protocolo Nuevo 2 Ventanas',
    'Panel Rotulos Electrónicos con 2 ventanas, 32x16 cada una, protocolo nuevo',
    'new', 2, 32, 16, 64, 16, 5200,
    'http://localhost:5657/api/v1/panels/send'
);
```

## Migración de Datos Existentes

### Paneles Existentes
Todos los paneles existentes se migran automáticamente al **Tipo 1 (Protocolo Antiguo)**:

```sql
UPDATE panels 
SET 
    panel_type_id = (SELECT id FROM panel_types WHERE name LIKE '%Protocolo Antiguo%'),
    protocol_version = 'old',
    service_endpoint = 'http://localhost:3000/api/panels/send',
    window_config = '{"windows": [{"id": 0, "coordinates": [0, 0, 64, 16], "description": "Ventana Principal"}]}',
    is_active = TRUE
WHERE panel_type_id IS NULL;
```

## Configuración de Ventanas

### Panel Tipo 1 (1 Ventana)
```json
{
  "windows": [
    {
      "id": 0,
      "coordinates": [0, 0, 64, 16],
      "description": "Ventana Principal"
    }
  ]
}
```

### Panel Tipo 2 (1 Ventana)
```json
{
  "windows": [
    {
      "id": 0,
      "coordinates": [0, 0, 64, 16],
      "description": "Ventana Principal"
    }
  ]
}
```

### Panel Tipo 3 (2 Ventanas)
```json
{
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
```

## Ejecución de la Migración

### 1. Preparación
```bash
# Verificar que estamos en el directorio correcto
cd /path/to/parking_altea

# Verificar prerequisitos
python run_migration.py
```

### 2. Backup Automático
El script crea automáticamente un backup de la base de datos antes de la migración:
```bash
# Backup se guarda como: backup_panels_YYYYMMDD_HHMMSS.sql
```

### 3. Ejecutar Migración
```bash
# Ejecutar migración completa
python run_migration.py
```

### 4. Verificación
El script verifica automáticamente que la migración se realizó correctamente:
- Tablas creadas
- Datos insertados
- Paneles migrados
- Índices creados

## Actualización del Frontend

### Nuevos Componentes
- `PanelTypeManager.jsx` - Gestión de tipos de paneles
- `panelTypeService.js` - Servicio para API de tipos de paneles

### Nuevas Funcionalidades
- Lista de tipos de paneles disponibles
- Formulario para crear/editar tipos de paneles
- Selección de tipo de panel por panel individual
- Validación de configuración de ventanas
- Información de protocolos y servicios

## API Endpoints

### Fabricantes
- `GET /api/manufacturers` - Listar fabricantes
- `GET /api/manufacturers/:id` - Obtener fabricante
- `POST /api/manufacturers` - Crear fabricante
- `PUT /api/manufacturers/:id` - Actualizar fabricante
- `DELETE /api/manufacturers/:id` - Eliminar fabricante

### Tipos de Paneles
- `GET /api/panel-types` - Listar tipos de paneles
- `GET /api/panel-types/:id` - Obtener tipo de panel
- `POST /api/panel-types` - Crear tipo de panel
- `PUT /api/panel-types/:id` - Actualizar tipo de panel
- `DELETE /api/panel-types/:id` - Eliminar tipo de panel
- `GET /api/panel-types/stats` - Estadísticas de uso

### Paneles (Actualizado)
- `GET /api/panels/:id?include_type=true` - Obtener panel con tipo
- `PATCH /api/panels/:id/type` - Actualizar tipo de panel

## Gestión desde el Frontend

### Acceso al Gestor de Tipos
1. Ir al menú de administración
2. Seleccionar "Gestión de Paneles"
3. Hacer clic en "Tipos de Paneles"

### Crear Nuevo Tipo
1. Hacer clic en "Nuevo Tipo de Panel"
2. Completar formulario:
   - Nombre y descripción
   - Seleccionar fabricante
   - Configurar protocolo (antiguo/nuevo)
   - Definir número de ventanas
   - Configurar dimensiones
   - Especificar endpoint del servicio
3. Guardar cambios

### Editar Panel Existente
1. Ir a la lista de paneles
2. Seleccionar panel a editar
3. Cambiar tipo de panel según corresponda
4. Guardar cambios

## Validaciones

### Configuración de Ventanas
- Número de ventanas debe coincidir con el tipo
- Dimensiones de ventanas deben ser correctas
- Coordenadas no pueden exceder límites del panel
- Ventanas no pueden solaparse

### Protocolos
- Panel Tipo 1: Solo protocolo antiguo
- Panel Tipo 2: Solo protocolo nuevo
- Panel Tipo 3: Solo protocolo nuevo

### Servicios
- Verificar que el endpoint del servicio esté disponible
- Validar formato de URL
- Comprobar conectividad

## Troubleshooting

### Problemas Comunes

#### 1. Error de Migración
```bash
# Verificar logs
tail -f migration_YYYYMMDD_HHMMSS.log

# Verificar conexión a base de datos
python -c "from src.models import engine; print('Conexión OK')"
```

#### 2. Paneles No Migrados
```sql
-- Verificar paneles sin tipo
SELECT * FROM panels WHERE panel_type_id IS NULL;

-- Migrar manualmente
UPDATE panels SET panel_type_id = 1 WHERE panel_type_id IS NULL;
```

#### 3. Error de Protocolo
```bash
# Verificar servicios
curl http://localhost:3000/api/panels/send
curl http://localhost:5657/api/v1/panels/send

# Reiniciar servicios si es necesario
sudo systemctl restart parking-panel
sudo systemctl restart panel-service-v2
```

#### 4. Error de Frontend
```bash
# Verificar dependencias
cd client && npm install

# Verificar build
npm run build
```

### Logs de Verificación
```bash
# Verificar migración
python verify_migration.py

# Verificar servicios
systemctl status parking-panel
systemctl status panel-service-v2

# Verificar base de datos
psql -d parking_altea -c "SELECT COUNT(*) FROM panel_types;"
```

## Rollback

### Si la Migración Falla
1. **Restaurar backup**:
```bash
psql -d parking_altea < backup_panels_YYYYMMDD_HHMMSS.sql
```

2. **Eliminar tablas nuevas**:
```sql
DROP TABLE IF EXISTS panel_types CASCADE;
DROP TABLE IF EXISTS manufacturers CASCADE;
```

3. **Revertir cambios en tabla panels**:
```sql
ALTER TABLE panels DROP COLUMN IF EXISTS panel_type_id;
ALTER TABLE panels DROP COLUMN IF EXISTS port;
ALTER TABLE panels DROP COLUMN IF EXISTS window_config;
ALTER TABLE panels DROP COLUMN IF EXISTS protocol_version;
ALTER TABLE panels DROP COLUMN IF EXISTS service_endpoint;
ALTER TABLE panels DROP COLUMN IF EXISTS is_active;
ALTER TABLE panels DROP COLUMN IF EXISTS last_protocol_check;
ALTER TABLE panels DROP COLUMN IF EXISTS protocol_status;
```

## Próximos Pasos

### 1. Testing
- [ ] Probar migración en entorno de desarrollo
- [ ] Verificar funcionamiento de todos los tipos de paneles
- [ ] Validar integración con servicios existentes

### 2. Deployment
- [ ] Ejecutar migración en producción
- [ ] Actualizar configuración de servicios
- [ ] Verificar conectividad de paneles

### 3. Documentación
- [ ] Actualizar manual de usuario
- [ ] Crear guías de configuración
- [ ] Documentar casos de uso

### 4. Monitoreo
- [ ] Configurar alertas para servicios
- [ ] Implementar logging avanzado
- [ ] Crear dashboard de estado

## Contacto

Para soporte técnico o consultas sobre la migración:
- **Equipo**: Parking Altea Development Team
- **Email**: info@swat-id.com
- **Documentación**: `/docs/panel_types_migration.md` 