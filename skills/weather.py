import urllib.request

class WeatherSkill:
    def __init__(self, state, ui):
        self.state = state
        self.ui = ui

    def get_weather(self, location="Toronto"):
        try:
            url = f"https://wttr.in/{location}?format=3"
            with urllib.request.urlopen(url, timeout=5) as response:
                if response.status == 200:
                    data = response.read().decode('utf-8').strip()
                    return f"Weather: {data}"
        except Exception: pass
        return "Weather: Data currently unavailable."

    def match(self, text):
        return "weather" in text.lower()

    def execute(self, text):
        report = self.get_weather("Toronto")
        self.ui.say(report)