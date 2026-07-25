function ShieldIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" width="28" height="28">
      <path d="M12 2L4 5v6c0 5.25 3.4 10.15 8 11.35C16.6 21.15 20 16.25 20 11V5l-8-3z" />
      <path d="M9 12l2 2 4-4" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export default function Header({ engineReady }) {
  return (
    <header className="header">
      <div className="header__brand">
        <div className="header__icon">
          <ShieldIcon />
        </div>
        <div>
          <h1>نظام البحث والتحري</h1>
          <p className="header__subtitle">OSINT · AI · Identity Engine</p>
        </div>
      </div>
      <div className={`status-pill ${engineReady ? "" : "status-pill--off"}`}>
        <span className="status-pill__dot" />
        {engineReady ? "المحرك جاهز" : "جاري التحميل..."}
      </div>
    </header>
  );
}
