import { notFound } from "next/navigation";
import { Shell } from "@/components/Shell";
import { apiGet, money, number } from "@/lib/api";

type Row = Record<string, unknown>;
type SectionConfig = { title: string; copy: string; endpoint: string; note: string; columns: [string, string, "money" | "number" | "text"][] };

const sections: Record<string, SectionConfig> = {
  inventory: { title: "Inventory", copy: "Control every production input by unit, stock balance, reorder level and average unit cost.", endpoint: "materials", note: "Brick production consumes material stock automatically. Purchases increase it and recalculate weighted average unit cost.", columns: [["name","Material","text"],["category","Category","text"],["unit","Unit","text"],["quantity_on_hand","On hand","number"],["reorder_level","Reorder level","number"],["average_unit_cost","Avg. unit cost","money"]] },
  purchasing: { title: "Purchasing", copy: "See supplier purchases across both divisions and the cost entering Tjekatjeka inventory.", endpoint: "purchases", note: "Material-linked purchases automatically increase raw-material stock and preserve supplier/reference information for audit.", columns: [["purchase_date","Date","text"],["supplier_name","Supplier","text"],["item_name","Item","text"],["reference","Reference","text"],["quantity","Quantity","number"],["unit_cost","Unit cost","money"],["total_cost","Total","money"]] },
  production: { title: "Brick Production", copy: "Measure actual raw-material consumption, rejects, good output and cost per saleable brick.", endpoint: "production", note: "A batch cannot consume more material than is in stock. Good output is added to finished-goods stock only after costing succeeds.", columns: [["production_date","Date","text"],["batch_no","Batch","text"],["produced_quantity","Produced","number"],["rejected_quantity","Rejected","number"],["good_quantity","Good bricks","number"],["total_cost","Batch cost","money"],["cost_per_good_unit","Cost / brick","money"]] },
  aluminium: { title: "Aluminium & Glass", copy: "Track each customer job from quote through fabrication and installation, with job-level profitability.", endpoint: "aluminium-jobs", note: "Material, labour, transport and other cost are compared with the quoted value so management can see profit by job.", columns: [["job_no","Job","text"],["customer_name","Customer","text"],["description","Description","text"],["status","Status","text"],["quote_amount","Quoted","money"],["total_cost","Cost","money"],["profit","Profit","money"]] },
  sales: { title: "Sales", copy: "Monitor finished-goods movement, customer value, delivery cost and revenue by branch.", endpoint: "sales", note: "Brick sales cannot exceed finished stock. Selling a product reduces its available quantity immediately.", columns: [["sale_date","Date","text"],["customer_name","Customer","text"],["quantity","Quantity","number"],["unit_price","Unit price","money"],["delivery_cost","Delivery","money"],["total_amount","Total","money"]] },
  finance: { title: "Finance & Expenses", copy: "Keep operating costs visible by branch, category and date instead of mixing every cost into one company total.", endpoint: "expenses", note: "The executive dashboard combines expenses with purchasing, fuel and maintenance to show tracked operating spend.", columns: [["expense_date","Date","text"],["category","Category","text"],["description","Description","text"],["reference","Reference","text"],["amount","Amount","money"]] },
  fleet: { title: "Fleet", copy: "Manage trucks and smaller vehicles with odometer, availability and operating-status visibility.", endpoint: "vehicles", note: "Fuel logs reject backwards odometer readings. Maintenance and fuel costs feed the management dashboard separately from branch purchasing.", columns: [["registration","Registration","text"],["make_model","Make / Model","text"],["vehicle_type","Type","text"],["odometer_km","Odometer km","number"],["status","Status","text"]] },
};

function display(value: unknown, kind: "money" | "number" | "text") {
  if (value === null || value === undefined || value === "") return "—";
  if (kind === "money") return money(value);
  if (kind === "number") return number(value);
  return String(value).replaceAll("_", " ");
}

export default async function SectionPage({ params }: { params: Promise<{ section: string }> }) {
  const { section } = await params;
  const config = sections[section];
  if (!config) notFound();
  const rows = await apiGet<Row[]>(config.endpoint, []);
  return (
    <Shell active={`/${section}`}>
      <section className="page-head">
        <div><span className="eyebrow">Operations module</span><h1>{config.title}</h1><p>{config.copy}</p></div>
        <span className="action-button">API-backed records</span>
      </section>
      <div className="note">{config.note}</div>
      <section className="metric-strip">
        <div className="card"><span>Records loaded</span><strong>{number(rows.length, 0)}</strong></div>
        <div className="card"><span>Data source</span><strong style={{fontSize:14}}>/api/v1/{config.endpoint}</strong></div>
        <div className="card"><span>Scope</span><strong style={{fontSize:14}}>Tjekatjeka Holdings</strong></div>
      </section>
      <section className="card table-card">
        {rows.length ? <div className="table-wrap"><table className="data-table"><thead><tr>{config.columns.map(([key,label]) => <th key={key}>{label}</th>)}</tr></thead><tbody>{rows.map((item, index) => <tr key={String(item.id ?? index)}>{config.columns.map(([key,,kind]) => <td key={key}>{display(item[key], kind)}</td>)}</tr>)}</tbody></table></div> : <div className="empty-state"><strong>No records yet</strong>Once transactions are entered through the Tjekatjeka API, they will appear in this live management table.</div>}
      </section>
    </Shell>
  );
}
