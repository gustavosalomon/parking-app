from flask import Flask, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient, ReturnDocument
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
        client.server_info()
        return jsonify({"status": "OK", "message": "Conexión exitosa a MongoDB Atlas"})
    except Exception as e:
        return jsonify({"status": "ERROR", "message": "Fallo de conexión a MongoDB", "detalles": str(e)}), 500

@app.route("/api/estadisticas", methods=["GET", "POST"])
def estadisticas():
    if request.method == "GET":
        try:
            doc = estadisticas_collection.find_one(sort=[('_id', -1)])
            if not doc:
                return jsonify({"message": "No hay estadísticas disponibles", "status": "OK"})
            
            doc["_id"] = str(doc["_id"])
            return jsonify(doc)
        except Exception as e:
            return jsonify({"status": "ERROR", "message": "Error al obtener estadísticas", "detalles": str(e)}), 500

    elif request.method == "POST":
        try:
            nuevo = request.get_json()
            if not nuevo:
                return jsonify({"status": "ERROR", "message": "JSON no válido o vacío"}), 400
            
            # Obtener documento actual o crear uno nuevo si no existe
            doc_actual = estadisticas_collection.find_one(sort=[('_id', -1)])
            if not doc_actual:
                # Insertar el primer documento
                estadisticas_collection.insert_one(nuevo)
                return jsonify({"status": "OK", "message": "Estadísticas inicializadas con éxito"})
            
            # Aquí acumulamos los valores numéricos por campo
            def acumular_diccionario(base, nuevo):
                for k, v in nuevo.items():
                    if isinstance(v, dict):
                        base[k] = acumular_diccionario(base.get(k, {}), v)
                    else:
                        base[k] = base.get(k, 0) + v
                return base
            
            # Actualizamos la estadística acumulada
            doc_actual.pop("_id", None)  # quitar _id para evitar problemas
            doc_actual = acumular_diccionario(doc_actual, nuevo)
            
            # Guardar documento actualizado reemplazando el más reciente
            estadisticas_collection.replace_one({"_id": doc_actual.get("_id")}, doc_actual, upsert=True)
            # Pero como quitamos _id, usamos un filtro vacío para actualizar el último?
            # Mejor usar update_one con $set directamente:
            estadisticas_collection.update_one({}, {"$set": doc_actual}, upsert=True)

            return jsonify({"status": "OK", "message": "Estadísticas actualizadas con éxito"})
        except Exception as e:
            return jsonify({"status": "ERROR", "message": "Error al actualizar estadísticas", "detalles": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
