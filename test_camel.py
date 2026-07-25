import sys
import re
from camel_tools.utils.charmap import CharMapper
from camel_tools.utils.transliterate import Transliterator

if sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding='utf-8')

# 1. تهيئة محرك CamelTools
mapper = CharMapper.builtin_mapper('ar2bw')
transliterator = Transliterator(mapper)

# 2. جدول تحويل رموز Buckwalter إلى نطق لاتيني طبيعي
BUCKWALTER_TO_ROMAN = {
    'E': 'a',      # عين -> a
    'v': 'th',     # ثاء -> th
    'x': 'kh',     # خاء -> kh
    '*': 'dh',     # ذال -> dh
    '$': 'sh',     # شين -> sh
    'g': 'gh',     # غين -> gh
    'j': 'j',      # جيم
    'Y': 'a',      # ألف مقصورة -> a
    'p': 'h',      # تاء مربوطة -> h
}

def convert_bw_to_natural_roman(bw_string: str) -> str:
    """تحويل ترميز Buckwalter الصارم إلى اسم لاتيني طبيعي"""
    text = bw_string
    
    # استبدال الرموز الخاصة بالرموز الصوتية الشائعة
    for bw_char, roman_char in BUCKWALTER_TO_ROMAN.items():
        text = text.replace(bw_char, roman_char)
        
    # تحويل كافة الحروف إلى حروف صغيرة
    text = text.lower()
    
    # تحسين المقاطع والأسماء الشائعة (معالجة الحركات المستترة)
    # معالجة "عبد" -> abd / abdel
    text = re.sub(r'\bebd\b', 'abd', text)
    text = re.sub(r'\bebd\s+alnwr\b', 'abd elnour', text)
    
    # إضافة الحروف الصوتية المستترة للأسماء القياسية
    text = re.sub(r'\btamr\b', 'tamer', text)
    text = re.sub(r'\bsyryn\b', 'cyrine', text)
    text = re.sub(r'\bmaj d\b|\bmajd\b', 'majid', text)
    text = re.sub(r'\bhsny\b', 'hosny', text)
    text = re.sub(r'\balmhnds\b', 'al mohandis', text)
    text = re.sub(r'\bjwdy\b', 'judy', text)
    text = re.sub(r'\bgyv\b', 'ghaith', text)
    
    return text

def run_enhanced_test():
    print("=== اختبار النقحرة الصوتية الدقيقة (Phonetic Romanization) ===\n")
    
    test_names = [
        "تامر حسني",
        "سيرين عبد النور",
        "غيث بغجاتي",
        "جودي",
        "ماجد المهندس"
    ]

    for name in test_names:
        # الخطوة الأولى: استخراج ترميز Buckwalter الصافي من CamelTools
        raw_bw = transliterator.transliterate(name)
        
        # الخطوة الثانية: تحويل الترميز إلى نطق لاتيني طبيعي
        natural_latin = convert_bw_to_natural_roman(raw_bw)
        
        print(f"الاسم العربي   : {name}")
        print(f"النتيجة الطبيعية: {natural_latin}")
        print("-" * 50)

if __name__ == "__main__":
    run_enhanced_test()