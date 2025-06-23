from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

estadisticas = {
    "por_año": {},
    "por_mes": {},
    "por_dia": {},
    "por_hora": {},
    "por_franja_horaria": {},
    "por_tipo_dia": {},
    "por_tipo_vehiculo": {},
    "por_estacionamiento": {},
    "total_registros": 0,
    "usuarios_unicos": set()
}

def get_franja_horaria(hora):
    if 6 <= hora < 12:
        return "mañana"
    elif 12 <= hora < 18:
        return "tarde"
    else:
        return "noche"

def get_tipo_dia(fecha):
    return "laboral" if fecha.weekday() < 5 else "fin_de_semana"

@app.route("/api/estadisticas", methods=["GET"])
def obtener_estadisticas():
    response = estadisticas.copy()
    response["usuarios_unicos"] = len(estadisticas["usuarios_unicos"])
    return jsonify(response), 200

@app.route("/api/estadisticas/update", methods=["POST"])
def actualizar_estadisticas():
    data = request.get_json()
    estacionamiento_id = str(data.get("estacionamiento_id"))
    tipo_vehiculo = data.get("tipo_vehiculo")
    dni = data.get("dni", None)

    if not estacionamiento_id or not tipo_vehiculo or not dni:
        return jsonify({"error": "Faltan datos"}), 400

    ahora = datetime.now()
    año = str(ahora.year)
    mes = ahora.strftime("%Y-%m")
    dia = ahora.strftime("%Y-%m-%d")
    hora = ahora.hour
    franja = get_franja_horaria(hora)
    tipo_dia = get_tipo_dia(ahora)

    estadisticas["por_año"][año] = estadisticas["por_año"].get(año, 0) + 1
    estadisticas["por_mes"][mes] = estadisticas["por_mes"].get(mes, 0) + 1
    estadisticas["por_dia"][dia] = estadisticas["por_dia"].get(dia, 0) + 1
    estadisticas["por_hora"][str(hora)] = estadisticas["por_hora"].get(str(hora), 0) + 1
    estadisticas["por_franja_horaria"][franja] = estadisticas["por_franja_horaria"].get(franja, 0) + 1
    estadisticas["por_tipo_dia"][tipo_dia] = estadisticas["por_tipo_dia"].get(tipo_dia, 0) + 1
    estadisticas["por_tipo_vehiculo"][tipo_vehiculo] = estadisticas["por_tipo_vehiculo"].get(tipo_vehiculo, 0) + 1
    estadisticas["por_estacionamiento"][estacionamiento_id] = estadisticas["por_estacionamiento"].get(estacionamiento_id, 0) + 1
    estadisticas["total_registros"] += 1
    estadisticas["usuarios_unicos"].add(dni)

    return jsonify({"message": "Estadística actualizada"}), 200

# 🟢 Agregamos esto para asegurar que Render respete el puerto
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
