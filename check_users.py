#!/usr/bin/env python3

import sys
import os
sys.path.append('src')

from models import User
from config import DB_URL
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def check_users():
    engine = create_engine(DB_URL, echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        users = session.query(User).all()
        print("Usuarios en la base de datos:")
        print("=" * 50)
        
        for user in users:
            print(f"ID: {user.id}")
            print(f"Email: {user.email}")
            print(f"Nombre: {user.name}")
            print(f"Activo: {user.is_active}")
            print("-" * 30)
            
        if not users:
            print("No hay usuarios en la base de datos")
            
    except Exception as e:
        print(f"Error al consultar usuarios: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    check_users() 