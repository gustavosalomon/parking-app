from flask import Flask, jsonify
from flask_cors import CORS
from pymongo import MongoClient
import os
from collections import defaultdict
from datetime import datetime

app = Flask(__name__)
CORS(app)

MONGO_URI = os.environ.get("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["smart_parking"]
collection = db["estadisticas"]

def franja_horaria(hora):
    hora = int(hora)
    if 0 <= hora < 6: return "madrugada"
    if 6 <= hora < 12: return "mañana"
    if 12 <= hora < 18: return "tarde"
    return "noche"

def tipo_dia(fecha):
    return "fin de semana" if datetime.strptime(fecha, "%Y-%m-%d").weekday() >= 5 else "laboral"

@app.route("/api/estadisticas")
def obtener_estadisticas():
    registros = list(collection.find())
    stats = {
        "por_hora": defaultdict(int),
        "por_dia": defaultdict(int),
        "por_mes": defaultdict(int),
        "por_año": defaultdict(int),
        "por_estacionamiento": defaultdict(int),
        "por_tipo_vehiculo": defaultdict(int),
        "por_franja_horaria": defaultdict(int),
        "por_tipo_dia": defaultdict(int),
        "usuarios_unicos": 0,
        "total_registros": 0
    }

    usuarios_set = set()

    for r in registros:
        try:
            fecha = r["fecha"]
            hora = r["hora"]
            id_est = str(r.get("id"))
            tipo_vehiculo = r.get("tipo_vehiculo", "desconocido")
            dni = r.get("dni", "N/A")

            stats["por_hora"][hora] += 1
            stats["por_dia"][fecha] += 1
            stats["por_mes"][fecha[:7]] += 1
            stats["por_año"][fecha[:4]] += 1
            stats["por_estacionamiento"][id_est] += 1
            stats["por_tipo_vehiculo"][tipo_vehiculo] += 1
            stats["por_franja_horaria"][franja_horaria(hora)] += 1
            stats["por_tipo_dia"][tipo_dia(fecha)] += 1
            usuarios_set.add(dni)
        except Exception as e:
            print(f"Error procesando registro: {r}\n{e}")

    stats["usuarios_unicos"] = len(usuarios_set)
    stats["total_registros"] = len(registros)

    return jsonify(stats)

@app.route("/test-mongo")
def test():
    try:
        client.server_info()
        return jsonify({"status": "OK", "message": "Conexión exitosa a MongoDB Atlas"})
    except Exception as e:
        return jsonify({"status": "ERROR", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)

