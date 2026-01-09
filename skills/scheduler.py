import re
from datetime import datetime, timedelta

class SchedulerSkill:
    def __init__(self, state, ui):
        self.state = state
        self.ui = ui
        self.TIME_RE = re.compile(r"\b([0-9]{1,2}):?([0-9]{2})?\s*(am|pm)?\b", re.I)
        self.WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

    def match(self, text):
        low = text.lower()
        if any(t in low for t in ["schedule", "agenda", "calendar", "clear"]): return True
        if ("delete" in low or "remove" in low) and any(x in low for x in ["event", "appointment", "schedule"]): return True
        return self.TIME_RE.search(text) is not None

    def execute(self, text):
        low = text.lower()
        if "clear" in low:
            self._handle_clear(low)
        elif any(t in low for t in ["schedule", "agenda", "calendar"]):
            self._handle_view(low)
        elif any(x in low for x in ["delete", "remove", "cancel"]):
            self._handle_remove(low)
        else:
            self._handle_add(text)

    def _get_iso_date(self, text):
        today = datetime.now().date()
        low = text.lower()
        if "tomorrow" in low: return (today + timedelta(days=1)).isoformat()
        for i, day in enumerate(self.WEEKDAYS):
            if day in low:
                delta = (i - today.weekday()) % 7
                if delta <= 0: delta += 7
                return (today + timedelta(days=delta)).isoformat()
        return today.isoformat()

    def _handle_view(self, text):
        d_iso = self._get_iso_date(text)
        appts = sorted([a for a in self.state.appointments if a.get("date") == d_iso], key=lambda x: x['time'])
        date_label = datetime.fromisoformat(d_iso).strftime("%A") if d_iso != datetime.now().date().isoformat() else "Today"
        
        if not appts:
            self.ui.say(f"{date_label}'s Agenda is currently clear.")
        else:
            msg = "\n".join([f"{i+1}. {a['time']} — {a['title']}" for i, a in enumerate(appts)])
            self.ui.say(f"{date_label}'s Agenda:\n{msg}")

    def _handle_remove(self, text):
        m = re.search(r"(\d+)", text)
        if m:
            idx = int(m.group(1)) - 1
            d_iso = self._get_iso_date(text) # Detects if user said "delete 1 from Saturday"
            appts = sorted([a for a in self.state.appointments if a.get("date") == d_iso], key=lambda x: x['time'])
            
            if 0 <= idx < len(appts):
                to_remove = appts[idx]
                self.state.remove_appointment(to_remove['title'])
                self.ui.success(f"Removed '{to_remove['title']}' from {d_iso}")
                return
        self.ui.error("Specify a valid event number and date (e.g., 'delete 1 from saturday').")

    def _handle_clear(self, text):
        d_iso = self._get_iso_date(text)
        original_count = len(self.state.appointments)
        self.state.appointments = [a for a in self.state.appointments if a.get("date") != d_iso]
        if len(self.state.appointments) < original_count:
            self.state.save()
            self.ui.success(f"Schedule for {d_iso} has been wiped.")
        else:
            self.ui.say(f"Schedule for {d_iso} was already clear.")

    def _handle_add(self, text):
        m = self.TIME_RE.search(text)
        if m:
            h, mn, p = int(m.group(1)), m.group(2) or "00", (m.group(3) or "").lower()
            if p == "pm" and h < 12: h += 12
            elif p == "am" and h == 12: h = 0
            elif not p and 1 <= h <= 7: h += 12
            
            t_str, d_iso = f"{h:02d}:{mn}", self._get_iso_date(text)
            
            # Cleaner title extraction: remove time and date keywords, but keep "to" if it's "go to"
            clean = text.replace(m.group(0), "")
            # Only remove "to" if it's followed by "my schedule/calendar"
            clean = re.sub(r'\b(add|schedule|remind me|at|for|tonight|today|tomorrow|this|my|calendar|agenda)\b', '', clean, flags=re.I)
            # Remove days
            for d in self.WEEKDAYS:
                clean = re.sub(rf'\b{d}\b', '', clean, flags=re.I)
            
            title = clean.strip() or "Appointment"
            self.state.add_appointment(t_str, title, d_iso)
            self.ui.success(f"Locked in: '{title}' at {t_str} for {d_iso}")
