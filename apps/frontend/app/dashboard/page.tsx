import Link from "next/link";
import { Shell } from "@/components/Shell";
import { apiGet, money, number } from "@/lib/api";

type Branch = { id: string; code: string; name: string; division: string; sales: number; expenses: number; purchases: number };
type LowStock = { id: string; name: string; quantity_on_hand: number; unit: string; reorder_level: number };
type FinishedStock = { id: string; name: string; quantity_on_hand: number; unit: string; selling_price: number };
type Dashboard = { period: string; sales: number; expenses: number; purchases: number; fuel: number; maintenance: number; operating_spend: number; cash_margin_proxy: number; production_units: number; active_aluminium_jobs: number; active_vehicles: number; low_stock: LowStock[]; finished_stock: FinishedStock[]; branches: Branch[] };
type ManagementSummary = { receivables:number; payables:number; net_working_balance:number; pending_deliveries:number; production_reject_rate_pct:number; average_brick_cost:number; aluminium_measured_area_m2:number; active_recipes:number };
type GovernanceSummary = { pending_approvals:number; unread_notifications:number; documents:number; active_employees:number; draft_payroll_runs:number };
type BankSummary={id:string;unreconciled?:number};
type QuoteSummary={id:string;status:string;total_amount:number|string;converted_invoice_id?:string|null};

const empty: Dashboard = { period: "", sales: 0, expenses: 0, purchases: 0, fuel: 0, maintenance: 0, operating_spend: 0, cash_margin_proxy: 0, production_units: 0, active_aluminium_jobs: 0, active_vehicles: 0, low_stock: [], finished_stock: [], branches: [] };
const emptyManagement: ManagementSummary = { receivables:0,payables:0,net_working_balance:0,pending_deliveries:0,production_reject_rate_pct:0,average_brick_cost:0,aluminium_measured_area_m2:0,active_recipes:0 };
const emptyGovernance: GovernanceSummary = { pending_approvals:0,unread_notifications:0,documents:0,active_employees:0,draft_payroll_runs:0 };

const modules = [
  ["/commercial", "COM", "Commercial", "Multi-line quotations with direct conversion into customer invoices."],
  ["/inventory", "INV", "Inventory", "Raw materials, units, reorder levels and stock position."],
  ["/production", "BRK", "Brick Production", "Input usage, output, rejects, batch cost and cost per brick."],
  ["/standards", "STD", "Recipes & Variance", "Approved mixes versus actual material usage and waste."],
  ["/aluminium", "ALG", "Aluminium & Glass", "Customer jobs, material cost, labour, transport and profitability."],
  ["/measurements", "MSR", "Measurements", "Site sizes, glass area and fabrication measurements."],
  ["/purchasing", "PO", "Purchasing", "Supplier purchases and automatic raw-material stock receipts."],
  ["/sales", "SAL", "Sales", "Finished-goods sales, delivery charges and branch revenue."],
  ["/deliveries", "DSP", "Deliveries", "Dispatch scheduling, trucks, drivers and delivery status."],
  ["/accounts", "AR", "Customer & Supplier Accounts", "Receivables, payables, invoices, bills and payments."],
  ["/finance", "FIN", "Finance & Expenses", "Operating expenses and branch-level spend control."],
  ["/ledger", "GL", "Ledger & Banking", "Balanced journals, trial balance and bank reconciliation."],
  ["/fleet", "FLT", "Fleet", "Trucks, small vehicles, odometers, fuel and maintenance."],
  ["/people", "HR", "People & Payroll", "Employee records, salary snapshots and approval-gated payroll."],
  ["/governance", "GOV", "Governance", "Approvals, roles, documents, notifications and audit trail."],
];

export default async function DashboardPage() {
  const [dashboard, management, governance, banks, quotes] = await Promise.all([
    apiGet<Dashboard>("dashboard", empty),
    apiGet<ManagementSummary>("management-summary", emptyManagement),
    apiGet<GovernanceSummary>("governance-summary", emptyGovernance),
    apiGet<BankSummary[]>("bank-accounts", []),
    apiGet<QuoteSummary[]>("quotes", []),
  ]);
  const connected = Boolean(dashboard.period);
  const openQuotes=quotes.filter(x=>!x.converted_invoice_id&&!['rejected','expired'].includes(x.status));
  const quotePipeline=openQuotes.reduce((sum,x)=>sum+Number(x.total_amount||0),0);
  const unreconciled=banks.reduce((sum,x)=>sum+Number(x.unreconciled||0),0);
  return (
    <Shell active="/dashboard">
      <section className="hero">
        <div><span className="eyebrow">Executive overview</span><h1>See what the business is costing, producing and controlling.</h1><p>One live view across Brick Works, Aluminium & Glass, finance, people, governance and the company fleet. Every operational transaction stays attached to the business activity that caused it.</p></div>
        <span className="hero-badge">{connected ? `Month from ${dashboard.period}` : "Waiting for live operational data"}</span>
      </section>

      <section className="kpi-grid">
        <div className="card kpi"><div className="kpi-head"><span>Monthly sales</span><span className="kpi-icon">M</span></div><strong>{money(dashboard.sales)}</strong><small>Consolidated company revenue</small></div>
        <div className="card kpi"><div className="kpi-head"><span>Operating spend</span><span className="kpi-icon">C</span></div><strong>{money(dashboard.operating_spend)}</strong><small>Purchases + expenses + fuel + maintenance</small></div>
        <div className="card kpi"><div className="kpi-head"><span>Good bricks produced</span><span className="kpi-icon">B</span></div><strong>{number(dashboard.production_units, 0)}</strong><small>Accepted production this month</small></div>
        <div className="card kpi"><div className="kpi-head"><span>Cash margin proxy</span><span className="kpi-icon">%</span></div><strong>{money(dashboard.cash_margin_proxy)}</strong><small className={dashboard.cash_margin_proxy >= 0 ? "positive" : "negative"}>Sales less tracked operating spend</small></div>
      </section>

      <section className="kpi-grid">
        <div className="card kpi"><div className="kpi-head"><span>Customers owe</span><span className="kpi-icon">AR</span></div><strong>{money(management.receivables)}</strong><small>Outstanding customer receivables</small></div>
        <div className="card kpi"><div className="kpi-head"><span>Supplier payables</span><span className="kpi-icon">AP</span></div><strong>{money(management.payables)}</strong><small>Outstanding supplier balances</small></div>
        <div className="card kpi"><div className="kpi-head"><span>Production reject rate</span><span className="kpi-icon">Q</span></div><strong>{number(management.production_reject_rate_pct,2)}%</strong><small>All recorded brick production</small></div>
        <div className="card kpi"><div className="kpi-head"><span>Pending deliveries</span><span className="kpi-icon">D</span></div><strong>{number(management.pending_deliveries,0)}</strong><small>Scheduled, loaded or in transit</small></div>
      </section>

      <section className="kpi-grid">
        <div className="card kpi"><div className="kpi-head"><span>Quote pipeline</span><span className="kpi-icon">Q</span></div><strong>{money(quotePipeline)}</strong><small>{openQuotes.length} open commercial quotes</small></div>
        <div className="card kpi"><div className="kpi-head"><span>Unreconciled bank items</span><span className="kpi-icon">GL</span></div><strong>{number(unreconciled,0)}</strong><small>Transactions still needing reconciliation</small></div>
        <div className="card kpi"><div className="kpi-head"><span>Pending approvals</span><span className="kpi-icon">A</span></div><strong>{number(governance.pending_approvals,0)}</strong><small>Director/admin decisions outstanding</small></div>
        <div className="card kpi"><div className="kpi-head"><span>Active employees</span><span className="kpi-icon">HR</span></div><strong>{number(governance.active_employees,0)}</strong><small>{governance.draft_payroll_runs} draft payroll runs</small></div>
      </section>

      <section className="section-grid">
        <div className="card panel"><div className="panel-head"><h2>Division performance</h2><span>Current month</span></div>{dashboard.branches.length ? <div className="branch-grid">{dashboard.branches.map((branch) => <div className="branch-card" key={branch.id}><div className="branch-top"><div><span className="branch-code">{branch.code}</span><h3>{branch.name}</h3></div><span className="eyebrow">{branch.division}</span></div><div className="branch-values"><span>Sales<strong>{money(branch.sales)}</strong></span><span>Expenses<strong>{money(branch.expenses)}</strong></span><span>Purchases<strong>{money(branch.purchases)}</strong></span></div></div>)}</div> : <div className="empty-state"><strong>No branch transactions yet</strong>Seeded Brick Works and Aluminium branches will appear here once the backend is running.</div>}</div>
        <div className="card panel"><div className="panel-head"><h2>Attention required</h2><span>Low raw-material stock</span></div>{dashboard.low_stock.length ? <div className="stock-list">{dashboard.low_stock.slice(0, 7).map((item) => <div className="stock-row" key={item.id}><strong>{item.name}</strong><span>{number(item.quantity_on_hand)} {item.unit}</span></div>)}</div> : <div className="empty-state"><strong>No low-stock warnings</strong>Materials at or below reorder level will be highlighted here.</div>}</div>
      </section>

      <section className="kpi-grid" style={{ marginTop: 18 }}>
        <div className="card kpi"><div className="kpi-head"><span>Avg. brick production cost</span><span className="kpi-icon">B</span></div><strong>{money(management.average_brick_cost)}</strong><small>Across recorded good output</small></div>
        <div className="card kpi"><div className="kpi-head"><span>Measured aluminium/glass</span><span className="kpi-icon">A</span></div><strong>{number(management.aluminium_measured_area_m2,2)} m²</strong><small>Captured fabrication area</small></div>
        <div className="card kpi"><div className="kpi-head"><span>Fuel cost</span><span className="kpi-icon">F</span></div><strong>{money(dashboard.fuel)}</strong><small>Fleet fuel this month</small></div>
        <div className="card kpi"><div className="kpi-head"><span>Maintenance</span><span className="kpi-icon">R</span></div><strong>{money(dashboard.maintenance)}</strong><small>Vehicle repairs and service cost</small></div>
      </section>

      <section className="module-grid">{modules.map(([href, icon, title, copy]) => <Link className="card module-card" href={href} key={href}><span className="mini-icon">{icon}</span><h3>{title}</h3><p>{copy}</p></Link>)}</section>
    </Shell>
  );
}
