"""
نظام المفاهيم والفهم
كل مفهوم عنده خصائص بدرجات
الاستنتاج بيحصل من الخصائص المشتركة
"""

import json
from datetime import datetime


class Concept:
    def __init__(self, name: str):
        self.name = name
        self.properties = {}      # خاصية → درجة (0-100)
        self.relations = {}       # مفهوم تاني → نوع العلاقة
        self.confidence = 0.5     # ثقته في فهمه للمفهوم ده
        self.learned_from = []    # من فين اتعلمه
        self.created_at = datetime.now().isoformat()

    def add_property(self, prop: str, degree: float, source: str = "تعليم"):
        """إضافة أو تحديث خاصية"""
        degree = max(0, min(100, degree))
        self.properties[prop] = {
            "degree": degree,
            "source": source,   # تعليم / استنتاج / تصحيح
            "confirmed": source == "تعليم",
        }
        if source not in self.learned_from:
            self.learned_from.append(source)

    def get_property_degree(self, prop: str) -> float:
        if prop in self.properties:
            return self.properties[prop]["degree"]
        return 0.0

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "properties": self.properties,
            "relations": self.relations,
            "confidence": self.confidence,
            "learned_from": self.learned_from,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Concept":
        c = cls(data["name"])
        c.properties = data.get("properties", {})
        c.relations = data.get("relations", {})
        c.confidence = data.get("confidence", 0.5)
        c.learned_from = data.get("learned_from", [])
        c.created_at = data.get("created_at", datetime.now().isoformat())
        return c


class ConceptGraph:
    """
    شبكة المفاهيم
    كل مفهوم node والعلاقات بينهم edges
    الاستنتاج بيمشي على الشبكة دي
    """

    def __init__(self):
        self.concepts = {}          # اسم → Concept
        self.inferences_made = []   # الاستنتاجات اللي عملها
        self.pending_questions = [] # أسئلة محتاج يسألها عشان يتأكد

    def add_concept(self, name: str, properties: dict,
                    source: str = "تعليم") -> Concept:
        """
        إضافة مفهوم جديد
        properties = {"خطر": 90, "حرارة": 85, "ضوء": 60}
        """
        if name not in self.concepts:
            self.concepts[name] = Concept(name)

        concept = self.concepts[name]
        for prop, degree in properties.items():
            concept.add_property(prop, degree, source)

        # لو اتعلم بشكل مباشر، الثقة أعلى
        if source == "تعليم":
            concept.confidence = min(1.0, concept.confidence + 0.2)
        elif source == "استنتاج":
            concept.confidence = min(0.7, concept.confidence + 0.1)

        # بعد إضافة مفهوم جديد، نحاول نستنتج علاقات
        self._infer_relations(name)

        return concept

    def correct_concept(self, name: str, property_name: str,
                        new_degree: float, reason: str = ""):
        """
        تصحيح خاصية في مفهوم
        ده بيحصل لما الكيان يغلط وإنت بتصححله
        """
        if name not in self.concepts:
            return False

        concept = self.concepts[name]
        old_degree = concept.get_property_degree(property_name)
        concept.add_property(property_name, new_degree, "تصحيح")

        # تسجيل التصحيح كتجربة تعلم
        self.inferences_made.append({
            "type": "تصحيح",
            "concept": name,
            "property": property_name,
            "old": old_degree,
            "new": new_degree,
            "reason": reason,
            "time": datetime.now().isoformat(),
        })

        # تحديث الاستنتاجات المرتبطة
        self._update_related_inferences(name, property_name, new_degree)
        return True

    def _infer_relations(self, new_concept_name: str):
        """
        استنتاج علاقات بين المفهوم الجديد والمفاهيم الموجودة
        بيدور على الخصائص المشتركة
        """
        if new_concept_name not in self.concepts:
            return

        new_concept = self.concepts[new_concept_name]
        new_props = new_concept.properties

        for existing_name, existing_concept in self.concepts.items():
            if existing_name == new_concept_name:
                continue

            # دور على خصائص مشتركة
            shared = []
            for prop, val in new_props.items():
                if prop in existing_concept.properties:
                    new_deg = val["degree"]
                    exist_deg = existing_concept.properties[prop]["degree"]
                    # لو الخاصية موجودة بدرجة مقاربة
                    if abs(new_deg - exist_deg) < 40:
                        shared.append({
                            "property": prop,
                            "new_degree": new_deg,
                            "existing_degree": exist_deg,
                        })

            if shared:
                # استنتاج: المفهومين مرتبطين
                self._make_inference(new_concept_name, existing_name, shared)

    def _make_inference(self, concept1: str, concept2: str,
                        shared_props: list):
        """
        عمل استنتاج بناءً على خصائص مشتركة
        """
        # حساب درجة الشبه
        similarity = len(shared_props) / max(
            len(self.concepts[concept1].properties),
            len(self.concepts[concept2].properties),
            1
        )

        if similarity < 0.2:  # لو الشبه ضعيف جداً، متستنتجش
            return

        # الخصائص اللي موجودة في concept2 بس مش في concept1
        missing_props = {}
        c2_props = self.concepts[concept2].properties
        c1_props = self.concepts[concept1].properties

        for prop, val in c2_props.items():
            if prop not in c1_props:
                # استنتاج: concept1 ممكن يكون عنده الخاصية دي
                inferred_degree = val["degree"] * similarity
                missing_props[prop] = inferred_degree

        if missing_props:
            # إضافة الخصائص المستنتجة بثقة أقل
            for prop, degree in missing_props.items():
                self.concepts[concept1].add_property(
                    prop, degree, "استنتاج"
                )

            inference = {
                "type": "استنتاج",
                "from": concept2,
                "to": concept1,
                "shared": [p["property"] for p in shared_props],
                "inferred": missing_props,
                "confidence": round(similarity, 2),
                "time": datetime.now().isoformat(),
                "confirmed": False,
            }
            self.inferences_made.append(inference)

            # لو الاستنتاج مهم، يضيف سؤال للتحقق
            for prop, degree in missing_props.items():
                if degree > 50:  # لو الخاصية المستنتجة عالية
                    self.pending_questions.append({
                        "question": f"{concept1} عنده {prop}؟",
                        "about": concept1,
                        "property": prop,
                        "inferred_degree": degree,
                        "confidence": similarity,
                        "urgency": degree / 100,
                    })

    def _update_related_inferences(self, concept: str,
                                   property_name: str, new_degree: float):
        """
        لما بيتصحح مفهوم، يحدث الاستنتاجات المرتبطة بيه
        """
        for inf in self.inferences_made:
            if (inf.get("from") == concept and
                    property_name in inf.get("inferred", {})):
                # تحديث الاستنتاج
                inf["inferred"][property_name] = new_degree * inf["confidence"]
                inf["confirmed"] = True

    def query(self, text: str) -> dict:
        """
        استعلام: إيه اللي يعرفه عن موضوع معين؟
        """
        result = {
            "direct": [],      # مفاهيم موجودة مباشرة
            "inferred": [],    # مفاهيم استنتجها
            "questions": [],   # أسئلة مرتبطة
        }

        words = text.split()
        for word in words:
            if len(word) < 2:
                continue
            # دور على المفهوم في الشبكة
            if word in self.concepts:
                c = self.concepts[word]
                result["direct"].append({
                    "concept": word,
                    "properties": c.properties,
                    "confidence": c.confidence,
                })

        # دور على استنتاجات مرتبطة
        for inf in self.inferences_made[-10:]:
            for word in words:
                if word in inf.get("to", "") or word in inf.get("from", ""):
                    result["inferred"].append(inf)
                    break

        # أسئلة مرتبطة
        for q in self.pending_questions:
            for word in words:
                if word in q.get("about", ""):
                    result["questions"].append(q)
                    break

        return result

    def get_most_urgent_question(self) -> dict:
        """
        إيه أهم سؤال محتاج يسأله دلوقتي؟
        """
        if not self.pending_questions:
            return {}
        # ترتيب حسب الأهمية
        sorted_q = sorted(
            self.pending_questions,
            key=lambda x: x.get("urgency", 0),
            reverse=True
        )
        return sorted_q[0]

    def remove_question(self, question_text: str):
        """إزالة سؤال بعد ما بيتجاوب"""
        self.pending_questions = [
            q for q in self.pending_questions
            if q.get("question") != question_text
        ]

    def stats(self) -> dict:
        return {
            "concepts": len(self.concepts),
            "inferences": len(self.inferences_made),
            "pending_questions": len(self.pending_questions),
        }

    def to_dict(self) -> dict:
        return {
            "concepts": {k: v.to_dict() for k, v in self.concepts.items()},
            "inferences_made": self.inferences_made[-50:],
            "pending_questions": self.pending_questions,
        }

    def from_dict(self, data: dict):
        for name, cdata in data.get("concepts", {}).items():
            self.concepts[name] = Concept.from_dict(cdata)
        self.inferences_made = data.get("inferences_made", [])
        self.pending_questions = data.get("pending_questions", [])
