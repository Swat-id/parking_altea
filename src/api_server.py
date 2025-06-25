from flask import Flask, request, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import config
from models import Base, Parking, ScheduledMessage, OccupancyHistory
from datetime import datetime

app = Flask(__name__)
engine = create_engine(config.DB_URL, echo=False)
Session = sessionmaker(bind=engine)
Base.metadata.create_all(engine)

@app.route('/parkings', methods=['GET'])
def list_parkings():
    session = Session()
    parks = session.query(Parking).all()
    data = [{{
        'id': p.id,
        'name': p.name,
        'location': p.location,
        'max_capacity': p.max_capacity,
        'current_occupancy': p.current_occupancy,
        'status': p.status
    }} for p in parks]
    session.close()
    return jsonify(data)

@app.route('/parking/<int:pid>', methods=['GET'])
def get_parking(pid):
    session = Session()
    p = session.query(Parking).get(pid)
    if not p:
        return jsonify({'error':'Not found'}), 404
    data = {{
        'id': p.id,
        'name': p.name,
        'max_capacity': p.max_capacity,
        'current_occupancy': p.current_occupancy,
        'free_spaces': p.max_capacity - p.current_occupancy,
        'status': p.status
    }}
    session.close()
    return jsonify(data)

@app.route('/parking/<int:pid>/occupancy', methods=['POST'])
def set_occupancy(pid):
    req = request.get_json(force=True)
    new_occ = req.get('occupancy')
    session = Session()
    p = session.query(Parking).get(pid)
    if not p:
        session.close()
        return jsonify({'error':'Not found'}), 404
    p.current_occupancy = max(0, min(new_occ, p.max_capacity))
    p.status = 'LIBRE'
    # opcional: ajustar status
    hist = OccupancyHistory(parking_id=pid, occupancy=p.current_occupancy, source='manual')
    session.add(hist)
    session.commit()
    session.close()
    return jsonify({'status':'ok'})

@app.route('/parking/<int:pid>/message', methods=['POST'])
def schedule_message(pid):
    req = request.get_json(force=True)
    start = datetime.fromisoformat(req.get('start'))
    end = datetime.fromisoformat(req.get('end'))
    text = req.get('message')
    session = Session()
    msg = ScheduledMessage(parking_id=pid, start_time=start, end_time=end, message=text)
    session.add(msg)
    session.commit()
    session.close()
    return jsonify({'status':'ok'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=config.API_PORT)