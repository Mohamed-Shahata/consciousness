"""
core/emotion.py
Emotion system - dopamine simulation
"""
from datetime import datetime


class EmotionSystem:
    def __init__(self):
        self.dopamine = 50.0
        self.states = {
            "فضول":   0.7,
            "ارتياح": 0.5,
            "تشويش":  0.2,
            "ملل":    0.0,
            "رفض":    0.0,
            "خوف":    0.0,
        }
        self.idle_time = 0

    def reward(self, amount: float, reason: str = ""):
        self.dopamine = min(100, self.dopamine + amount)
        self.states["ارتياح"] = min(1.0, self.states["ارتياح"] + 0.08)
        self.states["ملل"]    = max(0.0, self.states["ملل"]    - 0.15)
        self.states["خوف"]    = max(0.0, self.states["خوف"]    - 0.05)
        # Negative emotions decay on reward
        self.states["تشويش"] = max(0.0, self.states["تشويش"] - 0.05)
        self.states["رفض"]   = max(0.0, self.states["رفض"]   - 0.08)
        self.idle_time = 0

    def punish(self, amount: float, reason: str = ""):
        self.dopamine = max(0, self.dopamine - amount)
        self.states["تشويش"] = min(0.8, self.states["تشويش"] + 0.1)
        self.states["ارتياح"] = max(0.0, self.states["ارتياح"] - 0.05)
        self.idle_time = 0

    def trigger_fear(self, intensity: float = 0.5):
        self.states["خوف"] = min(0.9, self.states["خوف"] + intensity * 0.6)
        self.dopamine = max(0, self.dopamine - intensity * 15)

    def trigger_rejection(self):
        self.states["رفض"] = min(0.8, self.states["رفض"] + 0.3)
        self.dopamine = max(20, self.dopamine - 4)

    def tick(self):
        """Natural decay every tick - emotions return to baseline over time"""
        self.idle_time += 1

        # Boredom increases with inactivity
        if self.idle_time > 5:
            self.states["ملل"] = min(0.8, self.states["ملل"] + 0.05)
            self.dopamine = max(30, self.dopamine - 0.5)

        # Natural decay of negative emotions
        self.states["تشويش"] = max(0.1, self.states["تشويش"] * 0.97)
        self.states["رفض"]   = max(0.0, self.states["رفض"]   * 0.95)
        self.states["خوف"]   = max(0.0, self.states["خوف"]   * 0.96)

        # Curiosity stays naturally high
        self.states["فضول"] = max(0.3, self.states["فضول"] - 0.005)

    def dominant(self) -> str:
        return max(self.states, key=self.states.get)

    def summary(self) -> dict:
        return {
            "dopamine": round(self.dopamine, 1),
            "dominant": self.dominant(),
            "states":   {k: round(v, 2) for k, v in self.states.items()},
        }

    def to_dict(self) -> dict:
        return {"dopamine": self.dopamine, "states": self.states}

    def from_dict(self, d: dict):
        self.dopamine = d.get("dopamine", 50.0)
        saved_states = d.get("states", {})
        # Apply saved states but cap negative emotions at 0.8
        for k, v in saved_states.items():
            if k in self.states:
                if k in ("تشويش", "رفض", "خوف"):
                    self.states[k] = min(0.8, v)
                else:
                    self.states[k] = v
