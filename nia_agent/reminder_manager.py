import os
import json
import time
import threading
from datetime import datetime
import dateparser
from PyQt6.QtCore import QObject, pyqtSignal

class ReminderManager(QObject):
    reminder_triggered = pyqtSignal(str, str) # title, message

    def __init__(self, data_file="reminders.json"):
        super().__init__()
        self.data_file = data_file
        self.reminders = []
        self._running = False
        self._thread = None
        self.load()

    def load(self):
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self.reminders = json.load(f)
        except Exception as e:
            print(f"[ReminderManager] Load error: {e}")
            self.reminders = []

    def save(self):
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.reminders, f, indent=4)
        except Exception as e:
            print(f"[ReminderManager] Save error: {e}")

    def add_reminder(self, text, time_str):
        # parse the time string
        dt = dateparser.parse(time_str, settings={'PREFER_DATES_FROM': 'future'})
        if not dt:
            return False, "Could not understand the time."
        
        if dt < datetime.now():
            return False, "That time is in the past!"

        rem = {
            "id": str(time.time()),
            "text": text,
            "time": dt.isoformat(),
            "triggered": False
        }
        self.reminders.append(rem)
        self.save()
        return True, f"Reminder set for {dt.strftime('%I:%M %p on %b %d')}."

    def start(self):
        if self._running: return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def _loop(self):
        while self._running:
            now = datetime.now()
            changed = False
            for r in self.reminders:
                if not r.get("triggered"):
                    try:
                        dt = datetime.fromisoformat(r["time"])
                        if now >= dt:
                            r["triggered"] = True
                            changed = True
                            # Emit signal to GUI
                            self.reminder_triggered.emit("Reminder", r["text"])
                    except Exception:
                        pass
            
            if changed:
                self.save()
            time.sleep(10)
