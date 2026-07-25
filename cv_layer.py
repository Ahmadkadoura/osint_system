"""
cv_layer.py
============
هذه الوحدة (Module) مسؤولة فقط عن التواصل مع "قسم البحث بالصورة"
(النوت بوك الذي يعمل على Colab ومرفوع عبر FastAPI + ngrok).

فكرتها بسيطة: بدل ما ترسل الصورة يدوياً من Postman، هذا الملف
يقوم بنفس العملية بالضبط لكن عن طريق كود بايثون داخل مشروعك.

لا تحتوي هذه الوحدة على أي منطق NLP أو معالجة أسماء - فقط اتصال + عرض نتائج.
"""

import os
import requests

# ============================================================
# ⚙️ إعدادات الاتصال بالنوت بوك
# ============================================================
# ملاحظة مهمة جداً:
# رابط ngrok يتغير في كل مرة تُعيد فيها تشغيل خلايا النوت بوك على Colab
# (لأن Colab يعطيك جلسة جديدة كل مرة). لذلك بعد كل مرة تشغّل فيها
# النوت بوك، انسخ الرابط الجديد من مخرجات آخر خلية وضعه هنا بدل القديم.
CV_API_BASE_URL = "https://polygon-unscented-expenses.ngrok-free.dev"
CV_API_KEY = "12345678"
REQUEST_TIMEOUT = 180  # بالثواني - تحليل الصورة قد يأخذ وقتاً


def check_api_health() -> bool:
    """يتأكد أن النوت بوك شغّال فعلاً قبل ما نرسل له صورة (توفير وقت)."""
    try:
        resp = requests.get(f"{CV_API_BASE_URL}/health", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            print(f"[+] السيرفر يعمل | الـ Pipeline محمّل: {data.get('pipeline_loaded')}")
            return True
        print(f"[!] السيرفر رد بحالة غير متوقعة: {resp.status_code}")
        return False
    except requests.exceptions.RequestException as e:
        print(f"[!] تعذر الاتصال بالسيرفر. تأكد أن النوت بوك يعمل والرابط محدّث. التفاصيل: {e}")
        return False


def search_by_image(image_path: str, query_name: str = "") -> dict | None:
    """
    يرسل الصورة + الاسم المشتبه به إلى endpoint الخاص بـ /analyze
    ويرجع النتيجة كـ dict (نفس الشكل اللي كان يظهر لك في Postman).
    """
    if not os.path.exists(image_path):
        print(f"[!] المسار غير موجود: {image_path}")
        return None

    headers = {"X-API-Key": CV_API_KEY}
    data = {"query_name": query_name}

    print(f"[*] جاري إرسال الصورة: {os.path.basename(image_path)} ...")
    print("[*] قد يأخذ التحليل عدة دقائق حسب حمل السيرفر على Colab، الرجاء الانتظار...")

    try:
        with open(image_path, "rb") as f:
            files = {"file": (os.path.basename(image_path), f, "application/octet-stream")}
            response = requests.post(
                f"{CV_API_BASE_URL}/analyze",
                headers=headers,
                data=data,
                files=files,
                timeout=REQUEST_TIMEOUT,
            )

        if response.status_code == 200:
            return response.json()
        if response.status_code == 401:
            print("[!] خطأ توثيق (401): تأكد أن X-API-Key صحيح.")
            return None

        print(f"[!] فشل الطلب - كود الحالة: {response.status_code}")
        print(response.text[:500])
        return None

    except requests.exceptions.Timeout:
        print("[!] انتهت مهلة الانتظار. السيرفر يأخذ وقتاً أطول من المتوقع، جرّب مجدداً.")
        return None
    except requests.exceptions.ConnectionError:
        print("[!] تعذر الاتصال بالسيرفر. تأكد أن النوت بوك يعمل وأن رابط ngrok محدّث في الأعلى.")
        return None
    except Exception as e:
        print(f"[!] خطأ غير متوقع أثناء الاتصال: {e}")
        return None


def display_results(response_json: dict) -> None:
    """يعرض نتائج البحث بالصورة بشكل منظم في الطرفية بدل الـ JSON الخام."""
    if not response_json:
        print("[!] لا توجد نتائج لعرضها.")
        return

    query_name = response_json.get("query_name", "")
    total = response_json.get("total_results", 0)
    results = response_json.get("results", [])

    print("\n" + "=" * 60)
    print(f"نتائج البحث بالصورة عن: {query_name or 'غير محدد'}")
    print(f"عدد النتائج المكتشفة: {total}")
    print("=" * 60)

    if not results:
        print("لم يتم العثور على أي تطابقات.")
        return

    for i, item in enumerate(results, start=1):
        print(f"\n--- النتيجة رقم {i} ---")
        print(f"  المنصة        : {item.get('platform', 'غير معروف')}")
        print(f"  اسم المستخدم  : {item.get('username', 'غير متوفر')}")
        print(f"  الرابط        : {item.get('url', '')}")
        print(f"  نسبة الثقة    : {item.get('confidence_score', 0)}% ({item.get('confidence_label', '')})")
        print(f"  حساب رسمي؟    : {'نعم' if item.get('official') else 'لا'}")

        flags = item.get("risk_flags", [])
        if flags:
            print(f"  تنبيهات        : {', '.join(flags)}")

        contact = item.get("contact_info", {}) or {}
        if contact.get("emails"):
            print(f"  إيميلات        : {', '.join(contact['emails'])}")
        if contact.get("phones"):
            print(f"  هواتف          : {', '.join(contact['phones'])}")

    print("\n" + "=" * 60)


def run_image_search() -> None:
    """
    نقطة الدخول الوحيدة التي يحتاجها main.py.
    كل ما عليه فعله هو استدعاء هذه الدالة، وهي تتكفل بكل شيء:
    التحقق من السيرفر، أخذ المدخلات، الإرسال، وعرض النتائج.
    """
    print("\n--- قسم البحث بالصورة (OSINT البصري) ---")

    if not check_api_health():
        print("[!] لا يمكن المتابعة لأن السيرفر غير متاح حالياً.")
        print("    تأكد من: 1) النوت بوك شغّال على Colab   2) رابط ngrok محدّث في cv_layer.py")
        return

    image_path = input("أدخل المسار الكامل للصورة (مثال: C:\\Users\\me\\photo.jpg): ").strip().strip('"')
    query_name = input("أدخل الاسم المشتبه به (اختياري - اضغط Enter للتخطي): ").strip()

    result = search_by_image(image_path, query_name)
    display_results(result)