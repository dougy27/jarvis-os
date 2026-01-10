from typing import Dict, Any, List

class TherapyEngine:
    """
    Core engine for processing emotional data and identifying cognitive distortions.
    Provides context to the LLM/Conversation skill to make Jarvis more empathetic.
    """
    def __init__(self, state):
        self.state = state
        self.distortions_library = [
            "All-or-Nothing Thinking",
            "Overgeneralization",
            "Mental Filter",
            "Disqualifying the Positive",
            "Jumping to Conclusions",
            "Magnification/Minimization",
            "Emotional Reasoning",
            "Should Statements",
            "Labeling",
            "Personalization"
        ]

    def analyze(self, text: str):
        """
        Main entry point used by skills to process user input for therapy insights.
        """
        self.update_state(text)

    def get_prompt_context(self) -> str:
        """
        Returns a string representation of the user's current psychological 
        state to be used by the Conversation/LLM skill.
        """
        data = self.state.therapy_data
        emotions = data.get("emotions", {})
        distortions = data.get("distortions", {})
        trend = data.get("mood_trend", 0.0)

        # Identify dominant emotion
        dominant_emotion = max(emotions, key=emotions.get) if emotions else "neutral"
        
        # Identify active distortions
        active_distortions = [d for d, count in distortions.items() if count > 0]
        dist_str = ", ".join(active_distortions) if active_distortions else "None detected"

        context = (
            f"\n[THERAPY CONTEXT]\n"
            f"- Dominant Emotion: {dominant_emotion}\n"
            f"- Mood Trend: {'Improving' if trend > 0 else 'Declining' if trend < 0 else 'Stable'} ({trend})\n"
            f"- Detected Cognitive Distortions: {dist_str}\n"
        )
        
        if trend < -0.5:
            context += "- Note: User seems highly distressed. Prioritize empathy and validation."
        
        return context

    def analyze_mood(self, text: str) -> Dict[str, Any]:
        """Heuristic-based mood analysis."""
        text_low = text.lower()
        emotions = self.state.therapy_data.get("emotions", {
            "joy": 0.5, "anxiety": 0.2, "sadness": 0.1, "anger": 0.1, "calm": 0.5
        }).copy()
        
        # Sentiment-based increments
        if any(word in text_low for word in ["sad", "lonely", "down", "unhappy", "depressed", "miserable"]):
            emotions["sadness"] = min(1.0, emotions.get("sadness", 0) + 0.15)
            emotions["joy"] = max(0.0, emotions.get("joy", 0) - 0.1)
        
        if any(word in text_low for word in ["anxious", "worried", "scared", "stress", "panic", "overwhelmed"]):
            emotions["anxiety"] = min(1.0, emotions.get("anxiety", 0) + 0.15)
            emotions["calm"] = max(0.0, emotions.get("calm", 0) - 0.15)

        if any(word in text_low for word in ["happy", "great", "awesome", "good", "excellent", "excited"]):
            emotions["joy"] = min(1.0, emotions.get("joy", 0) + 0.15)
            emotions["sadness"] = max(0.0, emotions.get("sadness", 0) - 0.15)
            emotions["calm"] = min(1.0, emotions.get("calm", 0) + 0.05)

        if any(word in text_low for word in ["angry", "mad", "annoyed", "frustrated", "hate"]):
            emotions["anger"] = min(1.0, emotions.get("anger", 0) + 0.2)
            emotions["calm"] = max(0.0, emotions.get("calm", 0) - 0.2)

        return emotions

    def detect_distortions(self, text: str) -> Dict[str, int]:
        """Identify potential cognitive distortions based on keywords."""
        text_low = text.lower()
        found = self.state.therapy_data.get("distortions", {}).copy()

        # Should Statements
        if any(w in text_low for w in ["should", "must", "ought to", "have to"]):
            found["Should Statements"] = found.get("Should Statements", 0) + 1

        # All-or-Nothing Thinking
        if any(w in text_low for w in ["always", "never", "everyone", "nobody", "impossible", "perfect"]):
            found["All-or-Nothing Thinking"] = found.get("All-or-Nothing Thinking", 0) + 1
            
        # Jumping to Conclusions
        if any(w in text_low for w in ["i know they", "probably thinks", "it's going to fail", "it's over"]):
            found["Jumping to Conclusions"] = found.get("Jumping to Conclusions", 0) + 1

        return found

    def update_state(self, text: str):
        """Processes the text and persists the results to the state."""
        new_emotions = self.analyze_mood(text)
        new_distortions = self.detect_distortions(text)
        
        positivity = new_emotions.get("joy", 0) + new_emotions.get("calm", 0)
        negativity = new_emotions.get("sadness", 0) + new_emotions.get("anxiety", 0) + new_emotions.get("anger", 0)
        trend = positivity - negativity

        self.state.therapy_data.update({
            "emotions": new_emotions,
            "distortions": new_distortions,
            "mood_trend": round(trend, 2)
        })
        self.state.save()