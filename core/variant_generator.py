import datetime
from typing import List, Dict, Any
from core.entity import ParsedEntity

class VariantGenerator:
    def __init__(self, max_variants: int = 25): # رفعنا الحد الأقصى الافتراضي لاقتراح خيارات أكثر
        self.max_variants = max_variants

    def generate_social_handles(self, 
                                 parsed_entity: ParsedEntity,
                                 first_latin_variants: List[tuple], 
                                 last_name_variants: List[tuple],
                                 birth_year: int = None) -> List[Dict[str, Any]]:
        """
        توليد معرفات ممتدة ومتنوعة مع مراعاة المقاطع الجزئية لاسم العائلة،
        وإضافة المسافات، وتفكيك "ال" التعريف ديناميكياً.
        """
        F = first_latin_variants[0][0].lower() if first_latin_variants else ""
        L = last_name_variants[0][0].lower() if last_name_variants else ""
        
        if not F:
            return []

        # استخراج مقاطع أحرف العائلة ديناميكياً (أكثر من حرف بناءً على طلبك)
        f = F[0]
        l1 = L[0] if L else ""
        l2 = L[:2] if len(L) >= 2 else l1
        l3 = L[:3] if len(L) >= 3 else l2

        handles = set()

        # --- الأنماط العربية النظيفة ---
        handles.add(f"{parsed_entity.first_name} {parsed_entity.last_name}")

        # --- الأنماط اللاتينية النصية الحرة ---
        if L:
            # 1. أنماط ممتدة للحروف (إظهار أكثر من حرف من الاسم الثاني)
            handles.add(f"{F}.{l2}")          # abrahim.al
            handles.add(f"{F}_{l2}")          # abrahim_al
            handles.add(f"{F}.{l3}")          # abrahim.ala
            handles.add(f"{F}_{l3}")          # abrahim_ala
            handles.add(f"{f}.{l3}")          # a.ala

            # 2. أنماط تحتوي على فراغ بين الاسم الأول والثاني بناءً على طلبك
            handles.add(f"{F} {L}")           # abrahim alamri
            handles.add(f"{L} {F}")           # alamri abrahim

            # الأنماط القياسية المتصلة والمفصولة برموز
            handles.add(f"{F}_{L}")
            handles.add(f"{F}.{L}")
            handles.add(f"{F}{L}")
            handles.add(f"{f}_{L}")
            handles.add(f"{f}.{L}")
            handles.add(f"{F}_{l1}")

            # 2ب. الاتجاه المعاكس: اسم العائلة كامل + حرف أول من الاسم الأول
            handles.add(f"{L}_{f}")          # alsahr_k
            handles.add(f"{L}.{f}")          # alsahr.k
            handles.add(f"{L}{f}")           # alsahrk

            # 2ج. دمج معكوس بدون فاصل (اسم العائلة + الاسم الأول)
            handles.add(f"{L}{F}")           # alsahrkadhm

            # 2د. بادئات إنجليزية شائعة جداً بحسابات السوشال ميديا الحقيقية
            handles.add(f"its.{F}")
            handles.add(f"its_{F}")
            handles.add(f"itz_{F}")
            handles.add(f"the.{F}")
            handles.add(f"the_{F}")
            handles.add(f"real_{F}")
            handles.add(f"real_{F}_{L}")
            handles.add(f"official_{F}")
            handles.add(f"official_{F}_{L}")
            handles.add(f"{F}_official")
            handles.add(f"{F}_{L}_official")
            handles.add(f"iam_{F}")
            handles.add(f"im.{F}")

            # 2هـ. فاصل سفلي/نقطة بادئة أو لاحقة (نمط شائع جداً بالحسابات الشخصية)
            handles.add(f"_{F}_")
            handles.add(f"_{F}")
            handles.add(f"{F}_")
            handles.add(f".{F}.")

            # 3. معالجة ذكية لـ "ال" التعريف (إذا كان الاسم اللاتيني يبدأ بـ al)
            # مثال: ابراهيم العمري -> F="ibrahim", L="alamri"
            if L.startswith("al") and len(L) > 2:
                al_prefix = "al"
                actual_last_name = L[2:] # اسم العائلة مجرداً من "الـ"
                
                # وضع فراغات بين الأول والـ التعريف واسم العائلة (f"{F} al {actual_last_name}")
                handles.add(f"{F} {al_prefix} {actual_last_name}")   # ibrahim al amri
                handles.add(f"{F}_{al_prefix}_{actual_last_name}")   # ibrahim_al_amri
                handles.add(f"{F}.{al_prefix}.{actual_last_name}")   # ibrahim.al.amri
                handles.add(f"{al_prefix} {actual_last_name} {F}")   # al amri ibrahim

            # --- الحساب الديناميكي للأرقام الدلالية ---
            current_year = 2026
            if birth_year and (1940 <= birth_year <= current_year):
                short_year = str(birth_year)[-2:]
                full_year = str(birth_year)
                age = current_year - birth_year

                handles.add(f"{F} {L} {short_year}")
                handles.add(f"{F}_{L}_{short_year}")
                handles.add(f"{F}_{L}_{age}")
                # سنة الميلاد الكاملة بأربع خانات (نمط شائع جداً أيضاً وليس فقط آخر خانتين)
                handles.add(f"{F}_{L}_{full_year}")
                handles.add(f"{F}{L}{full_year}")
                if L.startswith("al") and len(L) > 2:
                    handles.add(f"{F}_{al_prefix}_{L[2:]}_{short_year}")
            else:
                short_current_year = str(current_year)[-2:]
                handles.add(f"{F}_{L}_{short_current_year}")

            # --- لواحق رقمية عامة شائعة جداً عندما يكون المعرف الأصلي محجوزاً على المنصة ---
            for suffix in ("1", "01", "07", "23", "99"):
                handles.add(f"{F}_{L}{suffix}")
                handles.add(f"{F}{L}{suffix}")

        else:
            # في حال وجود اسم أول فقط
            handles.add(f"{F}")
            handles.add(f"its.{F}")
            handles.add(f"its_{F}")
            handles.add(f"the.{F}")
            handles.add(f"real_{F}")
            handles.add(f"official_{F}")
            handles.add(f"_{F}_")
            if birth_year:
                handles.add(f"{F}{str(birth_year)[-2:]}")
                handles.add(f"{F}{birth_year}")
            for suffix in ("1", "01", "07", "23", "99"):
                handles.add(f"{F}{suffix}")

        # --- 4. مرحلة التطهير البرمجي المحسن ---
        formatted_handles = []
        for handle in handles:
            # سمحنا هنا بعبور الفراغ " " ضمن الـ whitelist لتمرير الأنماط الجديدة بنجاح
            cleaned_chars = [char for char in handle if char.isalnum() or char in "._- "]
            handle_clean = "".join(cleaned_chars).strip().lower()
            
            if not handle_clean:
                continue

            # حساب الجودة (إعطاء سكور ممتاز للأنماط المفككة والاحترافية)
            if " " in handle_clean:
                score = 0.98  # سكور صدارة للأسماء ذات الفراغات الطبيعية الهيكلية
            elif "_" in handle_clean or "." in handle_clean:
                score = 0.95  
            elif any(char.isdigit() for char in handle_clean):
                score = 0.75  
            else:
                score = 0.85

            formatted_handles.append({
                "latin_name": handle_clean,
                "score": score
            })

        # ترتيب وتوسيع نافذة المخرجات المقترحة لتظهر خيارات أكثر
        return sorted(formatted_handles, key=lambda x: x['score'], reverse=True)[:self.max_variants]