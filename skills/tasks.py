import re

class TaskSkill:
    def __init__(self, state, ui):
        self.state = state
        self.ui = ui

    def match(self, text):
        low = text.lower()
        if any(w in low for w in ["task", "to do", "todo", "list"]): return True
        if re.match(r"^(delete|remove|done|complete|finish)\s+\d+$", low): return True
        if low.startswith("add ") and not any(x in low for x in ["schedule", "calendar", "event"]):
            return True
        return False

    def execute(self, text):
        low = text.lower()
        
        # 1. Numbered Removal Logic
        match = re.match(r"^(delete|remove|done|complete|finish)\s+(\d+)$", low)
        if match:
            idx = int(match.group(2)) - 1
            tasks = self.state.task_memory
            if 0 <= idx < len(tasks):
                removed = tasks[idx]
                self.state.remove_task(removed['text'])
                self.ui.success(f"Task cleared: {removed['text']}")
            else:
                self.ui.error(f"Task #{idx+1} not found.")
            return

        # 2. Add Logic with Cleaner Stripping
        if "add" in low:
            # Aggressively strip filler words
            clean_text = text
            # Remove command words and "to/my" artifacts
            fillers = [
                r'\badd\b', r'\bthe following\b', r'\btasks\b', r'\btask\b', 
                r'\bto do list\b', r'\btodo list\b', r'\bto my\b', r'\bto the\b', 
                r'\bto list\b', r'\blist\b', r'\bmy\b', r'\bto\b'
            ]
            for f in fillers:
                clean_text = re.sub(f, '', clean_text, flags=re.I)
            
            clean_text = clean_text.replace(":", "").strip()
            # Split by commas for multi-adds
            new_items = [t.strip() for t in clean_text.split(",") if t.strip()]
            
            if new_items:
                self.state.update_tasks(new_items)
                item_str = ", ".join(new_items)
                self.ui.success(f"Added {len(new_items)} task(s): {item_str}")
                return

        # 3. View Logic
        tasks_list = self.state.task_memory
        if not tasks_list:
            self.ui.say("Your to-do list is empty.")
        else:
            tasks_str = "\n".join([f"{i+1}. {t['text']}" for i, t in enumerate(tasks_list)])
            self.ui.say(f"To-Do List:\n{tasks_str}")
