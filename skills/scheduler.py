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
        if any(t in low for t in ["schedule", "agenda", "calendar", "clear", "week", "upcoming"]): return True
        if ("delete" in low or "remove" in low) and any(x in low for x in ["event", "appointment", "schedule"]): return True
        # Catch numerical deletes if focus is already schedule
        if self.state.last_focus == "schedule" and re.match(r"^(delete|remove|done|complete|finish)\s+\d+$", low):
            return True
        return self.TIME_RE.search(text) is not None

    def execute(self, text):
        low = text.lower()
        
        # 1. Handle explicit clearing
        if "clear" in low:
            self._handle_clear(low)
            
        # 2. Handle deletions/removals
        elif any(x in low for x in ["delete", "remove", "cancel", "done", "finish"]):
            self._handle_remove(low)
            
        # 3. Handle additions (Prioritized over view if 'add' and a time are present)
        elif "add" in low and self.TIME_RE.search(text):
            self._handle_add(text)
            
        # 4. Handle viewing the schedule/agenda
        elif any(t in low for t in ["schedule", "agenda", "calendar", "week", "upcoming"]):
            self._handle_view(low)
            
        # 5. Fallback to add (matches based on TIME_RE from match() logic)
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
        low = text.lower()
        today = datetime.now().date()
        
        # --- RANGE VIEW LOGIC (Week Ahead) ---
        if "week" in low or "upcoming" in low:
            start_date = today
            end_date = today + timedelta(days=7)
            
            # Find all appointments in the next 7 days
            upcoming = []
            for a in self.state.appointments:
                try:
                    appt_date = datetime.fromisoformat(a.get("date")).date()
                    if start_date <= appt_date <= end_date:
                        upcoming.append(a)
                except ValueError:
                    continue
            
            upcoming.sort(key=lambda x: (x['date'], x['time']))
            self.state.view_buffer = list(upcoming)
            
            if not upcoming:
                self.ui.say(f"Your agenda is clear for the upcoming week.")
            else:
                msg = []
                current_day = None
                for i, a in enumerate(upcoming):
                    day_label = datetime.fromisoformat(a['date']).strftime("%A, %b %d")
                    if day_label != current_day:
                        msg.append(f"\n📅 {day_label}:")
                        current_day = day_label
                    msg.append(f"   {i+1}. {a['time']} — {a['title']}")
                
                self.ui.say("\n".join(msg).strip())
            return

        # --- SINGLE DAY VIEW LOGIC ---
        d_iso = self._get_iso_date(text)
        # Filter and sort
        appts = sorted([a for a in self.state.appointments if a.get("date") == d_iso], key=lambda x: x['time'])
        
        # POPULATE VIEW BUFFER: This allows "delete 1" to work relative to this specific list
        self.state.view_buffer = list(appts)
        
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
            
            # Use the anchored view_buffer if it belongs to the schedule
            if self.state.last_focus == "schedule" and self.state.view_buffer:
                items = self.state.view_buffer
            else:
                # Fallback to current day if no buffer exists
                d_iso = self._get_iso_date(text)
                items = sorted([a for a in self.state.appointments if a.get("date") == d_iso], key=lambda x: x['time'])
            
            if 0 <= idx < len(items):
                to_remove = items[idx]
                # Specific removal using title AND date from the buffer object
                self.state.remove_appointment(to_remove['title'], to_remove.get('date'))
                self.ui.success(f"Removed '{to_remove['title']}' from {to_remove.get('date', 'schedule')}")
                # Clear buffer to prevent double-deletion errors
                self.state.view_buffer = []
                return
                
        self.ui.error("Specify a valid event number. You may need to view the agenda first.")

    def _handle_clear(self, text):
        d_iso = self._get_iso_date(text)
        original_count = len(self.state.appointments)
        self.state.appointments = [a for a in self.state.appointments if a.get("date") != d_iso]
        if len(self.state.appointments) < original_count:
            self.state.save()
            self.state.view_buffer = []
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
            
            clean = text.replace(m.group(0), "")
            clean = re.sub(r'\b(add|schedule|remind me|at|for|tonight|today|tomorrow|this|my|calendar|agenda)\b', '', clean, flags=re.I)
            for d in self.WEEKDAYS:
                clean = re.sub(rf'\b{d}\b', '', clean, flags=re.I)
            
            title = clean.strip() or "Appointment"
            self.state.add_appointment(t_str, title, d_iso)
            # Additions reset buffer focus
            self.state.view_buffer = []
            self.ui.success(f"Locked in: '{title}' at {t_str} for {d_iso}")