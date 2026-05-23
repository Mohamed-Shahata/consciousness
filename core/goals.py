"""
core/goals.py
نظام الأهداف والتاسكات
الكيان بيختار أهدافه بناءً على اللي بيحبه
"""
from datetime import datetime
import uuid


class Task:
    def __init__(self, title: str, description: str, priority: int = 5):
        self.id          = str(uuid.uuid4())[:8]
        self.title       = title
        self.description = description
        self.priority    = priority   # 1-10
        self.done        = False
        self.created_at  = datetime.now().isoformat()
        self.done_at     = None
        self.reflection  = ""         # تأمله بعد ما يخلص

    def complete(self, reflection: str = ""):
        self.done       = True
        self.done_at    = datetime.now().isoformat()
        self.reflection = reflection

    def to_dict(self) -> dict:
        return {
            "id":          self.id,
            "title":       self.title,
            "description": self.description,
            "priority":    self.priority,
            "done":        self.done,
            "created_at":  self.created_at,
            "done_at":     self.done_at,
            "reflection":  self.reflection,
        }


class Goal:
    def __init__(self, title: str, why: str, passion_level: float = 0.5):
        self.id            = str(uuid.uuid4())[:8]
        self.title         = title
        self.why           = why           # ليه هو اختار الهدف ده
        self.passion_level = passion_level  # 0-1 مستوى شغفه بيه
        self.tasks         = []
        self.created_at    = datetime.now().isoformat()
        self.status        = "نشط"         # نشط / مكتمل / متروك

    def add_task(self, title: str, description: str, priority: int = 5) -> Task:
        task = Task(title, description, priority)
        self.tasks.append(task)
        return task

    @property
    def progress(self) -> float:
        if not self.tasks: return 0.0
        done = sum(1 for t in self.tasks if t.done)
        return done / len(self.tasks)

    @property
    def is_complete(self) -> bool:
        return self.tasks and all(t.done for t in self.tasks)

    def to_dict(self) -> dict:
        return {
            "id":            self.id,
            "title":         self.title,
            "why":           self.why,
            "passion_level": self.passion_level,
            "tasks":         [t.to_dict() for t in self.tasks],
            "progress":      round(self.progress, 2),
            "status":        self.status,
            "created_at":    self.created_at,
        }


class GoalSystem:
    def __init__(self):
        self.goals       = []
        self.interests   = {}    # موضوع → مستوى اهتمام (0-1)
        self.specialty   = None  # تخصصه اللي اختاره

    def discover_interest(self, topic: str, enjoyment: float):
        """لما يتعلم حاجة ويحس إنه بيستمتع بيها"""
        if topic not in self.interests:
            self.interests[topic] = enjoyment
        else:
            # متوسط متحرك
            self.interests[topic] = (self.interests[topic] + enjoyment) / 2

        # لو في موضوع وصل لمستوى عالي، ممكن يبقى تخصصه
        if self.interests[topic] > 0.75 and not self.specialty:
            self.specialty = topic

    def create_goal(self, title: str, why: str,
                    passion_level: float = 0.5) -> Goal:
        goal = Goal(title, why, passion_level)
        self.goals.append(goal)
        return goal

    def get_active_goals(self) -> list:
        return [g for g in self.goals if g.status == "نشط"]

    def get_next_task(self):
        """إيه التاسك الأهم دلوقتي؟"""
        for goal in sorted(self.get_active_goals(),
                           key=lambda g: g.passion_level, reverse=True):
            pending = [t for t in goal.tasks if not t.done]
            if pending:
                return goal, sorted(pending,
                                    key=lambda t: t.priority,
                                    reverse=True)[0]
        return None, None

    def summary(self) -> dict:
        active = self.get_active_goals()
        return {
            "specialty":      self.specialty,
            "interests":      dict(sorted(self.interests.items(),
                                          key=lambda x: x[1],
                                          reverse=True)[:5]),
            "active_goals":   len(active),
            "total_goals":    len(self.goals),
            "goals_preview":  [{"title": g.title,
                                 "progress": g.progress}
                                for g in active[:3]],
        }

    def to_dict(self) -> dict:
        return {
            "goals":     [g.to_dict() for g in self.goals],
            "interests": self.interests,
            "specialty": self.specialty,
        }

    def from_dict(self, d: dict):
        self.interests = d.get("interests", {})
        self.specialty = d.get("specialty")
        for gd in d.get("goals", []):
            g = Goal(gd["title"], gd["why"], gd.get("passion_level", 0.5))
            g.id         = gd.get("id", g.id)
            g.status     = gd.get("status", "نشط")
            g.created_at = gd.get("created_at", g.created_at)
            for td in gd.get("tasks", []):
                t             = Task(td["title"], td["description"],
                                     td.get("priority", 5))
                t.id          = td.get("id", t.id)
                t.done        = td.get("done", False)
                t.done_at     = td.get("done_at")
                t.reflection  = td.get("reflection", "")
                g.tasks.append(t)
            self.goals.append(g)
