import { useState } from "react";

export default function ImageSearchForm({ onSubmit, loading, cvAvailable }) {
  const [preview, setPreview] = useState(null);
  const [file, setFile] = useState(null);

  const handleFile = (e) => {
    const selected = e.target.files?.[0];
    setFile(selected || null);
    if (selected) {
      setPreview(URL.createObjectURL(selected));
    } else {
      setPreview(null);
    }
  };

  return (
    <form
      className="form"
      onSubmit={(e) => {
        e.preventDefault();
        if (!file) return;
        const form = e.target;
        onSubmit({ file, queryName: form.queryName.value });
      }}
    >
      {!cvAvailable && (
        <div className="alert alert--warning">
          سيرفر البحث بالصورة غير متصل حالياً. تأكد من تشغيل النوت بوك على Colab وتحديث رابط ngrok في
          cv_layer.py
        </div>
      )}

      <div className="form__group">
        <label>صورة الهدف</label>
        <div className="file-drop">
          <input type="file" accept="image/*" onChange={handleFile} required />
          {preview ? (
            <img src={preview} alt="معاينة" className="file-drop__preview" />
          ) : (
            <span className="file-drop__hint">اسحب الصورة هنا أو انقر للاختيار</span>
          )}
        </div>
      </div>

      <div className="form__group">
        <label htmlFor="queryName">الاسم المشتبه به (اختياري)</label>
        <input id="queryName" name="queryName" type="text" placeholder="مثال: أحمد محمد" />
      </div>

      <button type="submit" className="btn btn--primary" disabled={loading || !file}>
        {loading && <span className="spinner" />}
        {loading ? "جاري التحليل — قد يستغرق دقائق..." : "بدء البحث بالصورة"}
      </button>
    </form>
  );
}
