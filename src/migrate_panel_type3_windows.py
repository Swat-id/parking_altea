#!/usr/bin/env python3
"""
Script de Migración para asignar ventanas a paneles Tipo 3 existentes
- Ventana 0: Plazas libres totales del parking
- Ventana 1: Plazas PMR libres del parking
"""

import os
import sys
from sqlalchemy import create_engine, text
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration_panel_type3_windows.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Importar configuración
try:
    from config import DB_URL
    DATABASE_URL = DB_URL
except ImportError:
    # Fallback si no se puede importar config
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres@localhost:5432/parking_altea')

def migrate_panel_type3_windows(engine):
    """Asignar ventanas a paneles Tipo 3 existentes"""
    logger.info("Iniciando migración de ventanas para paneles Tipo 3...")
    
    try:
        with engine.connect() as conn:
            # 1. Identificar paneles Tipo 3
            # Tipo 3 tiene windows_count = 2 o panel_type_id = 3
            logger.info("Identificando paneles Tipo 3...")
            result = conn.execute(text("""
                SELECT p.id, p.parking_id, p.panel_type_id, p.windows_count
                FROM panels p
                LEFT JOIN panel_types pt ON pt.id = p.panel_type_id
                WHERE (p.panel_type_id = 3 OR pt.windows_count = 2 OR p.windows_count = 2)
                  AND p.is_active = true
            """))
            type3_panels = result.fetchall()
            
            logger.info(f"✅ Encontrados {len(type3_panels)} paneles Tipo 3")
            
            if len(type3_panels) == 0:
                logger.info("No hay paneles Tipo 3 para migrar")
                return
            
            # 2. Para cada panel Tipo 3, crear asignaciones de ventanas
            assigned_count = 0
            skipped_count = 0
            
            for panel in type3_panels:
                panel_id = panel[0]
                parking_id = panel[1]
                panel_type_id = panel[2]
                windows_count = panel[3]
                
                if not parking_id:
                    logger.warning(f"Panel {panel_id} no tiene parking_id asignado, omitiendo...")
                    skipped_count += 1
                    continue
                
                logger.info(f"Procesando panel {panel_id} (parking {parking_id})...")
                
                # Verificar si ya tiene asignaciones
                existing_check = conn.execute(text("""
                    SELECT COUNT(*) FROM parking_panel_windows
                    WHERE panel_id = :panel_id
                """), {"panel_id": panel_id})
                existing_count = existing_check.scalar()
                
                if existing_count > 0:
                    logger.info(f"  Panel {panel_id} ya tiene {existing_count} asignación(es), omitiendo...")
                    skipped_count += 1
                    continue
                
                # Crear asignación para ventana 0: Plazas libres totales
                try:
                    conn.execute(text("""
                        INSERT INTO parking_panel_windows 
                        (panel_id, window_id, parking_id, display_type, sensor_type, is_active, created_at, updated_at)
                        VALUES 
                        (:panel_id, 0, :parking_id, 'parking', NULL, TRUE, NOW(), NOW())
                    """), {
                        "panel_id": panel_id,
                        "parking_id": parking_id
                    })
                    logger.info(f"  ✅ Ventana 0 asignada: Plazas libres totales")
                except Exception as e:
                    logger.error(f"  ❌ Error asignando ventana 0: {e}")
                    continue
                
                # Crear asignación para ventana 1: Plazas PMR libres
                try:
                    conn.execute(text("""
                        INSERT INTO parking_panel_windows 
                        (panel_id, window_id, parking_id, display_type, sensor_type, is_active, created_at, updated_at)
                        VALUES 
                        (:panel_id, 1, :parking_id, 'sensor_group', 'PMR', TRUE, NOW(), NOW())
                    """), {
                        "panel_id": panel_id,
                        "parking_id": parking_id
                    })
                    logger.info(f"  ✅ Ventana 1 asignada: Plazas PMR libres")
                    assigned_count += 1
                except Exception as e:
                    logger.error(f"  ❌ Error asignando ventana 1: {e}")
                    # Intentar eliminar la ventana 0 si falló la 1
                    try:
                        conn.execute(text("""
                            DELETE FROM parking_panel_windows
                            WHERE panel_id = :panel_id AND window_id = 0
                        """), {"panel_id": panel_id})
                    except:
                        pass
                    continue
            
            conn.commit()
            
            logger.info(f"✅ Migración completada:")
            logger.info(f"   - Paneles procesados: {assigned_count}")
            logger.info(f"   - Paneles omitidos: {skipped_count}")
            logger.info(f"   - Total paneles Tipo 3: {len(type3_panels)}")
            
            # 3. Verificar que las asignaciones se crearon correctamente
            verify_result = conn.execute(text("""
                SELECT COUNT(*) FROM parking_panel_windows ppw
                INNER JOIN panels p ON p.id = ppw.panel_id
                WHERE (p.panel_type_id = 3 OR p.windows_count = 2)
                  AND ppw.is_active = true
            """))
            total_assignments = verify_result.scalar()
            logger.info(f"✅ Total de asignaciones activas para paneles Tipo 3: {total_assignments}")
            
            logger.info("✅ Migración de ventanas para paneles Tipo 3 completada exitosamente")
    except Exception as e:
        logger.error(f"❌ Error en migración de ventanas para paneles Tipo 3: {e}")
        raise

def run_migration():
    logger.info("============================================================")
    logger.info("Iniciando migración: asignar ventanas a paneles Tipo 3")
    logger.info("============================================================")
    
    engine = None
    try:
        engine = create_engine(DATABASE_URL)
        logger.info("Conexión a base de datos establecida")
        
        migrate_panel_type3_windows(engine)
        
        logger.info("============================================================")
        logger.info("✅ Migración completada exitosamente")
        logger.info("============================================================")
    except Exception as e:
        logger.error(f"❌ Migración fallida: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
    finally:
        if engine:
            engine.dispose()

if __name__ == '__main__':
    run_migration()

