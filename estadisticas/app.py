from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import pymongo
import os

app = Flask(__name__)
CORS(app)

# Conexión a MongoDB Atlas (reemplazá si no es correcto)
MONGO_URI = os.getenv("MONGO_URI", "TU_MONGO_URI_AQUI")
client = pymongo.MongoClient(MONGO_URI)
db = client["smart_parking"]
estadisticas_col = db["estadisticas"]

@app.route('/api/estadisticas/update', methods=['POST'])
def registrar_estadistica():
    data = request.get_json()
    estacionamiento_id = data.get("estacionamiento_id")
    tipo_vehiculo = data.get("tipo_vehiculo")
    dni = data.get("dni")

    if not estacionamiento_id or not tipo_vehiculo:
        return jsonify({"error": "Faltan datos requeridos"}), 400

    estadistica = {
        "estacionamiento_id": estacionamiento_id,
        "tipo_vehiculo": tipo_vehiculo,
        "dni": dni,
        "timestamp": datetime.now()
    }

    estadisticas_col.insert_one(estadistica)
    return jsonify({"message": "Estadística registrada correctamente"}), 200

@app.route('/test-mongo', methods=['GET'])
def test():
    return jsonify({"ok": True})

if __name__ == '__main__':
    app.run()
