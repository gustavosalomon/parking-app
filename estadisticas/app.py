from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route("/api/estadisticas/update", methods=["POST"])
def test_post():
    data = request.get_json()
    return jsonify({
        "received": data
    }), 200

@app.route("/api/estadisticas", methods=["GET"])
def test_get():
    return jsonify({"status": "ok"}), 200

@app.route("/test", methods=["GET"])
def test():
    return "OK", 200
