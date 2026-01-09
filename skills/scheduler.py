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
        # View commands
        if any(t in low for t in ["schedule", "agenda", "lock in", "rename"]): return True
        # Explicit removal
        if ("delete" in low or "remove" in low) and any(x in low for x in ["event", "appointment", "calendar", "schedule"]):
            return True
        if "cancel" in low: return True
        # Adding with time
        has_time = self.TIME_RE.search(text)
        actions = ["add", "book", "make", "set", "create", "plan", "going", "meet", "remind"]
        if has_time and any(w in low for w in actions): return True
        return False

    def execute(self, text):
        low = text.lower()
        if any(t in low for t in ["schedule", "agenda"]):
            self._handle_view(low)
            return
        if any(w in low for w in ["delete", "remove", "cancel"]):
            self._handle_remove(low)
            return
        self._handle_add(text)

    def _get_iso_date(self, text):
        today = datetime.now().date()
        low = text.lower()
        if "tomorrow" in low: return (today + timedelta(days=1)).isoformat()
        for i, day in enumerate(self.WEEKDAYS):
            if day in low:
                delta = (i - today.weekday()) % 7
                if delta == 0: delta = 7
                return (today + timedelta(days=delta)).isoformat()
        return today.isoformat()

    def _handle_view(self, text):
        target_date = self._get_iso_date(text)
        appts = [a for a in self.state.appointments if a.get("date") == target_date]
        appts.sort(key=lambda x: x['time'])
        
        date_label = "Today" if target_date == datetime.now().date().isoformat() else datetime.fromisoformat(target_date).strftime("%A")
        if not appts:
            self.ui.say(f"{date_label}'s Agenda: Currently clear.")
        else:
            msg = "\n".join([f"{i+1}. {a['time']} — {a['title']}" for i, a in enumerate(appts)])
            self.ui.say(f"{date_label}'s Agenda:\n{msg}")

    def _handle_remove(self, text):
        # Look for a number
        match = re.search(r"(\d+)", text)
        if match:
            idx = int(match.group(1)) - 1
            target_date = self._get_iso_date(text)
            appts = [a for a in self.state.appointments if a.get("date") == target_date]
            appts.sort(key=lambda x: x['time'])
            if 0 <= idx < len(appts):
                to_remove = appts[idx]
                self.state.remove_appointment(to_remove['title'])
                self.ui.success(f"Removed from schedule: '{to_remove['title']}'")
                return
        self.ui.error("Could not find that event in the specified schedule.")

    def _handle_add(self, text):
        m = self.TIME_RE.search(text)
        if m:
            h, m_val, p = m.group(1), m.group(2) or "00", m.group(3) or ""
            hour = int(h)
            if p.lower() == "pm" and hour < 12: hour += 12
            elif p.lower() == "am" and hour == 12: hour = 0
            formatted_time = f"{hour:02d}:{m_val}"
            
            date_iso = self._get_iso_date(text)
            clean_text = re.sub(r'\b(add|schedule|remind me|at|to|for|tonight|today|tomorrow|' + '|'.join(self.WEEKDAYS) + r')\b', '', text, flags=re.I)
            clean_text = clean_text.replace(m.group(0), "").strip()
            title = clean_text if clean_text else "Appointment"
            
            self.state.add_appointment(time=formatted_time, title=title, date=date_iso)
            self.ui.success(f"Locked in: '{title}' at {formatted_time}")