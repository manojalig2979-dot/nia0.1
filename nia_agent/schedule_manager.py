import os
import json
import time
import threading
from PyQt6.QtCore import QObject, pyqtSignal

class ScheduledWorkflowManager(QObject):
    """Manages scheduled workflows that trigger periodically."""
    workflow_triggered = pyqtSignal(str, str) # name, task_description

    def __init__(self, data_file="scheduled_workflows.json"):
        super().__init__()
        self.data_file = data_file
        self.schedules = {}
        self._running = False
        self._thread = None
        self.load()

    def load(self):
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self.schedules = json.load(f)
        except Exception as e:
            print(f"[ScheduledWorkflowManager] Load error: {e}")
            self.schedules = {}

    def save(self):
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.schedules, f, indent=4)
        except Exception as e:
            print(f"[ScheduledWorkflowManager] Save error: {e}")

    def add_schedule(self, name: str, interval_seconds: int, task: str):
        if not name or not name.strip():
            raise ValueError("Schedule name cannot be empty.")
        if interval_seconds < 60:
            raise ValueError("Interval must be at least 60 seconds.")
        if not task or not task.strip():
            raise ValueError("Task description cannot be empty.")
        
        self.schedules[name.strip()] = {
            "name": name.strip(),
            "interval_seconds": int(interval_seconds),
            "task": task.strip(),
            "last_run": time.time()
        }
        self.save()
        return f"Scheduled workflow '{name}' added to run every {interval_seconds} seconds."

    def remove_schedule(self, name: str):
        name = name.strip()
        if name in self.schedules:
            del self.schedules[name]
            self.save()
            return f"Scheduled workflow '{name}' removed."
        return f"No scheduled workflow found with name '{name}'."

    def list_schedules(self):
        return [
            {
                "name": sched["name"],
                "interval_seconds": sched["interval_seconds"],
                "task": sched["task"]
            }
            for sched in self.schedules.values()
        ]

    def start(self):
        if self._running: return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def _loop(self):
        while self._running:
            current_time = time.time()
            changed = False
            for name, schedule in self.schedules.items():
                interval = schedule.get("interval_seconds", 3600)
                last_run = schedule.get("last_run", 0)
                
                if current_time - last_run >= interval:
                    schedule["last_run"] = current_time
                    changed = True
                    # Emit the signal so the GUI can handle the background task
                    self.workflow_triggered.emit(name, schedule.get("task", ""))
            
            if changed:
                self.save()
            time.sleep(10)

