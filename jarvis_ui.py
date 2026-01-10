import re

class JarvisUI:
    USER_TAG = "🧑 MASTER ›"
    BOT_TAG = "🤵 JARVIS ›"
    
    BOLD = "\033[1m"
    END = "\033[0m"
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"

    def banner(self, state):
        concise = "ON" if state.settings.get("concise") else "OFF"
        print(f"{self.BOLD}Jarvis Butler v9.6 (Forensic Core){self.END} | Concise: {concise}")

    def prompt(self):
        return input(f"\n{self.USER_TAG} ").strip()

    def say(self, text, state=None):
        formatted = re.sub(r'\*\*(.*?)\*\*', f'{self.BOLD}\\1{self.END}', text)
        print(f"\n{self.BOT_TAG} {formatted}")
        if state:
            state.log_chat("assistant", text)

    def system(self, text):
        print(f"\n⚙️ SYSTEM › {text}")

    def success(self, text, state=None):
        print(f"\n{self.GREEN}✅ {text}{self.END}")
        if state:
            state.log_chat("assistant", f"Success: {text}")

    def error(self, text, state=None):
        print(f"\n{self.RED}❌ {text}{self.END}")
        if state:
            state.log_chat("assistant", f"Error: {text}")
        
    def alert(self, text, state=None):
        print(f"\n{self.YELLOW}🔔 {text}{self.END}")
        if state:
            state.log_chat("assistant", f"Alert: {text}")