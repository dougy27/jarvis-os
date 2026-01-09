import ollama
from datetime import datetime, timedelta

class ConversationSkill:
    def __init__(self, state, ui):
        self.state = state
        self.ui = ui
        self.model = "llama3.1:8b"

    def match(self, text):
        return True # Catch-all

    def execute(self, text):
        # Fix: Generate a 7-day snapshot so Saturday isn't "invisible"
        now = datetime.now()
        today = now.date()
        horizon = today + timedelta(days=7)
        
        upcoming = []
        for a in self.state.appointments:
            try:
                appt_date = datetime.fromisoformat(a.get("date")).date()
                if today <= appt_date <= horizon:
                    label = "Today" if appt_date == today else appt_date.strftime("%A")
                    upcoming.append(f"{label} {a['time']} - {a['title']}")
            except:
                continue
        
        tasks = [t['text'] for t in self.state.task_memory]
        
        snapshot = (
            f"SYSTEM SNAPSHOT ({now.strftime('%H:%M')}):\n"
            f"Current Date: {now.strftime('%A, %B %d, %Y')}\n"
            f"Upcoming 7-Day Schedule: {', '.join(upcoming) if upcoming else 'Clear'}\n"
            f"Pending Tasks: {', '.join(tasks) if tasks else 'None'}\n"
            "---"
        )

        # Fix: Updated prompt to ignore snapshot for jokes/general chat
        system_prompt = (
            "You are Jarvis, a formal and witty butler. "
            "You have access to the SYSTEM SNAPSHOT provided below. "
            "ONLY refer to the snapshot if the user asks about their schedule, tasks, or life data. "
            "For general knowledge, jokes, or chit-chat, ignore the snapshot content. "
            "Do NOT summarize history. Be concise and witty."
        )

        messages = [
            {"role": "system", "content": f"{system_prompt}\n\n{snapshot}"}
        ]
        
        recent_history = self.state.chat_history[-4:] 
        messages.extend(recent_history)
        messages.append({"role": "user", "content": text})

        self.ui.say("Thinking...") 

        try:
            resp = ollama.chat(model=self.model, messages=messages)
            response_text = resp["message"]["content"]
            self.ui.say(response_text)
            self.state.log_chat("assistant", response_text)
        except Exception as e:
            self.ui.error(f"Cognitive Core Offline: {e}")