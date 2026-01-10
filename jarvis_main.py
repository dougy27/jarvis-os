import sys
import os
import time
import io
import threading
import socket
import traceback
import logging
from datetime import datetime
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

# Absolute path resolution for reliability
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from jarvis_core import JarvisRouter, JarvisState, NotificationService, Config, ContextEngine, NLPProcessor
from jarvis_ui import JarvisUI

# --- WEB BRIDGE INTEGRATION ---
app = Flask(__name__)
CORS(app)

# Silence Flask/Werkzeug request logging to hide API polling spam
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
app.logger.disabled = True

shared_router = None
shared_state = None
shared_ui = None
start_time = time.time()

# --- CONTEXT ENGINE HELPERS ---

def cleanup_declined_context(chat_history: list, user_message: str) -> None:
    """When user declines suggestions, mark the context to prevent LLM re-suggestions."""
    negative_responses = ['no', 'nope', 'nah', 'cancel', 'nevermind', 'never mind', "don't", 'stop', 'forget it']
    if user_message.lower().strip() in negative_responses:
        # Find the last assistant message and insert a hidden system instruction
        for i in range(len(chat_history) - 1, -1, -1):
            msg = chat_history[i]
            if msg.get('role') == 'assistant':
                chat_history.insert(i + 1, {
                    'role': 'system',
                    'content': '[User declined these suggestions - do not reference them again]'
                })
                break

def should_suppress_context(chat_history: list, lookback: int = 4) -> bool:
    """Check if user recently declined suggestions to prevent contextual hallucination loops."""
    if len(chat_history) < 1: return False
    recent = chat_history[-lookback:] if len(chat_history) > lookback else chat_history
    negative_responses = ['no', 'nope', 'nah', 'cancel', 'nevermind', 'never mind', "don't", 'stop']
    for msg in recent:
        if msg.get('role') == 'user' and msg.get('content', '').lower().strip() in negative_responses:
            return True
    return False

def extract_schedule_from_context(user_message: str, chat_history: list) -> list:
    """Extract schedulable items from recent context with guardrails for reminders and negatives."""
    if should_suppress_context(chat_history): return []

    last_jarvis_msg = None
    last_jarvis_index = None
    if chat_history:
        for i, msg in enumerate(reversed(chat_history)):
            if msg.get('role') == 'assistant':
                last_jarvis_msg = msg.get('content')
                last_jarvis_index = len(chat_history) - 1 - i
                break
    
    if not last_jarvis_msg: return []
    user_lower = user_message.lower().strip()

    # Filters: Reminders and stale context
    reminder_patterns = ['remind me', 'reminder', 'set timer', 'set alarm', 'in 1 minute', 'in 5 minutes']
    if any(pattern in user_lower for pattern in reminder_patterns): return []
    if last_jarvis_index is not None and (len(chat_history) - last_jarvis_index) > 3: return []

    # Triggers
    schedule_triggers = ['schedule that', 'add that to', 'create those', 'plan that', 'add those', 'book that']
    simple_affirmations = ['yes', 'proceed', 'confirm', 'go ahead', 'do it', 'sure', 'okay']
    triggered = False
    if user_lower in simple_affirmations:
        scheduling_questions = ['shall i schedule', 'shall i proceed', 'would you like me to schedule', 'shall i add']
        if any(q in last_jarvis_msg.lower() for q in scheduling_questions): triggered = True
    elif any(trigger in user_lower for trigger in schedule_triggers): triggered = True
        
    if not triggered: return []

    appointments = []
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    # Comprehensive activity mapping including narrative items
    activities_map = {
        'dim lights': ('18:00', 'Set ambiance - dim lights'),
        'candles': ('18:15', 'Light candles'),
        'music': ('18:00', 'Relaxing music'),
        'playlist': ('18:00', 'Relaxing music'),
        'dinner': ('19:00', 'Relaxing dinner'),
        'meal': ('19:00', 'Evening meal'),
        'tea': ('16:00', 'Tea time'),
        'chamomile': ('19:30', 'Chamomile tea'),
        'quiche': ('19:00', 'Vegetable quiche'),
        'read': ('20:30', 'Reading session'),
        'book': ('20:30', 'Evening reading'),
        'bath': ('21:00', 'Warm bath'),
        'massage': ('21:30', 'Self-massage'),
        'meditation': ('07:00', 'Meditation session'),
        'workout': ('08:00', 'Morning workout'),
        'walk': ('17:00', 'Evening walk'),
        'yoga': ('07:30', 'Yoga practice')
    }

    msg_lower = last_jarvis_msg.lower()
    found_activities = set()
    for activity, (start_time, default_title) in activities_map.items():
        if activity in msg_lower and activity not in found_activities:
            found_activities.add(activity)
            sentences = [s.strip() for s in last_jarvis_msg.split('.') if s.strip()]
            title = default_title
            for sentence in sentences:
                if activity in sentence.lower() and len(sentence) < 100:
                    clean = sentence.replace('May I propose', '').replace('I suggest', '')
                    clean = clean.replace('Perhaps', '').replace('We might', '').replace('I shall', '').strip()
                    if clean and len(clean) > 5: title = clean[:60]
                    break
            appointments.append({'title': title, 'date': current_date, 'time': start_time, 'location': 'Home'})
    return appointments

# --- MIDDLEWARE & SECURITY ---

@app.after_request
def add_headers(response):
    """Add security and caching headers."""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    if request.path.startswith('/api/'):
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response

@app.errorhandler(Exception)
def handle_error(error):
    """Global error handler."""
    print(f"❌ API Error: {error}")
    return jsonify({"error": str(error), "type": error.__class__.__name__}), 500

# --- API ENDPOINTS ---

@app.route('/')
def serve_dashboard():
    return send_from_directory(BASE_DIR, "dashboard.html")

@app.route('/api/state', methods=['GET'])
def get_state():
    """Returns current system state as JSON."""
    if not shared_state: return jsonify({"error": "Offline"}), 500
    return jsonify({
        'appointments': shared_state.appointments,
        'task_memory': shared_state.task_memory,
        'chat_history': shared_state.chat_history,
        'settings': shared_state.settings,
        'last_focus': shared_state.last_focus,
        'therapy_data': shared_state.therapy_data
    }), 200

@app.route('/api/suggestions')
def get_suggestions():
    if shared_state:
        context = ContextEngine(shared_state)
        return jsonify({"suggestions": context.get_proactive_suggestions()})
    return jsonify({"suggestions": []})

@app.route('/api/nlp/parse-time', methods=['POST'])
def parse_natural_time():
    data = request.json
    parsed = NLPProcessor.parse_time(data.get("text", ""))
    if parsed:
        return jsonify({
            "success": True, 
            "datetime": parsed.isoformat(), 
            "human": parsed.strftime("%A, %B %d at %I:%M %p")
        })
    return jsonify({"success": False, "error": "Could not parse time"})

@app.route('/api/tasks/batch', methods=['POST'])
def batch_task_operations():
    if not shared_state: return jsonify({"error": "Offline"}), 500
    data = request.json
    action = data.get("action")
    if action == "create":
        shared_state.update_tasks(data.get("tasks", []), priority=data.get("priority", "medium"))
        return jsonify({"status": "created"})
    elif action in ["delete", "complete"]:
        shared_state.save_snapshot()
        for t_id in sorted(data.get("ids", []), reverse=True):
            if 0 <= t_id < len(shared_state.task_memory):
                if action == "delete": shared_state.task_memory.pop(t_id)
                else: shared_state.task_memory[t_id]["completed"] = True
        shared_state.save()
        return jsonify({"status": action + "d"})
    return jsonify({"error": "Invalid action"}), 400

@app.route('/api/tasks', methods=['POST'])
def create_task():
    if not shared_state: return jsonify({"error": "Offline"}), 500
    data = request.json
    text = data.get("text", "").strip()
    if not text: return jsonify({"error": "Task text required"}), 400
    shared_state.update_tasks([text], priority=data.get("priority", "medium"))
    return jsonify({"status": "created", "task": text}), 201

@app.route('/api/tasks/<int:task_id>', methods=['PATCH'])
def edit_task_endpoint(task_id):
    if not shared_state: return jsonify({"error": "Offline"}), 500
    if task_id < 0 or task_id >= len(shared_state.task_memory): return jsonify({"error": "Not found"}), 404
    data = request.json
    success = shared_state.edit_task(task_id, text=data.get("text"), priority=data.get("priority"))
    return jsonify({"status": "updated" if success else "failed"}), 200 if success else 500

@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task_endpoint(task_id):
    if not shared_state: return jsonify({"error": "Offline"}), 500
    if task_id < 0 or task_id >= len(shared_state.task_memory): return jsonify({"error": "Not found"}), 404
    shared_state.save_snapshot()
    shared_state.task_memory.pop(task_id)
    shared_state.save()
    return jsonify({"status": "deleted"}), 200

@app.route('/api/appointments', methods=['POST'])
def create_appointment():
    if not shared_state: return jsonify({"error": "Offline"}), 500
    data = request.json
    title, date, time_val = data.get("title", ""), data.get("date", ""), data.get("time", "")
    if not title or not date or not time_val: return jsonify({"error": "Missing fields"}), 400
    shared_state.add_appointment(time_val, title, date, location=data.get("location", "Home"))
    return jsonify({"status": "created"}), 201

@app.route('/api/appointments/<int:appt_id>', methods=['PUT'])
def edit_appointment_endpoint(appt_id):
    if not shared_state: return jsonify({"error": "Offline"}), 500
    if appt_id < 0 or appt_id >= len(shared_state.appointments): return jsonify({"error": "Not found"}), 404
    data = request.json
    shared_state.save_snapshot()
    for key in ["title", "date", "time", "location"]:
        if key in data: shared_state.appointments[appt_id][key] = data[key]
    shared_state.save()
    return jsonify({"status": "updated"}), 200

@app.route('/api/appointments/<int:appt_id>', methods=['DELETE'])
def delete_appointment_endpoint(appt_id):
    if not shared_state: return jsonify({"error": "Offline"}), 500
    if appt_id < 0 or appt_id >= len(shared_state.appointments): return jsonify({"error": "Not found"}), 404
    shared_state.save_snapshot()
    shared_state.appointments.pop(appt_id)
    shared_state.save()
    return jsonify({"status": "deleted"}), 200

@app.route('/api/command', methods=['POST'])
def handle_command():
    """Main API for processing user commands with contextual intelligence."""
    data = request.json
    command = data.get("command", "")
    if shared_router and command:
        cleanup_declined_context(shared_state.chat_history, command)
        contextual_appts = extract_schedule_from_context(command, shared_state.chat_history)
        
        if contextual_appts:
            shared_state.save_snapshot()
            time_groups = {}
            for appt in contextual_appts:
                t = appt['time']
                if t not in time_groups: time_groups[t] = []
                time_groups[t].append(appt['title'])
            
            for t, titles in time_groups.items():
                shared_state.add_appointment(t, " + ".join(titles[:3]), contextual_appts[0]['date'], location='Home')
            
            appt_list = "\n  • ".join([f"{a['time']} - {a['title']}" for a in contextual_appts])
            msg = f"✅ Scheduled {len(contextual_appts)} items from conversation context:\n  • {appt_list}"
            shared_ui.say(msg)
            shared_state.chat_history.append({'role': 'assistant', 'content': msg})
            shared_state.save()
            return jsonify({"status": "uplink_received", "feedback": msg})
        
        threading.Thread(target=shared_router.route_and_execute, args=(command,)).start()
        return jsonify({"status": "uplink_received"})
    return jsonify({"status": "error"}), 400

# --- BACKGROUND SERVICES ---

def background_monitor(state, stop_event):
    sent_alerts = set()
    while not stop_event.is_set():
        now = datetime.now()
        cur_time, today = now.strftime("%H:%M"), now.date().isoformat()
        for appt in list(state.appointments):
            if appt.get("date") == today and appt['time'] == cur_time:
                alert_id = f"{appt['title']}_{cur_time}"
                if alert_id not in sent_alerts:
                    NotificationService.send(f"⏰ {appt['title']}", title="Jarvis Reminder")
                    sent_alerts.add(alert_id)
        time.sleep(30)

def run_web_bridge():
    """Run Flask server without console request logs."""
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    app.run(host='0.0.0.0', port=8000, debug=False, use_reloader=False, threaded=True)

# --- MAIN EXECUTION ---

def main():
    global shared_router, shared_state, shared_ui
    print("\n" + "="*60 + "\n🤖 JARVIS INITIALIZATION SEQUENCE\n" + "="*60)
    try:
        Config.load()
        shared_state = JarvisState.load()
        shared_ui = JarvisUI()
        shared_router = JarvisRouter(shared_state, shared_ui)
        print("✅ Core systems online\n")
    except Exception as e:
        print(f"❌ CRITICAL: {e}"); traceback.print_exc(); return

    shared_ui.banner(shared_state)
    
    try:
        if "briefing" in shared_router.skills:
            print("📋 Running briefing...\n")
            shared_router.skills["briefing"].execute("") 
    except Exception as e: shared_ui.error(f"Briefing Error: {e}")

    threading.Thread(target=run_web_bridge, daemon=True).start()
    stop_event = threading.Event()
    threading.Thread(target=background_monitor, args=(shared_state, stop_event), daemon=True).start()

    # Network Diagnostics
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]; s.close()
    except: local_ip = "127.0.0.1"

    print("\n" + "="*60 + "\n🚀 JARVIS NEURAL LINK ACTIVE\n" + "="*60)
    print(f"  Local:   http://127.0.0.1:8000\n  Network: http://{local_ip}:8000")
    print(f"  Tasks: {len(shared_state.task_memory)} | Appts: {len(shared_state.appointments)}")
    print("="*60 + "\n")

    while True:
        try:
            user_input = shared_ui.prompt()
            if not user_input or user_input.lower() in ["quit", "exit"]: break
            
            cleanup_declined_context(shared_state.chat_history, user_input)
            contextual_appts = extract_schedule_from_context(user_input, shared_state.chat_history)
            
            if contextual_appts:
                shared_state.save_snapshot()
                for appt in contextual_appts:
                    shared_state.add_appointment(appt['time'], appt['title'], appt['date'], location='Home')
                
                appt_list = "\n  • ".join([f"{a['time']} - {a['title']}" for a in contextual_appts])
                msg = f"✅ Scheduled {len(contextual_appts)} items from conversation context:\n  • {appt_list}"
                
                shared_ui.say(msg)
                shared_state.chat_history.append({'role': 'assistant', 'content': msg})
                shared_state.save()
            else:
                shared_router.route_and_execute(user_input)
        except KeyboardInterrupt: break
        except Exception as e: shared_ui.error(f"Kernel Error: {e}"); traceback.print_exc()

    print("\n🔴 Initiating shutdown..."); stop_event.set(); shared_state.save()
    shared_ui.say("Standing by. Sleep well, Master."); print("✨ Offline.\n")

if __name__ == "__main__":
    main()