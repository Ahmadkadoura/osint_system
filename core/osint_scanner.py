import requests
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any

class OSINTScanner:
    def __init__(self):
        # متصفح وهمي (User-Agent) لإقناع السيرفرات بأن الطلب قادم من متصفح حقيقي وليس بوت
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        # كل منصة إلها طريقة تحقق مختلفة عن قصد: الفحص العام (status_code == 200) غير موثوق
        # لأن Instagram و X تطبيقات SPA ترجع 200 لأي رابط بروفايل بغض النظر عن وجوده فعلياً.
        self.checkers = {
            "facebook": self._check_facebook,
            "instagram": self._check_instagram,
            "x": self._check_x,
        }

    def _check_facebook(self, handle: str) -> Dict[str, Any]:
        """فيسبوك يحوّل (redirect) الروابط غير الموجودة لصفحة تسجيل الدخول، لذلك نفحص الرابط النهائي."""
        clean_handle = handle.replace(" ", "")
        url = f"https://www.facebook.com/{clean_handle}"
        try:
            response = requests.get(url, headers=self.headers, timeout=6, allow_redirects=True)
            if response.status_code == 200 and "/login" not in response.url:
                return {"platform": "facebook", "status": "Found", "url": url}
            return {"platform": "facebook", "status": "Not Found", "url": None}
        except requests.RequestException:
            return {"platform": "facebook", "status": "Error / Timeout", "url": None}

    def _check_instagram(self, handle: str) -> Dict[str, Any]:
        """صفحة البروفايل نفسها ترجع 200 دايماً (SPA)، لذلك نستخدم الـ API الداخلي بدلاً منها."""
        clean_handle = handle.replace(" ", "")
        profile_url = f"https://www.instagram.com/{clean_handle}"
        api_url = "https://www.instagram.com/api/v1/users/web_profile_info/"
        headers = {**self.headers, "x-ig-app-id": "936619743392459"}
        try:
            response = requests.get(api_url, headers=headers, params={"username": clean_handle}, timeout=6)
            if response.status_code == 200:
                if response.json().get("data", {}).get("user"):
                    return {"platform": "instagram", "status": "Found", "url": profile_url}
                return {"platform": "instagram", "status": "Not Found", "url": None}
            if response.status_code == 404:
                return {"platform": "instagram", "status": "Not Found", "url": None}
            # 429/403 تعني حجب مؤقت من إنستغرام - لا نعرف الحقيقة فعلياً هنا فلا نجزم بالنتيجة
            return {"platform": "instagram", "status": "Unknown / Rate-Limited", "url": None}
        except (requests.RequestException, ValueError):
            return {"platform": "instagram", "status": "Error / Timeout", "url": None}

    def _check_x(self, handle: str) -> Dict[str, Any]:
        """
        منذ إغلاق X لكل الوصول غير الموثّق، لا توجد طريقة موثوقة للتحقق من وجود حساب
        بدون تسجيل دخول أو API رسمي - لذلك نتجنب تزوير نتيجة "Found" بدل الفحص الوهمي السابق.
        """
        return {"platform": "x", "status": "Unverified (requires X API auth)", "url": None}

    def scan_handle(self, handle: str) -> List[Dict[str, Any]]:
        """
        يفحص المعرف عبر جميع المنصات بالتوازي باستخدام التعدد البرمجي (Threading)
        """
        found_links = []

        # تشغيل الفحص بالتوازي على المنصات الثلاث لتسريع العملية
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(checker, handle) for checker in self.checkers.values()]

            for future in futures:
                result = future.result()
                if result["status"] == "Found":
                    found_links.append({
                        "platform": result["platform"],
                        "profile_url": result["url"]
                    })

        return found_links