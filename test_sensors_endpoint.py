#!/usr/bin/env python3
"""
Script para probar específicamente el endpoint de sensores
Simula llamadas como diferentes tipos de usuarios
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
import json
from src.models import User, IndividualSensor, UserParking
from src.config import Session
from src.auth import create_token

def test_sensors_endpoint():
    session = Session()
    
    try:
        print("=== TEST ENDPOINT SENSORES ===")
        
        # 1. Obtener usuarios de prueba
        users = session.query(User).all()
        print(f"\n1. USUARIOS DISPONIBLES:")
        for user in users:
            print(f"   ID: {user.id}, Email: {user.email}, Rol: {user.role}")
        
        if not users:
            print("   ❌ No hay usuarios en la base de datos")
            return
        
        # 2. Contar sensores totales
        total_sensors = session.query(IndividualSensor).count()
        print(f"\n2. SENSORES TOTALES EN BD: {total_sensors}")
        
        # Mostrar distribución por parking
        sensors_by_parking = session.execute("""
            SELECT parking_id, COUNT(*) as count 
            FROM individual_sensors 
            GROUP BY parking_id 
            ORDER BY parking_id
        """).fetchall()
        
        print("   Distribución por parking:")
        for row in sensors_by_parking:
            parking_id = row[0] if row[0] else "NULL"
            count = row[1]
            print(f"     Parking {parking_id}: {count} sensores")
        
        # 3. Probar endpoint para cada usuario
        print(f"\n3. PRUEBAS DEL ENDPOINT /api/sensors:")
        
        base_url = "http://localhost:6001"  # Ajustar si es necesario
        
        for user in users:
            print(f"\n   👤 USUARIO: {user.email} (Rol: {user.role})")
            
            try:
                # Crear token para este usuario
                token_data = create_token(user.id, user.email, user.role)
                token = token_data['access_token']
                
                headers = {
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json'
                }
                
                # Llamar al endpoint
                response = requests.get(f"{base_url}/api/sensors", headers=headers)
                
                if response.status_code == 200:
                    sensors_data = response.json()
                    print(f"      ✅ Respuesta exitosa: {len(sensors_data)} sensores")
                    
                    # Mostrar algunos detalles
                    if sensors_data:
                        parking_ids = set()
                        for sensor in sensors_data:
                            if sensor.get('parking_id'):
                                parking_ids.add(sensor['parking_id'])
                        print(f"      📍 Parkings en respuesta: {sorted(parking_ids)}")
                        
                        # Mostrar primeros 3 sensores como ejemplo
                        print(f"      📋 Primeros sensores:")
                        for i, sensor in enumerate(sensors_data[:3]):
                            print(f"         {i+1}. ID: {sensor.get('id')}, Parking: {sensor.get('parking_id')}, Tipo: {sensor.get('sensor_type')}")
                    else:
                        print(f"      📋 Sin sensores en respuesta")
                    
                    # Para usuarios regulares, verificar que solo vean sus parkings
                    if user.role != 'superadmin':
                        user_parkings = session.query(UserParking).filter(UserParking.user_id == user.id).all()
                        assigned_parking_ids = [up.parking_id for up in user_parkings]
                        print(f"      🔒 Parkings asignados al usuario: {assigned_parking_ids}")
                        
                        # Verificar si hay sensores de parkings no asignados
                        unauthorized_parkings = parking_ids - set(assigned_parking_ids)
                        if unauthorized_parkings:
                            print(f"      ❌ ERROR: Ve sensores de parkings no asignados: {unauthorized_parkings}")
                        else:
                            print(f"      ✅ Solo ve sensores de parkings asignados")
                    
                else:
                    print(f"      ❌ Error HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                print(f"      ❌ Error probando usuario {user.email}: {e}")
        
        print(f"\n✅ TEST COMPLETADO")
        
    except Exception as e:
        print(f"❌ Error durante test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    test_sensors_endpoint()
