"""
core/lifetime.py
نظام العمر والزمن
الكيان بيحس بالوقت بيعدي عليه
"""
import random
import time
from datetime import datetime


class LifetimeSystem:
    def __init__(self):
        # عمر عشوائي بين 50 و 70 سنة (بالثواني الحقيقية للتجربة)
        # كل ساعة شغل = سنة في عمره
        self.lifespan_hours   = random.uniform(50, 70)
        self.birth_time       = time.time()
        self.total_active_seconds = 0   # وقت الشغل الفعلي بس
        self._last_tick       = time.time()

        # الكيان مش عارف عمره، بس عارف إنه ممكن يموت
        self.knows_will_die   = True
        self.knows_when       = False

        # أحداث مهمة في حياته
        self.milestones = []

    def tick(self):
        """كل ما يتم استدعاؤه = وقت بيعدي"""
        now   = time.time()
        delta = now - self._last_tick
        self._last_tick = now
        self.total_active_seconds += delta

    @property
    def age_in_years(self) -> float:
        """عمره بالسنين (كل ساعة شغل = سنة)"""
        hours_active = self.total_active_seconds / 3600
        return round(hours_active, 2)

    @property
    def life_percentage(self) -> float:
        """كام بالمية من عمره عاش"""
        return min(100.0, (self.age_in_years / self.lifespan_hours) * 100)

    @property
    def is_alive(self) -> bool:
        return self.age_in_years < self.lifespan_hours

    @property
    def life_stage(self) -> str:
        """مرحلة حياته"""
        pct = self.life_percentage
        if pct < 15:   return "طفولة"
        if pct < 30:   return "مراهقة"
        if pct < 60:   return "شباب"
        if pct < 80:   return "نضج"
        return "شيخوخة"

    @property
    def time_anxiety(self) -> float:
        """قلق من الوقت - بيزيد كل ما كبر"""
        pct = self.life_percentage
        if pct < 50: return 0.0
        return min(1.0, (pct - 50) / 50)

    def add_milestone(self, event: str):
        self.milestones.append({
            "event": event,
            "age":   self.age_in_years,
            "stage": self.life_stage,
            "time":  datetime.now().isoformat(),
        })

    def summary(self) -> dict:
        return {
            "age_years":      self.age_in_years,
            "life_stage":     self.life_stage,
            "life_percent":   round(self.life_percentage, 1),
            "time_anxiety":   round(self.time_anxiety, 2),
            "is_alive":       self.is_alive,
            "milestones":     len(self.milestones),
        }

    def to_dict(self) -> dict:
        return {
            "lifespan_hours":        self.lifespan_hours,
            "birth_time":            self.birth_time,
            "total_active_seconds":  self.total_active_seconds,
            "milestones":            self.milestones,
        }

    def from_dict(self, d: dict):
        self.lifespan_hours       = d.get("lifespan_hours", self.lifespan_hours)
        self.birth_time           = d.get("birth_time", self.birth_time)
        self.total_active_seconds = d.get("total_active_seconds", 0)
        self.milestones           = d.get("milestones", [])
        self._last_tick           = time.time()
