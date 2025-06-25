import csv
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import config
from models import Base, Parking, Access, Panel

engine = create_engine(config.DB_URL)
Session = sessionmaker(bind=engine)
Base.metadata.create_all(engine)

# Obtener el directorio base del proyecto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_DIR = os.path.join(BASE_DIR, 'csv_templates')

MAPPINGS = {
    'parkings.csv': (Parking, ['name','location','max_capacity','threshold_dense','threshold_full']),
    'accesses.csv': (Access, ['parking_id','ip','line','name']),
    'panels.csv': (Panel, ['parking_id','name','ip'])
}

if __name__ == '__main__':
    session = Session()
    for file, (Model, fields) in MAPPINGS.items():
        csv_path = os.path.join(CSV_DIR, file)
        with open(csv_path) as f:
            reader = csv.DictReader(f)
            for row in reader:
                if file == 'accesses.csv' or file == 'panels.csv':
                    obj = Model(parking_id=int(row['parking_id']))
                else:
                    obj = Model()
                for field in fields:
                    if field in ['max_capacity','threshold_dense','threshold_full','line']:
                        setattr(obj, field, int(row[field]))
                    elif field == 'parking_id':
                        continue
                    else:
                        setattr(obj, field, row[field])
                session.add(obj)
    session.commit()
    session.close()
    print("Datos cargados exitosamente")