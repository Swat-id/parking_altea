from sqlalchemy import create_engine
import config
from models import Base

def init_database():
    """Crear todas las tablas en la base de datos"""
    engine = create_engine(config.DB_URL, echo=True)
    Base.metadata.create_all(engine)
    print("Base de datos inicializada correctamente")

if __name__ == '__main__':
    init_database() 