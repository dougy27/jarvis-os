import re

class TaskSkill:
    def __init__(self, state, ui):
        self.state = state
        self.ui = ui

    def match(self, text):
        low = text.lower()
        return "task" in low or "to do" in low or "todo" in low or "add" in low

    def execute(self, text):
        low = text.lower()
        
        if low.startswith(("remove task", "delete task")):
            parts = text.split("task", 1)
            if len(parts) > 1 and parts[1].strip().isdigit():
                idx = int(parts[1].strip()) - 1
                tasks = self.state.task_memory
                if 0 <= idx < len(tasks):
                    removed = tasks[idx]
                    self.state.remove_task(removed['text'])
                    self.ui.success(f"Removed task: {removed['text']}")
                else: self.ui.error("Task not found.")
            return

        if "add" in low and ("task" in low or "list" in low or "to do" in low):
            clean_text = re.sub(r'\b(add|the following|tasks|task|to the list|to do list|to my list)\b', '', text, flags=re.I)
            clean_text = clean_text.replace(":", "").strip()
            new_items = [t.strip() for t in clean_text.split(",") if t.strip()]
            if new_items:
                self.state.update_tasks(new_items)
                self.ui.success(f"Added {len(new_items)} task(s): {', '.join(new_items)}")
                return
            else:
                self.ui.error("I couldn't identify the tasks to add.")
                return

        if "task" in low or "to do" in low:
            if not self.state.task_memory:
                self.ui.say("No open tasks.")
            else:
                tasks = "\n".join([f"{i+1}. {t['text']}" for i, t in enumerate(self.state.task_memory)])
                self.ui.say(f"To-Do List:\n{tasks}")