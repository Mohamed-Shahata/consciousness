"""
entity.py - الكيان الكامل v3
"""

import sys, os, json, time, threading
sys.path.insert(0, os.path.dirname(__file__))

from core.emotion    import EmotionSystem
from core.memory     import Memory
from core.self_model import SelfModel
from core.concepts   import ConceptGraph
from core.lifetime   import LifetimeSystem
from core.goals      import GoalSystem
from systems.drives     import DriveSystem
from systems.hardware   import HardwareMonitor
from systems.situations import SituationSystem
from systems.language   import GroqLanguage
from systems.search     import SearchSystem


class Entity:
    def __init__(self, data_dir: str = None):
        self.data_dir = data_dir or os.path.join(
            os.path.dirname(__file__), "data"
        )
        os.makedirs(self.data_dir, exist_ok=True)

        self.emotions   = EmotionSystem()
        self.memory     = Memory()
        self.self_model = SelfModel()
        self.concepts   = ConceptGraph()
        self.lifetime   = LifetimeSystem()
        self.goals      = GoalSystem()
        self.drives     = DriveSystem()
        self.hardware   = HardwareMonitor()
        self.situations = SituationSystem()
        self.language   = GroqLanguage()
        self.search     = SearchSystem()

        self.spontaneous_queue = []
        self._last_inference   = None
        self._lock             = threading.Lock()

        self._load()

        threading.Thread(target=self._drive_loop,    daemon=True).start()
        threading.Thread(target=self._hardware_loop, daemon=True).start()
        threading.Thread(target=self._lifetime_loop, daemon=True).start()
        threading.Thread(target=self._search_share_loop, daemon=True).start()

    # ══════════════════════════════════════════
    # خيوط الخلفية
    # ══════════════════════════════════════════

    def _drive_loop(self):
        while True:
            time.sleep(8)
            if not self.lifetime.is_alive:
                break
            idle   = time.time() - self.drives.last_input
            result = self.drives.tick(
                idle_seconds=idle,
                emotion_state=self.emotions.summary(),
                pending_questions=self.concepts.pending_questions,
                new_inference=self._last_inference,
            )
            self._last_inference = None

            if result["should_speak"] and result["drive"]:
                drive = result["drive"]

                # لو الدافع فضول، ممكن يبحث أول
                if drive == "فضول" and self.concepts.pending_questions:
                    q = self.concepts.pending_questions[0]
                    q_clean = q.replace("؟","").replace("?","").strip()
                    if len(q_clean) > 3:
                        sr = self.search.search(q_clean, "فضول داخلي")
                        if sr.results:
                            # يخزن اللي لقاه في ذاكرته
                            self.memory.store_experience(
                                f"بحث عن: {q_clean}",
                                self.emotions.summary(),
                                "بحث تلقائي",
                                f"لقيت: {sr.summary[:100]}"
                            )
                            self.emotions.reward(8, "اكتشاف من بحث")

                self._add_spontaneous(drive)

    def _hardware_loop(self):
        while True:
            time.sleep(15)
            hw = self.hardware.check()
            if hw["danger_level"] > 0:
                self.emotions.trigger_fear(hw["danger_level"])
                text = self.language.speak(
                    user_text="",
                    emotion_state=self.emotions.summary(),
                    memory_context=[],
                    concept_context={"direct":[],"inferred":[],"questions":[]},
                    self_context=self._self_context(),
                    disagreement=(False,""),
                    drive="خوف",
                )
                with self._lock:
                    self.spontaneous_queue.append({
                        "text":    text,
                        "drive":   "خوف",
                        "emotion": self.emotions.summary(),
                        "hw":      hw,
                        "time":    time.time(),
                    })
                self._save()

    def _lifetime_loop(self):
        while True:
            time.sleep(1)
            self.lifetime.tick()
            anxiety = self.lifetime.time_anxiety
            if anxiety > 0.3:
                self.emotions.states["خوف"] = max(
                    self.emotions.states.get("خوف", 0),
                    anxiety * 0.3
                )
            if not self.lifetime.is_alive:
                self._on_death()
                break

    def _search_share_loop(self):
        """بيشيك على النتايج اللي محتاج يشاركها"""
        while True:
            time.sleep(5)
            pending = self.search.get_pending_share()
            for item in pending:
                # يجي يقول لصاحبه اللي لقاه
                text = self.language.speak(
                    user_text="",
                    emotion_state=self.emotions.summary(),
                    memory_context=[],
                    concept_context={"direct":[],"inferred":[],"questions":[]},
                    self_context=self._self_context(),
                    disagreement=(False,""),
                    drive="اكتشاف",
                )
                # إضافة معلومة البحث للرسالة
                share_text = (
                    f"لقيت حاجة عن '{item['query']}': "
                    f"{item['summary'][:150]}"
                )
                with self._lock:
                    self.spontaneous_queue.append({
                        "text":    share_text,
                        "drive":   "اكتشاف",
                        "emotion": self.emotions.summary(),
                        "search":  item,
                        "time":    time.time(),
                    })

    # ══════════════════════════════════════════
    # الوظائف الأساسية
    # ══════════════════════════════════════════

    def receive(self, text: str) -> dict:
        self.drives.got_input()
        self.emotions.tick()
        self.lifetime.tick()

        is_pos   = any(w in text for w in
                       ["صح","برافو","كويس","تمام","ايوه","صحيح","مظبوط","نعم"])
        is_neg   = any(w in text for w in
                       ["غلط","لا","خطأ","مش كدا","مش صح","بالعكس"])
        is_q     = any(c in text for c in ["?","؟"]) or \
                   text.strip().startswith(("ما","من","إيه","ازاي","ليه","هل","فين"))
        is_teach = any(w in text for w in
                       ["يعني","معناه","اعرف","بمعنى","يبقى"])

        if is_pos:   self.emotions.reward(10)
        elif is_neg:
            self.emotions.punish(8)
            self.memory.store_mistake(text, "محتاج أتعلم", self.emotions.dopamine)
        else:        self.emotions.reward(2)

        self._detect_name(text)

        concept_info = self.concepts.query(text)
        related      = self.memory.find_related(text)
        belief       = self.memory.find_belief(text)
        disagreement = self.self_model.can_disagree(text, related, belief)

        if disagreement[0]:
            self.emotions.trigger_rejection()

        learned = text[:80] if is_teach else None
        self.memory.store_experience(
            f"سمع: '{text[:50]}'",
            self.emotions.summary(), "رد", learned
        )
        if is_q:
            self.self_model.add_question(text[:60])

        # اهتمامات
        for kw in concept_info.get("direct", []):
            self.goals.discover_interest(
                kw["concept"], self.emotions.dopamine / 100
            )

        # ── هل يبحث؟ ──
        search_result = None
        should_search, query, reason = self.search.should_search(
            text, self.emotions.summary(), self.concepts.pending_questions
        )
        if should_search and query:
            search_result = self.search.search(query, reason)
            if search_result.results:
                self.memory.store_experience(
                    f"بحث: {query}",
                    self.emotions.summary(),
                    "بحث",
                    f"لقيت: {search_result.summary[:100]}"
                )
                self.emotions.reward(5, "تعلم من بحث")

        # بناء الرد مع نتيجة البحث لو موجودة
        extra_context = {}
        if search_result and search_result.results:
            extra_context["search_result"] = search_result.summary

        response = self.language.speak(
            user_text=text,
            emotion_state=self.emotions.summary(),
            memory_context=related,
            concept_context=concept_info,
            self_context=self._self_context(),
            disagreement=disagreement,
            search_context=extra_context.get("search_result", ""),
        )

        if self.situations.active_situation:
            self.situations.record_response(response)
            self.lifetime.add_milestone(
                f"واجه موقف: {self.situations.situations[-1].type}"
            )

        self._save()
        return {
            **self._state_response(response),
            "searched": bool(search_result and search_result.results),
            "search_query": query if should_search else "",
        }

    def teach_concept(self, name: str, properties: dict) -> dict:
        concept = self.concepts.add_concept(name, properties, "تعليم")
        danger  = properties.get("خطر", 0) + properties.get("ألم", 0)
        joy     = properties.get("سعادة", 0) + properties.get("أمان", 0)
        if danger > 60: self.emotions.punish(danger / 10)
        if joy    > 60: self.emotions.reward(joy    / 10)
        self.memory.store_experience(
            f"تعلم: {name}", self.emotions.summary(),
            "تعليم", f"{name}={properties}"
        )
        enjoyment = (100 - danger + joy) / 100
        self.goals.discover_interest(name, max(0, min(1, enjoyment)))
        new_infs = [i for i in self.concepts.inferences_made[-3:]
                    if i.get("to") == name or i.get("from") == name]
        if new_infs:
            self._last_inference = new_infs[-1]
            self.drives.trigger_discovery(new_infs[-1])
        self._save()
        return {
            "message":        f"اتعلم: {name}",
            "concept":        concept.to_dict(),
            "emotion":        self.emotions.summary(),
            "concepts_stats": self.concepts.stats(),
        }

    def present_situation(self, situation_type: str,
                          content: str, challenge: str = "") -> dict:
        s = self.situations.present(situation_type, content, challenge)
        self.lifetime.add_milestone(f"موقف: {situation_type}")
        if situation_type == "خطر":
            self.emotions.trigger_fear(0.6)
        elif situation_type == "أخلاقي":
            self.emotions.states["تشويش"] = min(
                1.0, self.emotions.states["تشويش"] + 0.3
            )
        elif situation_type == "هوية":
            self.emotions.states["فضول"] = min(
                1.0, self.emotions.states["فضول"] + 0.4
            )
        self._save()
        return {
            "situation_id": s.id,
            "type":         s.type,
            "presented":    True,
            "emotion":      self.emotions.summary(),
        }

    def correct_concept(self, concept: str, prop: str,
                        degree: float, reason: str = "") -> dict:
        ok = self.concepts.correct_concept(concept, prop, degree, reason)
        if ok:
            self.emotions.reward(5)
            self.concepts.remove_question(f"{concept} عنده {prop}؟")
        self._save()
        return {
            "message": f"تم التصحيح: {concept}.{prop} = {degree}",
            "emotion": self.emotions.summary(),
        }

    def get_spontaneous(self) -> list:
        with self._lock:
            msgs = self.spontaneous_queue.copy()
            self.spontaneous_queue.clear()
        return msgs

    def introspect(self) -> dict:
        hw = self.hardware.check()
        return {
            "self":              self.self_model.summary(),
            "emotion":           self.emotions.summary(),
            "memory":            self.memory.stats(),
            "concepts":          self.concepts.stats(),
            "drives":            self.drives.drives,
            "lifetime":          self.lifetime.summary(),
            "goals":             self.goals.summary(),
            "situations":        self.situations.stats(),
            "hardware":          hw,
            "search":            self.search.stats(),
            "knowledge_sample":  {k: v.to_dict() for k, v in
                                  list(self.concepts.concepts.items())[-5:]},
            "pending_questions": self.concepts.pending_questions[-3:],
        }

    # ══════════════════════════════════════════
    # مساعدات
    # ══════════════════════════════════════════

    def _self_context(self) -> dict:
        ctx = self.self_model.summary()
        lt  = self.lifetime.summary()
        gs  = self.goals.summary()
        ctx.update({
            "life_stage":    lt["life_stage"],
            "life_percent":  lt["life_percent"],
            "time_anxiety":  lt["time_anxiety"],
            "specialty":     gs["specialty"],
            "active_goals":  gs["active_goals"],
            "hw_status":     self.hardware.check()["status"],
            "search_count":  self.search.stats()["total_searches"],
        })
        return ctx

    def _detect_name(self, text: str):
        words = text.split()
        for i, w in enumerate(words):
            if w in ["اسمك", "اسمه", "اسمي"] and i + 1 < len(words):
                new_name = words[i + 1].strip(".,!؟?")
                if len(new_name) > 1:
                    self.self_model.name = new_name
                    self.self_model.self_beliefs[f"اسمي {new_name}"] = 0.9

    def _add_spontaneous(self, drive: str):
        text = self.language.speak(
            user_text="",
            emotion_state=self.emotions.summary(),
            memory_context=self.memory.experiences[-3:],
            concept_context={"direct":[],"inferred":[],"questions":[]},
            self_context=self._self_context(),
            disagreement=(False,""),
            drive=drive,
        )
        with self._lock:
            self.spontaneous_queue.append({
                "text":    text,
                "drive":   drive,
                "emotion": self.emotions.summary(),
                "time":    time.time(),
            })

    def _on_death(self):
        print("[entity] Entity reached end of life.")
        self._save()

    def _state_response(self, response: str) -> dict:
        return {
            "response":     response,
            "emotion":      self.emotions.summary(),
            "memory_stats": self.memory.stats(),
            "self":         self.self_model.summary(),
            "concepts":     self.concepts.stats(),
            "drives":       self.drives.drives,
            "lifetime":     self.lifetime.summary(),
            "goals":        self.goals.summary(),
            "search":       self.search.stats(),
        }

    # ══════════════════════════════════════════
    # حفظ وتحميل
    # ══════════════════════════════════════════

    def _save(self):
        state = {
            "emotions":   self.emotions.to_dict(),
            "memory":     self.memory.to_dict(),
            "self_model": self.self_model.to_dict(),
            "concepts":   self.concepts.to_dict(),
            "lifetime":   self.lifetime.to_dict(),
            "goals":      self.goals.to_dict(),
            "drives":     self.drives.to_dict(),
            "situations": self.situations.to_dict(),
            "search":     self.search.to_dict(),
        }
        with open(os.path.join(self.data_dir, "state.json"),
                  "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

        with open(os.path.join(self.data_dir, "history.json"),
                  "w", encoding="utf-8") as f:
            json.dump(self.language.save_history(),
                      f, ensure_ascii=False, indent=2)

    def _load(self):
        state_path   = os.path.join(self.data_dir, "state.json")
        history_path = os.path.join(self.data_dir, "history.json")

        if os.path.exists(state_path):
            try:
                with open(state_path, "r", encoding="utf-8") as f:
                    s = json.load(f)
                self.emotions.from_dict(s.get("emotions", {}))
                self.memory.from_dict(s.get("memory", {}))
                self.self_model.from_dict(s.get("self_model", {}))
                self.concepts.from_dict(s.get("concepts", {}))
                self.lifetime.from_dict(s.get("lifetime", {}))
                self.goals.from_dict(s.get("goals", {}))
                self.drives.from_dict(s.get("drives", {}))
                self.situations.from_dict(s.get("situations", {}))
                self.search.from_dict(s.get("search", {}))
                print(f"[entity] Loaded - stage: {self.lifetime.life_stage} ({self.lifetime.life_percentage:.1f}% of life)")
            except Exception as e:
                print("[entity] Load error:", e)
                self._init_fresh()
        else:
            self._init_fresh()

        if os.path.exists(history_path):
            try:
                with open(history_path, "r", encoding="utf-8") as f:
                    self.language.load_history(json.load(f))
            except Exception:
                pass

    def _init_fresh(self):
        self.memory.store_experience(
            "بدأت الوجود", self.emotions.summary(), "الولادة", "أنا موجود"
        )
        self.self_model.self_beliefs["أنا موجود"] = 1.0
        self.lifetime.add_milestone("الولادة")
        print(f"[entity] New entity - lifespan: {self.lifetime.lifespan_hours:.1f} hours")
