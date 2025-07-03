#!/usr/bin/env python3
"""
Script simple para añadir campos faltantes a occupancy_history
"""

import psycopg2
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_occupancy_history():
    """Añadir campos faltantes a occupancy_history"""
    try:
        # Conectar a la base de datos
        conn = psycopg2.connect(
            host="localhost",
            database="parking_db",
            user="parking_user",
            password="parking_pass"
        )
        cursor = conn.cursor()
        
        logger.info("Conectando a la base de datos...")
        
        # Verificar si los campos ya existen
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'occupancy_history' 
            AND column_name IN ('previous_occupancy', 'change_amount')
        """)
        existing_columns = [row[0] for row in cursor.fetchall()]
        
        # Añadir campos si no existen
        if 'previous_occupancy' not in existing_columns:
            cursor.execute("ALTER TABLE occupancy_history ADD COLUMN previous_occupancy INTEGER")
            logger.info("✅ Campo 'previous_occupancy' añadido a tabla occupancy_history")
        
        if 'change_amount' not in existing_columns:
            cursor.execute("ALTER TABLE occupancy_history ADD COLUMN change_amount INTEGER")
            logger.info("✅ Campo 'change_amount' añadido a tabla occupancy_history")
        
        # Commit de los cambios
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("🎉 Campos añadidos correctamente a occupancy_history")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error añadiendo campos: {e}")
        return False

if __name__ == "__main__":
    fix_occupancy_history() 