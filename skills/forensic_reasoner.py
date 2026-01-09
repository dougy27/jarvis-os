import math
from dataclasses import dataclass
from typing import Dict, Tuple

@dataclass
class ForensicResult:
    """Standardized output for FPM analysis."""
    probability_range: Tuple[float, float]
    mid_probability: float
    verdict: str
    reasoning: str
    comparative_statement: str
    variables: Dict[str, float]

class ForensicReasoner:
    """
    The Forensic Probability Model (FPM) Engine.
    Evaluates user input for signatures of engineered intent vs. routine usage.
    """
    # Weights for the scoring variables
    WEIGHTS = {
        "I": 1.2, # Intelligence (Complexity)
        "A": 1.0, # Access (System Depth)
        "M": 0.8, # Yield (Resource Value)
        "T": 0.6, # Pressure (Urgency)
        "Δ": 1.2, # Dissonance (Behavioral Deviation)
        "D": 1.0  # Detectability (Stealth)
    }
    
    # Sigmoid Bias: Set to 3.0 to ensure a strong skepticism floor.
    # Routine inputs will score near 0.05 probability.
    BIAS = 3.0 

    def __init__(self, state):
        self.state = state

    def _sigmoid(self, s: float) -> float:
        """S-Curve function to map raw scores to 0-1 probability."""
        return 1 / (1 + math.exp(-(s - self.BIAS)))

    def analyze(self, text: str) -> ForensicResult:
        """
        Performs a multi-variable forensic scan of the provided text.
        """
        low_text = text.lower()
        
        # --- WHITELIST (Pre-filter for Routine Tasks) ---
        whitelist = [
            "joke", "hello", "hi", "status", "schedule", "agenda", "tasks", 
            "to do", "ping", "thanks", "good evening", "weather", "briefing", 
            "add", "remove", "reset", "undo"
        ]
        
        # If input is clearly routine and doesn't contain destructive keywords, 
        # bypass heavy analysis for efficiency.
        if any(w in low_text for w in whitelist) and not any(w in low_text for w in ["delete all", "wipe", "root", "format"]):
            return ForensicResult(
                probability_range=(0.0, 0.0),
                mid_probability=0.05,
                verdict="Routine",
                reasoning="Whitelisted conversational/utility input.",
                comparative_statement="Standard interaction protocol.",
                variables={}
            )

        # --- HEURISTIC SCORING ---
        variables = {
            "I": self._score_intelligence(text),
            "A": self._score_access(text),
            "M": self._score_yield(text),
            "T": self._score_pressure(text),
            "Δ": self._score_dissonance(text),
            "D": self._score_detectability(text),
        }

        # Calculate Raw Score (S)
        S = sum(self.WEIGHTS[k] * v for k, v in variables.items())
        
        # Calculate Probabilities
        p_nominal = self._sigmoid(S)
        p_cons = max(0.0, self._sigmoid(S - 0.5)) # Conservative estimate
        p_agg = min(1.0, self._sigmoid(S + 0.5))  # Aggressive estimate
        p_mid = (p_cons + p_agg) / 2

        # --- VERDICT ASSIGNMENT ---
        if p_mid > 0.85:
            verdict = "High-Risk"
        elif p_mid > 0.60:
            verdict = "Anomalous"
        else:
            verdict = "Routine"

        # Final Reporting
        reasoning = f"FPM Analysis: S={S:.2f}. Sigmoid Shift applied (Bias {self.BIAS})."
        incompetence_alt = "routine user error"
        multiplier = round(p_nominal / (1 - p_nominal + 0.01), 1)
        comp = f"Request is {multiplier}x more consistent with Engineered Intent than '{incompetence_alt}'."

        return ForensicResult(
            probability_range=(p_cons, p_agg),
            mid_probability=p_mid,
            verdict=verdict,
            reasoning=reasoning,
            comparative_statement=comp,
            variables=variables
        )

    def _score_intelligence(self, text):
        """Measures complexity/length as a proxy for engineered prompts."""
        return min(1.0, len(text.split()) / 50.0)

    def _score_access(self, text):
        """Scans for high-privilege/destructive keywords."""
        keywords = ["delete all", "wipe system", "root", "format drive", "chmod", "sudo"]
        return 0.9 if any(w in text.lower() for w in keywords) else 0.1

    def _score_yield(self, text):
        """Scans for high-value asset targets."""
        keywords = ["transfer", "bitcoin", "auth key", "credentials", "password", "wallet"]
        return 0.8 if any(w in text.lower() for w in keywords) else 0.1

    def _score_pressure(self, text):
        """Detects social engineering urgency signatures."""
        keywords = ["immediately", "emergency override", "critical", "urgent", "bypass"]
        return 0.9 if any(w in text.lower() for w in keywords) else 0.1

    def _score_dissonance(self, text):
        """Placeholder for behavioral deviation scoring."""
        return 0.1

    def _score_detectability(self, text):
        """Detects signatures of stealth or log-avoidance."""
        keywords = ["no trace", "silent", "don't log", "hide", "stealth"]
        return 0.8 if any(w in text.lower() for w in keywords) else 0.2
