class SystemSkill:
    def __init__(self, state, ui):
        self.state = state
        self.ui = ui

    def match(self, text):
        low = text.lower().strip()
        return low in ["status", "quit", "exit", "debug state", "undo", "reset", "clear chat"]

    def execute(self, text):
        low = text.lower().strip()
        if low in ["quit", "exit"]:
            raise KeyboardInterrupt
        
        if low == "undo":
            if self.state.restore_snapshot():
                self.ui.success("Last action undone. State restored.")
            else:
                self.ui.error("Nothing to undo.")
            return
            
        if low in ["reset", "clear chat"]:
            self.state.chat_history = []
            self.state.save()
            self.ui.success("Conversation history wiped. I am ready for new instructions.")
            return
        
        if low == "status":
            self.ui.system(
                f"Persona: {self.state.settings.get('mood', 'Formal')}\n"
                f"Memory: {len(self.state.appointments)} events, {len(self.state.task_memory)} tasks"
            )
            
        if low == "debug state":
            self.ui.system(f"Appointments: {self.state.appointments}\nTasks: {self.state.task_memory}")