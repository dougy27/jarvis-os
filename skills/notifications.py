from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import re

class NotificationSkill:
    def __init__(self, state, ui):
        self.state = state
        self.ui = ui
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        
    def match(self, text):
        low = text.lower()
        # Match both immediate and delayed notifications
        return any(phrase in low for phrase in [
            "ping me", "remind me", "notification in", "alert me", "notify me"
        ])

    def execute(self, text):
        # Import here to avoid circular dependency
        from jarvis_core import NotificationService
        
        low = text.lower()
        
        # ============================================
        # IMMEDIATE PING TEST
        # ============================================
        if low.strip() == "ping me":
            NotificationService.send("Connectivity Verified", title="JARVIS")
            self.ui.success("Ping sent.")
            return
        
        # ============================================
        # DELAYED REMINDERS (e.g., "in 10 minutes")
        # ============================================
        delay_match = re.search(r'in (\d+)\s*(second|minute|hour|day)s?', low)
        if delay_match:
            amount = int(delay_match.group(1))
            unit = delay_match.group(2)
            
            # Extract message after "to" or "that"
            message_match = re.search(r'(?:to|that)\s+(.+)', text, re.IGNORECASE)
            message = message_match.group(1).strip() if message_match else "Reminder from JARVIS"
            
            # Calculate run time
            delta_map = {
                'second': timedelta(seconds=amount),
                'minute': timedelta(minutes=amount),
                'hour': timedelta(hours=amount),
                'day': timedelta(days=amount)
            }
            run_time = datetime.now() + delta_map[unit]
            
            # Schedule notification
            self.scheduler.add_job(
                NotificationService.send,
                'date',
                run_date=run_time,
                args=[message, "JARVIS Reminder"],
                misfire_grace_time=60
            )
            
            time_str = f"{amount} {unit}{'s' if amount > 1 else ''}"
            self.ui.success(f"Reminder scheduled for {time_str} from now: '{message}'")
            return
        
        # ============================================
        # SPECIFIC TIME (e.g., "at 3pm")
        # ============================================
        time_match = re.search(r'at (\d+):?(\d*)?\s*(am|pm)?', low)
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2)) if time_match.group(2) else 0
            meridiem = time_match.group(3)
            
            # Convert to 24-hour format
            if meridiem == 'pm' and hour < 12:
                hour += 12
            elif meridiem == 'am' and hour == 12:
                hour = 0
            
            # Extract message
            message_match = re.search(r'(?:to|that)\s+(.+)', text, re.IGNORECASE)
            message = message_match.group(1).strip() if message_match else "Scheduled reminder"
            
            # Build target time
            run_time = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
            if run_time < datetime.now():
                run_time += timedelta(days=1)  # Schedule for tomorrow
            
            self.scheduler.add_job(
                NotificationService.send,
                'date',
                run_date=run_time,
                args=[message, "JARVIS Reminder"],
                misfire_grace_time=60
            )
            
            self.ui.success(f"Reminder scheduled for {run_time.strftime('%I:%M %p')}: '{message}'")
            return
        
        # ============================================
        # FALLBACK
        # ============================================
        self.ui.say("I didn't understand that timing. Try: 'ping me' or 'remind me in 5 minutes to check the oven'", self.state)
