from typing import List, Dict, Any

class VariantRanker:
    def __init__(self):
        # تحديد الأوزان والمكافآت (Heuristic Weights) للتحكم في الترتيب
        self.BONUS_FULL_NAME = 0.25      # مكافأة الاسم المكتمل الأركان
        self.PENALTY_SHORT_NAME = -0.15   # خصم للاختصارات أو الأسماء الناقصة
        self.PENALTY_WITH_CONTEXT = -0.05 # خصم خفيف جداً إذا كانت الصيغة محشوة بالمهنة/المدينة لتقديم الاسم النقي أولاً

    def rank_variants(self, variants: List[Dict[str, Any]], has_middle_name: bool = False) -> List[Dict[str, Any]]:
        """
        يستقبل قائمة الصيغ غير المرتبة، ويحسب السكور النهائي لكل صيغة بناءً على القواعد، ثم يعيدها مرتبة تنازلياً.
        """
        ranked_results = []

        for var in variants:
            latin_name = var["latin_name"]
            base_score = var["score"] # السكور القادم من الـ transliterator
            
            # حساب عدد الكلمات في الصيغة اللاتينية الحالية
            word_count = len(latin_name.split())
            
            final_score = base_score

            # 1. قاعدة الـ Completeness (الاسم الكامل):
            # إذا كان الاسم الأصلي يحتوي على اسم أوسط، والصيغة الحالية حافظت عليه (3 كلمات أو أكثر)
            if has_middle_name and word_count >= 3:
                final_score += self.BONUS_FULL_NAME
            
            # 2. قاعدة الـ Short Names (الأسماء المختصرة):
            # إذا تم اختصار الاسم لكلمة واحدة أو اثنتين فقط رغم وجود أسماء وسطى
            elif has_middle_name and word_count < 3:
                final_score += self.PENALTY_SHORT_NAME

            # 3. فحص وجود سياق إضافي (مثل كلمات المهن المحشوة في الصيغة إن وجدت)
            # هذه القاعدة تضمن بقاء الاسم النظيف المجرد في الصدارة
            if any(prof in latin_name.lower() for prof in ["eng", "dr", "professor"]):
                final_score += self.PENALTY_WITH_CONTEXT

            # إبقاء السكور محصوراً في نطاق منطقي وضمان عدم تخطي 1.0 كحد أقصى إلا لو أردت ذلك
            final_score = min(max(final_score, 0.0), 1.0)

            ranked_results.append({
                "latin_name": latin_name,
                "final_score": round(final_score, 4),
                "base_score": base_score
            })

        # ترتيب القائمة بالكامل تنازلياً بناءً على الـ final_score الجديد
        sorted_ranked_results = sorted(ranked_results, key=lambda x: x['final_score'], reverse=True)
        return sorted_ranked_results

# 