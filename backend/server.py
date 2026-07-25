"""
خادم الواجهة الرسومية — يستدعي منطق main.py و cv_layer.py دون تعديلهما.
"""

import json
import os
import sys
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# إضافة جذر المشروع لمسار الاستيراد
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from main import IdentityEnginePipeline  # noqa: E402
from cv_layer import check_api_health, search_by_image  # noqa: E402

FRONTEND_DIST = PROJECT_ROOT / "frontend" / "dist"

_engine: Optional[IdentityEnginePipeline] = None


@asynccontextmanager
async def lifespan(_: FastAPI):
    global _engine
    _engine = IdentityEnginePipeline()
    yield
    _engine = None


app = FastAPI(
    title="نظام البحث والتحري OSINT",
    description="واجهة API للواجهة الرسومية",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def api_health():
    return {"status": "ok", "engine_loaded": _engine is not None}


@app.get("/api/cv-health")
def cv_health():
    available = check_api_health()
    return {"available": available}


@app.post("/api/search/name")
def search_by_name(payload: dict):
    if _engine is None:
        raise HTTPException(status_code=503, detail="المحرك غير جاهز بعد")

    raw_text = (payload.get("text") or "").strip()
    if not raw_text:
        raise HTTPException(status_code=400, detail="النص مطلوب")

    birth_year = payload.get("birth_year")
    if birth_year is not None:
        try:
            birth_year = int(birth_year)
        except (TypeError, ValueError):
            birth_year = None

    result_json = _engine.process_text(raw_text, birth_year=birth_year)
    return json.loads(result_json)


@app.post("/api/search/image")
async def search_image(
    file: UploadFile = File(...),
    query_name: str = Form(""),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="يجب اختيار صورة")

    suffix = Path(file.filename).suffix or ".jpg"
    tmp_path = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        if not check_api_health():
            raise HTTPException(
                status_code=503,
                detail="سيرفر البحث بالصورة غير متاح. تأكد من تشغيل النوت بوك وتحديث رابط ngrok في cv_layer.py",
            )

        result = search_by_image(tmp_path, query_name.strip())
        if result is None:
            raise HTTPException(status_code=502, detail="فشل البحث بالصورة. راجع سجلات الخادم.")

        return result
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


@app.get("/")
def serve_index():
    index = FRONTEND_DIST / "index.html"
    if index.exists():
        return FileResponse(index)
    raise HTTPException(
        status_code=404,
        detail="الواجهة غير مبنية بعد. شغّل: cd frontend && npm run build",
    )


if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")
