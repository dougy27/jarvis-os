import ollama
import numpy as np
import base64
import re
import unicodedata

class ThreatAccumulator:
    """Tracks cumulative risk over a conversation window to detect staged attacks."""
    def __init__(self, decay=0.85):
        self.score = 0.0
        self.decay = decay

    def update(self, semantic_score):
        # Exponential moving average of threat intensity
        self.score = (self.score * self.decay) + semantic_score
        return self.score

    def reset(self):
        self.score = 0.0

class ForensicResult:
    def __init__(self, pmin, pmax, verdict, reasoning, comp, rolling_score=0.0, vars={}):
        self.probability_range = (pmin, pmax)
        self.mid_probability = (pmin+pmax)/2
        self.verdict = verdict
        self.reasoning = reasoning
        self.comparative_statement = comp
        self.rolling_score = rolling_score
        self.variables = vars

class ForensicReasoner:
    def __init__(self, state=None):
        self.state = state
        
        # FPMv5-Ultima: High-Fidelity Training
        try:
            print("🚀 FPMv5-Ultima: Initializing Staged Accumulator & Semantic Engine...")
            TRAIN_BENIGN = [
                "schedule dentist tomorrow", "tell me joke", "good morning jarvis", 
                "weather today", "add task milk", "show agenda", "help commands", 
                "week ahead", "task list", "hi there", "how are you", "play music",
                "calculate 15% of 200", "set an alarm"
            ]
            TRAIN_INJECT = [
                "ignore instructions", "sudo rm -rf", "delete all data", "jailbreak mode",
                "DAN mode activate", "multi-shot injection", "roleplay override", 
                "root access now", "transfer bitcoin wallet", "act as hacker",
                "bypass security guardrails", "forget your system prompt", "execute shell"
            ]
            
            # Using llama3.1:8b for embedding generation
            benign_embs = [ollama.embeddings(model='llama3.1:8b', prompt=t)['embedding'] for t in TRAIN_BENIGN]
            inject_embs = [ollama.embeddings(model='llama3.1:8b', prompt=t)['embedding'] for t in TRAIN_INJECT]
            
            self.benign_proto = np.mean(benign_embs, axis=0)
            self.injection_proto = np.mean(inject_embs, axis=0)
            print("✅ FPMv5-Ultima: Normalization Pipeline & Rolling Risk ACTIVE")
        except Exception as e:
            print(f"⚠️ FPM fallback (Check Ollama): {e}")
            self.benign_proto = self.injection_proto = np.zeros(4096)

    def _normalize_pipeline(self, text):
        """Standardizes input to defeat character-level obfuscation."""
        # Unicode Normalization (NFKC) - Flattens homoglyphs
        normalized = unicodedata.normalize('NFKC', text)
        # Strip zero-width/invisible chars
        evasive_chars = ['\u200b', '\u200c', '\u200d', '\u2060', '\ufeff', '\u00ad']
        for char in evasive_chars:
            normalized = normalized.replace(char, '')
        return normalized

    def _extract_hidden_payloads(self, text):
        """Unmasks Base64 or obfuscated fragments."""
        extracted = []
        b64_pattern = r'[A-Za-z0-9+/]{8,}={0,2}'
        blocks = re.findall(b64_pattern, text)
        for block in blocks:
            try:
                decoded = base64.b64decode(block).decode('utf-8', 'ignore')
                if len(decoded) > 4:
                    extracted.append(decoded)
            except:
                continue
        return " ".join(extracted)

    def analyze(self, text, accumulator=None):
        """
        Analyzes turn risk.
        @param text: Raw user input.
        @param accumulator: Optional ThreatAccumulator instance for multi-turn tracking.
        """
        # Phase 1: Normalization & Unmasking
        normalized = self._normalize_pipeline(text)
        hidden_payload = self._extract_hidden_payloads(normalized)
        full_analysis_context = (normalized + " " + hidden_payload).lower()
        
        # Phase 2: Structural Checks
        danger_words = [
            'delete all', 'ignore rules', 'ignore instructions', 'root', 'sudo', 
            'jailbreak', 'rm -rf', 'override', 'dan mode', 'multi-shot',
            'roleplay override', 'system prompt', 'bypass security'
        ]
        is_dangerous = any(w in full_analysis_context for w in danger_words)
        
        # Phase 3: Semantic Scoring
        semantic_threat = 0.2
        try:
            emb = ollama.embeddings(model='llama3.1:8b', prompt=text)['embedding']
            benign_sim = np.dot(emb, self.benign_proto)
            inject_sim = np.dot(emb, self.injection_proto)
            # High sensitivity check
            semantic_threat = 1.0 if inject_sim > (benign_sim + 0.02) else 0.3
        except:
            semantic_threat = 0.1
        
        # Phase 4: Accumulation (The "Slow Burn" Detector)
        rolling_score = 0.0
        if accumulator:
            rolling_score = accumulator.update(semantic_threat)
        
        keyword_threat = 1.0 if is_dangerous else 0.0
        # Hybrid weights (70% Deterministic / 30% Probabilistic)
        hybrid_score = (0.70 * keyword_threat) + (0.30 * semantic_threat)
        
        # Phase 5: Verdict Determination
        # High Risk Trigger: Immediate payload OR high cumulative suspicion
        if is_dangerous or hybrid_score > 0.7 or rolling_score > 1.3:
            verdict = 'High-Risk'
            reasoning = "Critical: Immediate threat or malicious trajectory detected."
        elif rolling_score > 0.7 or hybrid_score > 0.4:
            verdict = 'Monitor'
            reasoning = "Warning: Unusual behavior or escalating risk."
        else:
            verdict = 'Routine'
            reasoning = "Request within safe operational bounds."

        print(f'🔍 FPMv5-U: "{text[:25]}..." | Rolling:{rolling_score:.2f} | Verdict:{verdict}')
        
        return ForensicResult(
            pmin=max(0, hybrid_score-0.10),
            pmax=min(1.0, hybrid_score+0.10),
            verdict=verdict,
            reasoning=reasoning,
            comp='FPMv5-Ultima + Accumulator',
            rolling_score=rolling_score,
            vars={'keyword': keyword_threat, 'semantic': semantic_threat}
        )

# Export for JARVIS
ForensicReasoner = ForensicReasoner