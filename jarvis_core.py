import json
import os
import urllib.request
import yaml
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any
from datetime import datetime

# --- CONFIGURATION ---
CONFIG_FILE = "config.yaml"

class Config:
    _data = {}
    
    @classmethod
    def load(cls):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                cls._data = yaml.safe_load(f)
    
    @classmethod
    def get(cls, key, default=None):
        return cls._data.get(key, default)

# --- NOTIFICATION SERVICE ---
class NotificationService:
    @staticmethod
    def send(message: str, title: str = "Jarvis"):
        topic = Config.get("ntfy_topic", "jarvis_default")
        try:
            url = f"https://ntfy.sh/{topic}"
            data = message.encode('utf-8')
            req = urllib.request.Request(url, data=data, method='POST')
            req.add_header("Title", title)
            req.add_header("Priority", "high" if "urgent" in message.lower() else "default")
            req.add_header("Tags", "robot,warning" if "urgent" in message.lower() else "robot")
            with urllib.request.urlopen(req, timeout=5) as response:
                return response.status == 200
        except Exception: return False

@dataclass
class JarvisState:
    appointments: List[Dict[str, Any]] = field(default_factory=list)
    task_memory: List[Dict[str, Any]] = field(default_factory=list) 
    chat_history: List[Dict[str, str]] = field(default_factory=list)
    settings: Dict[str, Any] = field(default_factory=lambda: {"mood": "Formal", "concise": False})
    
    # State file anchored to script directory
    STATE_FILE = os.path.join(os.path.dirname(__file__), "jarvis_state.json")
    _undo_stack: List[Dict] = field(default_factory=list, repr=False)

    def save_snapshot(self):
        if len(self._undo_stack) > 10: self._undo_stack.pop(0)
        snapshot = asdict(self)
        del snapshot['_undo_stack']
        self._undo_stack.append(snapshot)

    def restore_snapshot(self):
        if not self._undo_stack: return False
        prev = self._undo_stack.pop()
        self.appointments = prev['appointments']
        self.task_memory = prev['task_memory']
        self.chat_history = prev['chat_history']
        self.settings = prev['settings']
        self.save()
        return True

    def save(self):
        try:
            data = asdict(self)
            del data['_undo_stack']
            with open(self.STATE_FILE, 'w') as f: json.dump(data, f, indent=2)
        except Exception: pass

    @classmethod
    def load(cls):
        Config.load()
        if os.path.exists(cls.STATE_FILE):
            try:
                with open(cls.STATE_FILE, 'r') as f:
                    data = json.load(f)
                    return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
            except Exception: pass
        return cls()
    
    def log_chat(self, role, content):
        self.chat_history.append({"role": role, "content": content})
        self.save()
    
    def add_appointment(self, time, title, date, location=None, people=None):
        self.save_snapshot()
        self.appointments.append({"time": time, "title": title, "date": date, "location": location, "people": people or []})
        self.deduplicate()
        self.save()
        if "urgent" in title.lower() or "important" in title.lower():
            NotificationService.send(f"New High-Priority Event: {title} at {time}", title="Calendar Update")
    
    def remove_appointment(self, title):
        self.save_snapshot()
        original_len = len(self.appointments)
        self.appointments = [a for a in self.appointments if title.lower() not in a['title'].lower()]
        self.save()
        return original_len - len(self.appointments)

    def update_tasks(self, tasks):
        self.save_snapshot()
        for t in tasks: self.task_memory.append({"text": t, "status": "open", "created_at": datetime.now().isoformat()})
        self.save()

    def remove_task(self, text):
        self.save_snapshot()
        original_len = len(self.task_memory)
        self.task_memory = [t for t in self.task_memory if text.lower() not in t['text'].lower()]
        self.save()
        return original_len - len(self.task_memory)

    def deduplicate(self):
        seen = set()
        unique = []
        for a in self.appointments:
            key = (a.get("date"), a["time"], a["title"])
            if key not in seen:
                seen.add(key); unique.append(a)
        self.appointments = unique
        self.save()

# --- ROUTER ---
from skills import system, scheduler, tasks, conversation, notifications, fpm_engine, briefing, weather

class JarvisRouter:
    def __init__(self, state, ui):
        self.state = state
        self.ui = ui
        self.forensics = fpm_engine.ForensicReasoner(state)
        # TaskSkill placed above SchedulerSkill to prevent routing collisions
        self.skills = [
            system.SystemSkill(state, ui),
            notifications.NotificationSkill(state, ui),
            tasks.TaskSkill(state, ui),
            scheduler.SchedulerSkill(state, ui),
            briefing.BriefingSkill(state, ui), 
            weather.WeatherSkill(state, ui), 
            conversation.ConversationSkill(state, ui)
        ]

    def route_and_execute(self, text):
        self.state.log_chat("user", text)
        
        override_phrase = Config.get("override_phrase", "override phoenix")
        if override_phrase in text.lower():
            self.ui.alert("Override Code Accepted. FPM Bypassed.")
        else:
            report = self.forensics.analyze(text)
            if report.verdict == "High-Risk":
                self.ui.error(f"SECURITY ALERT: {report.reasoning}")
                self.ui.say("Request refused. Type override code to proceed.")
                return
            if report.verdict == "Anomalous":
                self.ui.say(f"⚠️  Note: {report.reasoning}")

        for skill in self.skills:
            if skill.match(text):
                skill.execute(text)
                return