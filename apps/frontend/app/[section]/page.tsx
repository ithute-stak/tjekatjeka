import { notFound } from "next/navigation";
import { CreateRecordForm } from "@/components/CreateRecordForm";
import { Shell } from "@/components/Shell";
import { apiGet, money, number } from "@/lib/api";

type Row = Record<string, unknown>;
type Branch = { id: string; code: string; name: string; division: string };
type Material = { id: string; branch_id?: string | null; name: string; unit: string; quantity_on_hand?: number | string };
type Product = { id: string; branch_id: string; name: string; unit: string; selling_price?: number | string; quantity_on_hand?: number | string };
type Vehicle = { id: string; registration: string; make_model: string; odometer_km?: number | string };
type SectionConfig = { title: string; copy: string; endpoint: string; note: string; columns: [string, string, "money" | "number" | "text"][] };

const sections: Record<string, SectionConfig> = {
  inventory: { title: "Inventory", copy: "Control every production input by unit, stock balance, reorder level and average unit cost.", endpoint: "materials", note: "Brick production consumes material stock automatically. Purchases increase it and recalculate weighted average unit cost.", columns: [["name","Material","text"],["category","Category","text"],["unit","Unit","text"],["quantity_on_hand","On hand","number"],["reorder_level","Reorder level","number"],["average_unit_cost","Avg. unit cost","money"]] },
  purchasing: { title: "Purchasing", copy: "Record supplier purchases across both divisions and control the cost entering Tjekatjeka inventory.", endpoint: "purchases", note: "Material-linked purchases automatically increase raw-material stock and preserve supplier/reference information for audit.", columns: [["purchase_date","Date","text"],["supplier_name","Supplier","text"],["item_name","Item","text"],["reference","Reference","text"],["quantity","Quantity","number"],["unit_cost","Unit cost","money"],["total_cost","Total","money"]] },
  production: { title: "Brick Production", copy: "Post real production batches with material consumption, rejects, good output and cost per saleable brick.", endpoint: "production", note: "A batch cannot consume more material than is in stock. Good output is added to finished-goods stock only after costing succeeds.", columns: [["production_date","Date","text"],["batch_no","Batch","text"],["produced_quantity","Produced","number"],["rejected_quantity","Rejected","number"],["good_quantity","Good bricks","number"],["total_cost","Batch cost","money"],["cost_per_good_unit","Cost / brick","money"]] },
  aluminium: { title: "Aluminium & Glass", copy: "Create customer jobs and monitor quotation value, direct costs and job-level profitability.", endpoint: "aluminium-jobs", note: "Material, labour, transport and other cost are compared with the quoted value so management can see profit by job.", columns: [["job_no","Job","text"],["customer_name","Customer","text"],["description","Description","text"],["status","Status","text"],["quote_amount","Quoted","money"],["total_cost","Cost","money"],["profit","Profit","money"]] },
  sales: { title: "Sales", copy: "Record finished-goods sales, customer value, delivery cost and revenue by branch.", endpoint: "sales", note: "Brick sales cannot exceed finished stock. Selling a product reduces its available quantity immediately.", columns: [["sale_date","Date","text"],["customer_name","Customer","text"],["quantity","Quantity","number"],["unit_price","Unit price","money"],["delivery_cost","Delivery","money"],["total_amount","Total","money"]] },
  finance: { title: "Finance & Expenses", copy: "Capture operating costs by branch, category and date instead of mixing every cost into one company total.", endpoint: "expenses", note: "The executive dashboard combines expenses with purchasing, fuel and maintenance to show tracked operating spend.", columns: [["expense_date","Date","text"],["category","Category","text"],["description","Description","text"],["reference","Reference","text"],["amount","Amount","money"]] },
  fleet: { title: "Fleet", copy: "Manage trucks and smaller vehicles, fuel consumption, odometer control and maintenance costs.", endpoint: "vehicles", note: "Fuel logs reject backwards odometer readings. Maintenance and fuel costs feed the management dashboard separately from branch purchasing.", columns: [["registration","Registration","text"],["make_model","Make / Model","text"],["vehicle_type","Type","text"],["odometer_km","Odometer km","number"],["status","Status","text"]] },
};

function display(value: unknown, kind: "money" | "number" | "text") {
  if (value === null || value === undefined || value === "") return "—";
  if (kind === "money") return money(value);
  if (kind === "number") return number(value);
  return String(value).replaceAll("_", " ");
}

function DataTable({ rows, columns, empty = "No records yet." }: { rows: Row[]; columns: SectionConfig["columns"]; empty?: string }) {
  return rows.length ? (
    <div className="table-wrap"><table className="data-table"><thead><tr>{columns.map(([key,label]) => <th key={key}>{label}</th>)}</tr></thead><tbody>{rows.map((item, index) => <tr key={String(item.id ?? index)}>{columns.map(([key,,kind]) => <td key={key}>{display(item[key], kind)}</td>)}</tr>)}</tbody></table></div>
  ) : <div className="empty-state"><strong>{empty}</strong>Use the entry form above to begin recording live operations.</div>;
}

export default async function SectionPage({ params }: { params: Promise<{ section: string }> }) {
  const { section } = await params;
  const config = sections[section];
  if (!config) notFound();

  const [rows, branches, materials, products, vehicles, fuelRows, maintenanceRows] = await Promise.all([
    apiGet<Row[]>(config.endpoint, []),
    apiGet<Branch[]>("branches", []),
    apiGet<Material[]>("materials", []),
    apiGet<Product[]>("products", []),
    apiGet<Vehicle[]>("vehicles", []),
    section === "fleet" ? apiGet<Row[]>("fuel", []) : Promise.resolve([] as Row[]),
    section === "fleet" ? apiGet<Row[]>("maintenance", []) : Promise.resolve([] as Row[]),
  ]);

  return (
    <Shell active={`/${section}`}>
      <section className="page-head">
        <div><span className="eyebrow">Operations module</span><h1>{config.title}</h1><p>{config.copy}</p></div>
        <span className="action-button">Live operations</span>
      </section>
      <div className="note">{config.note}</div>
      <section className="metric-strip">
        <div className="card"><span>Records loaded</span><strong>{number(rows.length, 0)}</strong></div>
        <div className="card"><span>Business rule</span><strong style={{fontSize:14}}>Validated by FastAPI</strong></div>
        <div className="card"><span>Scope</span><strong style={{fontSize:14}}>Tjekatjeka Holdings</strong></div>
      </section>

      <CreateRecordForm section={section} branches={branches} materials={materials} products={products} vehicles={vehicles} />

      <section className="card table-card record-table">
        <div className="table-title"><div><span className="eyebrow">History</span><h2>{config.title} records</h2></div><span>{rows.length} loaded</span></div>
        <DataTable rows={rows} columns={config.columns} />
      </section>

      {section === "fleet" ? (
        <div className="fleet-history-grid">
          <section className="card table-card"><div className="table-title"><div><span className="eyebrow">Running cost</span><h2>Fuel log</h2></div><span>{fuelRows.length} entries</span></div><DataTable rows={fuelRows} columns={[["log_date","Date","text"],["litres","Litres","number"],["price_per_litre","Price / L","money"],["total_cost","Total","money"],["odometer_km","Odometer","number"],["purpose","Purpose","text"]]} empty="No fuel entries yet." /></section>
          <section className="card table-card"><div className="table-title"><div><span className="eyebrow">Mechanical cost</span><h2>Maintenance log</h2></div><span>{maintenanceRows.length} entries</span></div><DataTable rows={maintenanceRows} columns={[["service_date","Date","text"],["description","Work","text"],["cost","Cost","money"],["odometer_km","Odometer","number"]]} empty="No maintenance entries yet." /></section>
        </div>
      ) : null}
    </Shell>
  );
}
