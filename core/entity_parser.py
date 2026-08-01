import os
import json
import re
from typing import List, Optional
from core.entity import Entity, ParsedEntity

class ArabicEntityParser:
    def __init__(self):
        # تحديد مسار الموارد (Resources)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        self.resources_dir = os.path.join(project_root, "resources")
        
        # تحميل القواميس
        self.professions = self._load_json_resource("professions.json")
        self.cities = self._load_json_resource("cities.json")
        
        # الكلمات المفتاحية للأسماء المركبة (السوابق واللواحق الشائعة)
        self.compound_prefixes = ["عبد", "ابو", "ام", "ابن", "بنت", "ذو"]
        self.compound_suffixes = ["الدين", "الله"]

    def _load_json_resource(self, filename: str) -> list:
        """تحميل ملفات القواميس بأمان"""
        path = os.path.join(self.resources_dir, filename)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def _merge_adjacent_entities(self, entities: List[Entity]) -> List[Entity]:
        """المرحلة 1: دمج الكيانات المتجاورة من نفس النوع (مثل: علاء + أحمد + الشريف)"""
        if not entities:
            return []
            
        merged = []
        current = entities[0]
        
        for next_entity in entities[1:]:
            # إذا كان الكيانان متتاليين ومن نفس النوع، ادمجهما
            # نفحص المسافة التقريبية بين نهاية الأول وبداية الثاني لضمان التتابع
            if current.label == next_entity.label and (next_entity.start - current.end) <= 2:
                current.text = f"{current.text} {next_entity.text}".strip()
                current.end = next_entity.end
                current.confidence = (current.confidence + next_entity.confidence) / 2
            else:
                merged.append(current)
                current = next_entity
        merged.append(current)
        return merged

    def _tokenize_name_with_compounds(self, full_name: str) -> List[str]:
        """المرحلة 2: تقطيع الاسم إلى كلمات مع الحفاظ على الأسماء المركبة ككتلة واحدة"""
        words = full_name.split()
        tokens = []
        skip_next = False
        
        for i in range(len(words)):
            if skip_next:
                skip_next = False
                continue
                
            current_word = words[i]
            
            # فحص السوابق المركبة (مثل: عبد الرحمن)
            if current_word in self.compound_prefixes and i + 1 < len(words):
                tokens.append(f"{current_word} {words[i+1]}")
                skip_next = True
            # فحص اللواحق المركبة (مثل: سيف الدين)
            elif i + 1 < len(words) and words[i+1] in self.compound_suffixes:
                tokens.append(f"{current_word} {words[i+1]}")
                skip_next = True
            else:
                tokens.append(current_word)
                
        return tokens

    def parse(self, entities: List[Entity], original_text: str = "") -> Optional[ParsedEntity]:
        """العقل المدبر: يحول قائمة الكيانات الخام إلى هوية واحدة مفسرة"""
        if not entities:
            return None

        # 1. دمج الكيانات المتجاورة أولاً
        merged_entities = self._merge_adjacent_entities(entities)
        
        # استخراج الكيانات الأساسية المتوفرة
        pers_entity = next((e for e in merged_entities if e.label == "PERS"), None)
        loc_entity = next((e for e in merged_entities if e.label == "LOC"), None)
        
        if not pers_entity:
            return None # محرك الهويات يتطلب وجود شخص على الأقل
            
        full_name = pers_entity.text
        
        # 2. معالجة وتقطيع الاسم الذكي
        name_tokens = self._tokenize_name_with_compounds(full_name)
        
        # توزيع حقول الاسم الإجبارية والاختيارية
        first_name = name_tokens[0] if len(name_tokens) > 0 else ""
        # لو الاسم كلمة واحدة فقط، نترك last_name فاضياً بدل تكرار الاسم الأول -
        # تكراره كان يولّد معرفات فاسدة مثل "cristiano_cristiano"
        last_name = name_tokens[-1] if len(name_tokens) > 1 else ""
        middle_names = name_tokens[1:-1] if len(name_tokens) > 2 else []
        
        # 3. اكتشاف المهنة من النص الأصلي أو القاموس
        detected_profession = None
        for prof in self.professions:
            if prof in original_text:
                detected_profession = prof
                break
                
        # 4. تأكيد الموقع من الـ NER أو المعجم
        detected_location = loc_entity.text if loc_entity else None
        if not detected_location:
            for city in self.cities:
                if city in original_text:
                    detected_location = city
                    break

        # 5. حساب الـ Confidence الإجمالي (متوسط ثقة الكيانات المستخرجة)
        total_confidence = pers_entity.confidence
        if loc_entity:
            total_confidence = (total_confidence + loc_entity.confidence) / 2

        return ParsedEntity(
            full_name=full_name,
            first_name=first_name,
            last_name=last_name,
            middle_names=middle_names,
            profession=detected_profession,
            location=detected_location,
            confidence=round(total_confidence, 2)
        )

