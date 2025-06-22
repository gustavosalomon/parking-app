from flask import Flask, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient
import os

app = Flask(__name__)
CORS(app)

MONGO_URI = os.environ.get("MONGO_URI")
if not MONGO_URI:
    raise Exception("ERROR: La variable de entorno MONGO_URI no está configurada")

client = MongoClient(MONGO_URI)
db = client["smart_parking"]
estadisticas_collection = db["estadisticas"]

def inicializar_estadisticas():
    # Documento inicial con todos los campos vacíos o cero
    doc = {
        "por_dia": {},
        "por_hora": {},
        "por_mes": {},
        "por_año": {},
        "por_tipo_vehiculo": {},
        "por_estacionamiento": {},
        "por_tipo_dia": {},
        "por_franja_horaria": {},
        "total_registros": 0,
        "usuarios_unicos": 0
    }
    estadisticas_collection.insert_one(doc)

def sumar_diccionarios(destino, origen):
    for k, v in origen.items():
        destino[k] = destino.get(k, 0) + v

@app.route("/test-mongo")
def test_mongo():
    try:
        client.server_info()
        return jsonify({"status": "OK", "message": "Conexión exitosa a MongoDB Atlas"})
    except Exception as e:
        return jsonify({"status": "ERROR", "message": "Fallo de conexión a MongoDB", "detalles": str(e)}), 500

@app.route("/api/estadisticas", methods=["GET", "POST"])
def estadisticas():
    # Obtener documento único
    doc = estadisticas_collection.find_one()
    if not doc:
        inicializar_estadisticas()
        doc = estadisticas_collection.find_one()

    if request.method == "GET":
        # Convertir _id a str y devolver documento
        doc["_id"] = str(doc["_id"])
        return jsonify(doc)

    if request.method == "POST":
        data = request.json
        if not data:
            return jsonify({"status": "ERROR", "message": "No se enviaron datos"}), 400

        # Actualizar sumando valores
        for campo in ["por_dia", "por_hora", "por_mes", "por_año", "por_tipo_vehiculo",
                      "por_estacionamiento", "por_tipo_dia", "por_franja_horaria"]:
            if campo in data:
                sumar_diccionarios(doc.get(campo, {}), data[campo])

        # Sumar total_registros y usuarios_unicos
        doc["total_registros"] = doc.get("total_registros", 0) + data.get("total_registros", 0)
        doc["usuarios_unicos"] = doc.get("usuarios_unicos", 0) + data.get("usuarios_unicos", 0)

        # Guardar documento actualizado en MongoDB (usando reemplazo)
        estadisticas_collection.replace_one({"_id": doc["_id"]}, doc)

        doc["_id"] = str(doc["_id"])
        return jsonify({"status": "OK", "message": "Estadísticas actualizadas", "datos": doc})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
