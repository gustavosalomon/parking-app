from flask import Flask, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime
from collections import defaultdict

app = Flask(__name__)
CORS(app)

# Conexion a MongoDB Atlas
MONGO_URI = "mongodb://admin:admin123@cluster0-shard-00-00.2owahcw.mongodb.net:27017,cluster0-shard-00-01.2owahcw.mongodb.net:27017,cluster0-shard-00-02.2owahcw.mongodb.net:27017/smart_parking?ssl=true&replicaSet=atlas-13p8m5-shard-0&authSource=admin&retryWrites=true&w=majority"
client = MongoClient(MONGO_URI)
db = client['smart_parking']

spots_collection = db['parking_spots']
estadisticas_collection = db['estadisticas']
users_collection = db['users']

def find_user_by_dni(dni):
    return users_collection.find_one({"dni": dni}, {"_id": 0})

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
        spots = list(spots_collection.find({}, {"_id": 0}))
        spots = add_rotated(spots)
        return jsonify(spots)

    data = request.get_json()
    if not data or 'action' not in data:
        return jsonify({"error": "Falta 'action' en la solicitud"}), 400

    action = data['action']

    if action == 'register':
        required = ['nombre', 'apellido', 'dni', 'tipo_vehiculo', 'celular', 'password']
        for field in required:
            if field not in data or not data[field]:
                return jsonify({"error": f"Falta campo obligatorio: {field}"}), 400

        if find_user_by_dni(data['dni']):
            return jsonify({"error": "Usuario ya registrado con ese DNI"}), 400

        new_user = {
            "nombre": data['nombre'],
            "apellido": data['apellido'],
            "dni": data['dni'],
            "tipo_vehiculo": data['tipo_vehiculo'],
            "celular": data['celular'],
            "password": data['password']
        }
        users_collection.insert_one(new_user)
        return jsonify({"message": "Registro exitoso"}), 201

    elif action == 'login':
        dni = data.get('dni')
        password = data.get('password')
        if not dni or not password:
            return jsonify({"error": "DNI y contraseña son obligatorios"}), 400

        user = find_user_by_dni(dni)
        if not user or user.get('password') != password:
            return jsonify({"error": "DNI o contraseña incorrectos"}), 401

        user.pop('password', None)
        return jsonify({"message": "Login exitoso", "user": user})

    else:
        return jsonify({"error": "Acción no soportada"}), 400

@app.route('/api/parking-spots/<int:spot_id>', methods=['PUT'])
def update_spot(spot_id):
    data = request.get_json()
    if not data or 'status' not in data:
        return jsonify({"error": "Falta 'status' en la solicitud"}), 400

    new_status = data['status']
    user_obj = data.get('user', None)

    if new_status not in ['vacío', 'ocupado']:
        return jsonify({"error": "Estado inválido"}), 400

    spot = spots_collection.find_one({"id": spot_id}, {"_id": 0})
    if not spot:
        return jsonify({"error": "Spot no encontrado"}), 404

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if new_status == 'ocupado':
        if spot['status'] != 'ocupado':
            spot['status'] = 'ocupado'
            spot['start_time'] = now
            spot['end_time'] = None
            spot['user'] = user_obj or {}
    elif new_status == 'vacío':
        if spot['status'] != 'vacío':
            spot['status'] = 'vacío'
            spot['end_time'] = now
            spot['user'] = None

    spots_collection.replace_one({"id": spot_id}, spot, upsert=True)
    spot = add_rotated([spot])[0]
    return jsonify(spot)

@app.route('/api/estadisticas', methods=['GET'])
def obtener_estadisticas():
    estadisticas = estadisticas_collection.find_one({}, {"_id": 0})
    if not estadisticas:
        estadisticas = {
            "por_dia": {}, "por_hora": {}, "por_mes": {}, "por_año": {},
            "por_tipo_vehiculo": {}, "por_estacionamiento": {},
            "por_tipo_dia": {}, "por_franja_horaria": {},
            "total_registros": 0, "usuarios_unicos": 0
        }
    return jsonify(estadisticas)

if __name__ == '__main__':
    app.run(debug=True)
