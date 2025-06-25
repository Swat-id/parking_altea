from flask import Flask, request, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import config
from models import Base, Parking, Access, OccupancyHistory
from panel_client import broadcast

app = Flask(__name__)
engine = create_engine(config.DB_URL, echo=False)
Session = sessionmaker(bind=engine)
Base.metadata.create_all(engine)

@app.route('/', methods=['POST'])
def handle_camera():
    data = request.get_json(force=True)
    ip = request.headers.get('X-Forwarded-For') or request.remote_addr
    line = data.get('line')
    veh_in = data.get('Vehicle In', 0)
    veh_out = data.get('Vehicle Out', 0)

    session = Session()
    access = session.query(Access).filter_by(ip=ip, line=line).first()
    if not access:
        session.close()
        return jsonify({'error':'Access not found'}), 404

    # Calcular deltas
    delta_in = veh_in - access.last_vehicle_in if access.last_vehicle_in else 0
    delta_out = veh_out - access.last_vehicle_out if access.last_vehicle_out else 0
    access.last_vehicle_in = veh_in
    access.last_vehicle_out = veh_out

    # Actualizar parking
    parking = access.parking
    parking.current_occupancy += (delta_in - delta_out)
    parking.current_occupancy = max(0, min(parking.current_occupancy, parking.max_capacity))

    # Registrar histórico
    hist = OccupancyHistory(
        parking_id=parking.id,
        occupancy=parking.current_occupancy,
        source='camera'
    )
    session.add(hist)

    # Calcular estado
    occ = parking.current_occupancy
    if parking.fixed_message_flag:
        message = None
    else:
        if occ >= parking.threshold_full:
            parking.status = 'OCUPADO'
        elif occ >= parking.threshold_dense:
            parking.status = 'DENSO'
        else:
            parking.status = 'LIBRE'
        free = parking.max_capacity - occ
        message = f"{parking.name}: {free} libres ({parking.status})"
        broadcast(parking, message)

    session.commit()
    session.close()
    return jsonify({'status':'ok'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=config.CAMERA_PORT)