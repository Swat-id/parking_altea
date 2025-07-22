#!/usr/bin/env python3
import sys
import os
sys.path.append('src')

from models import Parking, Panel
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import DB_URL

engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)
session = Session()

parkings = session.query(Parking).all()
print("Parkings con paneles:")
for p in parkings:
    panels = session.query(Panel).filter(Panel.parking_id == p.id).all()
    print(f"ID: {p.id} - {p.name} - Paneles: {len(panels)}")
    if panels:
        for panel in panels:
            print(f"  - Panel: {panel.ip} ({panel.name})")

session.close() 