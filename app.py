from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import json
import os
from datetime import datetime
import io
import pandas as pd

app = Flask(__name__)
CORS(app)

DATA_FILE = 'data/parking_spots.json'
HISTORY_FILE = 'data/parking_history.json'

# --- Asegurar carpetas y archivos ---
def ensure_files():
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    if not os.path.exists(DATA_FILE):
        spots = []
        for i in range(16):
            spots.append({
                "id": i,
                "lat": -26.0814 + (i * 0.000021),
                "lon": -58.275488 + (i * 0.000013),
                "status": "vacío",
                "start_time": None,
                "end_time": None,
                "user": None
            })
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(spots, f, indent=2)

    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f, indent=2)

ensure_files()

def load_json(file):
    with open(file, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(file, data):
    with open(file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

# --- Cargar spots ---
def load_spots():
    return load_json(DATA_FILE)

def save_spots(spots):
    save_json(DATA_FILE, spots)

# --- Cargar historial ---
def load_history():
    return load_json(HISTORY_FILE)

def save_history(history):
    save_json(HISTORY_FILE, history)

# --- API: obtener spots con geometría rotada (igual que front) ---
def add_rotated(spots, width=4, height=2.6, angle=147.5):
    for spot in spots:
        spot['rotated'] = {
            'width': width,
            'height': height,
            'angle': angle
        }
    return spots

@app.route('/api/parking-spots', methods=['GET'])
def api_get_spots():
    spots = load_spots()
    spots = add_rotated(spots)
    return jsonify(spots)

# --- API: actualizar estado de un spot ---
@app.route('/api/parking-spots/<int:spot_id>', methods=['PUT'])
def api_update_spot(spot_id):
    data = request.get_json()
    new_status = data.get('status')
    user = data.get('user', None)
    if new_status not in ['vacío', 'ocupado']:
        return jsonify({"error": "Estado inválido"}), 400

    spots = load_spots()
    history = load_history()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for spot in spots:
        if spot['id'] == spot_id:
            if new_status == 'ocupado' and spot['status'] != 'ocupado':
                spot['status'] = 'ocupado'
                spot['start_time'] = now
                spot['end_time'] = None
                spot['user'] = user or f"usuario_{spot_id}"

                # Agregar al historial inicio
                history.append({
                    "id": spot_id,
                    "user": spot['user'],
                    "start_time": now,
                    "end_time": None
                })

            elif new_status == 'vacío' and spot['status'] != 'vacío':
                spot['status'] = 'vacío'
                spot['end_time'] = now

                # Actualizar historial último registro abierto
                for record in reversed(history):
                    if record['id'] == spot_id and record['end_time'] is None:
                        record['end_time'] = now
                        break

                spot['user'] = None

            save_spots(spots)
            save_history(history)
            return jsonify(spot)

    return jsonify({"error": "Spot no encontrado"}), 404

# --- API: obtener historial completo ---
@app.route('/api/parking-history', methods=['GET'])
def api_get_history():
    history = load_history()
    return jsonify(history)

# --- API: estadísticas de ocupación diaria ---
@app.route('/api/parking-stats/daily', methods=['GET'])
def api_daily_stats():
    history = load_history()
    stats = {}
    for record in history:
        start_date = record['start_time'][:10] if record['start_time'] else None
        if start_date:
            stats[start_date] = stats.get(start_date, 0) + 1
    return jsonify(stats)

# --- API: exportar Excel ---
@app.route('/api/export-excel', methods=['GET'])
def api_export_excel():
    history = load_history()
    df = pd.DataFrame(history)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Historial')
    output.seek(0)
    return send_file(output, attachment_filename="parking_history.xlsx", as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
