"""
نقطة التشغيل للواجهة الرسومية.

يشغّل خادم API (الذي يستدعي منطق main.py) ويفتح المتصفح تلقائياً.
لم يتم تعديل main.py أو أي ملف أساسي آخر.

الاستخدام:
    python run_ui.py
"""

import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"
DIST_DIR = FRONTEND_DIR / "dist"


def ensure_frontend_built():
    if (DIST_DIR / "index.html").exists():
        return True

    print("[*] جاري بناء الواجهة لأول مرة...")
    npm = "npm.cmd" if sys.platform == "win32" else "npm"
    try:
        subprocess.run([npm, "install"], cwd=FRONTEND_DIR, check=True)
        subprocess.run([npm, "run", "build"], cwd=FRONTEND_DIR, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"[!] فشل بناء الواجهة: {e}")
        print("    جرّب يدوياً: cd frontend && npm install && npm run build")
        return False


def find_free_port(host: str, start: int = 8001, end: int = 8010) -> int:
    """يبحث عن منفذ متاح إذا كان المنفذ الافتراضي مشغولاً."""
    for port in range(start, end + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind((host, port))
                return port
            except OSError:
                continue
    raise RuntimeError(f"لا يوجد منفذ متاح بين {start} و {end}")


def main():
    print("=" * 60)
    print("نظام البحث والتحري (OSINT) — الواجهة الرسومية")
    print("=" * 60)

    if not ensure_frontend_built():
        sys.exit(1)

    host = "127.0.0.1"
    preferred_port = 8001

    try:
        port = find_free_port(host, preferred_port, preferred_port + 10)
    except RuntimeError as e:
        print(f"[!] {e}")
        sys.exit(1)

    url = f"http://{host}:{port}"

    if port != preferred_port:
        print(f"[!] المنفذ {preferred_port} مشغول — سيتم استخدام المنفذ {port}")
    print(f"[*] جاري تشغيل الخادم على {url}")
    print("[*] اضغط Ctrl+C لإيقاف البرنامج")
    print()

    import threading

    def open_browser():
        time.sleep(1.5)
        webbrowser.open(url)

    threading.Thread(target=open_browser, daemon=True).start()

    import uvicorn

    uvicorn.run(
        "backend.server:app",
        host=host,
        port=port,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
