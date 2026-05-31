from flask import Flask, request, jsonify
from flask_cors import CORS
import hashlib
import time

app = Flask(__name__)
CORS(app)

USERS = {"surgeon01": {"pin": "1234", "role": "SURGEON"}}

@app.route('/login', methods=['POST'])
def login():
    incoming = request.json
    user = USERS.get(incoming.get('username'))
    if user and user['pin'] == incoming.get('pin'):
        return jsonify({"status": "SUCCESS", "role": user['role']})
    return jsonify({"status": "FAIL"}), 401

@app.route('/analyze', methods=['POST'])
def analyze():
    raw_data = request.json
    risk_score = 0.15 
    fingerprint = hashlib.sha256(str(raw_data).encode()).hexdigest()
    return jsonify({"risk": risk_score, "integrity_hash": fingerprint[:10]})

if __name__ == '__main__':
    print("--- SURGESENSE SECURE BACKEND ACTIVE ---")
    app.run(port=8080) # Using 8080 for Mac compatibility




