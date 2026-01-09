import re

class TaskSkill:
    def __init__(self, state, ui):
        self.state = state
        self.ui = ui

    def match(self, text):
        low = text.lower()
        # Explicit task words
        if any(w in low for w in ["task", "to do", "todo", "list"]): return True
        # Generic numbered commands (e.g., "delete 1", "done 2", "remove 4")
        if re.match(r"^(delete|remove|done|complete|finish)\s+\d+$", low): return True
        # Adding items
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
                self.ui.error(f"Task #{idx+1} not found in your list.")
            return

        # 2. Add Logic
        if "add" in low:
            clean_text = re.sub(r'\b(add|the following|tasks|task|to the list|to do list|to my list)\b', '', text, flags=re.I)
            clean_text = clean_text.replace(":", "").strip()
            new_items = [t.strip() for t in clean_text.split(",") if t.strip()]
            if new_items:
                self.state.update_tasks(new_items)
                self.ui.success(f"Added {len(new_items)} task(s) to your list.")
                return

        # 3. View Logic
        if any(w in low for w in ["task", "to do", "todo", "list"]):
            if not self.state.task_memory:
                self.ui.say("Your to-do list is currently empty.")
            else:
                tasks_str = "\n".join([f"{i+1}. {t['text']}" for i, t in enumerate(self.state.task_memory)])
                self.ui.say(f"To-Do List:\n{tasks_str}")