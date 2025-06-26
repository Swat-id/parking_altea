#!/usr/bin/env python3
"""
Script para crear los usuarios iniciales del sistema
Toni Alos y Iván Martí con sus respectivas contraseñas
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User
from auth import create_user, hash_password
from config import DB_URL

def create_initial_users():
    """Crear los usuarios iniciales del sistema"""
    
    # Configurar conexión a la base de datos
    engine = create_engine(DB_URL, echo=False)
    Session = sessionmaker(bind=engine)
    
    # Crear tablas si no existen
    Base.metadata.create_all(engine)
    
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
    
    print("Creando usuarios iniciales...")
    
    for user_data in initial_users:
        print(f"Creando usuario: {user_data['name']} ({user_data['email']})")
        
        user, error = create_user(
            name=user_data['name'],
            email=user_data['email'],
            password=user_data['password']
        )
        
        if error:
            print(f"Error al crear usuario {user_data['name']}: {error}")
        else:
            print(f"✅ Usuario {user_data['name']} creado exitosamente con ID: {user.id}")
    
    print("\nProceso completado!")
    
    # Mostrar usuarios creados
    session = Session()
    users = session.query(User).all()
    print(f"\nTotal de usuarios en la base de datos: {len(users)}")
    for user in users:
        print(f"- {user.name} ({user.email}) - ID: {user.id}")
    session.close()

if __name__ == '__main__':
    create_initial_users() 