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
        # Fix: Guard against routing task-related deletes to scheduler
        if "task" in low:
            return False
            
        triggers = ["schedule", "agenda", "lock in", "cancel", "delete", "remove", "rename"]
        if any(t in low for t in triggers): return True
        has_time = self.TIME_RE.search(text)
        actions = ["add", "book", "make", "set", "create", "plan", "going", "meet", "remind"]
        if has_time and any(w in low for w in actions): return True
        return False

    def execute(self, text):
        low = text.lower()
        
        if "lock in" in low or "confirm plan" in low:
            self._handle_lock_in()
            return

        if "schedule" in low or "agenda" in low:
            self._handle_view(low)
            return

        if any(low.startswith(x) for x in ["cancel", "remove schedule", "delete schedule", "remove event", "delete", "remove"]):
            self._handle_remove(low)
            return

        if low.startswith("rename"):
            self._handle_rename(low)
            return

        self._handle_add(text)

    def _get_iso_date(self, text):
        today = datetime.now().date()
        low = text.lower()
        
        if "tomorrow" in low: return (today + timedelta(days=1)).isoformat()
        if "today" in low: return today.isoformat()
        
        for i, day_name in enumerate(self.WEEKDAYS):
            if day_name in low:
                today_idx = today.weekday()
                target_idx = i
                delta = (target_idx - today_idx) % 7
                if delta <= 0: delta += 7
                return (today + timedelta(days=delta)).isoformat()
        
        return today.isoformat()

    def _handle_view(self, text):
        target_date = self._get_iso_date(text)
        appts = [a for a in self.state.appointments if a.get("date") == target_date]
        appts.sort(key=lambda x: x['time'])
        
        date_label = "Today"
        if target_date != datetime.now().date().isoformat():
            date_label = datetime.fromisoformat(target_date).strftime("%A")

        if not appts:
            self.ui.say(f"{date_label}'s Agenda:\nCurrently clear.")
        else:
            msg = "\n".join([f"{i+1}. {a['time']} — {a['title']}" for i, a in enumerate(appts)])
            self.ui.say(f"{date_label}'s Agenda:\n{msg}")

    def _handle_remove(self, text):
        parts = text.split(" ", 1)
        if len(parts) < 2:
            self.ui.error("Please specify a valid event number or range.")
            return

        target = parts[1].strip().lower()

        # Fix: Support for single index or ranges like "1 to 4" or "1-3"
        if target.isdigit():
            start_idx = end_idx = int(target)
        else:
            m = re.match(r"^(\d+)\s*(?:-|\s+to\s+)\s*(\d+)$", target)
            if not m:
                self.ui.error("Specify a number or range (e.g., 'delete 2' or 'delete 1 to 4').")
                return
            start_idx, end_idx = int(m.group(1)), int(m.group(2))
            if start_idx > end_idx: start_idx, end_idx = end_idx, start_idx

        today_iso = datetime.now().date().isoformat()
        appts = [a for a in self.state.appointments if a.get("date") == today_iso]
        appts.sort(key=lambda x: x['time'])
        
        removed_any = False
        titles_removed = []

        # Iterate in reverse to avoid index shifting
        for idx in range(end_idx, start_idx - 1, -1):
            zero_idx = idx - 1
            if 0 <= zero_idx < len(appts):
                to_remove = appts[zero_idx]
                self.state.remove_appointment(to_remove['title'])
                titles_removed.append(to_remove['title'])
                removed_any = True

        if not removed_any:
            self.ui.error("Event number(s) not found in today's view.")
        else:
            self.ui.success(f"Removed: {', '.join(titles_removed)}")

    def _handle_add(self, text):
        m = self.TIME_RE.search(text)
        if m:
            h = m.group(1)
            m_val = m.group(2) or "00"
            p = m.group(3) or ""
            
            hour = int(h)
            p_low = p.lower()
            if p_low == "pm" and hour < 12: hour += 12
            elif p_low == "am" and hour == 12: hour = 0
            elif not p_low and 1 <= hour <= 7: hour += 12
            
            formatted_time = f"{hour:02d}:{m_val}"
            date_iso = self._get_iso_date(text)
            
            clean_text = text.replace(m.group(0), "")
            clean_text = re.sub(r'\b(add|schedule|book|set|create|plan|going to|remind me to|remind me|at|to|for|tonight)\b', '', clean_text, flags=re.I)
            days_pattern = '|'.join(self.WEEKDAYS + ['today', 'tomorrow'])
            clean_text = re.sub(r'\b(' + days_pattern + r')\b', '', clean_text, flags=re.I)
            
            clean_text = clean_text.replace('"', '').replace("'", "").strip()
            title = re.sub(r'\s+', ' ', clean_text)
            if not title: title = "Appointment"
            
            self.state.add_appointment(time=formatted_time, title=title, date=date_iso)
            
            pretty_date = datetime.fromisoformat(date_iso).strftime("%A")
            if date_iso == datetime.now().date().isoformat(): pretty_date = "Today"
                
            self.ui.success(f"Locked in: '{title}' for {pretty_date} at {formatted_time}")

    def _handle_rename(self, text):
        self.ui.success("Rename logic stub.")

    def _handle_lock_in(self):
        self.ui.success("Lock-in logic stub.")