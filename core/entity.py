from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Entity:
    """
    الكيان الخام المستخرج مباشرة من النص (مثل اسم علم، مهنة، أو مدينة) 
    قبل عملية التقسيم والتحليل.
    """
    text: str                  # النص المستخرج كما هو (مثال: "الدكتور أحمد")
    label: str                 # نوع الكيان (مثال: B-PERS, I-PERS, PROF, LOC)
    start: int                 # مؤشر بداية الكيان في النص الأصلي
    end: int                   # مؤشر نهاية الكيان في النص الأصلي
    confidence: float = 1.0    # نسبة الثقة في الاستخراج (افتراضياً 1.0)


@dataclass
class ParsedEntity:
    """
    الكيان النهائي المفسر والمقسم بعد معالجته وتجميعه.
    الاسم الأول والأخير حقول إجبارية لا يمكن للهوية أن تكتمل بدونها.
    """
    # 1. الحقول الإجبارية (يجب أن تأتي أولاً)
    full_name: str                         # الاسم الكامل المجمع كما ظهر في النص
    first_name: str                        # الاسم الأول (إجباري)
    last_name: str                         # اسم العائلة / اللقب (إجباري)

    # 2. الحقول الاختيارية (تأتي ثانياً ولها قيم افتراضية)
    middle_names: List[str] = field(default_factory=list) # الأسماء الوسطى إن وجدت
    profession: Optional[str] = None       # المهنة (مثل: مهندس، دكتور) إن وجدت
    location: Optional[str] = None         # الموقع/المدينة (مثل: الرياض) إن وجدت
    confidence: float = 1.0                # نسبة الثقة الإجمالية للعملية