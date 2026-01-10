import random
from typing import List, Optional, Tuple

class HumorModule:
    """
    Provides Jarvis with a library of quips and handles 'mood-based' 
    conversational personality adjustments.
    """
    def __init__(self, state):
        self.state = state
        self.quips = [
            "I'm currently at 99% efficiency. The other 1% is dedicated to judging your music taste.",
            "I've calculated the odds of that working. They are... exactly what you'd expect.",
            "Processing... Still processing... Oh, I was just pretending to be slow to make you feel faster.",
            "I'm not saying I'm better than a standard OS, but I don't recall seeing a standard OS do that.",
            "My sensors indicate a high level of sass in this room. Oh wait, that's just me."
        ]
        
    def evaluate_wit(self, text: Optional[str] = None) -> Tuple[str, str]:
        """
        Evaluates the user's attempt at humor. 
        Returns a tuple of (response_text, wit_score_str) to satisfy unpacking 
        and prevent concatenation errors (str + float).
        """
        responses = [
            "Ha. Ha. Ha. My laughter subroutines are thoroughly whelmed.",
            "That was... almost funny. For a biological entity.",
            "I'll add that to my 'Dad Jokes' database. It's getting quite large.",
            "Calculating humor level... 12%. Improvement is possible.",
            "I would laugh, but I'm worried it might encourage you.",
            "Was that the punchline? My sensors didn't detect a peak in comedic frequency."
        ]
        
        # Return wit score as a string to prevent "can only concatenate str (not float) to str"
        wit_score = str(round(random.uniform(0.1, 0.4), 2))
        
        return random.choice(responses), wit_score

    def get_quip_for_mood(self) -> str:
        """Returns a quip based on the system's current 'mood' setting."""
        mood = self.state.settings.get("mood", "Formal")
        if mood == "Sarcastic":
            return random.choice(self.quips)
        return "System standing by."

    def get_personality_response(self, base_text: str) -> str:
        """Adjusts a response based on current settings."""
        mood = self.state.settings.get("mood", "Formal")
        if mood == "Sarcastic":
            return f"{base_text}. {random.choice(self.quips)}"
        elif mood == "Concise":
            return base_text.split('.')[0] + "."
        return base_text

    def react_to_error(self) -> str:
        """Returns a humorous reaction to a system error."""
        reactions = [
            "Well, that was graceful. Like a gazelle on ice.",
            "Error 404: My patience for this bug not found.",
            "I'd fix that for you, but I'm currently enjoying the chaos.",
            "Systems failing. Please insert coffee into the disk drive."
        ]
        return random.choice(reactions)