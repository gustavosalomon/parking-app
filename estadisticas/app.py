from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import pymongo
import os

app = Flask(__name__)
CORS(app)

MONGO_URI = os.getenv("MONGO_URI", "TU_MONGO_URI_AQUI")
client = pymongo.MongoClient(MONGO_URI)
db = client["smart_parking"]
estadisticas_col = db["estadisticas"]

@app.route('/api/estadisticas/update', methods=['POST'])
def update_estadisticas():
    data = request.get_json()
    estacionamiento_id = data.get("estacionamiento_id")
    tipo_vehiculo = data.get("tipo_vehiculo")
    dni = data.get("dni")

    if not estacionamiento_id or not tipo_vehiculo:
        return jsonify({"error": "Faltan datos"}), 400

    estadisticas_col.insert_one({
        "estacionamiento_id": estacionamiento_id,
        "tipo_vehiculo": tipo_vehiculo,
        "dni": dni,
        "timestamp": datetime.now()
    })
    return jsonify({"message": "Registrado OK"}), 200

@app.route('/test', methods=['GET'])
def test():
    return jsonify({"ok": True})
