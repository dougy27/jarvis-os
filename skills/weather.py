import urllib.request
import json
from jarvis_core import Config

class WeatherSkill:
    def __init__(self, state, ui):
        self.state = state
        self.ui = ui

    def match(self, text):
        return "weather" in text.lower()

    def get_weather(self, city=None):
        # Priority: Method argument > Config file > Default
        search_city = city or Config.get("location", "Ottawa")
        
        try:
            # Using wttr.in for a simple, no-key-required weather check
            url = f"https://wttr.in/{search_city}?format=%C+|+%t"
            with urllib.request.urlopen(url, timeout=5) as response:
                condition_temp = response.read().decode('utf-8').strip()
                return f"Weather: {search_city.capitalize()}: {condition_temp}"
        except Exception:
            return f"Weather: Unable to reach meteorological services for {search_city}."

    def execute(self, text):
        # Extract city if mentioned, e.g., "weather in London"
        words = text.lower().split()
        city = None
        if "in" in words:
            city_idx = words.index("in") + 1
            if city_idx < len(words):
                city = words[city_idx]
        
        report = self.get_weather(city)
        self.ui.say(report)