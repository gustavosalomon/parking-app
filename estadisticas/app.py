from flask import Flask, jsonify
from flask_cors import CORS
from pymongo import MongoClient
import os

app = Flask(__name__)
CORS(app)

# Leer URI MongoDB Atlas de variable de entorno
MONGO_URI = os.environ.get("MONGO_URI")
if not MONGO_URI:
    raise Exception("ERROR: La variable de entorno MONGO_URI no está configurada")

client = MongoClient(MONGO_URI)
db = client["smart_parking"]
estadisticas_collection = db["estadisticas"]

@app.route("/test-mongo")
def test_mongo():
    try:
        # Forzar conexión para probar si está OK
        client.server_info()
        return jsonify({"status": "OK", "message": "Conexión exitosa a MongoDB Atlas"})
    except Exception as e:
        return jsonify({"status": "ERROR", "message": "Fallo de conexión a MongoDB", "detalles": str(e)}), 500

@app.route("/api/estadisticas")
def obtener_estadisticas():
    try:
        doc = estadisticas_collection.find_one(sort=[('_id', -1)])  # último registro
        if not doc:
            return jsonify({"message": "No hay estadísticas disponibles", "status": "OK"})
        
        # Convertir _id ObjectId a str para evitar problemas al serializar JSON
        doc["_id"] = str(doc["_id"])
        return jsonify(doc)
    except Exception as e:
        return jsonify({"status": "ERROR", "message": "Error al obtener estadísticas", "detalles": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
