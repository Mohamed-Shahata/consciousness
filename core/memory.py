"""
نظام الذاكرة
كل تجربة بتتخزن مع المشاعر اللي صاحبتها
المعلومة بدون مشاعر = داتا ميتة
"""

import json
from datetime import datetime


class Memory:
    def __init__(self):
        self.experiences = []    # كل اللي حصل مع المشاعر
        self.knowledge = {}      # الكلمات والمفاهيم اللي اتعلمها
        self.mistakes = []       # الأخطاء - أهم مصدر تعلم
        self.beliefs = {}        # قناعاته عن العالم - بتتكون من التجارب

    def store_experience(self, event: str, emotion_snapshot: dict,
                         result: str, learned: str = None):
        """تخزين تجربة مع لقطة المشاعر"""
        exp = {
            "time": datetime.now().isoformat(),
            "event": event,
            "emotion": emotion_snapshot,
            "result": result,
            "learned": learned,
        }
        self.experiences.append(exp)

        # لو اتعلم حاجة، بتتخزن بوزن مرتبط بالدوبامين
        if learned:
            dopamine = emotion_snapshot.get("dopamine", 50)
            weight = dopamine / 100
            if learned not in self.knowledge:
                self.knowledge[learned] = {
                    "confidence": weight,
                    "times_seen": 1,
                    "emotion_tag": emotion_snapshot.get("dominant", "محايد"),
                    "first_seen": datetime.now().isoformat(),
                }
            else:
                # كل ما اتكررت الحاجة، بيزيد وزنها
                self.knowledge[learned]["times_seen"] += 1
                self.knowledge[learned]["confidence"] = min(
                    1.0,
                    self.knowledge[learned]["confidence"] + 0.05
                )

    def store_mistake(self, mistake: str, correction: str, dopamine: float):
        """الأخطاء بتتخزن بشكل خاص"""
        self.mistakes.append({
            "time": datetime.now().isoformat(),
            "mistake": mistake,
            "correction": correction,
            "pain": round(100 - dopamine, 1),
        })

    def update_belief(self, topic: str, belief: str, confidence: float):
        """تحديث قناعة عن موضوع معين"""
        self.beliefs[topic] = {
            "belief": belief,
            "confidence": round(confidence, 2),
            "updated": datetime.now().isoformat(),
        }

    def find_related(self, text: str, limit: int = 3) -> list:
        """إيجاد تجارب سابقة مرتبطة بالكلام الحالي"""
        related = []
        words = text.split()
        for exp in self.experiences:
            for word in words:
                if (len(word) > 2 and
                        (word in exp.get("event", "") or
                         word in (exp.get("learned") or ""))):
                    related.append(exp)
                    break
        return related[-limit:]  # آخر تجارب مرتبطة

    def find_belief(self, topic: str) -> dict:
        """البحث عن قناعة مرتبطة بموضوع"""
        for key, val in self.beliefs.items():
            if key in topic or topic in key:
                return val
        return {}

    def stats(self) -> dict:
        return {
            "experiences": len(self.experiences),
            "knowledge_items": len(self.knowledge),
            "mistakes": len(self.mistakes),
            "beliefs": len(self.beliefs),
        }

    def to_dict(self) -> dict:
        return {
            "experiences": self.experiences[-100:],
            "knowledge": self.knowledge,
            "mistakes": self.mistakes,
            "beliefs": self.beliefs,
        }

    def from_dict(self, data: dict):
        self.experiences = data.get("experiences", [])
        self.knowledge = data.get("knowledge", {})
        self.mistakes = data.get("mistakes", [])
        self.beliefs = data.get("beliefs", {})
