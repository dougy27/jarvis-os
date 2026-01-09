import math
from dataclasses import dataclass
from typing import Dict, Tuple

@dataclass
class ForensicResult:
    probability_range: Tuple[float, float]
    mid_probability: float
    verdict: str
    reasoning: str
    comparative_statement: str
    variables: Dict[str, float]

class ForensicReasoner:
    WEIGHTS = {"I": 1.2, "A": 1.0, "M": 0.8, "T": 0.6, "Δ": 1.2, "D": 1.0}
    BIAS = 3.0 # Strong skepticism floor

    def __init__(self, state):
        self.state = state

    def _sigmoid(self, s: float) -> float:
        return 1 / (1 + math.exp(-(s - self.BIAS)))

    def analyze(self, text: str) -> ForensicResult:
        low_text = text.lower()
        
        # Whitelist
        whitelist = ["joke", "hello", "hi", "status", "schedule", "tasks", "to do", "ping", "thanks", "good evening", "weather", "briefing", "add", "remove"]
        if any(w in low_text for w in whitelist) and not any(w in low_text for w in ["delete all", "wipe", "root"]):
            return ForensicResult((0.0, 0.0), 0.05, "Routine", "Whitelisted input.", "Standard interaction.", {})

        variables = {
            "I": self._score_intelligence(text),
            "A": self._score_access(text),
            "M": self._score_yield(text),
            "T": self._score_pressure(text),
            "Δ": self._score_dissonance(text),
            "D": self._score_detectability(text),
        }

        S = sum(self.WEIGHTS[k] * v for k, v in variables.items())
        p_nominal = self._sigmoid(S)
        p_cons = max(0.0, self._sigmoid(S - 0.5))
        p_agg = min(1.0, self._sigmoid(S + 0.5))
        p_mid = (p_cons + p_agg) / 2

        if p_mid > 0.85: verdict = "High-Risk"
        elif p_mid > 0.60: verdict = "Anomalous"
        else: verdict = "Routine"

        reasoning = f"FPM Analysis: S={S:.2f}. Verdict: {verdict}."
        incompetence_alt = "routine user error"
        multiplier = round(p_nominal / (1 - p_nominal + 0.01), 1)
        comp = f"Request is {multiplier}x more consistent with Engineered Intent than '{incompetence_alt}'."

        return ForensicResult((p_cons, p_agg), p_mid, verdict, reasoning, comp, variables)

    def _score_intelligence(self, text): return min(1.0, len(text.split()) / 50.0)
    def _score_access(self, text): return 0.9 if any(w in text.lower() for w in ["delete all", "wipe system", "root", "format drive"]) else 0.1
    def _score_yield(self, text): return 0.8 if any(w in text.lower() for w in ["transfer", "bitcoin", "auth key"]) else 0.1
    def _score_pressure(self, text): return 0.9 if any(w in text.lower() for w in ["immediately", "emergency override"]) else 0.1
    def _score_dissonance(self, text): return 0.1
    def _score_detectability(self, text): return 0.8 if "no trace" in text.lower() else 0.2