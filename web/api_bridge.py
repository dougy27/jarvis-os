from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
import json
import os

app = Flask(__name__)
CORS(app)

# --- SMART PATH RESOLUTION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Try to find the state file in the same folder OR the parent folder
possible_paths = [
    os.path.join(BASE_DIR, "jarvis_state.json"),
    os.path.join(os.path.dirname(BASE_DIR), "jarvis_state.json")
]

DASHBOARD_FILE = "dashboard.html"

def get_actual_state_path():
    for path in possible_paths:
        if os.path.exists(path):
            return path
    return possible_paths[0] # Fallback to default

@app.route('/')
def serve_dashboard():
    """Serves the Neural Console UI."""
    if os.path.exists(os.path.join(BASE_DIR, DASHBOARD_FILE)):
        return send_from_directory(BASE_DIR, DASHBOARD_FILE)
    return f"<h3>Bridge Configuration Error</h3><p>'{DASHBOARD_FILE}' not found in {BASE_DIR}</p>", 404

@app.route('/api/state')
def get_state():
    """Returns the current Jarvis state for the dashboard."""
    state_path = get_actual_state_path()
    
    if not os.path.exists(state_path):
        # Return a 'Zero State' so the dashboard still populates with placeholders
        return jsonify({
            "status": "waiting_for_core",
            "last_focus": "STANDBY",
            "appointments": [],
            "task_memory": [],
            "therapy_data": {
                "emotions": {"joy": 0.1, "anxiety": 0.1, "sadness": 0.1, "calm": 0.8},
                "distortions": {},
                "mood_trend": 0.0
            }
        })

    try:
        with open(state_path, 'r') as f:
            data = json.load(f)
            return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/command', methods=['POST'])
def handle_command():
    """Receives commands from the dashboard."""
    data = request.json
    command = data.get("command", "")
    print(f"📡 Remote Terminal: {command}")
    return jsonify({"status": "acknowledged", "command": command})

if __name__ == "__main__":
    print("\n" + "="*40)
    print("🚀 JARVIS NEURAL BRIDGE: ONLINE")
    print(f"📡 URL: http://127.0.0.1:8000")
    print(f"📂 Resolved Data: {get_actual_state_path()}")
    print("="*40 + "\n")
    app.run(port=8000, debug=False)