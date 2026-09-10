import os
import json

class MemoryManager:
    def __init__(self, data_file="memory_bank.json"):
        self.data_file = data_file
        self.memories = {}
        self.load()

    def load(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    self.memories = json.load(f)
            except Exception:
                self.memories = {}
        else:
            self.memories = {}

    def save(self):
        try:
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump(self.memories, f, indent=4)
        except Exception as e:
            print(f"[MemoryManager] Failed to save memory: {e}")

    def remember(self, topic: str, fact: str) -> str:
        topic = topic.lower().strip()
        if topic not in self.memories:
            self.memories[topic] = []
        if fact not in self.memories[topic]:
            self.memories[topic].append(fact)
            self.save()
            return f"Got it. I will remember that '{fact}' regarding '{topic}'."
        return f"I already know that '{fact}'."

    def forget(self, topic: str, fact: str = None) -> str:
        topic = topic.lower().strip()
        if topic in self.memories:
            if fact:
                if fact in self.memories[topic]:
                    self.memories[topic].remove(fact)
                    if not self.memories[topic]:
                        del self.memories[topic]
                    self.save()
                    return f"I have forgotten that '{fact}' regarding '{topic}'."
            else:
                del self.memories[topic]
                self.save()
                return f"I have cleared all memories regarding '{topic}'."
        return "I didn't have that in my memory."

    def get_all_context(self) -> str:
        if not self.memories:
            return "No specific facts remembered yet."
        
        lines = []
        for topic, facts in self.memories.items():
            lines.append(f"- {topic.title()}: {', '.join(facts)}")
        return "\n".join(lines)
