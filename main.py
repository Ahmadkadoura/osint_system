import sys
import os
import re
import json
import time
import random
from typing import Optional

# ============================================================
# القسم الأول: البحث بالاسم (الكود الذي أنشأته أنت مسبقاً - لم يتغير)
# ============================================================
from core.entity import ParsedEntity
from core.normalizer import ArabicNormalizer
from core.entity_extractor import ArabicEntityExtractor
from core.entity_parser import ArabicEntityParser
from core.transliterator import ArabicTransliterator
from core.variant_generator import VariantGenerator
from core.ranker import VariantRanker
from core.payload_builder import PayloadBuilder
from core.osint_scanner import OSINTScanner
from core.site_search import SiteSearchEngine

# ============================================================
# القسم الثاني: البحث بالصورة (الوحدة الجديدة التي تتصل بالنوت بوك)
# ============================================================
from cv_layer import run_image_search


class IdentityEnginePipeline:
    def __init__(self):
        print("[*] جاري تهيئة محرك الهويات والذكاء الاصطناعي محلياً...")

        self.normalizer = ArabicNormalizer()
        self.extractor = ArabicEntityExtractor()
        self.parser = ArabicEntityParser()
        self.transliterator = ArabicTransliterator()
        self.generator = VariantGenerator(max_variants=30)
        self.ranker = VariantRanker()
        self.osint = OSINTScanner()
        self.site_search = SiteSearchEngine()

        print("[+] تم تحميل المحرك وكافة القواعد بنجاح وهو جاهز للعمل!")

    @staticmethod
    def _parse_latin_name(text: str) -> Optional[ParsedEntity]:
        """
        نموذج الـ NER مدرّب حصراً على العربية - تمريره نصاً لاتينياً (إنجليزياً) بالكامل
        يجعله يقطّع الكلمات لأجزاء فرعية مشوّهة (wordpiece leakage مثل "am ##ad").
        لذلك لو كان النص لاتينياً بالأساس، نتخطى الـ NER والنقحرة تماماً ونقسّم الاسم مباشرة.
        """
        words = [w for w in re.split(r"\s+", text.strip()) if w]
        if not words:
            return None

        first_name = words[0]
        # لو الاسم كلمة واحدة فقط، نترك last_name فاضياً بدل تكرار الاسم الأول -
        # تكراره كان يولّد معرفات فاسدة مثل "cristiano_cristiano"
        last_name = words[-1] if len(words) > 1 else ""
        middle_names = words[1:-1] if len(words) > 2 else []

        return ParsedEntity(
            full_name=text.strip(),
            first_name=first_name,
            last_name=last_name,
            middle_names=middle_names,
            profession=None,
            location=None,
            confidence=1.0,
        )

    @staticmethod
    def _pick_latin_fallback_candidates(first_latin: list, last_latin: list, max_candidates: int = 3) -> list:
        """
        يبني عدة مرشحين لاتينيين محتملين بترتيب طبيعي (الاسم الأول ثم اسم العائلة)
        مباشرة من نتائج الـ transliterator - بدل الاعتماد على مرشح واحد فقط، لأن اختلاف
        بسيط بالتهجئة (ibrahem/ibrahim) قد يفوّت حساباً حقيقياً مفهرساً بتهجئة معينة فقط.
        بدل ranked_variants[0] الذي قد يكون النص العربي نفسه أو صيغة معكوسة (لأنها تتساوى
        بالسكور مع الصيغ اللاتينية الصحيحة).
        """
        if not first_latin:
            return []

        firsts = [f[0] for f in first_latin[:2]]
        if not last_latin:
            return firsts[:max_candidates]

        # نفضّل صيغ اسم العائلة التي فيها فراغ ("al omari") لأنها أقرب للإملاء الطبيعي
        # المستخدم بالبروفايلات الحقيقية، ثم البقية
        spaced = [l[0] for l in last_latin if " " in l[0]]
        plain = [l[0] for l in last_latin if " " not in l[0]]
        lasts = (spaced + plain)[:2]

        candidates = []
        for first in firsts:
            for last in lasts:
                name = f"{first} {last}"
                if name not in candidates:
                    candidates.append(name)
                if len(candidates) >= max_candidates:
                    return candidates

        return candidates

    def process_text(self, raw_text: str, birth_year: Optional[int] = None) -> str:
        try:
            raw_text = raw_text.strip()

            arabic_chars = sum(1 for ch in raw_text if "؀" <= ch <= "ۿ")
            latin_chars = sum(1 for ch in raw_text if ch.isascii() and ch.isalpha())

            if latin_chars > 0 and arabic_chars == 0:
                # النص لاتيني بالكامل (اسم مكتوب إنجليزي أصلاً) - لا حاجة لاستخراج أو نقحرة
                parsed_entity = self._parse_latin_name(raw_text)
                if not parsed_entity:
                    return json.dumps(PayloadBuilder.build_error_payload("لم يتم العثور على اسم صالح في النص الممرر.", 422), ensure_ascii=False, indent=4)

                first_latin = [(parsed_entity.first_name.lower(), 1.0)]
                last_latin = [(parsed_entity.last_name.lower(), 1.0)] if parsed_entity.last_name else []
            else:
                cleaned_text = self.normalizer.normalize(raw_text)

                raw_entities = self.extractor.extract(cleaned_text)
                if not raw_entities:
                    return json.dumps(PayloadBuilder.build_error_payload("لم يتم اكتشاف أي كيانات في النص ممرر.", 404), ensure_ascii=False, indent=4)

                parsed_entity = self.parser.parse(raw_entities, original_text=cleaned_text)
                if not parsed_entity:
                    return json.dumps(PayloadBuilder.build_error_payload("لم يتم العثور على اسم شخص مكتمل الأركان.", 422), ensure_ascii=False, indent=4)

                first_latin = self.transliterator.transliterate_word(parsed_entity.first_name)
                last_latin = self.transliterator.transliterate_word(parsed_entity.last_name) if parsed_entity.last_name else []

            raw_variants = self.generator.generate_social_handles(
                parsed_entity=parsed_entity,
                first_latin_variants=first_latin,
                last_name_variants=last_latin,
                birth_year=birth_year
            )

            has_middle = len(parsed_entity.middle_names) > 0
            ranked_variants = self.ranker.rank_variants(raw_variants, has_middle_name=has_middle)

            osint_results = {}
            # --- كود توسيع مقترحات الـ OSINT لزيادة النتائج ---
            expanded_candidates = set()
            for item in ranked_variants:
                name = item["latin_name"]
                # استبعاد أي محارف غير لاتينية
                if any(ord(c) > 127 for c in name):
                    continue
                    
                if " " in name:
                    # إذا كان الاسم يحتوي على فراغ، نرسل للـ OSINT خيارات بديلة حقيقية تزيد احتمالية الإصابة
                    expanded_candidates.add(name.replace(" ", "."))  # judy.ghaith
                    expanded_candidates.add(name.replace(" ", "_"))  # judy_ghaith
                    expanded_candidates.add(name.replace(" ", ""))   # judyghaith
                else:
                    expanded_candidates.add(name)

            # تحويلها إلى قائمة وأخذ أعلى 15 أو 20 خياراً للفحص المكثف
            candidates = list(expanded_candidates)[:20]
            print(f"[*] جاري فحص طبقة الـ OSINT للمعرفات الصدارة: {candidates}...")
            for idx, handle in enumerate(candidates):
                links = self.osint.scan_handle(handle)
                if links:
                    osint_results[handle] = links
                # فاصل زمني عشوائي بين كل معرف والذي يليه لتقليل احتمال حظر الـ IP من المنصات
                if idx < len(candidates) - 1:
                    time.sleep(random.uniform(0.6, 1))

            # --- بحث حقيقي عبر محرك بحث خارجي (site:) بدل الاعتماد فقط على تخمين المعرفات ---
            # نبحث بالاسم الأصلي + أفضل نقحرة لاتينية مقترحة (fallback تلقائي لو الحساب مفهرس بالإنجليزية فقط)
            latin_fallback_candidates = self._pick_latin_fallback_candidates(first_latin, last_latin)
            print(f"[*] جاري البحث الحقيقي عن: {parsed_entity.full_name} (بدائل لاتينية: {latin_fallback_candidates}) ...")
            site_search_results = self.site_search.search_all(parsed_entity.full_name, latin_names=latin_fallback_candidates)

            final_payload = PayloadBuilder.build_success_payload(parsed_entity, ranked_variants)
            final_payload["identity"]["osint_live_targets"] = osint_results
            final_payload["identity"]["site_search_results"] = site_search_results
            final_payload["metadata"]["birth_year_context"] = birth_year if birth_year else "Not Provided"

            return json.dumps(final_payload, ensure_ascii=False, indent=4)

        except Exception as e:
            error_payload = PayloadBuilder.build_error_payload(f"حدث خطأ داخلي في النظام: {str(e)}", 500)
            return json.dumps(error_payload, ensure_ascii=False, indent=4)


def run_name_search():
    """نقطة الدخول لقسم البحث بالاسم - تستدعي المحرك الذي بنيته أنت."""
    engine = IdentityEnginePipeline()

    raw_text = input("\nأدخل النص الذي يحتوي على الاسم للبحث فيه: ").strip()

    birth_year_input = input("سنة الميلاد إن وجدت (اختياري - اضغط Enter للتخطي): ").strip()
    birth_year = int(birth_year_input) if birth_year_input.isdigit() else None

    json_output = engine.process_text(raw_text, birth_year=birth_year)

    print("\n" + "=" * 60)
    print("نتائج البحث بالاسم:")
    print("=" * 60)
    print(json_output)


def main():
    """
    نقطة الدخول الموحّدة للمشروع بالكامل.
    تسأل المستخدم أولاً: بالاسم أم بالصورة، ثم توجّهه للقسم المناسب.
    """
    print("=" * 60)
    print("نظام البحث والتحري (OSINT) - القائمة الرئيسية")
    print("=" * 60)
    print("1) البحث باستخدام الاسم / نص")
    print("2) البحث باستخدام صورة")
    print("0) خروج")

    choice = input("\nاختر رقم القسم: ").strip()

    if choice == "1":
        run_name_search()
    elif choice == "2":
        run_image_search()
    elif choice == "0":
        print("تم إنهاء البرنامج.")
        sys.exit(0)
    else:
        print("[!] اختيار غير صحيح. الرجاء تشغيل البرنامج من جديد واختيار 1 أو 2.")


if __name__ == "__main__":
    main()