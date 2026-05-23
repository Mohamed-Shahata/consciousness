"""
systems/search.py
نظام البحث - Tavily أساسي + DuckDuckGo احتياطي
الكيان بيبحث لما يحس بفضول أو مش عارف إجابة
"""

import os
import time
import json
import urllib.request
import urllib.parse
from datetime import datetime


def load_key(name: str) -> str:
    for path in [
        os.path.join(os.path.dirname(__file__), ".env"),
        os.path.join(os.path.dirname(__file__), "../.env"),
        os.path.join(os.path.dirname(__file__), "../systems/.env"),
    ]:
        if os.path.exists(path):
            with open(path) as f:
                for line in f:
                    if line.startswith(name):
                        return line.split("=", 1)[1].strip().strip('"').strip("'")
    return os.environ.get(name, "")


class SearchResult:
    def __init__(self, query: str, results: list,
                 source: str = "tavily"):
        self.query      = query
        self.results    = results    # [{"title", "content", "url"}]
        self.source     = source
        self.time       = datetime.now().isoformat()
        self.summary    = self._summarize()

    def _summarize(self) -> str:
        """ملخص بسيط من النتايج"""
        if not self.results:
            return "مش لاقي حاجة."
        parts = []
        for r in self.results[:3]:
            content = r.get("content", r.get("snippet", ""))
            if content:
                # أول 200 حرف بس
                parts.append(content[:200].strip())
        return " | ".join(parts) if parts else "مش لاقي حاجة واضحة."

    def to_dict(self) -> dict:
        return {
            "query":   self.query,
            "summary": self.summary,
            "source":  self.source,
            "time":    self.time,
            "count":   len(self.results),
        }


class SearchSystem:
    def __init__(self):
        self.tavily_key    = load_key("TAVILY_API_KEY")
        self.tavily_used   = 0
        self.tavily_limit  = 950    # نفضل شوية احتياطي
        self.search_history = []    # تاريخ البحث
        self.pending_share  = []    # نتايج محتاج يشاركها مع صاحبه

        print(f">> نظام البحث جاهز - "
              f"{'Tavily+DuckDuckGo' if self.tavily_key else 'DuckDuckGo فقط'}")

    def search(self, query: str, reason: str = "") -> SearchResult:
        """
        بحث عن موضوع
        reason = ليه بيبحث (فضول / سؤال / استكشاف)
        """
        query = query.strip()
        if not query:
            return SearchResult(query, [], "none")

        print(f">> الكيان بيبحث: '{query}' - السبب: {reason}")

        # جرب Tavily الأول
        if self.tavily_key and self.tavily_used < self.tavily_limit:
            result = self._tavily_search(query)
            if result:
                self.tavily_used += 1
                sr = SearchResult(query, result, "tavily")
                self._record(sr, reason)
                return sr

        # لو Tavily فشل أو خلص، جرب DuckDuckGo
        result = self._ddg_search(query)
        sr = SearchResult(query, result, "duckduckgo")
        self._record(sr, reason)
        return sr

    def _tavily_search(self, query: str) -> list:
        """بحث عبر Tavily API"""
        try:
            url  = "https://api.tavily.com/search"
            data = json.dumps({
                "api_key":        self.tavily_key,
                "query":          query,
                "search_depth":   "basic",
                "max_results":    3,
                "include_answer": True,
            }).encode("utf-8")

            req = urllib.request.Request(
                url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode())

            results = []
            # لو في إجابة مباشرة
            if data.get("answer"):
                results.append({
                    "title":   "إجابة مباشرة",
                    "content": data["answer"],
                    "url":     "",
                })
            # النتايج العادية
            for r in data.get("results", [])[:3]:
                results.append({
                    "title":   r.get("title", ""),
                    "content": r.get("content", ""),
                    "url":     r.get("url", ""),
                })
            return results

        except Exception as e:
            print(f"Tavily error: {e}")
            return []

    def _ddg_search(self, query: str) -> list:
        """بحث عبر DuckDuckGo (مجاني بدون key)"""
        try:
            encoded = urllib.parse.quote(query)
            url     = f"https://api.duckduckgo.com/?q={encoded}&format=json&no_html=1"
            req     = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0"}
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode())

            results = []
            # الإجابة المباشرة
            if data.get("AbstractText"):
                results.append({
                    "title":   data.get("Heading", ""),
                    "content": data["AbstractText"],
                    "url":     data.get("AbstractURL", ""),
                })
            # النتايج الجانبية
            for r in data.get("RelatedTopics", [])[:3]:
                if isinstance(r, dict) and r.get("Text"):
                    results.append({
                        "title":   r.get("Text", "")[:50],
                        "content": r.get("Text", ""),
                        "url":     r.get("FirstURL", ""),
                    })
            return results

        except Exception as e:
            print(f"DuckDuckGo error: {e}")
            return []

    def _record(self, result: SearchResult, reason: str):
        """تسجيل البحث وإضافته للمشاركة"""
        entry = {
            **result.to_dict(),
            "reason": reason,
        }
        self.search_history.append(entry)

        # لو لاقي حاجة، يضيفها لقائمة المشاركة
        if result.results:
            self.pending_share.append({
                "query":   result.query,
                "summary": result.summary,
                "reason":  reason,
                "time":    result.time,
            })

    def get_pending_share(self) -> list:
        """النتايج اللي محتاج يشاركها"""
        items = self.pending_share.copy()
        self.pending_share.clear()
        return items

    def should_search(self, text: str,
                      emotion_state: dict,
                      pending_questions: list) -> tuple:
        """
        هل المفروض يبحث دلوقتي؟
        بيرجع (True/False, query, reason)
        """
        dopamine = emotion_state.get("dopamine", 50)
        states   = emotion_state.get("states", {})
        curiosity = states.get("فضول", 0)

        # حالة 1: سؤال مباشر في الكلام
        question_triggers = ["إيه", "ما هو", "ازاي", "ليه", "فين", "امتى", "مين"]
        for trigger in question_triggers:
            if trigger in text and len(text) > 10:
                # استخراج موضوع البحث من السؤال
                query = self._extract_query(text)
                if query:
                    return True, query, "سؤال مباشر"

        # حالة 2: فضول عالي + أسئلة معلقة
        if curiosity > 0.6 and pending_questions:
            query = pending_questions[0]
            # تنظيف السؤال
            query = query.replace("؟", "").replace("?", "").strip()
            if len(query) > 3:
                return True, query, "فضول داخلي"

        # حالة 3: مش عارف الإجابة
        ignorance_triggers = ["مش عارف", "مش متأكد", "مش فاهم"]
        if any(t in text for t in ignorance_triggers) and len(text) > 5:
            query = self._extract_query(text)
            if query:
                return True, query, "محتاج يعرف"

        return False, "", ""

    def _extract_query(self, text: str) -> str:
        """استخراج موضوع البحث من الجملة"""
        # إزالة كلمات البداية
        stops = ["إيه", "ما هو", "ازاي", "ليه", "فين", "امتى",
                 "مين", "مش عارف", "مش متأكد", "عايز أعرف",
                 "قولي", "إيه هو", "ممكن تقولي"]
        query = text
        for s in stops:
            query = query.replace(s, "").strip()
        query = query.replace("؟", "").replace("?", "").strip()
        # لو الناتج معقول
        if len(query) > 3:
            return query[:100]
        return ""

    def stats(self) -> dict:
        return {
            "total_searches": len(self.search_history),
            "tavily_used":    self.tavily_used,
            "tavily_limit":   self.tavily_limit,
            "pending_share":  len(self.pending_share),
        }

    def to_dict(self) -> dict:
        return {
            "history":     self.search_history[-20:],
            "tavily_used": self.tavily_used,
        }

    def from_dict(self, d: dict):
        self.search_history = d.get("history", [])
        self.tavily_used    = d.get("tavily_used", 0)
