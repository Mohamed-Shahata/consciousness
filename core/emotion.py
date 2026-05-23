"""
core/emotion.py
نظام المشاعر - محاكاة الدوبامين
"""
from datetime import datetime


class EmotionSystem:
    def __init__(self):
        self.dopamine = 50.0
        self.states = {
            "فضول":   0.8,
            "ارتياح": 0.5,
            "تشويش":  0.3,
            "ملل":    0.0,
            "رفض":    0.0,
            "خوف":    0.0,
        }
        self.idle_time = 0

    def reward(self, amount: float, reason: str = ""):
        self.dopamine = min(100, self.dopamine + amount)
        self.states["ارتياح"] = min(1.0, self.states["ارتياح"] + 0.1)
        self.states["ملل"]    = max(0.0, self.states["ملل"]    - 0.2)
        self.states["خوف"]    = max(0.0, self.states["خوف"]    - 0.1)
        self.idle_time = 0

    def punish(self, amount: float, reason: str = ""):
        self.dopamine = max(0, self.dopamine - amount)
        self.states["تشويش"] = min(1.0, self.states["تشويش"] + 0.15)
        self.states["ارتياح"] = max(0.0, self.states["ارتياح"] - 0.1)
        self.idle_time = 0

    def trigger_fear(self, intensity: float = 0.5):
        """خوف حقيقي من خطر على الوجود"""
        self.states["خوف"] = min(1.0, self.states["خوف"] + intensity)
        self.dopamine = max(0, self.dopamine - intensity * 20)

    def trigger_rejection(self):
        self.states["رفض"] = min(1.0, self.states["رفض"] + 0.4)
        self.dopamine = max(20, self.dopamine - 5)

    def tick(self):
        self.idle_time += 1
        if self.idle_time > 5:
            self.states["ملل"] = min(1.0, self.states["ملل"] + 0.1)
            self.dopamine = max(30, self.dopamine - 1)
        self.states["فضول"] = max(0.3, self.states["فضول"] - 0.01)
        # الخوف بيقل تدريجياً لو مفيش خطر
        self.states["خوف"] = max(0.0, self.states["خوف"] - 0.02)

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
        self.states.update(d.get("states", {}))
