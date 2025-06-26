#!/usr/bin/env python3
import psycopg2

def remove_test_user():
    try:
        conn = psycopg2.connect('postgresql://parking_user:parking_pass@localhost/parking_db')
        cursor = conn.cursor()
        
        print("=== ELIMINANDO USUARIO DE PRUEBA ===")
        
        # Delete test user
        cursor.execute("DELETE FROM users WHERE email = 'test@example.com'")
        deleted_count = cursor.rowcount
        
        if deleted_count > 0:
            conn.commit()
            print(f"✅ Usuario de prueba eliminado ({deleted_count} filas)")
        else:
            print("ℹ️  No se encontró usuario de prueba para eliminar")
        
        # Show remaining users
        print("\n=== USUARIOS RESTANTES ===")
        cursor.execute("SELECT id, name, email FROM users ORDER BY id")
        users = cursor.fetchall()
        
        for user_id, name, email in users:
            print(f"ID: {user_id}, Nombre: {name}, Email: {email}")
        
        print(f"\nTotal usuarios: {len(users)}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    remove_test_user() 