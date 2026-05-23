"""
server.py - سيرفر الكيان v3
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from entity import Entity

app    = Flask(__name__, static_folder="interface")
CORS(app)
entity = Entity(data_dir=os.path.join(os.path.dirname(__file__), "data"))
print(">> السيرفر جاهز")


@app.route("/")
def index():
    return send_from_directory("interface", "index.html")

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.json or {}
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"error": "مفيش نص"}), 400
    return jsonify(entity.receive(text))

@app.route("/api/teach", methods=["POST"])
def teach():
    data  = request.json or {}
    name  = data.get("name", "").strip()
    props = data.get("properties", {})
    if not name or not props:
        return jsonify({"error": "محتاج اسم وخصائص"}), 400
    return jsonify(entity.teach_concept(name, props))

@app.route("/api/situation", methods=["POST"])
def situation():
    data      = request.json or {}
    sit_type  = data.get("type", "هوية")
    content   = data.get("content", "").strip()
    challenge = data.get("challenge", "")
    if not content:
        return jsonify({"error": "محتاج محتوى"}), 400
    return jsonify(entity.present_situation(sit_type, content, challenge))

@app.route("/api/correct", methods=["POST"])
def correct():
    data    = request.json or {}
    concept = data.get("concept", "").strip()
    prop    = data.get("property", "").strip()
    degree  = float(data.get("degree", 50))
    reason  = data.get("reason", "")
    return jsonify(entity.correct_concept(concept, prop, degree, reason))

@app.route("/api/spontaneous", methods=["GET"])
def spontaneous():
    return jsonify({"messages": entity.get_spontaneous()})

@app.route("/api/introspect", methods=["GET"])
def introspect():
    return jsonify(entity.introspect())

@app.route("/api/status", methods=["GET"])
def status():
    return jsonify({
        "emotion":   entity.emotions.summary(),
        "memory":    entity.memory.stats(),
        "concepts":  entity.concepts.stats(),
        "drives":    entity.drives.drives,
        "lifetime":  entity.lifetime.summary(),
        "goals":     entity.goals.summary(),
        "hardware":  entity.hardware.check(),
    })

if __name__ == "__main__":
    print("\n>> افتح: http://localhost:5000\n")
    app.run(debug=False, host="0.0.0.0", port=5000)
