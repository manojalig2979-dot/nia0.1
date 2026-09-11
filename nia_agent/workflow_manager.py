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

    def create_project_task_workflow(self, task_description: str):
        if not task_description or not task_description.strip():
            raise ValueError("Task description must not be empty.")

        steps = [
            {"step": "inspect_project", "purpose": "Inventory project files and entry points."},
            {"step": "read_project_file", "purpose": "Read the most relevant source files for the task."},
            {"step": "inspect_code_symbols", "purpose": "Understand classes, functions, imports, and line locations."},
            {"step": "preview_multi_file_change", "purpose": "Prepare a combined preview of the intended edits."},
            {"step": "apply_multi_file_change", "purpose": "Apply the approved change only after explicit approval."},
            {"step": "validate_project", "purpose": "Run safe validation checks after the code change."},
            {"step": "review_git_changes", "purpose": "Review the resulting Git state before committing."},
            {"step": "commit_git_changes", "purpose": "Create a commit only after explicit approval."},
        ]

        return {
            "task_description": task_description.strip(),
            "steps": steps,
            "required_approvals": [
                "user_approval_before_apply",
                "user_approval_before_commit",
                "user_approval_before_push",
            ],
        }

    def get_match(self, user_command: str):
        cmd = user_command.lower().strip()
        for trig, data in self.workflows.items():
            if trig in cmd:
                return data
        return None
