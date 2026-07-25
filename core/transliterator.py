import os
import json
import heapq
from typing import List, Tuple

class ArabicTransliterator:
    def __init__(self):
        # تحديد مسار ملف القواعد
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        self.rules_path = os.path.join(project_root, "resources", "transliteration_rules.json")
        self.gazetteer_path = os.path.join(project_root, "resources", "name_gazetteer.json")

        # تحميل القواعد (الـ Graph)
        self.graph = self._load_rules()
        # تحميل قاموس الأسماء الشائعة (Whole-word lookup) — أولوية أعلى من القواعد الصوتية
        self.gazetteer = self._load_json(self.gazetteer_path)

    def _load_json(self, path: str) -> dict:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _load_rules(self) -> dict:
        """تحميل روابط الـ Graph وأوزانها من ملف الـ JSON"""
        if os.path.exists(self.rules_path):
            with open(self.rules_path, "r", encoding="utf-8") as f:
                return json.load(f)

        # قواعد افتراضية مبسطة جداً في حال عدم وجود الملف (يفضل التوسع بها في الـ JSON)
        return {
            "ع": [["a", 0.8], ["e", 0.2]],
            "ل": [["l", 1.0]],
            "ي": [["i", 0.5], ["y", 0.3], ["ee", 0.2]],
            "ق": [["q", 0.7], ["k", 0.3]]
        }

    def transliterate_word(self, word: str, top_k: int = 10) -> List[Tuple[str, float]]:
        if not word:
            return []

        # 0. أولاً: هل الاسم موجود بالكامل في قاموس الأسماء الشائعة؟
        # (إملاء حقيقي متعارف عليه بدل الاشتقاق الصوتي الحرفي)
        gazetteer_entry = self.gazetteer.get(word.strip())
        if gazetteer_entry:
            sorted_entry = sorted(gazetteer_entry, key=lambda x: x[1], reverse=True)
            return [(text, score) for text, score in sorted_entry[:top_k]]

        # تحميل القواعد المنفصلة بأمان من الـ JSON المتطور
        rules_general = self.graph.get("قواعد_عامة", self.graph)
        rules_context = self.graph.get("سياقات_صوتية", {})

        # طابور الأولويات: (-السكور، النص اللاتيني، مؤشر الحرف الحالي في الكلمة العربية)
        queue = [(-1.0, "", 0)]
        results = []

        while queue and len(results) < top_k * 4:
            current_score, current_text, char_idx = heapq.heappop(queue)
            current_score = -current_score

            if char_idx == len(word):
                results.append((current_text, round(current_score, 4)))
                continue

            # --- الخوارزمية العامة: فحص السياق المركب (Lookahead) ---
            transitions = None
            step_size = 1

            # إذا كان هناك حرف تالٍ، نفحص الثنائيات (Bigrams) أولاً
            if char_idx + 1 < len(word):
                bigram_key = f"{word[char_idx]}_{word[char_idx+1]}"
                if bigram_key in rules_context:
                    transitions = rules_context[bigram_key]
                    step_size = 2  # قفز حرفين لأننا عالجنا السياق بالكامل

            # إذا لم نجد سياقاً مركباً، نعود للقاعدة العامة للحرف المنفرد
            # (قاعدة "قواعد_عامة" جزئية، لذلك نكمل الحروف الناقصة من الجدول الكامل)
            if transitions is None:
                current_char = word[char_idx]
                transitions = rules_general.get(current_char) or self.graph.get(current_char, [[current_char, 1.0]])
                step_size = 1

            # توليد المسارات بناءً على القرار المتخذ ديناميكياً
            for latin_char, weight in transitions:
                new_score = current_score * weight
                new_text = current_text + latin_char
                heapq.heappush(queue, (-new_score, new_text, char_idx + step_size))

        # تصفية وترتيب النتائج
        unique_results = {}
        for text, score in results:
            if text not in unique_results or score > unique_results[text]:
                unique_results[text] = score

        sorted_results = sorted(unique_results.items(), key=lambda x: x[1], reverse=True)
        return sorted_results[:top_k]
