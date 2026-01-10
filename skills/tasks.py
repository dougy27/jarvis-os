import re

class TaskSkill:
    def __init__(self, state, ui):
        self.state = state
        self.ui = ui

    def match(self, text):
        low = text.lower()
        
        # 1. Explicit task-related keywords
        if any(w in low for w in ["task", "to do", "todo", "list"]): 
            return True
            
        # 2. Match "delete 1", "done 2", etc.
        if re.match(r"^(delete|remove|done|complete|finish)\s+\d+$", low): 
            return True
            
        # 3. Handle "add ..." with exclusion logic for the scheduler
        if low.startswith("add "):
            # Exclude explicit scheduling keywords
            if any(x in low for x in ["schedule", "calendar", "event", "tomorrow", "today"]):
                return False
            
            # Exclude specific time patterns (e.g., "at 3", "3pm", "14:30")
            # We look for "at " followed by a digit, or time-specific formats
            if "at " in low and re.search(r"at \d", low):
                return False
            if re.search(r"\b\d{1,2}(?::\d{2})?\s*(?:am|pm)\b|\b\d{1,2}:\d{2}\b", low, re.I):
                return False
                
            return True
            
        return False

    def execute(self, text):
        low = text.lower()
        
        # 1. Numbered Removal Logic utilizing View Buffer
        match = re.match(r"^(delete|remove|done|complete|finish)\s+(\d+)$", low)
        if match:
            idx = int(match.group(2)) - 1
            
            # Use view_buffer if it exists and focus is tasks
            if self.state.last_focus == "tasks" and self.state.view_buffer:
                items = self.state.view_buffer
            else:
                items = self.state.task_memory
                
            if 0 <= idx < len(items):
                # For tasks, items in buffer are dicts: {"text": "...", "status": "..."}
                target = items[idx]
                task_text = target.get('text') if isinstance(target, dict) else target
                
                self.state.remove_task(task_text)
                self.ui.success(f"Task cleared: {task_text}")
                # Clear buffer after successful action to prevent stale pointers
                self.state.view_buffer = [] 
            else:
                self.ui.error(f"Task #{idx+1} not found in current context.")
            return

        # 2. Add Logic
        if "add" in low:
            clean_text = text
            fillers = [
                r'\badd\b', r'\bthe following\b', r'\btasks\b', r'\btask\b', 
                r'\bto do list\b', r'\btodo list\b', r'\bto my\b', r'\bto the\b', 
                r'\bto list\b', r'\blist\b', r'\bmy\b', r'\bto\b'
            ]
            for f in fillers:
                clean_text = re.sub(f, '', clean_text, flags=re.I)
            
            clean_text = clean_text.replace(":", "").strip()
            new_items = [t.strip() for t in clean_text.split(",") if t.strip()]
            
            if new_items:
                self.state.update_tasks(new_items)
                item_str = ", ".join(new_items)
                self.ui.success(f"Added {len(new_items)} task(s): {item_str}")
                return

        # 3. View Logic (Populates Buffer)
        tasks_list = self.state.task_memory
        if not tasks_list:
            self.ui.say("Your to-do list is empty.")
            self.state.view_buffer = []
        else:
            # Anchor the current view into the state buffer
            self.state.view_buffer = list(tasks_list)
            tasks_str = "\n".join([f"{i+1}. {t['text']}" for i, t in enumerate(tasks_list)])
            self.ui.say(f"To-Do List:\n{tasks_str}")