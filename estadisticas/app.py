from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Datos simulados (o conexión MongoDB)
estadisticas = {
    "por_año": {},
    "por_dia": {},
    "por_estacionamiento": {},
    "por_franja_horaria": {},
    "por_hora": {},
    "por_mes": {},
    "por_tipo_dia": {},
    "por_tipo_vehiculo": {},
    "total_registros": 0,
    "usuarios_unicos": set()
}

def get_franja_horaria(hour):
    if 6 <= hour < 12:
        return "mañana"
    elif 12 <= hour < 18:
        return "tarde"
    else:
        return "noche"

def get_tipo_dia(date_obj):
    return "laboral" if date_obj.weekday() < 5 else "fin_de_semana"

@app.route("/api/estadisticas", methods=["GET"])
def obtener_estadisticas():
    copy_stats = estadisticas.copy()
    copy_stats["usuarios_unicos"] = len(estadisticas["usuarios_unicos"])
    return jsonify(copy_stats), 200

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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
