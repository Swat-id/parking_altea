#!/usr/bin/env python3

import sys
import os
sys.path.append('src')

from models import User
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import config

def check_users():
    try:
        engine = create_engine(config.DB_URL)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        users = session.query(User).all()
        print(f"Total usuarios en BD: {len(users)}")
        
        for user in users:
            print(f"ID: {user.id}, Email: {user.email}, Name: {user.name}")
        
        session.close()
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    check_users() 