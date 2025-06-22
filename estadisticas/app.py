from flask import Flask, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

# Conexión a MongoDB Atlas
MONGO_URI = os.environ.get("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["smart_parking"]
historial = db["parking_history"]

# Endpoint de prueba
@app.route("/test-mongo")
def test_mongo():
    try:
        client.server_info()
        return jsonify({"status": "OK", "message": "Conexión exitosa a MongoDB Atlas"})
    except Exception as e:
        return jsonify({"status": "ERROR", "message": str(e)}), 500

# Endpoint principal de estadísticas
@app.route("/api/estadisticas", methods=["GET"])
def obtener_estadisticas():
    registros = list(historial.find())
    estadisticas = {
        "por_hora": {},
        "por_dia": {},
        "por_mes": {},
        "por_año": {},
        "por_franja_horaria": {},
        "por_tipo_dia": {},
        "por_tipo_vehiculo": {},
        "por_estacionamiento": {},
        "usuarios_unicos": 0,
        "total_registros": len(registros),
    }

    usuarios_vistos = set()

    for r in registros:
        if "user" not in r or not r.get("start_time"):
            continue

        fecha = datetime.fromisoformat(r["start_time"])
        hora = str(fecha.hour)
        dia = fecha.strftime("%Y-%m-%d")
        mes = fecha.strftime("%Y-%m")
        año = fecha.strftime("%Y")

        tipo_vehiculo = r["user"].get("tipo_vehiculo", "N/A")
        dni = r["user"].get("dni", None)
        estacionamiento = str(r.get("id", "N/A"))

        # Franjas horarias
        if 6 <= fecha.hour < 12:
            franja = "mañana"
        elif 12 <= fecha.hour < 18:
            franja = "tarde"
        elif 18 <= fecha.hour < 24:
            franja = "noche"
        else:
            franja = "madrugada"

        # Tipo de día
        tipo_dia = "laboral" if fecha.weekday() < 5 else "fin de semana"

        for k, v in [
            ("por_hora", hora),
            ("por_dia", dia),
            ("por_mes", mes),
            ("por_año", año),
            ("por_tipo_vehiculo", tipo_vehiculo),
            ("por_estacionamiento", estacionamiento),
            ("por_franja_horaria", franja),
            ("por_tipo_dia", tipo_dia),
        ]:
            estadisticas[k][v] = estadisticas[k].get(v, 0) + 1

        if dni:
            usuarios_vistos.add(dni)

    estadisticas["usuarios_unicos"] = len(usuarios_vistos)

    return jsonify(estadisticas)

if __name__ == "__main__":
    app.run(debug=True)
