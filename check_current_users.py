#!/usr/bin/env python3
"""
Script para verificar usuarios actuales en la base de datos
"""

import sys
import os
sys.path.append('src')

from models import User
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import config

def check_users():
    """Verificar usuarios actuales en la BD"""
    engine = create_engine(config.DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        users = session.query(User).all()
        
        print("=== USUARIOS ACTUALES EN BD ===")
        print(f"Total usuarios: {len(users)}")
        print()
        
        for user in users:
            print(f"ID: {user.id}")
            print(f"Email: {user.email}")
            print(f"Name: {user.name}")
            print(f"Created: {user.created_at}")
            print("-" * 50)
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    check_users() 