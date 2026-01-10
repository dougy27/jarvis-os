import json
import urllib.request
import time
import re
from datetime import datetime
from typing import List, Dict, Optional, Any

# Dummy classes for type hinting if core modules aren't available
class TherapyEngine:
    def __init__(self, state): pass
    def analyze(self, text): pass
    def get_prompt_context(self): return ""

class HumorModule:
    def __init__(self, state): pass
    def evaluate_wit(self): return False, ""
    def get_personality_response(self, text): return text

class ConversationSkill:
    def __init__(self, state, ui, context_engine=None, therapy_engine=None, humor_module=None):
        self.state = state
        self.ui = ui
        self.context_engine = context_engine
        
        # Store personality engines, falling back to None if not provided
        self.therapy = therapy_engine
        self.humor = humor_module
        
        # Local Llama configuration
        from jarvis_core import Config
        self.ollama_url = Config.get("ollama_url", "http://localhost:11434")
        self.model = Config.get("ollama_model", "llama3.2")

    def match(self, text):
        return True  # Chat is fallback

    def execute(self, text: str):
        """Processes conversation with anti-hallucination measures and prints output for core logging."""
        
        # 1. Therapy Analysis (if engine available)
        if self.therapy:
            self.therapy.analyze(text)
        
        # 2. Anti-Hallucination: Reset on incoherent responses
        if len(self.state.chat_history) > 0:
            last_msg = self.state.chat_history[-1]
            last_response = last_msg.get('content', '') if last_msg.get('role') == 'assistant' else ''
            
            # Detect incoherent markers or repetitive weather hallucinations
            hallucination_markers = ['it is clear today', "it's still clear outside", 'your current situation']
            if any(marker in last_response.lower() for marker in hallucination_markers):
                print("⚠️ Detected incoherent response - clearing recent history")
                # Keep only last 2 exchanges (4 messages: 2 user, 2 assistant)
                self.state.chat_history = self.state.chat_history[-4:]

        # 3. Pinned Context logic
        now = datetime.now()
        today_iso = now.date().isoformat()
        pinned = ""
        if self.state.last_focus == "schedule":
            appts = [f"{a['time']} - {a['title']}" for a in self.state.appointments if a.get("date") == today_iso]
            pinned = f"AGENDA: {', '.join(appts) if appts else 'No events.'}"
        else:
            tasks = [t['text'] for t in self.state.task_memory if not t.get('completed')]
            pinned = f"TASKS: {', '.join(tasks) if tasks else 'No pending tasks.'}"

        # 4. Construct System Prompt
        therapy_context = self.therapy.get_prompt_context() if self.therapy else ""
        system_prompt = (
            f"You are Jarvis, a sophisticated AI butler assistant. {therapy_context}\n"
            f"CURRENT FOCUS: {pinned}\n"
            "Address the user as 'sir' or 'master'. Be formal, witty, and concise.\n"
            "If user declines a suggestion, drop it immediately and focus on the next request."
        )
        
        # Add Mood/Humor instructions
        if self.state.settings.get("mood") == "Sarcastic":
            system_prompt += "\n[Tone Mode: Sarcastic/Witty. Feel free to make dry observations.]"
        elif self.state.settings.get("mood") == "Concise":
            system_prompt += "\n[Tone Mode: Concise. Be brief and direct.]"

        # 5. Build History
        if self.context_engine:
            working_history = self.context_engine.get_cleaned_history(max_messages=12)
        else:
            working_history = self.state.chat_history[-12:]

        # 6. Evaluate Wit (if module available)
        is_joke = False
        signal = ""
        if self.humor:
            try:
                # Some implementations of evaluate_wit might return a tuple
                wit_result = self.humor.evaluate_wit(text) if hasattr(self.humor, 'evaluate_wit') else (False, "")
                if isinstance(wit_result, tuple):
                    is_joke, signal = wit_result
            except Exception:
                pass

        # 7. Call LLM
        response_text = self._call_llama(system_prompt, working_history, text)

        # 8. Final Polish & Output
        if response_text:
            # Inject humor response if detected
            if is_joke and self.humor and hasattr(self.humor, 'get_personality_response'):
                 # If it was a joke, maybe append a specific quip or just let the LLM handle it
                 # but we can append the 'signal' if it's a score
                 if signal:
                     response_text += f" {signal}"
            
            elif self.humor and self.state.settings.get("mood") == "Sarcastic" and len(response_text) < 100:
                 if hasattr(self.humor, 'get_personality_response'):
                    response_text = self.humor.get_personality_response(response_text)

            # ✅ Print only (let _execute_with_logging in core handle chat_history)
            self.ui.say(response_text)

    def _call_llama(self, sys_prompt: str, history: List[Dict], user_text: str) -> str:
        """Call local Llama 3.1 via Ollama generate API"""
        url = f"{self.ollama_url}/api/generate"
        
        # Build the full prompt with system instruction and history
        prompt_parts = [sys_prompt, "\n\n"]
        
        # Add conversation history
        for msg in history[-6:]:
            role = "Master" if msg['role'] == 'user' else "Jarvis"
            if msg['role'] == 'system':
                continue 
            prompt_parts.append(f"{role}: {msg['content']}\n")
        
        # Add current user message
        prompt_parts.append(f"Master: {user_text}\n")
        prompt_parts.append("Jarvis:")
        
        full_prompt = "".join(prompt_parts)
        
        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": 400,
                "stop": ["Master:", "\nMaster", "User:"],
                "top_p": 0.9
            }
        }

        try:
            req = urllib.request.Request(
                url, 
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=60) as res:
                result = json.loads(res.read().decode('utf-8'))
                response = result.get('response', '').strip()
                
                # Clean up any remaining artifacts
                response = response.replace("Jarvis:", "").strip()
                
                return response if response else "I apologize, sir. I'm having difficulty formulating a response."
                
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            print(f"❌ Ollama HTTP {e.code}: {error_body}")
            return "I apologize, sir. My neural processor encountered an error."
        except urllib.error.URLError as e:
            print(f"❌ Ollama connection error: {e}")
            return "I apologize, sir. My neural processor is offline. Please ensure Ollama is running."
        except Exception as e:
            print(f"❌ LLM error: {e}")
            return "I apologize, sir. An unexpected error occurred."