#!/usr/bin/env python3
import psycopg2

def check_users():
    try:
        conn = psycopg2.connect('postgresql://parking_user:parking_pass@localhost/parking_db')
        cursor = conn.cursor()
        
        print("=== USUARIOS EN LA BASE DE DATOS ===")
        
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
    check_users() 