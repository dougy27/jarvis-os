import sys
import os
import time
import threading
from datetime import datetime

# Ensure the script directory is in the path for module imports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from jarvis_core import JarvisRouter, JarvisState, NotificationService, Config
from jarvis_ui import JarvisUI
from skills.briefing import BriefingSkill

def background_monitor(state, stop_event):
    """
    Background thread that monitors upcoming appointments and triggers
    notifications when the current time matches an event time.
    """
    sent_alerts = set()
    while not stop_event.is_set():
        now = datetime.now()
        current_time_str = now.strftime("%H:%M")
        today_iso = now.date().isoformat()
        
        for appt in state.appointments:
            if appt.get("date") == today_iso:
                if appt['time'] == current_time_str:
                    alert_id = f"{appt['title']}_{appt['time']}_{today_iso}"
                    
                    if alert_id not in sent_alerts:
                        NotificationService.send(
                            f"ALARM: {appt['title']}", 
                            title="Jarvis Reminder"
                        )
                        print(f"\n🔔 REMINDER: {appt['title']}")
                        sent_alerts.add(alert_id)
        
        time.sleep(30)

def main():
    """
    Initializes the Jarvis system, starts the background monitor,
    and enters the primary user interaction loop.
    """
    state = JarvisState.load()
    ui = JarvisUI()
    router = JarvisRouter(state, ui)

    ui.banner(state)

    try:
        briefing = BriefingSkill(state, ui)
        briefing.execute()
    except Exception as e:
        ui.error(f"Briefing Error: {e}")

    stop_event = threading.Event()
    monitor_thread = threading.Thread(
        target=background_monitor, 
        args=(state, stop_event), 
        daemon=True
    )
    monitor_thread.start()

    while True:
        try:
            user_input = ui.prompt()
            if not user_input:
                continue
            
            router.route_and_execute(user_input)
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            ui.error(f"System Error: {e}")

    stop_event.set()
    state.save()
    ui.say("Standing by. Good evening, Master.")

if __name__ == "__main__":
    main()