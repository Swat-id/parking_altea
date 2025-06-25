import csv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import config
from models import Base, Parking, Access, Panel

engine = create_engine(config.DB_URL)
Session = sessionmaker(bind=engine)
Base.metadata.create_all(engine)

MAPPINGS = {{
    'parkings.csv': (Parking, ['name','location','max_capacity','threshold_dense','threshold_full']),
    'accesses.csv': (Access, ['parking_name','ip','line','name']),
    'panels.csv': (Panel, ['parking_name','name','ip'])
}}

if __name__ == '__main__':
    session = Session()
    for file, (Model, fields) in MAPPINGS.items():
        with open(f'../csv_templates/{file}') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if file == 'accesses.csv' or file == 'panels.csv':
                    parking = session.query(Parking).filter_by(name=row['parking_name']).first()
                    obj = Model(parking_id=parking.id)
                else:
                    obj = Model()
                for field in fields:
                    if field in ['max_capacity','threshold_dense','threshold_full','line']:
                        setattr(obj, field, int(row[field]))
                    elif field=='parking_name':
                        continue
                    else:
                        setattr(obj, field, row[field])
                session.add(obj)
    session.commit()
    session.close()