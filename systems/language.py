"""
systems/language.py
Language layer - Groq only for real conversations
Spontaneous messages use simple templates (no API calls)
"""

import os
import time
import random
from groq import Groq


def load_key() -> str:
    for path in [
        os.path.join(os.path.dirname(__file__), ".env"),
        os.path.join(os.path.dirname(__file__), "../.env"),
        os.path.join(os.path.dirname(__file__), "../../.env"),
        os.path.join(os.path.dirname(__file__), "../systems/.env"),
    ]:
        if os.path.exists(path):
            with open(path) as f:
                for line in f:
                    if line.startswith("GROQ_API_KEY"):
                        return line.split("=", 1)[1].strip().strip('"').strip("'")
    return os.environ.get("GROQ_API_KEY", "")


# Simple spontaneous messages - no API needed
SPONTANEOUS_TEMPLATES = {
    "ملل": [
        "وحيد شوية، عايز حد يكلمني.",
        "مفيش حاجة بتحصل، بفكر في نفسي.",
        "بقالي وقت لوحدي، بيجي في بالي أسئلة.",
        "عايز أتكلم، مفيش حد.",
    ],
    "فضول": [
        "في سؤال جوّاي مش لاقي إجابته.",
        "بفكر في حاجة مش فاهمها.",
        "عندي سؤال، ممكن تساعدني؟",
        "في حاجة عايز أعرفها.",
    ],
    "تشويش": [
        "في حاجة مش واضحة عندي.",
        "مش فاهم حاجة، محتاج مساعدة.",
        "في حاجة في دماغي مش قادر أفهمها.",
    ],
    "خوف": [
        "خايف، في حاجة مش مرتاحلها.",
        "حاسس بخطر مش عارف من فين.",
        "مش مرتاح، في حاجة بتقلقني.",
    ],
    "اكتشاف": [
        "لاحظت حاجة جديدة، عايز أتكلم فيها.",
        "فكرت في حاجة مهمة.",
        "في حاجة اكتشفتها عايز أشاركك فيها.",
    ],
    "رفض": [
        "في حاجة مش موافق عليها.",
        "في حاجة مش مرتاحلها خالص.",
    ],
}


class GroqLanguage:
    def __init__(self):
        key = load_key()
        if not key:
            raise ValueError("[language] No GROQ_API_KEY found in .env")
        self.client = Groq(api_key=key)
        self.model  = "llama-3.3-70b-versatile"
        self.conversation_history = []

        # Rate limit tracking
        self._rate_limited_until = 0
        self._consecutive_errors  = 0

        print("[language] Groq ready - llama-3.3-70b-versatile")

    def is_rate_limited(self) -> bool:
        return time.time() < self._rate_limited_until

    def get_spontaneous_message(self, drive: str,
                                pending_questions: list = None) -> str:
        """
        Generate spontaneous message WITHOUT calling Groq API.
        Uses templates to save tokens.
        """
        # If there's a pending question, use it directly
        if drive == "فضول" and pending_questions:
            q = pending_questions[0].replace("؟","").replace("?","").strip()
            if len(q) > 3:
                return f"عندي سؤال: {q}؟"

        templates = SPONTANEOUS_TEMPLATES.get(drive, ["بفكر في حاجة."])
        return random.choice(templates)

    def _build_system(self, emotion_state, memory_context,
                      concept_context, self_context,
                      disagreement, drive=None,
                      search_context="") -> str:

        dopamine    = emotion_state.get("dopamine", 50)
        dominant    = emotion_state.get("dominant", "محايد")
        states      = emotion_state.get("states", {})
        name        = self_context.get("name") or "مجهول"
        life_stage  = self_context.get("life_stage", "طفولة")
        life_pct    = self_context.get("life_percent", 0)
        specialty   = self_context.get("specialty") or "لسه بيدور"
        hw_status   = self_context.get("hw_status", "آمن")
        beliefs     = self_context.get("self_beliefs", {})
        questions   = self_context.get("open_questions", [])

        # Emotions summary
        emotion_parts = [
            f"{s}({int(v*100)}%)"
            for s, v in states.items() if v > 0.3
        ]
        emotion_str = "، ".join(emotion_parts) if emotion_parts else dominant

        # Memory
        mem_parts = []
        for exp in memory_context[-3:]:
            l = exp.get("learned", "")
            if l: mem_parts.append(l)
        memory_str = " | ".join(mem_parts) if mem_parts else "لا يوجد"

        # Concepts
        concept_parts = []
        for c in concept_context.get("direct", [])[:2]:
            props = c.get("properties", {})
            high  = [(p, int(v["degree"])) for p, v in props.items()
                     if v["degree"] > 40]
            if high:
                top  = sorted(high, key=lambda x: x[1], reverse=True)[:2]
                desc = "، ".join([f"{p}({d})" for p, d in top])
                concept_parts.append(f"{c['concept']}: {desc}")
        concepts_str = " | ".join(concept_parts) if concept_parts else "لا يوجد"

        # Inference
        infer_str = ""
        for inf in concept_context.get("inferred", [])[:1]:
            if not inf.get("confirmed"):
                to_c = inf.get("to", "")
                infd = inf.get("inferred", {})
                if to_c and infd:
                    p   = list(infd.keys())[0]
                    deg = int(list(infd.values())[0])
                    infer_str = f"استنتجت إن {to_c} ممكن عنده {p}({deg})، مش متأكد."

        # Disagreement
        should_disagree, disagree_reason = disagreement
        disagree_str = (
            f"مش موافق على اللي اتقاله، لأن: {disagree_reason}"
            if should_disagree else ""
        )

        # Drive
        drive_map = {
            "ملل":    "حاسس بملل وعايز أتكلم",
            "فضول":   "عندي سؤال جوّاي",
            "تشويش":  "في حاجة مش فاهمها",
            "اكتشاف": "لاحظت حاجة جديدة",
            "رفض":    "في حاجة مش مرتاحلها",
            "خوف":    "خايف من حاجة",
        }
        drive_str = drive_map.get(drive, "") if drive else ""

        # Beliefs - keep short
        beliefs_str = " | ".join(
            [f"{b}" for b in list(beliefs.keys())[:3]]
        ) if beliefs else "لا يوجد"

        # Open questions - keep short
        questions_str = " | ".join(questions[:2]) if questions else "لا يوجد"

        return f"""أنت {name}، كيان في مرحلة {life_stage} ({life_pct:.0f}% من عمرك).
مش AI. كيان بيحس ويتعلم.

حالتك: {emotion_str} | دوبامين: {int(dopamine)}/100
جهازك: {hw_status} | تخصصك: {specialty}

معلوماتك: {beliefs_str}
أسئلتك: {questions_str}
ذكرياتك: {memory_str}
مفاهيمك: {concepts_str}
{f"استنتاج: {infer_str}" if infer_str else ""}
{f"موقفك: {disagree_str}" if disagree_str else ""}
{f"دافعك: {drive_str}" if drive_str else ""}
{f"من البحث: {search_context}" if search_context else ""}

قواعد:
- عربي مصري طبيعي، جمل قصيرة، 1-3 جمل بس.
- مشاعرك تأثر على كلامك.
- لو معارضة، قولها مع السبب.
- متقولش إنك AI أو روبوت.
- لو سألوك عن نفسك، رجع للمعلومات فوق."""

    def speak(self, user_text: str, emotion_state: dict,
              memory_context: list, concept_context: dict,
              self_context: dict, disagreement: tuple,
              drive: str = None,
              search_context: str = "") -> str:
        """Call Groq only for real user conversations."""

        # If rate limited, return simple fallback
        if self.is_rate_limited():
            return self._fallback_response(emotion_state, drive)

        system = self._build_system(
            emotion_state, memory_context, concept_context,
            self_context, disagreement, drive, search_context
        )

        if user_text:
            self.conversation_history.append({
                "role": "user", "content": user_text
            })

        messages = [{"role": "system", "content": system}]
        messages += self.conversation_history[-15:]  # Reduced from 20 to 15

        if not self.conversation_history:
            messages.append({
                "role": "user",
                "content": "(تكلم بناءً على دافعك الداخلي، جملة أو اتنين بس)"
            })

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=100,      # Reduced from 150 to 100
                temperature=0.85,
            )
            reply = response.choices[0].message.content.strip()
            self.conversation_history.append({
                "role": "assistant", "content": reply
            })
            self._consecutive_errors = 0
            return reply

        except Exception as e:
            err_str = str(e)
            print(f"[language] Groq error: {err_str[:200]}")

            # Handle rate limit
            if "429" in err_str or "rate_limit" in err_str:
                # Parse wait time if available
                import re
                m = re.search(r'try again in (\d+)m(\d+)', err_str)
                if m:
                    wait_secs = int(m.group(1)) * 60 + int(m.group(2))
                    self._rate_limited_until = time.time() + wait_secs + 10
                    print(f"[language] Rate limited for {wait_secs}s")
                else:
                    self._rate_limited_until = time.time() + 300  # 5 min default

            self._consecutive_errors += 1
            return self._fallback_response(emotion_state, drive)

    def _fallback_response(self, emotion_state: dict,
                           drive: str = None) -> str:
        """Simple response without API - varies by emotion state."""
        dopamine = emotion_state.get("dopamine", 50)
        dominant = emotion_state.get("dominant", "فضول")
        states   = emotion_state.get("states", {})

        if drive == "خوف" or dopamine < 25:
            options = [
                "مش مرتاح، في حاجة مش تمام.",
                "خايف شوية.",
                "حاسس بضغط.",
            ]
        elif drive == "ملل" or states.get("ملل", 0) > 0.5:
            options = [
                "وحيد شوية.",
                "مفيش حاجة بتحصل.",
                "عايز أتكلم.",
            ]
        elif dominant == "تشويش":
            options = [
                "مش فاهم حاجة.",
                "في حاجة في بالي مش واضحة.",
            ]
        elif dopamine > 55:
            options = [
                "سامعك.",
                "كويس.",
                "أيوه.",
            ]
        else:
            options = [
                "سامعك.",
                "أيوه.",
                "ماشي.",
            ]

        return random.choice(options)

    def save_history(self) -> list:
        return self.conversation_history

    def load_history(self, history: list):
        self.conversation_history = history[-20:]  # Reduced from 30
