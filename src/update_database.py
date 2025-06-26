#!/usr/bin/env python3
"""
Script de actualización completa de la base de datos
Crea todas las tablas necesarias y carga los datos iniciales
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from models import Base, User, Parking, Access, Panel, UserParking, UserPanel, OccupancyHistory, ScheduledMessage
from auth import create_user, assign_parking_to_user, assign_panel_to_user
from config import DB_URL
import pandas as pd

def update_database():
    """Actualizar completamente la base de datos"""
    
    print("🚀 Iniciando actualización completa de la base de datos...")
    print("=" * 60)
    
    # Configurar conexión a la base de datos
    engine = create_engine(DB_URL, echo=False)
    Session = sessionmaker(bind=engine)
    
    try:
        # 1. Crear todas las tablas
        print("📋 Paso 1: Creando todas las tablas...")
        Base.metadata.create_all(engine)
        print("   ✅ Todas las tablas creadas exitosamente")
        
        # 2. Verificar conexión
        print("\n🔍 Paso 2: Verificando conexión a la base de datos...")
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print(f"   ✅ Conectado a PostgreSQL: {version}")
        
        # 3. Crear usuarios iniciales
        print("\n👥 Paso 3: Creando usuarios iniciales...")
        session = Session()
        
        # Verificar si los usuarios ya existen
        existing_users = session.query(User).all()
        if existing_users:
            print(f"   ℹ️  Ya existen {len(existing_users)} usuarios en la base de datos")
            for user in existing_users:
                print(f"      - {user.name} ({user.email})")
        else:
            print("   📝 Creando usuarios iniciales...")
            
            # Lista de usuarios iniciales
            initial_users = [
                {
                    'name': 'Toni Alos',
                    'email': 'atea.dti@altea.es',
                    'password': 'altea2025!'
                },
                {
                    'name': 'Iván Martí',
                    'email': 'gerenciapstd@altea.es',
                    'password': 'altea2025!'
                }
            ]
            
            for user_data in initial_users:
                user, error = create_user(
                    name=user_data['name'],
                    email=user_data['email'],
                    password=user_data['password']
                )
                
                if error:
                    print(f"   ❌ Error al crear usuario {user_data['name']}: {error}")
                else:
                    print(f"   ✅ Usuario {user_data['name']} creado exitosamente (ID: {user.id})")
        
        # 4. Cargar datos desde CSV
        print("\n📊 Paso 4: Cargando datos desde archivos CSV...")
        
        csv_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'csv_templates')
        
        # Cargar parkings
        parkings_file = os.path.join(csv_dir, 'parkings.csv')
        if os.path.exists(parkings_file):
            print("   📁 Cargando parkings desde CSV...")
            df_parkings = pd.read_csv(parkings_file)
            
            for _, row in df_parkings.iterrows():
                # Verificar si el parking ya existe
                existing_parking = session.query(Parking).filter(Parking.name == row['name']).first()
                if not existing_parking:
                    parking = Parking(
                        name=row['name'],
                        location=row.get('location', ''),
                        max_capacity=row['max_capacity'],
                        threshold_dense=row.get('threshold_dense', 70),
                        threshold_full=row.get('threshold_full', 90),
                        current_occupancy=row.get('current_occupancy', 0),
                        status=row.get('status', 'LIBRE')
                    )
                    session.add(parking)
                    print(f"      ✅ Parking '{row['name']}' agregado")
                else:
                    print(f"      ℹ️  Parking '{row['name']}' ya existe")
        
        # Cargar accesos/cámaras
        accesses_file = os.path.join(csv_dir, 'accesses.csv')
        if os.path.exists(accesses_file):
            print("   📁 Cargando accesos/cámaras desde CSV...")
            df_accesses = pd.read_csv(accesses_file)
            
            for _, row in df_accesses.iterrows():
                # Buscar el parking correspondiente
                parking = session.query(Parking).filter(Parking.name == row['parking_name']).first()
                if parking:
                    # Verificar si el acceso ya existe
                    existing_access = session.query(Access).filter(
                        Access.parking_id == parking.id,
                        Access.ip == row['ip']
                    ).first()
                    
                    if not existing_access:
                        access = Access(
                            parking_id=parking.id,
                            ip=row['ip'],
                            line=row['line'],
                            name=row.get('name', ''),
                            last_vehicle_in=row.get('last_vehicle_in', 0),
                            last_vehicle_out=row.get('last_vehicle_out', 0)
                        )
                        session.add(access)
                        print(f"      ✅ Acceso '{row['ip']}' para parking '{row['parking_name']}' agregado")
                    else:
                        print(f"      ℹ️  Acceso '{row['ip']}' para parking '{row['parking_name']}' ya existe")
                else:
                    print(f"      ⚠️  Parking '{row['parking_name']}' no encontrado para acceso '{row['ip']}'")
        
        # Cargar paneles
        panels_file = os.path.join(csv_dir, 'panels.csv')
        if os.path.exists(panels_file):
            print("   📁 Cargando paneles desde CSV...")
            df_panels = pd.read_csv(panels_file)
            
            for _, row in df_panels.iterrows():
                # Buscar el parking correspondiente
                parking = session.query(Parking).filter(Parking.name == row['parking_name']).first()
                if parking:
                    # Verificar si el panel ya existe
                    existing_panel = session.query(Panel).filter(
                        Panel.parking_id == parking.id,
                        Panel.name == row['name']
                    ).first()
                    
                    if not existing_panel:
                        panel = Panel(
                            parking_id=parking.id,
                            name=row['name'],
                            ip=row['ip']
                        )
                        session.add(panel)
                        print(f"      ✅ Panel '{row['name']}' para parking '{row['parking_name']}' agregado")
                    else:
                        print(f"      ℹ️  Panel '{row['name']}' para parking '{row['parking_name']}' ya existe")
                else:
                    print(f"      ⚠️  Parking '{row['parking_name']}' no encontrado para panel '{row['name']}'")
        
        # 5. Asignar todos los recursos a los usuarios
        print("\n🔗 Paso 5: Asignando recursos a usuarios...")
        
        # Obtener usuarios
        toni = session.query(User).filter(User.email == 'atea.dti@altea.es').first()
        ivan = session.query(User).filter(User.email == 'gerenciapstd@altea.es').first()
        
        if toni and ivan:
            # Obtener todos los parkings y paneles
            all_parkings = session.query(Parking).all()
            all_panels = session.query(Panel).all()
            
            print(f"   📊 Asignando {len(all_parkings)} parkings y {len(all_panels)} paneles a ambos usuarios...")
            
            # Asignar parkings a ambos usuarios
            for parking in all_parkings:
                # Verificar si ya están asignados
                toni_parking = session.query(UserParking).filter(
                    UserParking.user_id == toni.id,
                    UserParking.parking_id == parking.id
                ).first()
                
                ivan_parking = session.query(UserParking).filter(
                    UserParking.user_id == ivan.id,
                    UserParking.parking_id == parking.id
                ).first()
                
                if not toni_parking:
                    success, error = assign_parking_to_user(toni.id, parking.id)
                    if success:
                        print(f"      ✅ Parking '{parking.name}' asignado a Toni Alos")
                    else:
                        print(f"      ❌ Error asignando parking '{parking.name}' a Toni: {error}")
                
                if not ivan_parking:
                    success, error = assign_parking_to_user(ivan.id, parking.id)
                    if success:
                        print(f"      ✅ Parking '{parking.name}' asignado a Iván Martí")
                    else:
                        print(f"      ❌ Error asignando parking '{parking.name}' a Iván: {error}")
            
            # Asignar paneles a ambos usuarios
            for panel in all_panels:
                # Verificar si ya están asignados
                toni_panel = session.query(UserPanel).filter(
                    UserPanel.user_id == toni.id,
                    UserPanel.panel_id == panel.id
                ).first()
                
                ivan_panel = session.query(UserPanel).filter(
                    UserPanel.user_id == ivan.id,
                    UserPanel.panel_id == panel.id
                ).first()
                
                if not toni_panel:
                    success, error = assign_panel_to_user(toni.id, panel.id)
                    if success:
                        print(f"      ✅ Panel '{panel.name}' asignado a Toni Alos")
                    else:
                        print(f"      ❌ Error asignando panel '{panel.name}' a Toni: {error}")
                
                if not ivan_panel:
                    success, error = assign_panel_to_user(ivan.id, panel.id)
                    if success:
                        print(f"      ✅ Panel '{panel.name}' asignado a Iván Martí")
                    else:
                        print(f"      ❌ Error asignando panel '{panel.name}' a Iván: {error}")
        
        # 6. Commit de todos los cambios
        print("\n💾 Paso 6: Guardando todos los cambios...")
        session.commit()
        print("   ✅ Todos los cambios guardados exitosamente")
        
        # 7. Resumen final
        print("\n📋 RESUMEN FINAL:")
        print("=" * 40)
        
        # Contar registros
        users_count = session.query(User).count()
        parkings_count = session.query(Parking).count()
        accesses_count = session.query(Access).count()
        panels_count = session.query(Panel).count()
        user_parkings_count = session.query(UserParking).count()
        user_panels_count = session.query(UserPanel).count()
        
        print(f"👥 Usuarios: {users_count}")
        print(f"🏢 Parkings: {parkings_count}")
        print(f"📹 Cámaras/Accesos: {accesses_count}")
        print(f"📺 Paneles: {panels_count}")
        print(f"🔗 Asignaciones Usuario-Parking: {user_parkings_count}")
        print(f"🔗 Asignaciones Usuario-Panel: {user_panels_count}")
        
        print("\n🎉 ¡ACTUALIZACIÓN COMPLETADA EXITOSAMENTE!")
        print("La base de datos está lista para usar con la versión v2.1")
        
        session.close()
        return True
        
    except Exception as e:
        print(f"\n❌ Error durante la actualización: {str(e)}")
        session.rollback()
        session.close()
        return False

if __name__ == '__main__':
    success = update_database()
    sys.exit(0 if success else 1) 