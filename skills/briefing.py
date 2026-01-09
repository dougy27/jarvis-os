from datetime import datetime
import random
from skills.weather import WeatherSkill
from jarvis_core import Config

class BriefingSkill:
    def __init__(self, state, ui):
        self.state = state
        self.ui = ui
        self.weather = WeatherSkill(state, ui)

    def match(self, text):
        return any(w in text.lower() for w in ["briefing", "good morning", "summary"])

    def execute(self, text=None):
        now = datetime.now()
        date_str = now.strftime("%A, %B %d")
        user = "Boss"
        
        lines = []
        lines.append(f"Good morning, {user}. Today is {date_str}.")
        lines.append("-" * 40)
        
        today_iso = now.date().isoformat()
        todays_appts = [a for a in self.state.appointments if a.get("date") == today_iso]
        todays_appts.sort(key=lambda x: x['time'])
        
        if todays_appts:
            lines.append(f"📅 **Today's Schedule ({len(todays_appts)} events):**")
            for a in todays_appts:
                lines.append(f"   • {a['time']} – {a['title']}")
        else:
            lines.append("📅 **Schedule:** Clear. A blank canvas.")
            
        lines.append("")
        
        open_tasks = self.state.task_memory
        if open_tasks:
            top_3 = open_tasks[:3]
            lines.append(f"📝 **Top Tasks ({len(open_tasks)} pending):**")
            for t in top_3:
                lines.append(f"   • {t['text']}")
            if len(open_tasks) > 3:
                lines.append(f"     ...and {len(open_tasks)-3} more.")
        else:
            lines.append("📝 **Tasks:** All clear. Nice work.")
            
        lines.append("")
        
        # FIX: Pull location from config instead of hardcoding "Toronto"
        location = Config.get("location", "Ottawa")
        weather_report = self.weather.get_weather(location)
        lines.append(weather_report)
        
        quotes = ["Let's crush it.", "Focus on impact.", "One step at a time.", "The world is yours."]
        lines.append(f"\n💡 {random.choice(quotes)}")
        
        self.ui.say("\n".join(lines))