from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

DATA_DIR = 'data'
SPOTS_FILE = os.path.join(DATA_DIR, 'parking_spots.json')
HISTORY_FILE = os.path.join(DATA_DIR, 'parking_history.json')
USERS_FILE = os.path.join(DATA_DIR, 'users.json')

def ensure_files():
    os.makedirs(DATA_DIR, exist_ok=True)

    if not os.path.exists(SPOTS_FILE):
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
        with open(SPOTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(spots, f, indent=2)

    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f, indent=2)

    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f, indent=2)

ensure_files()

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def find_user_by_dni(users, dni):
    for u in users:
        if u['dni'] == dni:
            return u
    return None

def add_rotated(spots, width=4, height=2.6, angle=147.5):
    for spot in spots:
        spot['rotated'] = {
            'width': width,
            'height': height,
            'angle': angle
        }
    return spots

@app.route('/api/parking-spots', methods=['GET', 'POST'])
def spots_and_users():
    if request.method == 'GET':
        spots = load_json(SPOTS_FILE)
        spots = add_rotated(spots)
        return jsonify(spots)

    # POST: login or register
    data = request.get_json()
    if not data or 'action' not in data:
        return jsonify({"error": "Falta 'action' en la solicitud"}), 400

    action = data['action']
    users = load_json(USERS_FILE)

    if action == 'register':
        # Campos requeridos
        required = ['nombre', 'apellido', 'dni', 'tipo_vehiculo', 'celular', 'password']
        for field in required:
            if field not in data or not data[field]:
                return jsonify({"error": f"Falta campo obligatorio: {field}"}), 400

        if find_user_by_dni(users, data['dni']):
            return jsonify({"error": "Usuario ya registrado con ese DNI"}), 400

        new_user = {
            "nombre": data['nombre'],
            "apellido": data['apellido'],
            "dni": data['dni'],
            "tipo_vehiculo": data['tipo_vehiculo'],
            "celular": data['celular'],
            "password": data['password']  # Nota: en producción, encriptar la contraseña
        }
        users.append(new_user)
        save_json(USERS_FILE, users)
        return jsonify({"message": "Registro exitoso"}), 201

    elif action == 'login':
        dni = data.get('dni')
        password = data.get('password')
        if not dni or not password:
            return jsonify({"error": "DNI y contraseña son obligatorios"}), 400

        user = find_user_by_dni(users, dni)
        if not user or user.get('password') != password:
            return jsonify({"error": "DNI o contraseña incorrectos"}), 401

        # Login exitoso, devolvemos datos sin password
        user_safe = user.copy()
        user_safe.pop('password', None)
        return jsonify({"message": "Login exitoso", "user": user_safe})

    else:
        return jsonify({"error": "Acción no soportada"}), 400


@app.route('/api/parking-spots/<int:spot_id>', methods=['PUT'])
def update_spot(spot_id):
    data = request.get_json()
    if not data or 'status' not in data:
        return jsonify({"error": "Falta 'status' en la solicitud"}), 400

    new_status = data['status']
    user_obj = data.get('user', None)  # objeto con datos usuario completo o None

    if new_status not in ['vacío', 'ocupado']:
        return jsonify({"error": "Estado inválido"}), 400

    spots = load_json(SPOTS_FILE)
    history = load_json(HISTORY_FILE)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Para permitir solo un spot ocupado por usuario, verificamos si user ya tiene spot ocupado
    if new_status == 'ocupado' and user_obj:
        user_dni = user_obj.get('dni')
        if user_dni:
            for spot in spots:
                if spot['status'] == 'ocupado' and spot['user'] and spot['user'].get('dni') == user_dni and spot['id'] != spot_id:
                    return jsonify({"error": "El usuario ya tiene un spot ocupado"}), 400

    for spot in spots:
        if spot['id'] == spot_id:
            if new_status == 'ocupado' and spot['status'] != 'ocupado':
                spot['status'] = 'ocupado'
                spot['start_time'] = now
                spot['end_time'] = None
                spot['user'] = user_obj or {}

                history.append({
                    "id": spot_id,
                    "user": spot['user'],
                    "start_time": now,
                    "end_time": None
                })

            elif new_status == 'vacío' and spot['status'] != 'vacío':
                spot['status'] = 'vacío'
                spot['end_time'] = now

                for record in reversed(history):
                    if record['id'] == spot_id and record['end_time'] is None:
                        record['end_time'] = now
                        break

                spot['user'] = None

            save_json(SPOTS_FILE, spots)
            save_json(HISTORY_FILE, history)
            spot = add_rotated([spot])[0]
            return jsonify(spot)

    return jsonify({"error": "Spot no encontrado"}), 404


if __name__ == '__main__':
    app.run(debug=True)
