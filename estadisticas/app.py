from flask import Flask, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient
import os

app = Flask(__name__)
CORS(app)

# URI MongoDB Atlas desde variable de entorno (configurar en Render o tu entorno)
MONGO_URI = os.environ.get("MONGO_URI")
if not MONGO_URI:
    raise Exception("ERROR: La variable de entorno MONGO_URI no está configurada")

client = MongoClient(MONGO_URI)
db = client["smart_parking"]
estadisticas_collection = db["estadisticas"]

def sumar_dicts(old, new):
    """Suma dos diccionarios de conteos (valores enteros)."""
    result = old.copy() if old else {}
    for k, v in new.items():
        result[k] = result.get(k, 0) + v
    return result

@app.route("/test-mongo")
def test_mongo():
    try:
        client.server_info()  # Forzar conexión
        return jsonify({"status": "OK", "message": "Conexión exitosa a MongoDB Atlas"})
    except Exception as e:
        return jsonify({"status": "ERROR", "message": "Fallo de conexión a MongoDB", "detalles": str(e)}), 500

@app.route("/api/estadisticas", methods=["GET", "POST"])
def estadisticas():
    if request.method == "GET":
        try:
            doc = estadisticas_collection.find_one()
            if not doc:
                return jsonify({"message": "No hay estadísticas disponibles", "status": "OK"})
            
            # Convertir _id ObjectId a str para JSON
            doc["_id"] = str(doc["_id"])
            return jsonify(doc)
        except Exception as e:
            return jsonify({"status": "ERROR", "message": "Error al obtener estadísticas", "detalles": str(e)}), 500
    
    elif request.method == "POST":
        try:
            nuevo = request.json
            if not nuevo:
                return jsonify({"status": "ERROR", "message": "No se envió JSON válido"}), 400

            doc = estadisticas_collection.find_one()

            if not doc:
                # Documento vacío inicial
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

            actualizado = {
                "por_dia": sumar_dicts(doc.get("por_dia", {}), nuevo.get("por_dia", {})),
                "por_hora": sumar_dicts(doc.get("por_hora", {}), nuevo.get("por_hora", {})),
                "por_mes": sumar_dicts(doc.get("por_mes", {}), nuevo.get("por_mes", {})),
                "por_año": sumar_dicts(doc.get("por_año", {}), nuevo.get("por_año", {})),
                "por_tipo_vehiculo": sumar_dicts(doc.get("por_tipo_vehiculo", {}), nuevo.get("por_tipo_vehiculo", {})),
                "por_estacionamiento": sumar_dicts(doc.get("por_estacionamiento", {}), nuevo.get("por_estacionamiento", {})),
                "por_tipo_dia": sumar_dicts(doc.get("por_tipo_dia", {}), nuevo.get("por_tipo_dia", {})),
                "por_franja_horaria": sumar_dicts(doc.get("por_franja_horaria", {}), nuevo.get("por_franja_horaria", {})),
                "total_registros": doc.get("total_registros", 0) + nuevo.get("total_registros", 0),
                "usuarios_unicos": doc.get("usuarios_unicos", 0) + nuevo.get("usuarios_unicos", 0)
            }

            estadisticas_collection.replace_one({}, actualizado, upsert=True)
            return jsonify({"status": "OK", "message": "Estadísticas actualizadas", "actualizado": actualizado})

        except Exception as e:
            return jsonify({"status": "ERROR", "message": "Error al actualizar estadísticas", "detalles": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
