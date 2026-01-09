class NotificationSkill:
    def __init__(self, state, ui):
        self.state = state
        self.ui = ui

    def match(self, text):
        return text.lower().startswith("ping me")

    def execute(self, text):
        from jarvis_core import NotificationService
        NotificationService.send("Connectivity Verified")
        self.ui.success("Ping sent.")