from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

MONGO_URI = os.getenv("MONGO_URI")  # Asegurate que esté definido en Render
client = MongoClient(MONGO_URI)
db = client["smart_parking"]
estadisticas = db["estadisticas"]

def clasificar_franja_horaria(hora):
    hora = int(hora)
    if 6 <= hora < 12: return "mañana"
    elif 12 <= hora < 18: return "tarde"
    elif 18 <= hora < 24: return "noche"
    else: return "madrugada"

def es_laboral(fecha):
    dia = fecha.weekday()
    return "laboral" if dia < 5 else "fin de semana"

@app.route("/api/estadisticas/update", methods=["POST"])
def actualizar_estadisticas():
    data = request.get_json()
    if not data: return jsonify({"error": "Datos vacíos"}), 400

    fecha = datetime.utcnow()
    hoy_str = fecha.strftime("%Y-%m-%d")
    mes_str = fecha.strftime("%Y-%m")
    año_str = fecha.strftime("%Y")
    hora_str = str(fecha.hour)

    tipo_vehiculo = data.get("tipo_vehiculo", "desconocido")
    spot_id = str(data.get("id"))
    dni = str(data.get("dni", "N/A"))

    franja = clasificar_franja_horaria(hora_str)
    tipo_dia = es_laboral(fecha)

    estadisticas.update_one({}, {
        "$inc": {
            f"por_dia.{hoy_str}": 1,
            f"por_hora.{hora_str}": 1,
            f"por_mes.{mes_str}": 1,
            f"por_año.{año_str}": 1,
            f"por_tipo_vehiculo.{tipo_vehiculo}": 1,
            f"por_estacionamiento.{spot_id}": 1,
            f"por_tipo_dia.{tipo_dia}": 1,
            f"por_franja_horaria.{franja}": 1,
            "total_registros": 1
        },
        "$addToSet": { "dni_registrados": dni }
    }, upsert=True)

    # Actualizar el contador de usuarios únicos
    doc = estadisticas.find_one()
    usuarios = doc.get("dni_registrados", [])
    estadisticas.update_one({}, { "$set": { "usuarios_unicos": len(usuarios) } })

    return jsonify({"mensaje": "Estadísticas actualizadas correctamente"}), 200

@app.route("/api/estadisticas", methods=["GET"])
def obtener_estadisticas():
    doc = estadisticas.find_one({}, {'_id': False})
    if not doc:
        return jsonify({})
    return jsonify(doc)
