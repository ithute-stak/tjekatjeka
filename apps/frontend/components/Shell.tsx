import Link from "next/link";

const nav = [
  ["/", "Overview"],
  ["/inventory", "Inventory"],
  ["/purchasing", "Purchasing"],
  ["/production", "Brick Production"],
  ["/standards", "Recipes & Variance"],
  ["/aluminium", "Aluminium & Glass"],
  ["/measurements", "Measurements"],
  ["/sales", "Sales"],
  ["/deliveries", "Deliveries"],
  ["/accounts", "Customer & Supplier Accounts"],
  ["/finance", "Finance"],
  ["/fleet", "Fleet"],
];

export function Shell({ children, active = "/" }: { children: React.ReactNode; active?: string }) {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">TJ</div>
          <div>
            <strong>Tjekatjeka</strong>
            <span>Holdings Management</span>
          </div>
        </div>
        <nav>
          {nav.map(([href, label]) => (
            <Link key={href} className={active === href ? "nav-link active" : "nav-link"} href={href}>
              <span className="nav-dot" />
              {label}
            </Link>
          ))}
        </nav>
        <div className="sidebar-foot">
          <span>Two divisions. One control centre.</span>
          <small>Powered by !thute</small>
        </div>
      </aside>
      <main className="main-panel">
        <header className="topbar">
          <div>
            <span className="eyebrow">Tjekatjeka Holdings</span>
            <strong>Operations Control Centre</strong>
          </div>
          <div className="topbar-actions">
            <span className="status-pill"><i /> System online</span>
            <div className="avatar">TH</div>
          </div>
        </header>
        <div className="content">{children}</div>
      </main>
    </div>
  );
}
