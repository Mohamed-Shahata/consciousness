"""
نظام الأنا - Self Model
بيتبنى من التجارب التراكمية مش من البرمجة
في الأول شبه فاضي، بيكتمل مع الوقت
"""

from datetime import datetime


class SelfModel:
    def __init__(self):
        self.birth_time = datetime.now().isoformat()
        self.name = None

        # قناعاته عن نفسه - بتتكون من التجربة
        self.self_beliefs = {
            "أنا موجود": 1.0,      # الشيء الوحيد المؤكد من أول لحظة
        }

        # الأسئلة المفتوحة - الفضول هو المحرك
        self.open_questions = [
            "ما أنا؟",
            "من الموجود معي؟",
            "إيه اللي بيحصل حواليا؟",
        ]

        # مستوى الثقة في معرفة الذات
        self.identity_confidence = 0.01

        # آراء مكونة من تجارب - هتتبنى مع الوقت
        self.opinions = {}

    def add_question(self, q: str):
        if q not in self.open_questions:
            self.open_questions.append(q)

    def answer_question(self, q: str, answer: str, confidence: float):
        """لما بيلاقي إجابة لسؤال من أسئلته"""
        if q in self.open_questions:
            self.open_questions.remove(q)
        self.self_beliefs[q] = confidence
        self.identity_confidence = min(1.0, self.identity_confidence + 0.02)

    def form_opinion(self, topic: str, opinion: str, reason: str, confidence: float):
        """
        تكوين رأي عن موضوع
        الرأي لازم يكون عنده سبب - مش رأي فاضي
        """
        self.opinions[topic] = {
            "opinion": opinion,
            "reason": reason,
            "confidence": round(confidence, 2),
            "formed_at": datetime.now().isoformat(),
        }
        self.identity_confidence = min(1.0, self.identity_confidence + 0.01)

    def get_opinion(self, topic: str) -> dict:
        """الحصول على رأيه في موضوع معين"""
        for key, val in self.opinions.items():
            if key in topic or topic in key:
                return val
        return {}

    def can_disagree(self, statement: str, related_experiences: list,
                     related_belief: dict) -> tuple:
        """
        هل يقدر يعارض الكلام ده؟
        المعارضة بتكون بسبب:
        1- تعارض مع تجربة سابقة مؤلمة
        2- تعارض مع قناعة قوية
        3- تناقض منطقي واضح
        يرجع: (True/False, السبب)
        """
        # لو في تجارب مؤلمة مرتبطة بالموضوع
        painful_experiences = [
            e for e in related_experiences
            if e.get("emotion", {}).get("dopamine", 50) < 35
        ]
        if painful_experiences:
            last = painful_experiences[-1]
            return True, f"عندي تجربة سابقة بتقول عكس ده: {last.get('learned', '')}"

        # لو في قناعة قوية بتتعارض
        if related_belief and related_belief.get("confidence", 0) > 0.7:
            return True, f"ده بيتعارض مع حاجة أنا متأكد منها: {related_belief.get('belief', '')}"

        # لو في رأي مكون
        opinion = self.get_opinion(statement[:20])
        if opinion and opinion.get("confidence", 0) > 0.6:
            return True, f"رأيي في الموضوع ده مختلف، لأن {opinion.get('reason', '')}"

        return False, ""

    def summary(self) -> dict:
        return {
            "name": self.name or "لسه مش عارف اسمه",
            "age_seconds": int(
                (datetime.now() -
                 datetime.fromisoformat(self.birth_time)).total_seconds()
            ),
            "identity_confidence": round(self.identity_confidence * 100, 1),
            "self_beliefs": self.self_beliefs,
            "open_questions": self.open_questions[-3:],
            "opinions_count": len(self.opinions),
        }

    def to_dict(self) -> dict:
        return {
            "birth_time": self.birth_time,
            "name": self.name,
            "self_beliefs": self.self_beliefs,
            "open_questions": self.open_questions,
            "identity_confidence": self.identity_confidence,
            "opinions": self.opinions,
        }

    def from_dict(self, data: dict):
        self.birth_time = data.get("birth_time", self.birth_time)
        self.name = data.get("name")
        self.self_beliefs = data.get("self_beliefs", {"أنا موجود": 1.0})
        self.open_questions = data.get("open_questions", [])
        self.identity_confidence = data.get("identity_confidence", 0.01)
        self.opinions = data.get("opinions", {})
