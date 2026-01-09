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

    def say(self, text):
        formatted = re.sub(r'\*\*(.*?)\*\*', f'{self.BOLD}\\1{self.END}', text)
        print(f"\n{self.BOT_TAG} {formatted}")

    def system(self, text):
        print(f"\n⚙️ SYSTEM › {text}")

    def success(self, text):
        print(f"\n{self.GREEN}✅ {text}{self.END}")

    def error(self, text):
        print(f"\n{self.RED}❌ {text}{self.END}")
        
    def alert(self, text):
        print(f"\n{self.YELLOW}🔔 {text}{self.END}")