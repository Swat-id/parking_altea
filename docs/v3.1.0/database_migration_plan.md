# Plan de Migración de Base de Datos - v3.1.0

## 📋 Resumen de Cambios

**Versión origen**: v3.0.0  
**Versión destino**: v3.1.0_login  
**Fecha de migración**: Enero 2025  
**Tipo de migración**: Compatible hacia adelante

## 🔄 Cambios en la Base de Datos

### 1. **Tabla `users` - Nuevos Campos**

#### Campos a Agregar
```sql
-- Agregar campo role para diferenciar superadmin y usuario
ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'user' NOT NULL;

-- Agregar campo updated_at para auditoría
ALTER TABLE users ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- Agregar constraint para validar roles
ALTER TABLE users ADD CONSTRAINT chk_user_role 
CHECK (role IN ('superadmin', 'user'));
```

#### Índices a Crear
```sql
-- Índice para búsquedas eficientes por email
CREATE INDEX idx_users_email ON users(email);

-- Índice para filtros por rol
CREATE INDEX idx_users_role ON users(role);

-- Índice compuesto para consultas frecuentes
CREATE INDEX idx_users_active_role ON users(is_active, role);
```

### 2. **Datos Iniciales**

#### Usuarios del Sistema
```sql
-- Usuario superadmin inicial (contraseña: admin123!)
INSERT INTO users (name, email, password_hash, role, created_at, updated_at) VALUES 
(
    'Administrador del Sistema',
    'admin@parking-altea.es',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iQeO',
    'superadmin',
    NOW(),
    NOW()
);

-- Usuario Toni Alos (contraseña: altea2025!)
INSERT INTO users (name, email, password_hash, role, created_at, updated_at) VALUES 
(
    'Toni Alos',
    'atea.dti@altea.es',
    '$2b$12$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy',
    'user',
    NOW(),
    NOW()
);

-- Usuario Iván Martí (contraseña: altea2025!)
INSERT INTO users (name, email, password_hash, role, created_at, updated_at) VALUES 
(
    'Iván Martí',
    'gerenciapstd@altea.es',
    '$2b$12$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy',
    'user',
    NOW(),
    NOW()
);
```

#### Asignaciones Iniciales de Parkings
```sql
-- Asignar todos los parkings al superadmin
INSERT INTO user_parkings (user_id, parking_id, created_at)
SELECT 
    (SELECT id FROM users WHERE email = 'admin@parking-altea.es'),
    id,
    NOW()
FROM parkings;

-- Asignar parkings específicos a Toni Alos
INSERT INTO user_parkings (user_id, parking_id, created_at)
SELECT 
    (SELECT id FROM users WHERE email = 'atea.dti@altea.es'),
    id,
    NOW()
FROM parkings 
WHERE name IN ('P. Ciutat Esportiva', 'P. Port Altea', 'P. Estació Altea');

-- Asignar parkings específicos a Iván Martí
INSERT INTO user_parkings (user_id, parking_id, created_at)
SELECT 
    (SELECT id FROM users WHERE email = 'gerenciapstd@altea.es'),
    id,
    NOW()
FROM parkings 
WHERE name IN ('P. Altea Hills', 'P. Poble antic/Belles Arts 1', 'P. Poble antic/Belles Arts 2');
```

### 3. **Actualización de Modelos SQLAlchemy**

#### Modelo User Actualizado
```python
# src/models.py - Actualización del modelo User

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String(20), default='user', nullable=False)  # NUEVO
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())  # NUEVO
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relaciones existentes
    user_parkings = relationship('UserParking', back_populates='user')
    user_panels = relationship('UserPanel', back_populates='user')
    user_accesses = relationship('UserAccess', back_populates='user')
    
    def __repr__(self):
        return f"<User(id={self.id}, name='{self.name}', email='{self.email}', role='{self.role}')>"
    
    @property
    def is_superadmin(self):
        """Verificar si el usuario es superadmin"""
        return self.role == 'superadmin'
    
    @property
    def is_regular_user(self):
        """Verificar si el usuario es usuario regular"""
        return self.role == 'user'
```

## 📝 Script de Migración Completo

### **Script de Migración Automática**
```python
# scripts/migrate_to_v3_1_0.py

#!/usr/bin/env python3
"""
Script de migración de v3.0.0 a v3.1.0
Actualiza la base de datos para el sistema de login con roles
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import config
import bcrypt
from datetime import datetime

def hash_password(password: str) -> str:
    """Hashea una contraseña usando bcrypt"""
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
    return password_hash.decode('utf-8')

def migrate_database():
    """Ejecutar migración completa de la base de datos"""
    print("🚀 Iniciando migración a v3.1.0...")
    
    # Conectar a la base de datos
    engine = create_engine(config.DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # 1. Agregar campos a la tabla users
        print("📝 Agregando campos a la tabla users...")
        
        # Verificar si el campo role ya existe
        result = session.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'role'
        """))
        
        if not result.fetchone():
            session.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'user' NOT NULL"))
            print("✅ Campo 'role' agregado")
        else:
            print("ℹ️  Campo 'role' ya existe")
        
        # Verificar si el campo updated_at ya existe
        result = session.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'updated_at'
        """))
        
        if not result.fetchone():
            session.execute(text("ALTER TABLE users ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()"))
            print("✅ Campo 'updated_at' agregado")
        else:
            print("ℹ️  Campo 'updated_at' ya existe")
        
        # 2. Crear índices
        print("🔍 Creando índices...")
        
        # Índice en email
        try:
            session.execute(text("CREATE INDEX idx_users_email ON users(email)"))
            print("✅ Índice en email creado")
        except Exception as e:
            if "already exists" in str(e):
                print("ℹ️  Índice en email ya existe")
            else:
                raise e
        
        # Índice en role
        try:
            session.execute(text("CREATE INDEX idx_users_role ON users(role)"))
            print("✅ Índice en role creado")
        except Exception as e:
            if "already exists" in str(e):
                print("ℹ️  Índice en role ya existe")
            else:
                raise e
        
        # Índice compuesto
        try:
            session.execute(text("CREATE INDEX idx_users_active_role ON users(is_active, role)"))
            print("✅ Índice compuesto creado")
        except Exception as e:
            if "already exists" in str(e):
                print("ℹ️  Índice compuesto ya existe")
            else:
                raise e
        
        # 3. Agregar constraint de validación de roles
        print("🔒 Agregando constraint de roles...")
        try:
            session.execute(text("ALTER TABLE users ADD CONSTRAINT chk_user_role CHECK (role IN ('superadmin', 'user'))"))
            print("✅ Constraint de roles agregado")
        except Exception as e:
            if "already exists" in str(e):
                print("ℹ️  Constraint de roles ya existe")
            else:
                raise e
        
        # 4. Crear usuarios iniciales
        print("👥 Creando usuarios iniciales...")
        
        # Verificar si ya existen usuarios
        result = session.execute(text("SELECT COUNT(*) FROM users"))
        user_count = result.fetchone()[0]
        
        if user_count == 0:
            # Crear superadmin
            admin_password_hash = hash_password('admin123!')
            session.execute(text("""
                INSERT INTO users (name, email, password_hash, role, created_at, updated_at) 
                VALUES ('Administrador del Sistema', 'admin@parking-altea.es', :password_hash, 'superadmin', NOW(), NOW())
            """), {'password_hash': admin_password_hash})
            print("✅ Usuario superadmin creado")
            
            # Crear usuarios de ejemplo
            user_password_hash = hash_password('altea2025!')
            
            session.execute(text("""
                INSERT INTO users (name, email, password_hash, role, created_at, updated_at) 
                VALUES ('Toni Alos', 'atea.dti@altea.es', :password_hash, 'user', NOW(), NOW())
            """), {'password_hash': user_password_hash})
            print("✅ Usuario Toni Alos creado")
            
            session.execute(text("""
                INSERT INTO users (name, email, password_hash, role, created_at, updated_at) 
                VALUES ('Iván Martí', 'gerenciapstd@altea.es', :password_hash, 'user', NOW(), NOW())
            """), {'password_hash': user_password_hash})
            print("✅ Usuario Iván Martí creado")
        else:
            print(f"ℹ️  Ya existen {user_count} usuarios en la base de datos")
        
        # 5. Asignar parkings a usuarios
        print("🏢 Asignando parkings a usuarios...")
        
        # Obtener IDs de usuarios
        admin_result = session.execute(text("SELECT id FROM users WHERE email = 'admin@parking-altea.es'"))
        admin_user = admin_result.fetchone()
        
        toni_result = session.execute(text("SELECT id FROM users WHERE email = 'atea.dti@altea.es'"))
        toni_user = toni_result.fetchone()
        
        ivan_result = session.execute(text("SELECT id FROM users WHERE email = 'gerenciapstd@altea.es'"))
        ivan_user = ivan_result.fetchone()
        
        if admin_user:
            # Asignar todos los parkings al superadmin
            session.execute(text("""
                INSERT INTO user_parkings (user_id, parking_id, created_at)
                SELECT :admin_id, id, NOW()
                FROM parkings
                WHERE id NOT IN (SELECT parking_id FROM user_parkings WHERE user_id = :admin_id)
            """), {'admin_id': admin_user[0]})
            print("✅ Parkings asignados al superadmin")
        
        if toni_user:
            # Asignar parkings específicos a Toni Alos
            session.execute(text("""
                INSERT INTO user_parkings (user_id, parking_id, created_at)
                SELECT :toni_id, id, NOW()
                FROM parkings 
                WHERE name IN ('P. Ciutat Esportiva', 'P. Port Altea', 'P. Estació Altea')
                AND id NOT IN (SELECT parking_id FROM user_parkings WHERE user_id = :toni_id)
            """), {'toni_id': toni_user[0]})
            print("✅ Parkings asignados a Toni Alos")
        
        if ivan_user:
            # Asignar parkings específicos a Iván Martí
            session.execute(text("""
                INSERT INTO user_parkings (user_id, parking_id, created_at)
                SELECT :ivan_id, id, NOW()
                FROM parkings 
                WHERE name IN ('P. Altea Hills', 'P. Poble antic/Belles Arts 1', 'P. Poble antic/Belles Arts 2')
                AND id NOT IN (SELECT parking_id FROM user_parkings WHERE user_id = :ivan_id)
            """), {'ivan_id': ivan_user[0]})
            print("✅ Parkings asignados a Iván Martí")
        
        # 6. Actualizar timestamps existentes
        print("🕒 Actualizando timestamps...")
        session.execute(text("""
            UPDATE users 
            SET updated_at = created_at 
            WHERE updated_at IS NULL
        """))
        print("✅ Timestamps actualizados")
        
        # Commit de todos los cambios
        session.commit()
        print("✅ Migración completada exitosamente")
        
        # 7. Mostrar resumen
        print("\n📊 Resumen de la migración:")
        
        result = session.execute(text("SELECT COUNT(*) FROM users"))
        user_count = result.fetchone()[0]
        print(f"   - Usuarios totales: {user_count}")
        
        result = session.execute(text("SELECT role, COUNT(*) FROM users GROUP BY role"))
        for role, count in result.fetchall():
            print(f"   - Usuarios con rol '{role}': {count}")
        
        result = session.execute(text("SELECT COUNT(*) FROM user_parkings"))
        assignment_count = result.fetchone()[0]
        print(f"   - Asignaciones de parkings: {assignment_count}")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error durante la migración: {e}")
        raise e
    finally:
        session.close()

if __name__ == "__main__":
    migrate_database()
```

## 🔄 Script de Rollback

### **Script de Rollback (En caso de problemas)**
```python
# scripts/rollback_v3_1_0.py

#!/usr/bin/env python3
"""
Script de rollback de v3.1.0 a v3.0.0
Revierte los cambios de la migración de login
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import config

def rollback_migration():
    """Revertir migración a v3.1.0"""
    print("⚠️  Iniciando rollback de v3.1.0...")
    
    # Conectar a la base de datos
    engine = create_engine(config.DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # 1. Eliminar asignaciones de parkings
        print("🗑️  Eliminando asignaciones de parkings...")
        session.execute(text("DELETE FROM user_parkings"))
        print("✅ Asignaciones eliminadas")
        
        # 2. Eliminar usuarios creados
        print("👥 Eliminando usuarios...")
        session.execute(text("DELETE FROM users WHERE email IN ('admin@parking-altea.es', 'atea.dti@altea.es', 'gerenciapstd@altea.es')"))
        print("✅ Usuarios eliminados")
        
        # 3. Eliminar índices
        print("🔍 Eliminando índices...")
        try:
            session.execute(text("DROP INDEX IF EXISTS idx_users_email"))
            session.execute(text("DROP INDEX IF EXISTS idx_users_role"))
            session.execute(text("DROP INDEX IF EXISTS idx_users_active_role"))
            print("✅ Índices eliminados")
        except Exception as e:
            print(f"⚠️  Error eliminando índices: {e}")
        
        # 4. Eliminar constraint
        print("🔒 Eliminando constraint...")
        try:
            session.execute(text("ALTER TABLE users DROP CONSTRAINT IF EXISTS chk_user_role"))
            print("✅ Constraint eliminado")
        except Exception as e:
            print(f"⚠️  Error eliminando constraint: {e}")
        
        # 5. Eliminar campos agregados
        print("📝 Eliminando campos...")
        try:
            session.execute(text("ALTER TABLE users DROP COLUMN IF EXISTS updated_at"))
            session.execute(text("ALTER TABLE users DROP COLUMN IF EXISTS role"))
            print("✅ Campos eliminados")
        except Exception as e:
            print(f"⚠️  Error eliminando campos: {e}")
        
        # Commit de todos los cambios
        session.commit()
        print("✅ Rollback completado exitosamente")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error durante el rollback: {e}")
        raise e
    finally:
        session.close()

if __name__ == "__main__":
    rollback_migration()
```

## 📋 Checklist de Migración

### **Pre-Migración**
- [ ] **Backup completo** de la base de datos
- [ ] **Verificar espacio** en disco
- [ ] **Notificar usuarios** del mantenimiento
- [ ] **Preparar rollback** en caso de problemas

### **Durante la Migración**
- [ ] **Ejecutar script** de migración
- [ ] **Verificar logs** de errores
- [ ] **Comprobar integridad** de datos
- [ ] **Validar constraints** y índices

### **Post-Migración**
- [ ] **Verificar usuarios** creados
- [ ] **Comprobar asignaciones** de parkings
- [ ] **Testear autenticación** con nuevos usuarios
- [ ] **Validar permisos** y roles
- [ ] **Actualizar documentación**

## 🔍 Verificación de la Migración

### **Script de Verificación**
```python
# scripts/verify_migration_v3_1_0.py

#!/usr/bin/env python3
"""
Script de verificación de la migración v3.1.0
Valida que todos los cambios se aplicaron correctamente
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import config

def verify_migration():
    """Verificar que la migración se aplicó correctamente"""
    print("🔍 Verificando migración v3.1.0...")
    
    engine = create_engine(config.DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # 1. Verificar campos en tabla users
        print("📝 Verificando campos en tabla users...")
        
        result = session.execute(text("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            ORDER BY ordinal_position
        """))
        
        columns = {row[0]: row for row in result.fetchall()}
        
        required_columns = ['id', 'name', 'email', 'password_hash', 'role', 'created_at', 'updated_at', 'is_active']
        for col in required_columns:
            if col in columns:
                print(f"✅ Campo '{col}' presente")
            else:
                print(f"❌ Campo '{col}' faltante")
        
        # 2. Verificar índices
        print("🔍 Verificando índices...")
        
        result = session.execute(text("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE tablename = 'users'
        """))
        
        indexes = [row[0] for row in result.fetchall()]
        required_indexes = ['idx_users_email', 'idx_users_role', 'idx_users_active_role']
        
        for idx in required_indexes:
            if idx in indexes:
                print(f"✅ Índice '{idx}' presente")
            else:
                print(f"❌ Índice '{idx}' faltante")
        
        # 3. Verificar constraint
        print("🔒 Verificando constraint...")
        
        result = session.execute(text("""
            SELECT constraint_name 
            FROM information_schema.table_constraints 
            WHERE table_name = 'users' AND constraint_name = 'chk_user_role'
        """))
        
        if result.fetchone():
            print("✅ Constraint 'chk_user_role' presente")
        else:
            print("❌ Constraint 'chk_user_role' faltante")
        
        # 4. Verificar usuarios
        print("👥 Verificando usuarios...")
        
        result = session.execute(text("SELECT role, COUNT(*) FROM users GROUP BY role"))
        for role, count in result.fetchall():
            print(f"✅ {count} usuarios con rol '{role}'")
        
        # 5. Verificar asignaciones
        print("🏢 Verificando asignaciones de parkings...")
        
        result = session.execute(text("SELECT COUNT(*) FROM user_parkings"))
        assignment_count = result.fetchone()[0]
        print(f"✅ {assignment_count} asignaciones de parkings")
        
        # 6. Verificar datos de ejemplo
        print("📊 Verificando datos de ejemplo...")
        
        result = session.execute(text("""
            SELECT u.name, u.email, u.role, COUNT(up.parking_id) as parkings_count
            FROM users u
            LEFT JOIN user_parkings up ON u.id = up.user_id
            GROUP BY u.id, u.name, u.email, u.role
            ORDER BY u.role, u.name
        """))
        
        for name, email, role, parkings_count in result.fetchall():
            print(f"   - {name} ({email}): {role} - {parkings_count} parkings")
        
        print("✅ Verificación completada")
        
    except Exception as e:
        print(f"❌ Error durante la verificación: {e}")
        raise e
    finally:
        session.close()

if __name__ == "__main__":
    verify_migration()
```

---

**Documento creado**: Enero 2025  
**Versión**: v3.1.0_login  
**Estado**: Plan de migración completado 