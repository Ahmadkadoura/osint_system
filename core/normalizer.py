import re
from camel_tools.utils.normalize import (
    normalize_alef_ar,
    normalize_alef_maksura_ar,
    normalize_teh_marbuta_ar
)

class ArabicNormalizer:
    def __init__(self):
        # ريجكس يضم جميع علامات التشكيل العربية (الفتحة، الضمة، الكسرة، السكون، التنوين، والشدة)
        self.diacritics_regex = re.compile(r'[\u064B-\u0652\u0653\u0654\u0655]')
        
        # ريجكس لإزالة التطويل (الكشيدة)
        self.tatweel_regex = re.compile(r'\u0640')
        
        # ريجكس لإزالة الرموز، علامات الترقيم، والأقواس (مع الإبقاء على الحروف العربية، الإنجليزية، والأرقام)
        self.cleaned_text_regex = re.compile(r'[^\w\s\u0600-\u06FF]')
        
        # ريجكس لتنظيف المسافات الزائدة
        self.multiple_spaces_regex = re.compile(r'\s+')

    def remove_diacritics(self, text: str) -> str:
        """إزالة كافة أنواع التشكيل والشدة من النص"""
        return self.diacritics_regex.sub('', text)

    def normalize(self, text: str) -> str:
        """
        يقوم بتهيئة وتنظيف النص العربي عبر مراحل متتالية ومنظمة.
        """
        if not text or not isinstance(text, str):
            return ""

        # 1. إزالة التشكيل (عبر الـ Regex الخاص بنا لتجنب مشاكل الاستيراد)
        text = self.remove_diacritics(text)

        # 2. إزالة التطويل (الكشيدة)
        text = self.tatweel_regex.sub('', text)

        # 3. توحيد الهمزات (أ، إ، آ -> ا)
        text = normalize_alef_ar(text)

        # 4. توحيد التاء المربوطة والياء المقصورة
        text = normalize_teh_marbuta_ar(text)      # ة -> ه
        text = normalize_alef_maksura_ar(text)    # ى -> ي

        # 5. تنظيف الرموز وعلامات الترقيم غير المرغوبة
        text = self.cleaned_text_regex.sub(' ', text)

        # 6. تنظيف المسافات الزائدة وتوحيدها
        text = self.multiple_spaces_regex.sub(' ', text).strip()

        return text

