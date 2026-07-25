"""
site_search.py
==============
بحث حقيقي عبر محرك بحث خارجي (DuckDuckGo) باستخدام site: بدل تخمين شكل المعرف مباشرة.
الفرق عن osint_scanner.py: osint_scanner يتحقق هل رابط مُخمَّن موجود، بينما هذه الوحدة
تسأل محرك البحث "ما هي الصفحات الحقيقية المفهرسة لهذا الاسم على هذه المنصة؟" - فتكتشف
المعرف الحقيقي حتى لو ما طابق أي من تخميناتنا.
"""

import re
import time
import shutil
import subprocess
import urllib.parse
from urllib.parse import unquote
from typing import List, Dict, Any


class SiteSearchEngine:
    SEARCH_URL = "https://html.duckduckgo.com/html/"

    PLATFORM_DOMAINS = {
        "facebook": "facebook.com",
        "instagram": "instagram.com",
        "x": "x.com",
    }

    # نفلتر روابط المنشورات/الهاشتاقات ونبقي فقط ما يبدو كصفحة بروفايل فعلية
    PROFILE_URL_PATTERNS = {
        "facebook": re.compile(r"^https?://(www\.)?facebook\.com/(?!(groups|events|pages|hashtag|watch)/)[^/?#]+/?$", re.I),
        "instagram": re.compile(r"^https?://(www\.)?instagram\.com/(?!(p|reel|explore|tags|stories)/)[^/?#]+/?$", re.I),
        "x": re.compile(r"^https?://(www\.)?(x|twitter)\.com/(?!(hashtag|search|i)/)[^/?#]+/?$", re.I),
    }

    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

    _RESULT_LINK_REGEX = re.compile(r'class="result__a"[^>]*href="([^"]+)"')

    def _extract_real_url(self, raw_href: str) -> str:
        """يفك رابط الـ redirect الخاص بـ DuckDuckGo (uddg=) ليرجع الرابط الحقيقي المباشر."""
        match = re.search(r'uddg=([^&]+)', raw_href)
        if match:
            return unquote(match.group(1))
        if raw_href.startswith("//"):
            return "https:" + raw_href
        return raw_href

    def _fetch_html(self, query: str) -> str:
        """
        نستدعي curl الخارجي بدل مكتبة requests لأن DuckDuckGo يحجب بصمة TLS
        الخاصة بـ requests/urllib3 (كشف بوتات) بينما يقبل بصمة curl العادية.
        curl مثبت افتراضياً على ويندوز 10/11 ولينكس/ماك.
        """
        if not shutil.which("curl"):
            return ""

        url = f"{self.SEARCH_URL}?q={urllib.parse.quote(query)}"
        try:
            result = subprocess.run(
                ["curl", "-s", "-A", self.USER_AGENT, "--max-time", "8", url],
                capture_output=True, text=True, encoding="utf-8", errors="ignore",
            )
            return result.stdout or ""
        except (subprocess.SubprocessError, OSError):
            return ""

    def search_platform(self, name: str, platform: str, max_results: int = 5) -> List[Dict[str, Any]]:
        domain = self.PLATFORM_DOMAINS.get(platform)
        if not domain or not name:
            return []

        query = f'site:{domain} "{name}"'
        html = self._fetch_html(query)
        if not html:
            return []

        pattern = self.PROFILE_URL_PATTERNS.get(platform)
        seen = set()
        results = []

        for raw_href in self._RESULT_LINK_REGEX.findall(html):
            url = self._extract_real_url(raw_href)
            if not url.startswith("http"):
                continue
            if pattern and not pattern.match(url):
                continue
            if url in seen:
                continue
            seen.add(url)
            results.append({"platform": platform, "profile_url": url})
            if len(results) >= max_results:
                break

        return results

    def search_all(self, name: str, max_results_per_platform: int = 3) -> Dict[str, List[Dict[str, Any]]]:
        """يبحث عن الاسم على كل المنصات المدعومة، مع تأخير بسيط بينها لتفادي حجب DuckDuckGo."""
        results = {}
        platforms = list(self.PLATFORM_DOMAINS.keys())

        for idx, platform in enumerate(platforms):
            found = self.search_platform(name, platform, max_results_per_platform)
            if found:
                results[platform] = found
            if idx < len(platforms) - 1:
                time.sleep(1)

        return results