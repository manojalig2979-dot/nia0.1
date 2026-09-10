import os
import json

class WorkflowManager:
    def __init__(self, data_file="workflows.json"):
        self.data_file = data_file
        self.workflows = {}
        self.load()

    def load(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    self.workflows = json.load(f)
            except Exception:
                self.workflows = {}
        else:
            self.workflows = {}

    def save(self):
        try:
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump(self.workflows, f, indent=4)
        except Exception as e:
            print(f"[WorkflowManager] Failed to save workflows: {e}")

    def add_workflow(self, name: str, trigger: str, actions: list):
        trigger = trigger.lower().strip()
        self.workflows[trigger] = {
            "name": name,
            "actions": actions
        }
        self.save()

    def remove_workflow(self, trigger: str):
        trigger = trigger.lower().strip()
        if trigger in self.workflows:
            del self.workflows[trigger]
            self.save()

    def get_match(self, user_command: str):
        cmd = user_command.lower().strip()
        for trig, data in self.workflows.items():
            if trig in cmd:
                return data
        return None
