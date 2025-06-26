#!/usr/bin/env python3
"""
Script to check users, passwords, and permissions in the database
"""

import psycopg2
import sys
import os

# Add the src directory to the path to import config
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from config import DATABASE_URL
except ImportError:
    print("Error: No se puede importar config.py. Asegúrate de estar en el directorio correcto.")
    sys.exit(1)

def check_users_and_permissions():
    """Check all users, their passwords, and permissions"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        print("=== VERIFICACIÓN DE USUARIOS Y PERMISOS ===\n")
        
        # Check all users
        cursor.execute("""
            SELECT id, name, email, password_hash, created_at 
            FROM users 
            ORDER BY id
        """)
        users = cursor.fetchall()
        
        print(f"Total de usuarios en la base de datos: {len(users)}\n")
        
        # Expected users with their passwords
        expected_users = {
            'info@swat-id.com': 'admin123!',
            'toni.alos@swat-id.com': 'toni123!',
            'ivan.marti@swat-id.com': 'ivan123!'
        }
        
        for user_id, name, email, password_hash, created_at in users:
            print(f"Usuario ID: {user_id}")
            print(f"Nombre: {name}")
            print(f"Email: {email}")
            print(f"Fecha creación: {created_at}")
            
            # Check if password matches expected
            if email in expected_users:
                expected_password = expected_users[email]
                # For now, just show the expected password without bcrypt verification
                print(f"Contraseña esperada: {expected_password}")
            else:
                print(f"⚠️  Usuario no esperado en la lista")
            
            # Check user permissions
            cursor.execute("""
                SELECT p.name as parking_name, p.id as parking_id
                FROM user_parkings up
                JOIN parkings p ON up.parking_id = p.id
                WHERE up.user_id = %s
            """, (user_id,))
            parkings = cursor.fetchall()
            
            cursor.execute("""
                SELECT p.name as panel_name, p.id as panel_id
                FROM user_panels up
                JOIN panels p ON up.panel_id = p.id
                WHERE up.user_id = %s
            """, (user_id,))
            panels = cursor.fetchall()
            
            cursor.execute("""
                SELECT a.name as camera_name, a.id as camera_id
                FROM user_cameras uc
                JOIN accesses a ON uc.camera_id = a.id
                WHERE uc.user_id = %s
            """, (user_id,))
            cameras = cursor.fetchall()
            
            print(f"Parkings asignados: {len(parkings)}")
            for parking_name, parking_id in parkings:
                print(f"  - {parking_name} (ID: {parking_id})")
            
            print(f"Paneles asignados: {len(panels)}")
            for panel_name, panel_id in panels:
                print(f"  - {panel_name} (ID: {panel_id})")
            
            print(f"Cámaras asignadas: {len(cameras)}")
            for camera_name, camera_id in cameras:
                print(f"  - {camera_name} (ID: {camera_id})")
            
            print("-" * 50)
        
        # Check total resources
        cursor.execute("SELECT COUNT(*) FROM parkings")
        result = cursor.fetchone()
        total_parkings = result[0] if result else 0
        
        cursor.execute("SELECT COUNT(*) FROM panels")
        result = cursor.fetchone()
        total_panels = result[0] if result else 0
        
        cursor.execute("SELECT COUNT(*) FROM accesses")
        result = cursor.fetchone()
        total_cameras = result[0] if result else 0
        
        print(f"\n=== RESUMEN DE RECURSOS ===")
        print(f"Total parkings: {total_parkings}")
        print(f"Total paneles: {total_panels}")
        print(f"Total cámaras: {total_cameras}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    check_users_and_permissions() 