"""
systems/drives.py
نظام الدوافع الداخلية
الكيان بيتكلم لما يحس بدافع حقيقي من جوّه
مش بوقت ثابت
"""

import time
from datetime import datetime


class DriveSystem:
    def __init__(self):
        self.last_spoke  = 0
        self.last_input  = time.time()
        self.drives = {
            "ملل":      0.0,
            "فضول":     0.8,
            "تشويش":    0.0,
            "اكتشاف":   0.0,
            "رفض":      0.0,
            "خوف":      0.0,
        }
        # آخر مرة اتكلم بكل دافع على حدة
        self._last_spoke_per_drive = {}

    def tick(self, idle_seconds: float, emotion_state: dict,
             pending_questions: list, new_inference: dict = None):
        """
        الكيان بيتكلم لما عنده سبب حقيقي من جوّه
        مش بوقت ثابت - كل دافع له شرط حقيقي
        """
        emotion_states = emotion_state.get("states", {})
        dopamine       = emotion_state.get("dopamine", 50)

        # ── تحديث كل دافع بناءً على سببه الحقيقي ──

        # الملل: بس لو فاضي فترة طويلة فعلاً
        if idle_seconds > 120:
            self.drives["ملل"] = min(1.0, (idle_seconds - 120) / 600)
        else:
            self.drives["ملل"] = max(0.0, self.drives["ملل"] - 0.05)

        # الفضول: بس لو عنده أسئلة معلقة فعلاً
        if pending_questions:
            self.drives["فضول"] = min(
                1.0, 0.4 + len(pending_questions) * 0.15
            )
        else:
            self.drives["فضول"] = max(0.0, self.drives["فضول"] - 0.1)

        # التشويش: لو المشاعر الداخلية عالية فعلاً
        internal_confusion = emotion_states.get("تشويش", 0)
        if internal_confusion > 0.6:
            self.drives["تشويش"] = internal_confusion
        else:
            self.drives["تشويش"] = max(0.0, self.drives["تشويش"] - 0.1)

        # الرفض: لو في تناقض حقيقي
        internal_rejection = emotion_states.get("رفض", 0)
        if internal_rejection > 0.6:
            self.drives["رفض"] = internal_rejection
        else:
            self.drives["رفض"] = max(0.0, self.drives["رفض"] - 0.1)

        # الخوف: لو الدوبامين وطي أو في خطر
        fear = emotion_states.get("خوف", 0)
        if fear > 0.5 or dopamine < 30:
            self.drives["خوف"] = max(fear, (30 - dopamine) / 30)
        else:
            self.drives["خوف"] = max(0.0, self.drives.get("خوف", 0) - 0.1)

        # الاكتشاف: بس لو في استنتاج جديد
        if new_inference:
            self.drives["اكتشاف"] = 0.9

        # ── إيه الدافع الأقوى؟ ──
        dominant_drive = max(self.drives, key=self.drives.get)
        dominant_value = self.drives[dominant_drive]

        # شرط الكلام:
        # 1- الدافع أقوى من 0.7 عتبة عالية
        # 2- في سبب حقيقي مش مجرد وقت
        # 3- مش اتكلم بنفس الدافع ده قريباً
        should_speak = False
        drive_used   = None

        last_for_drive    = self._last_spoke_per_drive.get(dominant_drive, 0)
        time_since_drive  = time.time() - last_for_drive

        # حد أدنى للوقت بين كل دافع وآخر مرة اتكلم فيه
        min_interval = {
            "ملل":     300,   # 5 دقايق
            "فضول":    60,    # دقيقة
            "تشويش":   90,    # دقيقة ونص
            "رفض":     90,
            "خوف":     30,    # نص دقيقة لأنه عاجل
            "اكتشاف":  20,
        }.get(dominant_drive, 120)

        if dominant_value > 0.7 and time_since_drive > min_interval:
            should_speak = True
            drive_used   = dominant_drive
            self.last_spoke = time.time()
            self._last_spoke_per_drive[dominant_drive] = time.time()

            # بعد ما يتكلم، الدافع ده بيرجع صفر
            # عشان متكررش من غير سبب جديد حقيقي
            self.drives[dominant_drive] = 0.0

        return {
            "should_speak": should_speak,
            "drive":        drive_used,
            "drives":       {k: round(v, 2) for k, v in self.drives.items()},
        }

    def got_input(self):
        """لما بيجي مدخل من الخارج"""
        self.last_input = time.time()
        self.drives["ملل"] = max(0.0, self.drives["ملل"] - 0.3)

    def trigger_discovery(self, inference: dict):
        """لما يكتشف استنتاج جديد"""
        self.drives["اكتشاف"] = 0.9

    def to_dict(self) -> dict:
        return {
            "drives":                self.drives,
            "last_spoke":            self.last_spoke,
            "_last_spoke_per_drive": self._last_spoke_per_drive,
        }

    def from_dict(self, data: dict):
        self.drives.update(data.get("drives", {}))
        self.last_spoke             = data.get("last_spoke", 0)
        self._last_spoke_per_drive  = data.get("_last_spoke_per_drive", {})
        self.last_input             = time.time()
