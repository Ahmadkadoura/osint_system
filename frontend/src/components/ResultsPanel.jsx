function KeyValue({ label, value }) {
  if (value === null || value === undefined || value === "") return null;
  const display =
    typeof value === "string" || typeof value === "number" ? String(value) : value;
  return (
    <div className="kv">
      <span className="kv__label">{label}</span>
      <span className="kv__value">{display}</span>
    </div>
  );
}

function LinkValue({ label, url }) {
  if (!url) return null;
  return (
    <div className="kv">
      <span className="kv__label">{label}</span>
      <span className="kv__value">
        <a href={url} target="_blank" rel="noreferrer" className="osint-link">
          {url}
        </a>
      </span>
    </div>
  );
}

function normalizeOsintLink(link) {
  if (typeof link === "string") return { platform: null, url: link };
  if (link && typeof link === "object") {
    return {
      platform: link.platform || null,
      url: link.profile_url || link.url || null,
    };
  }
  return { platform: null, url: null };
}

function NameResults({ data }) {
  if (data.status === "error") {
    return (
      <div className="alert alert--error">
        {data.error?.message || "حدث خطأ غير معروف"}
      </div>
    );
  }

  const identity = data.identity || {};
  const arabic = identity.arabic_analysis || {};
  const components = arabic.components || {};
  const attrs = arabic.extracted_attributes || {};
  const suggestions = identity.latin_transliterations?.top_suggestions || [];
  const osint = identity.osint_live_targets || {};
  const siteSearch = identity.site_search_results || {};

  return (
    <>
      <section className="formatted__section">
        <h3>تحليل الاسم العربي</h3>
        <KeyValue label="الاسم الكامل" value={arabic.full_name} />
        <KeyValue label="الاسم الأول" value={components.first_name} />
        <KeyValue label="الأسماء الوسطى" value={components.middle_names?.join(" ") || "—"} />
        <KeyValue label="اسم العائلة" value={components.last_name} />
        <KeyValue label="المهنة" value={attrs.profession} />
        <KeyValue label="الموقع" value={attrs.location} />
        <KeyValue label="درجة الثقة" value={data.metadata?.confidence_score} />
        <KeyValue label="سنة الميلاد" value={data.metadata?.birth_year_context} />
      </section>

      {suggestions.length > 0 && (
        <section className="formatted__section">
          <h3>اقتراحات المعرفات اللاتينية</h3>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>الترتيب</th>
                  <th>المعرف</th>
                  <th>الدرجة</th>
                </tr>
              </thead>
              <tbody>
                {suggestions.map((s) => (
                  <tr key={s.rank}>
                    <td>{s.rank}</td>
                    <td className="mono">{s.name}</td>
                    <td>{s.score}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {Object.keys(siteSearch).length > 0 && (
        <section className="formatted__section">
          <h3>حسابات حقيقية مكتشفة عبر البحث</h3>
          {Object.entries(siteSearch).map(([platform, links]) => (
            <div key={platform} className="osint-block">
              <div className="osint-block__handle mono">{platform}</div>
              {(Array.isArray(links) ? links : []).map((link, i) => {
                const url = link?.profile_url || link?.url;
                if (!url) return null;
                return (
                  <a key={i} href={url} target="_blank" rel="noreferrer" className="osint-link">
                    {url}
                  </a>
                );
              })}
            </div>
          ))}
        </section>
      )}

      {Object.keys(osint).length > 0 && (
        <section className="formatted__section">
          <h3>نتائج OSINT المباشرة (تخمين المعرفات)</h3>
          {Object.entries(osint).map(([handle, links]) => (
            <div key={handle} className="osint-block">
              <div className="osint-block__handle mono">@{handle}</div>
              {(Array.isArray(links) ? links : []).map((rawLink, i) => {
                const { platform, url } = normalizeOsintLink(rawLink);
                if (!url) return null;
                return (
                  <a key={i} href={url} target="_blank" rel="noreferrer" className="osint-link">
                    {platform ? `${platform}: ` : ""}
                    {url}
                  </a>
                );
              })}
            </div>
          ))}
        </section>
      )}
    </>
  );
}

function ImageResults({ data }) {
  const results = data.results || [];

  return (
    <>
      <section className="formatted__section">
        <h3>ملخص البحث بالصورة</h3>
        <KeyValue label="الاسم المستهدف" value={data.query_name || "غير محدد"} />
        <KeyValue label="عدد النتائج" value={data.total_results ?? results.length} />
      </section>

      {results.length === 0 ? (
        <p className="empty-msg">لم يتم العثور على أي تطابقات.</p>
      ) : (
        results.map((item, i) => (
          <section key={i} className="formatted__section result-card">
            <h3>النتيجة رقم {i + 1}</h3>
            <KeyValue label="المنصة" value={item.platform} />
            <KeyValue label="اسم المستخدم" value={item.username} />
            <LinkValue label="الرابط" url={item.url} />
            <KeyValue
              label="نسبة الثقة"
              value={`${item.confidence_score ?? 0}% (${item.confidence_label || ""})`}
            />
            <KeyValue label="حساب رسمي؟" value={item.official ? "نعم" : "لا"} />
            {item.risk_flags?.length > 0 && (
              <KeyValue label="تنبيهات" value={item.risk_flags.join("، ")} />
            )}
            {item.contact_info?.emails?.length > 0 && (
              <KeyValue label="إيميلات" value={item.contact_info.emails.join("، ")} />
            )}
            {item.contact_info?.phones?.length > 0 && (
              <KeyValue label="هواتف" value={item.contact_info.phones.join("، ")} />
            )}
          </section>
        ))
      )}
    </>
  );
}

export default function ResultsPanel({ mode, data, onDownloadPdf, pdfLoading, resultsRef }) {
  if (!data) return null;

  const title = mode === "name" ? "نتائج البحث بالاسم" : "نتائج البحث بالصورة";

  return (
    <div className="results">
      <div className="results__header">
        <h2>{title}</h2>
        <div className="results__actions">
          <button
            type="button"
            className="btn btn--secondary"
            onClick={onDownloadPdf}
            disabled={pdfLoading}
          >
            {pdfLoading ? <span className="spinner" /> : null}
            {pdfLoading ? "جاري التصدير..." : "تنزيل PDF"}
          </button>
        </div>
      </div>

      <div className="results__body" ref={resultsRef}>
        {mode === "name" ? <NameResults data={data} /> : <ImageResults data={data} />}

        <details className="raw-json">
          <summary>عرض JSON الخام</summary>
          <pre>{JSON.stringify(data, null, 2)}</pre>
        </details>
      </div>
    </div>
  );
}
