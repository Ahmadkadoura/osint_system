export default function NameSearchForm({ onSubmit, loading }) {
  return (
    <form
      className="form"
      onSubmit={(e) => {
        e.preventDefault();
        const form = e.target;
        onSubmit({
          text: form.text.value,
          birthYear: form.birthYear.value,
        });
      }}
    >
      <div className="form__group">
        <label htmlFor="text">النص الذي يحتوي على الاسم</label>
        <textarea
          id="text"
          name="text"
          rows={4}
          placeholder="مثال: محمد أحمد العلي مهندس برمجيات من دمشق"
          required
        />
      </div>

      <div className="form__group form__group--inline">
        <label htmlFor="birthYear">سنة الميلاد (اختياري)</label>
        <input
          id="birthYear"
          name="birthYear"
          type="number"
          min="1900"
          max="2100"
          placeholder="مثال: 1995"
        />
      </div>

      <button type="submit" className="btn btn--primary" disabled={loading}>
        {loading && <span className="spinner" />}
        {loading ? "جاري التحليل..." : "بدء البحث بالاسم"}
      </button>
    </form>
  );
}
