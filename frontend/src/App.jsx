import { useCallback, useEffect, useRef, useState } from "react";
import { checkCvHealth, checkHealth, searchByImage, searchByName } from "./api";
import { downloadResultsPdf } from "./utils/pdfExport";
import Header from "./components/Header";
import NameSearchForm from "./components/NameSearchForm";
import ImageSearchForm from "./components/ImageSearchForm";
import ResultsPanel from "./components/ResultsPanel";

const MODES = {
  name: "name",
  image: "image",
};

export default function App() {
  const [mode, setMode] = useState(MODES.name);
  const [engineReady, setEngineReady] = useState(false);
  const [cvAvailable, setCvAvailable] = useState(false);
  const [loading, setLoading] = useState(false);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [error, setError] = useState(null);
  const [results, setResults] = useState(null);
  const resultsRef = useRef(null);

  useEffect(() => {
    checkHealth()
      .then(() => setEngineReady(true))
      .catch(() => setEngineReady(false));

    checkCvHealth()
      .then((d) => setCvAvailable(d.available))
      .catch(() => setCvAvailable(false));
  }, []);

  const handleNameSearch = useCallback(async ({ text, birthYear }) => {
    setLoading(true);
    setError(null);
    setResults(null);
    try {
      const data = await searchByName(text, birthYear);
      setResults(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  const handleImageSearch = useCallback(async ({ file, queryName }) => {
    setLoading(true);
    setError(null);
    setResults(null);
    try {
      const data = await searchByImage(file, queryName);
      setResults(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  const handleDownloadPdf = useCallback(async () => {
    if (!resultsRef.current) return;
    setPdfLoading(true);
    try {
      const prefix = mode === "name" ? "name-search" : "image-search";
      const date = new Date().toISOString().slice(0, 10);
      await downloadResultsPdf(resultsRef.current, `osint-${prefix}-${date}.pdf`);
    } catch {
      setError("فشل تصدير ملف PDF");
    } finally {
      setPdfLoading(false);
    }
  }, [mode]);

  return (
    <div className="app">
      <div className="grid-bg" aria-hidden="true" />
      <Header engineReady={engineReady} />

      <main className="container">
        <div className="tabs" role="tablist">
          <button
            type="button"
            role="tab"
            className={`tab ${mode === MODES.name ? "tab--active" : ""}`}
            onClick={() => {
              setMode(MODES.name);
              setError(null);
            }}
          >
            <span className="tab__dot" />
            البحث بالاسم / نص
          </button>
          <button
            type="button"
            role="tab"
            className={`tab ${mode === MODES.image ? "tab--active" : ""}`}
            onClick={() => {
              setMode(MODES.image);
              setError(null);
            }}
          >
            <span className="tab__dot" />
            البحث بالصورة
          </button>
        </div>

        <div className="panel">
          {mode === MODES.name ? (
            <NameSearchForm onSubmit={handleNameSearch} loading={loading} />
          ) : (
            <ImageSearchForm
              onSubmit={handleImageSearch}
              loading={loading}
              cvAvailable={cvAvailable}
            />
          )}
        </div>

        {error && <div className="alert alert--error" style={{ marginTop: "1rem" }}>{error}</div>}

        <ResultsPanel
          mode={mode}
          data={results}
          onDownloadPdf={handleDownloadPdf}
          pdfLoading={pdfLoading}
          resultsRef={resultsRef}
        />
      </main>

      <footer className="footer">
        <span>نظام البحث والتحري — مشروع تخرج</span>
        <span className="footer__mono">OSINT LAYER v1.0</span>
      </footer>
    </div>
  );
}
