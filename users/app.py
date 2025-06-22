from flask import Flask, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient
import os

app = Flask(__name__)  # DEFINIMOS app PRIMERO
CORS(app)

# Conexión a MongoDB Atlas usando variable de entorno
MONGO_URI = os.environ.get("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["smart_parking"]
users_collection = db["users"]

@app.route("/hello")
def hello():
    return "Hola mundo!"

@app.route("/api/users/register", methods=["GET", "POST"])
def register():
    data = request.get_json()
    required_fields = ["nombre", "apellido", "dni", "tipo_vehiculo", "celular", "password"]

    if not data or not all(field in data and data[field] for field in required_fields):
        return jsonify({"error": "Faltan campos obligatorios"}), 400

    if users_collection.find_one({"dni": data["dni"]}):
        return jsonify({"error": "DNI ya registrado"}), 400

    users_collection.insert_one(data)
    return jsonify({"message": "Registro exitoso"}), 201

@app.route("/api/users/login", methods=["GET", "POST"])
def login():
    data = request.get_json()
    dni = data.get("dni")
    password = data.get("password")

    if not dni or not password:
        return jsonify({"error": "DNI y contraseña son obligatorios"}), 400

    user = users_collection.find_one({"dni": dni})
    if not user or user.get("password") != password:
        return jsonify({"error": "DNI o contraseña incorrectos"}), 401

    user.pop("_id", None)
    user.pop("password", None)
    return jsonify({"message": "Login exitoso", "user": user})

@app.route("/test-mongo")
def test_connection():
    try:
        client.server_info()
        return jsonify({"status": "OK", "message": "Conexión exitosa a MongoDB Atlas"})
    except Exception as e:
        return jsonify({"status": "ERROR", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
