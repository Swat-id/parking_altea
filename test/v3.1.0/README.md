# Tests v3.1.0 - Login System

## 📋 Descripción

Este directorio contiene todos los scripts de prueba para la versión v3.1.0 del sistema de login con roles. Los tests están organizados por funcionalidad y se ejecutan de forma independiente.

## 🗂️ Estructura de Archivos

```
test/v3.1.0/
├── README.md                           # Este archivo
├── test_migration_t1_1_t1_2.py        # Tests para T1.1 y T1.2
├── validate_migration_scripts.py       # Validación de scripts
└── [futuros archivos de test]         # Tests para próximas tareas
```

## 🧪 Scripts de Prueba

### **test_migration_t1_1_t1_2.py**
**Propósito**: Validar las tareas T1.1 y T1.2 completadas

**Funcionalidades probadas**:
- ✅ Campos de base de datos (`role`, `updated_at`)
- ✅ Constraint de validación de roles
- ✅ Índices de optimización
- ✅ Usuarios iniciales creados
- ✅ Asignaciones de parkings
- ✅ Propiedades del modelo User
- ✅ Integridad de datos

**Uso**:
```bash
cd test/v3.1.0
python test_migration_t1_1_t1_2.py
```

### **validate_migration_scripts.py**
**Propósito**: Validar sintaxis y estructura de scripts sin ejecutarlos

**Funcionalidades validadas**:
- ✅ Sintaxis Python de todos los scripts
- ✅ Imports requeridos
- ✅ Funciones críticas
- ✅ SQL queries importantes
- ✅ Estructura de archivos

**Uso**:
```bash
cd test/v3.1.0
python validate_migration_scripts.py
```

## 📊 Estado de los Tests

### **Sprint 1: Base de Datos y Modelos**
- [x] **T1.1** - Script de migración de base de datos
  - [x] Test de campos de base de datos
  - [x] Test de constraint de roles
  - [x] Test de índices
  - [x] Test de usuarios iniciales
  - [x] Test de asignaciones de parkings
  - [x] Test de integridad de datos

- [x] **T1.2** - Actualización de modelos SQLAlchemy
  - [x] Test de propiedades del modelo User
  - [x] Test de campos nuevos
  - [x] Test de métodos helper

- [ ] **T1.3** - Crear datos iniciales
  - [ ] Test de creación de usuarios
  - [ ] Test de asignación de parkings
  - [ ] Test de permisos iniciales

- [ ] **T1.4** - Script de verificación
  - [ ] Test de verificación completa
  - [ ] Test de validación de datos

- [ ] **T1.5** - Tests de migración
  - [ ] Test de rollback
  - [ ] Test de integridad post-migración

### **Próximos Sprints**
- [ ] **Sprint 2**: Tests de autenticación y autorización
- [ ] **Sprint 3**: Tests de frontend y protección de rutas
- [ ] **Sprint 4**: Tests de administración y gestión

## 🔧 Configuración

### **Requisitos**
- Python 3.8+
- SQLAlchemy
- PostgreSQL (para tests de base de datos)
- Acceso a la base de datos del proyecto

### **Variables de Entorno**
Los tests utilizan la configuración del archivo `src/config.py`:
- `DB_URL`: URL de conexión a la base de datos
- Otras configuraciones del proyecto

### **Ejecución Local vs Remota**
- **Local**: Para desarrollo y validación de scripts
- **Remota**: Para validación post-despliegue en el servidor

## 📝 Convenciones de Naming

### **Archivos de Test**
- `test_<funcionalidad>_<tarea>.py`: Tests específicos de tareas
- `validate_<tipo>_<archivo>.py`: Validación de archivos
- `test_<sprint>_<componente>.py`: Tests por sprint

### **Funciones de Test**
- `test_<numero>_<descripcion>`: Tests individuales
- `test_<componente>_<funcionalidad>`: Tests por componente

## 🚨 Consideraciones Importantes

### **Base de Datos**
- Los tests modifican la base de datos
- Ejecutar solo en entorno de desarrollo o servidor de pruebas
- Hacer backup antes de ejecutar tests destructivos

### **Datos de Prueba**
- Los tests crean usuarios de prueba
- Usar emails únicos para evitar conflictos
- Limpiar datos de prueba después de los tests

### **Servidor Remoto**
- Ejecutar tests después del despliegue
- Verificar que los servicios están activos
- Revisar logs en caso de fallos

## 📞 Soporte

### **En caso de Fallos**
1. Revisar logs de la aplicación
2. Verificar conectividad a la base de datos
3. Comprobar permisos de archivos
4. Validar configuración del entorno

### **Debugging**
- Usar `print()` para debug en scripts
- Revisar `sys.path` para imports
- Verificar rutas de archivos

## 🔄 Actualización

Este directorio se actualiza automáticamente con cada nueva tarea del roadmap. Mantener sincronizado con el estado del desarrollo.

---

**Última actualización**: [Fecha]
**Versión**: v3.1.0_login
**Estado**: En desarrollo 