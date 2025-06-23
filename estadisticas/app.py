from flask import Flask, jsonify, request
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
def actualizar_estadisticas():
    data = request.json
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

@app.route('/test-mongo')
def test_mongo():
    return jsonify({"success": True})

if __name__ == '__main__':
    app.run(debug=True)
