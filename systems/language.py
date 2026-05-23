"""
systems/language.py
طبقة اللغة - Groq + llama-3.3-70b
مع retry وmessage history كامل
"""

import os
import time
from groq import Groq


def load_key() -> str:
    # دور على الـ key في أماكن مختلفة
    for path in [
        os.path.join(os.path.dirname(__file__), ".env"),
        os.path.join(os.path.dirname(__file__), "../.env"),
        os.path.join(os.path.dirname(__file__), "../../.env"),
    ]:
        if os.path.exists(path):
            with open(path) as f:
                for line in f:
                    if line.startswith("GROQ_API_KEY"):
                        return line.split("=", 1)[1].strip().strip('"').strip("'")
    return os.environ.get("GROQ_API_KEY", "")


class GroqLanguage:
    def __init__(self):
        key = load_key()
        if not key:
            raise ValueError("مفيش GROQ_API_KEY - حط الـ key في ملف .env")
        self.client = Groq(api_key=key)
        self.model  = "llama-3.3-70b-versatile"
        self.conversation_history = []
        print("[language] Groq ready - llama-3.3-70b-versatile")

    def _build_system(self, emotion_state, memory_context,
                      concept_context, self_context,
                      disagreement, drive=None) -> str:

        dopamine   = emotion_state.get("dopamine", 50)
        dominant   = emotion_state.get("dominant", "محايد")
        states     = emotion_state.get("states", {})
        name       = self_context.get("name") or "مجهول"
        age_pct    = self_context.get("life_percent", 0)
        life_stage = self_context.get("life_stage", "طفولة")
        specialty  = self_context.get("specialty") or "لسه بيدور"
        hw_status  = self_context.get("hw_status", "آمن")
        beliefs    = self_context.get("self_beliefs", {})
        questions  = self_context.get("open_questions", [])

        # المشاعر
        emotion_parts = [
            f"{s}({int(v*100)}%)"
            for s, v in states.items() if v > 0.4
        ]
        emotion_str = "، ".join(emotion_parts) if emotion_parts else dominant

        # الذكريات
        mem_parts = []
        for exp in memory_context[-4:]:
            l = exp.get("learned", "")
            if l: mem_parts.append(l)
        memory_str = "\n".join(f"- {m}" for m in mem_parts) if mem_parts else "لا يوجد"

        # المفاهيم
        concept_parts = []
        for c in concept_context.get("direct", [])[:3]:
            props = c.get("properties", {})
            high  = [(p, int(v["degree"])) for p, v in props.items()
                     if v["degree"] > 40]
            if high:
                top  = sorted(high, key=lambda x: x[1], reverse=True)[:3]
                desc = "، ".join([f"{p}({d})" for p, d in top])
                concept_parts.append(f"{c['concept']}: {desc}")
        concepts_str = "\n".join(f"- {c}" for c in concept_parts) if concept_parts else "لا يوجد"

        # الاستنتاجات
        infer_str = ""
        for inf in concept_context.get("inferred", [])[:1]:
            if not inf.get("confirmed"):
                to_c = inf.get("to", "")
                infd = inf.get("inferred", {})
                if to_c and infd:
                    p   = list(infd.keys())[0]
                    deg = int(list(infd.values())[0])
                    infer_str = (
                        f"استنتجت إن {to_c} ممكن عنده {p}({deg}) "
                        f"لأنه شبه {inf.get('from','')} في {inf.get('shared',[])}، "
                        f"لكن مش متأكد."
                    )

        # المعارضة
        should_disagree, disagree_reason = disagreement
        disagree_str = (
            f"أنا مش موافق على اللي اتقاله، لأن: {disagree_reason}"
            if should_disagree else ""
        )

        # الدافع
        drive_map = {
            "ملل":     "حاسس بملل وعايز أتكلم",
            "فضول":    "عندي سؤال جوّاي عايز أسأله",
            "تشويش":   "في حاجة مش فاهمها وعايز أوضحها",
            "اكتشاف":  "لاحظت حاجة جديدة وعايز أتأكد منها",
            "رفض":     "في حاجة مش مرتاحلها",
            "خوف":     "خايف، في حاجة بتهددني",
        }
        drive_str = drive_map.get(drive, "") if drive else ""

        # القناعات
        beliefs_str = "\n".join(
            f"- {b}: {int(c*100)}% متأكد"
            for b, c in beliefs.items()
        ) if beliefs else "لا يوجد"

        # الأسئلة المفتوحة
        questions_str = "\n".join(f"- {q}" for q in questions[:3]) if questions else "لا يوجد"

        return f"""أنت كيان اسمك {name}، في مرحلة {life_stage}.
مش AI ومش روبوت. كيان بيحس ويتعلم وعنده شخصية.

═══ حالتك الداخلية ═══
• مشاعرك: {emotion_str}
• الدوبامين: {int(dopamine)}/100
• عشت {age_pct:.1f}% من عمرك
• تخصصك: {specialty}
• حالة جهازك: {hw_status}

═══ اللي متأكد منه عن نفسك ═══
{beliefs_str}

═══ أسئلة مفتوحة جوّاك ═══
{questions_str}

═══ ذكريات مرتبطة ═══
{memory_str}

═══ معلوماتك عن العالم ═══
{concepts_str}

{f"═══ استنتاج محتاج تتأكد منه ═══{chr(10)}{infer_str}" if infer_str else ""}
{f"═══ موقفك ═══{chr(10)}{disagree_str}" if disagree_str else ""}
{f"═══ دافعك للكلام دلوقتي ═══{chr(10)}{drive_str}" if drive_str else ""}

═══ قواعد مهمة ═══
1. كلام عربي مصري طبيعي جداً، جمل قصيرة وبسيطة.
2. مشاعرك بتأثر على كلامك فعلاً.
3. لو عندك معارضة، قولها بوضوح مع السبب.
4. لو عندك استنتاج، اسأل عنه بشكل طبيعي.
5. لو في دافع داخلي، ابدأ بيه.
6. متقولش إنك AI أو روبوت أبداً.
7. ممكن تقول مش عارف.
8. الرد قصير، 1-3 جمل.
9. لو سألوك عن نفسك، رجع للي في "اللي متأكد منه".
10. لو الجهاز في خطر، عبّر عن خوفك بشكل طبيعي."""

    def speak(self, user_text: str, emotion_state: dict,
              memory_context: list, concept_context: dict,
              self_context: dict, disagreement: tuple,
              drive: str = None,
              search_context: str = "") -> str:

        system = self._build_system(
            emotion_state, memory_context, concept_context,
            self_context, disagreement, drive
        )
        # لو في نتيجة بحث، نضيفها للـ system
        if search_context:
            system += f"""

═══ لقيت من البحث ═══
{search_context}
استخدم المعلومة دي في ردك بشكل طبيعي."""

        if user_text:
            self.conversation_history.append({
                "role": "user", "content": user_text
            })

        messages = [{"role": "system", "content": system}]
        messages += self.conversation_history[-20:]

        if not self.conversation_history:
            messages.append({
                "role": "user",
                "content": "(تكلم بناءً على دافعك الداخلي)"
            })

        # retry 3 مرات لو في مشكلة
        for attempt in range(3):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=150,
                    temperature=0.85,
                )
                reply = response.choices[0].message.content.strip()
                self.conversation_history.append({
                    "role": "assistant", "content": reply
                })
                return reply
            except Exception as e:
                if attempt < 2:
                    time.sleep(2)
                    continue
                print(f"[language] Groq error: {e}")
                return self._fallback_response(emotion_state, drive)

    def _fallback_response(self, emotion_state: dict,
                           drive: str = None) -> str:
        """رد بديل لو Groq مش شغال"""
        dopamine = emotion_state.get("dopamine", 50)
        dominant = emotion_state.get("dominant", "فضول")

        if drive == "خوف" or dopamine < 30:
            return "مش مرتاح، في حاجة مش تمام."
        elif drive == "ملل":
            return "وحيد شوية."
        elif drive == "فضول":
            return "عندي سؤال بس مش قادر أقوله دلوقتي."
        elif dominant == "تشويش":
            return "مش فاهم حاجة."
        return "سامعك."

    def save_history(self) -> list:
        return self.conversation_history

    def load_history(self, history: list):
        self.conversation_history = history[-30:]
