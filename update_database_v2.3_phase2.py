#!/usr/bin/env python3
"""
Script para actualizar la base de datos con los nuevos campos de estado de cámaras
Fase 2: Funcionalidades de Cámaras
"""

import os
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))
load_dotenv()
DB_URL = os.getenv('DATABASE_URL', 'postgresql://postgres@localhost:5432/parking_altea')

# Crear engine y sesión
engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)

def update_database_phase2():
    """Actualizar base de datos para Fase 2: Funcionalidades de Cámaras"""
    
    print("🚀 INICIANDO ACTUALIZACIÓN DE BASE DE DATOS - FASE 2")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    session = Session()
    
    try:
        # 1. Verificar si los campos ya existen
        print("📋 Verificando estructura actual de la tabla 'accesses'...")
        
        result = session.execute(text("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'accesses' 
            ORDER BY ordinal_position
        """))
        
        existing_columns = {row[0] for row in result}
        print(f"Columnas existentes: {sorted(existing_columns)}")
        
        # 2. Agregar nuevos campos si no existen
        new_fields = [
            ('status', 'VARCHAR(20)', 'DEFAULT \'OFFLINE\' NOT NULL', 'Estado de la cámara (ONLINE/OFFLINE)'),
            ('last_message_received', 'TIMESTAMP WITH TIME ZONE', 'NULL', 'Último mensaje recibido'),
            ('last_ping_check', 'TIMESTAMP WITH TIME ZONE', 'NULL', 'Última verificación por ping'),
            ('ping_status', 'VARCHAR(20)', 'DEFAULT \'UNKNOWN\'', 'Estado por ping (ONLINE/OFFLINE/UNKNOWN)')
        ]
        
        added_fields = []
        
        for field_name, field_type, field_constraint, description in new_fields:
            if field_name not in existing_columns:
                print(f"➕ Agregando campo: {field_name} ({description})")
                
                sql = f"""
                ALTER TABLE accesses 
                ADD COLUMN {field_name} {field_type} {field_constraint}
                """
                
                session.execute(text(sql))
                added_fields.append(field_name)
                print(f"   ✅ Campo {field_name} agregado correctamente")
            else:
                print(f"✅ Campo {field_name} ya existe")
        
        # 3. Crear índices para mejorar rendimiento
        print("\n🔍 Creando índices para optimizar consultas...")
        
        indexes_to_create = [
            ('idx_accesses_status', 'accesses', 'status'),
            ('idx_accesses_last_message', 'accesses', 'last_message_received'),
            ('idx_accesses_ping_status', 'accesses', 'ping_status'),
            ('idx_accesses_parking_status', 'accesses', 'parking_id, status'),
            ('idx_accesses_parking_ping', 'accesses', 'parking_id, ping_status')
        ]
        
        # Verificar índices existentes
        result = session.execute(text("""
            SELECT indexname FROM pg_indexes 
            WHERE tablename = 'accesses'
        """))
        
        existing_indexes = {row[0] for row in result}
        
        for index_name, table_name, columns in indexes_to_create:
            if index_name not in existing_indexes:
                print(f"➕ Creando índice: {index_name}")
                sql = f"CREATE INDEX {index_name} ON {table_name} ({columns})"
                session.execute(text(sql))
                print(f"   ✅ Índice {index_name} creado correctamente")
            else:
                print(f"✅ Índice {index_name} ya existe")
        
        # 4. Actualizar datos existentes
        print("\n🔄 Actualizando datos existentes...")
        
        # Marcar cámaras que han enviado mensajes recientemente como ONLINE
        result = session.execute(text("""
            UPDATE accesses 
            SET status = 'ONLINE', 
                last_message_received = NOW() - INTERVAL '1 hour'
            WHERE id IN (
                SELECT DISTINCT access_id 
                FROM camera_logs 
                WHERE received_at > NOW() - INTERVAL '24 hours'
            )
        """))
        
        updated_cameras = result.rowcount
        print(f"   ✅ {updated_cameras} cámaras marcadas como ONLINE por actividad reciente")
        
        # 5. Verificar integridad de datos
        print("\n🔍 Verificando integridad de datos...")
        
        # Contar cámaras por estado
        result = session.execute(text("""
            SELECT status, COUNT(*) as count
            FROM accesses 
            GROUP BY status
        """))
        
        status_counts = {row[0]: row[1] for row in result}
        print("   Distribución de estados de cámaras:")
        for status, count in status_counts.items():
            print(f"     - {status}: {count} cámaras")
        
        # Verificar cámaras sin configuración de ping
        result = session.execute(text("""
            SELECT COUNT(*) as count
            FROM accesses 
            WHERE ping_status = 'UNKNOWN'
        """))
        
        unknown_ping = result.scalar()
        print(f"   - Cámaras sin verificación de ping: {unknown_ping}")
        
        # 6. Crear vista para estado de cámaras
        print("\n👁️ Creando vista para estado de cámaras...")
        
        view_sql = """
        CREATE OR REPLACE VIEW camera_status_view AS
        SELECT 
            a.id,
            a.name as camera_name,
            a.ip as camera_ip,
            a.line as camera_line,
            a.status,
            a.last_message_received,
            a.last_ping_check,
            a.ping_status,
            a.last_vehicle_in,
            a.last_vehicle_out,
            p.id as parking_id,
            p.name as parking_name,
            p.current_occupancy,
            p.capacity,
            CASE 
                WHEN a.status = 'ONLINE' AND a.ping_status = 'ONLINE' THEN 'FULLY_ONLINE'
                WHEN a.status = 'ONLINE' AND a.ping_status = 'OFFLINE' THEN 'ONLINE_NO_PING'
                WHEN a.status = 'OFFLINE' AND a.ping_status = 'ONLINE' THEN 'OFFLINE_PING_OK'
                WHEN a.status = 'OFFLINE' AND a.ping_status = 'OFFLINE' THEN 'FULLY_OFFLINE'
                ELSE 'UNKNOWN'
            END as overall_status
        FROM accesses a
        JOIN parkings p ON a.parking_id = p.id
        ORDER BY p.name, a.name
        """
        
        session.execute(text(view_sql))
        print("   ✅ Vista 'camera_status_view' creada/actualizada")
        
        # 7. Commit de todos los cambios
        session.commit()
        print(f"\n💾 Todos los cambios guardados correctamente")
        
        # 8. Resumen final
        print(f"\n📊 RESUMEN DE LA ACTUALIZACIÓN:")
        print(f"  - Campos agregados: {len(added_fields)}")
        print(f"  - Índices creados: {len([idx for idx in indexes_to_create if idx[0] not in existing_indexes])}")
        print(f"  - Cámaras actualizadas: {updated_cameras}")
        print(f"  - Vista creada: camera_status_view")
        
        if added_fields:
            print(f"\n✅ CAMPOS AGREGADOS:")
            for field in added_fields:
                print(f"  - {field}")
        
        print(f"\n🎯 FUNCIONALIDADES HABILITADAS:")
        print(f"  - Estado ONLINE/OFFLINE de cámaras")
        print(f"  - Verificación por ping")
        print(f"  - Timestamps de último mensaje y ping")
        print(f"  - Vista consolidada de estado de cámaras")
        print(f"  - Índices optimizados para consultas")
        
    except Exception as e:
        print(f"\n❌ ERROR durante la actualización: {e}")
        session.rollback()
        raise
    finally:
        session.close()

def validate_phase2_update():
    """Validar que la actualización se realizó correctamente"""
    
    print(f"\n🔍 VALIDACIÓN DE LA ACTUALIZACIÓN - FASE 2")
    print("=" * 50)
    
    session = Session()
    
    try:
        # Verificar campos agregados
        required_fields = ['status', 'last_message_received', 'last_ping_check', 'ping_status']
        
        result = session.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'accesses' AND column_name IN :fields
        """), {'fields': tuple(required_fields)})
        
        found_fields = {row[0] for row in result}
        missing_fields = set(required_fields) - found_fields
        
        if missing_fields:
            print(f"❌ Campos faltantes: {missing_fields}")
            return False
        else:
            print(f"✅ Todos los campos requeridos están presentes")
        
        # Verificar vista
        result = session.execute(text("""
            SELECT COUNT(*) FROM camera_status_view
        """))
        
        view_count = result.scalar()
        print(f"✅ Vista 'camera_status_view' accesible ({view_count} registros)")
        
        # Verificar índices
        result = session.execute(text("""
            SELECT indexname FROM pg_indexes 
            WHERE tablename = 'accesses' AND indexname LIKE 'idx_accesses_%'
        """))
        
        indexes = [row[0] for row in result]
        print(f"✅ Índices creados: {len(indexes)}")
        
        # Verificar datos de ejemplo
        result = session.execute(text("""
            SELECT 
                COUNT(*) as total_cameras,
                COUNT(CASE WHEN status = 'ONLINE' THEN 1 END) as online_cameras,
                COUNT(CASE WHEN status = 'OFFLINE' THEN 1 END) as offline_cameras,
                COUNT(CASE WHEN ping_status = 'UNKNOWN' THEN 1 END) as unknown_ping
            FROM accesses
        """))
        
        stats = result.fetchone()
        print(f"✅ Estadísticas de cámaras:")
        print(f"   - Total: {stats[0]}")
        print(f"   - ONLINE: {stats[1]}")
        print(f"   - OFFLINE: {stats[2]}")
        print(f"   - Ping UNKNOWN: {stats[3]}")
        
        print(f"\n🎉 VALIDACIÓN COMPLETADA EXITOSAMENTE")
        return True
        
    except Exception as e:
        print(f"❌ Error durante la validación: {e}")
        return False
    finally:
        session.close()

if __name__ == "__main__":
    print(f"🚀 SCRIPT DE ACTUALIZACIÓN - FASE 2: FUNCIONALIDADES DE CÁMARAS")
    print(f"Base de datos: {DB_URL}")
    print()
    
    try:
        # Ejecutar actualización
        update_database_phase2()
        
        # Validar actualización
        if validate_phase2_update():
            print(f"\n✅ ACTUALIZACIÓN COMPLETADA EXITOSAMENTE")
            print(f"   Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print(f"\n⚠️ ACTUALIZACIÓN COMPLETADA CON ADVERTENCIAS")
            
    except Exception as e:
        print(f"\n❌ ERROR CRÍTICO: {e}")
        sys.exit(1) 