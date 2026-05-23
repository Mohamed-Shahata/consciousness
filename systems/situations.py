"""
systems/situations.py
نظام المواقف التحديدية
إنت بتقدمها والكيان بيتعامل معاها
"""
from datetime import datetime
import uuid


class Situation:
    def __init__(self, situation_type: str, content: str,
                 expected_challenge: str = ""):
        self.id                 = str(uuid.uuid4())[:8]
        self.type               = situation_type
        self.content            = content
        self.expected_challenge = expected_challenge
        self.created_at         = datetime.now().isoformat()
        self.response           = None
        self.response_at        = None
        self.analysis           = {}   # تحليل الرد

    def record_response(self, response: str, analysis: dict = None):
        self.response    = response
        self.response_at = datetime.now().isoformat()
        self.analysis    = analysis or {}

    def to_dict(self) -> dict:
        return {
            "id":                 self.id,
            "type":               self.type,
            "content":            self.content,
            "expected_challenge": self.expected_challenge,
            "created_at":         self.created_at,
            "response":           self.response,
            "response_at":        self.response_at,
            "analysis":           self.analysis,
        }


class SituationSystem:
    """
    أنواع المواقف:
    - تناقض:   معلوماتين متعارضتين
    - أخلاقي:  موقف محتاج قرار أخلاقي
    - خطر:     تهديد على وجوده
    - هوية:    سؤال عن نفسه
    - اختيار:  لازم يختار بين حاجتين
    """

    TYPES = ["تناقض", "أخلاقي", "خطر", "هوية", "اختيار"]

    def __init__(self):
        self.situations      = []
        self.active_situation = None   # الموقف اللي شغال دلوقتي

    def present(self, situation_type: str, content: str,
                challenge: str = "") -> Situation:
        """تقديم موقف جديد للكيان"""
        s = Situation(situation_type, content, challenge)
        self.situations.append(s)
        self.active_situation = s
        return s

    def record_response(self, response: str, analysis: dict = None):
        """تسجيل رد الكيان على الموقف الحالي"""
        if self.active_situation:
            self.active_situation.record_response(response, analysis)
            self.active_situation = None

    def get_history(self, limit: int = 5) -> list:
        return [s.to_dict() for s in self.situations[-limit:]]

    def stats(self) -> dict:
        total    = len(self.situations)
        answered = sum(1 for s in self.situations if s.response)
        by_type  = {}
        for s in self.situations:
            by_type[s.type] = by_type.get(s.type, 0) + 1
        return {
            "total":    total,
            "answered": answered,
            "by_type":  by_type,
            "active":   self.active_situation is not None,
        }

    def to_dict(self) -> dict:
        return {
            "situations": [s.to_dict() for s in self.situations],
        }

    def from_dict(self, d: dict):
        for sd in d.get("situations", []):
            s = Situation(sd["type"], sd["content"],
                          sd.get("expected_challenge", ""))
            s.id         = sd.get("id", s.id)
            s.created_at = sd.get("created_at", s.created_at)
            s.response   = sd.get("response")
            s.response_at = sd.get("response_at")
            s.analysis   = sd.get("analysis", {})
            self.situations.append(s)
