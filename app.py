from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

DATA_FILE = 'data/parking_spots.json'

# ---------- Asegurar existencia de carpeta y archivo ----------
def ensure_data_file():
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    if not os.path.exists(DATA_FILE):
        default_data = []
        for i in range(16):
            default_data.append({
                "id": i,
                "lat": -26.0814 + (i * 0.000021),  # ajustable
                "lon": -58.275488 + (i * 0.000013),  # ajustable
                "status": "vacío",
                "start_time": None,
                "end_time": None,
                "user": None
            })
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(default_data, f, ensure_ascii=False, indent=2)

# ---------- Utilidades para archivo JSON ----------
def load_parking_spots():
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_parking_spots(spots):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(spots, f, ensure_ascii=False, indent=2)

# ---------- Añadir geometría rectangular simple ----------
def add_rectangles_to_spots(spots, offset_lat=0.000008, offset_lon=0.000010):
    for spot in spots:
        spot["rect"] = {
            "north": spot["lat"] + offset_lat,
            "south": spot["lat"] - offset_lat,
            "east":  spot["lon"] + offset_lon,
            "west":  spot["lon"] - offset_lon
        }
    return spots

# ---------- Añadir geometría rotada ----------
def add_rotated_rectangles_to_spots(spots, width=4, height=2.6, angle=147.5):
    for spot in spots:
        spot["rotated"] = {
            "width": width,
            "height": height,
            "angle": angle
        }
    return spots

# ---------- Inicialización ----------
ensure_data_file()
parking_spots = load_parking_spots()

# ---------- API: obtener todos los espacios ----------
@app.route('/api/parking-spots', methods=['GET'])
def get_parking_spots():
    enriched = add_rectangles_to_spots(parking_spots.copy())
    enriched = add_rotated_rectangles_to_spots(enriched)
    return jsonify(enriched)

# ---------- API: actualizar un espacio ----------
@app.route('/api/parking-spots/<int:spot_id>', methods=['PUT'])
def update_parking_spot(spot_id):
    data = request.get_json()
    new_status = data.get('status')
    user = data.get('user', None)  # opcional

    if new_status not in ['vacío', 'ocupado']:
        return jsonify({'error': 'Estado inválido'}), 400

    current_time = datetime.now().strftime('%H:%M')

    for spot in parking_spots:
        if spot['id'] == spot_id:
            if new_status == 'ocupado':
                spot['status'] = 'ocupado'
                spot['start_time'] = current_time
                spot['end_time'] = None
                spot['user'] = user or f"usuario_{spot_id}"
            elif new_status == 'vacío':
                spot['status'] = 'vacío'
                spot['end_time'] = current_time
            save_parking_spots(parking_spots)
            return jsonify(spot)

    return jsonify({'error': 'ID no encontrado'}), 404

# ---------- Ejecución ----------
if __name__ == '__main__':
   
