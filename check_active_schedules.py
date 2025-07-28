#!/usr/bin/env python3
import sys
import os
sys.path.append('src')

from models import PanelSchedule
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import DB_URL

engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)
session = Session()

schedules = session.query(PanelSchedule).filter(PanelSchedule.is_active == True).all()
print("Programaciones activas:")
for s in schedules:
    print(f"ID: {s.id} - {s.name} - Parking: {s.parking_id} - Mensaje: {s.message}")
    print(f"  Horario: {s.start_time} - {s.end_time}")
    print(f"  Fechas: {s.start_date} - {s.end_date}")
    print(f"  Días: L={s.monday} M={s.tuesday} X={s.wednesday} J={s.thursday} V={s.friday} S={s.saturday} D={s.sunday}")

session.close() 