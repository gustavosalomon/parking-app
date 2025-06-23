from flask import Flask, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient, UpdateOne
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

MONGO_URI = os.environ.get("MONGO_URI")
if not MONGO_URI:
    raise Exception("ERROR: La variable de entorno MONGO_URI no está configurada")

client = MongoClient(MONGO_URI)
db = client["smart_parking"]
estadisticas_collection = db["estadisticas"]

def actualizar_contador(diccionario, clave, incremento=1):
    diccionario[clave] = diccionario.get(clave, 0) + incremento

@app.route("/api/estadisticas/update", methods=["POST"])
def actualizar_estadisticas():
    data = request.json
    # Ejemplo data esperado: 
    # {
    #   "tipo_vehiculo": "auto",
    #   "estacionamiento_id": "3",
    #   "hora": "14",
    #   "dia": "2025-06-21",
    #   "mes": "2025-06",
    #   "año": "2025",
    #   "tipo_dia": "laboral",
    #   "franja_horaria": "tarde",
    #   "usuario_id": "dni_o_id_usuario"
    # }

    filtro = {"_id": "estadisticas_unicas"}

    actualizacion = {
        "$inc": {
            f"por_tipo_vehiculo.{data.get('tipo_vehiculo')}": 1,
            f"por_estacionamiento.{data.get('estacionamiento_id')}": 1,
            f"por_hora.{data.get('hora')}": 1,
            f"por_dia.{data.get('dia')}": 1,
            f"por_mes.{data.get('mes')}": 1,
            f"por_año.{data.get('año')}": 1,
            f"por_tipo_dia.{data.get('tipo_dia')}": 1,
            f"por_franja_horaria.{data.get('franja_horaria')}": 1,
            "total_registros": 1
        }
    }

    # Actualizar usuarios únicos con addToSet
    if "usuario_id" in data and data["usuario_id"]:
        actualizacion["$addToSet"] = {"usuarios_unicos_set": data["usuario_id"]}

    # Upsert documento acumulado
    result = estadisticas_collection.update_one(filtro, {
        **actualizacion,
        "$setOnInsert": {
            "por_tipo_vehiculo": {},
            "por_estacionamiento": {},
            "por_hora": {},
            "por_dia": {},
            "por_mes": {},
            "por_año": {},
            "por_tipo_dia": {},
            "por_franja_horaria": {},
            "total_registros": 0,
            "usuarios_unicos_set": []
        }
    }, upsert=True)

    return jsonify({"status": "OK", "message": "Estadísticas actualizadas"}), 200

@app.route("/api/estadisticas", methods=["GET"])
def obtener_estadisticas():
    doc = estadisticas_collection.find_one({"_id": "estadisticas_unicas"})
    if not doc:
        return jsonify({"message": "No hay estadísticas disponibles", "status": "OK"})

    # Copiar documento y calcular usuarios_unicos contando el set
    doc = {k: v for k, v in doc.items() if k != "_id" and k != "usuarios_unicos_set"}
    doc["usuarios_unicos"] = len(estadisticas_collection.find_one({"_id": "estadisticas_unicas"}).get("usuarios_unicos_set", []))

    return jsonify(doc)

@app.route("/test-mongo")
def test_mongo():
    try:
        client.server_info()
        return jsonify({"status": "OK", "message": "Conexión exitosa a MongoDB Atlas"})
    except Exception as e:
        return jsonify({"status": "ERROR", "message": "Fallo de conexión a MongoDB", "detalles": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
