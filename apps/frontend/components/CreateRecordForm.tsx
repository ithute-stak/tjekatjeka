"use client";

import { FormEvent, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

type Branch = { id: string; code: string; name: string; division: string };
type Material = { id: string; branch_id?: string | null; name: string; unit: string; quantity_on_hand?: number | string };
type Product = { id: string; branch_id: string; name: string; unit: string; selling_price?: number | string; quantity_on_hand?: number | string };
type Vehicle = { id: string; registration: string; make_model: string; odometer_km?: number | string };

type Props = {
  section: string;
  branches: Branch[];
  materials: Material[];
  products: Product[];
  vehicles: Vehicle[];
};

type Feedback = { kind: "success" | "error"; text: string } | null;
type ProductionInput = { material_id: string; quantity: string };

const today = () => new Date().toISOString().slice(0, 10);
const text = (data: FormData, key: string) => String(data.get(key) ?? "").trim();
const optional = (data: FormData, key: string) => text(data, key) || null;
const numeric = (data: FormData, key: string, fallback = 0) => {
  const value = Number(data.get(key));
  return Number.isFinite(value) ? value : fallback;
};

async function post(endpoint: string, body: unknown) {
  const response = await fetch(`/api/backend/${endpoint}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = payload?.detail;
    const message = Array.isArray(detail)
      ? detail.map((item: { msg?: string }) => item.msg).filter(Boolean).join("; ")
      : typeof detail === "string"
        ? detail
        : "The record could not be saved.";
    throw new Error(message);
  }
  return payload;
}

function BranchSelect({ branches, name = "branch_id", required = false, onChange }: { branches: Branch[]; name?: string; required?: boolean; onChange?: (value: string) => void }) {
  return (
    <label>Branch
      <select name={name} required={required} defaultValue="" onChange={(event) => onChange?.(event.target.value)}>
        <option value="">{required ? "Select branch" : "Company / shared"}</option>
        {branches.map((branch) => <option key={branch.id} value={branch.id}>{branch.name}</option>)}
      </select>
    </label>
  );
}

export function CreateRecordForm({ section, branches, materials, products, vehicles }: Props) {
  const router = useRouter();
  const [feedback, setFeedback] = useState<Feedback>(null);
  const [busy, setBusy] = useState(false);
  const [branchId, setBranchId] = useState("");
  const [inventoryMode, setInventoryMode] = useState<"create" | "adjust">("create");
  const [fleetMode, setFleetMode] = useState<"vehicle" | "fuel" | "maintenance">("vehicle");
  const [inputs, setInputs] = useState<ProductionInput[]>([{ material_id: "", quantity: "" }]);

  const branchProducts = useMemo(() => products.filter((item) => !branchId || item.branch_id === branchId), [products, branchId]);
  const branchMaterials = useMemo(() => materials.filter((item) => !branchId || !item.branch_id || item.branch_id === branchId), [materials, branchId]);

  async function submit(event: FormEvent<HTMLFormElement>, endpoint: string, build: (data: FormData) => unknown, success: string) {
    event.preventDefault();
    setBusy(true);
    setFeedback(null);
    const form = event.currentTarget;
    try {
      await post(endpoint, build(new FormData(form)));
      setFeedback({ kind: "success", text: success });
      form.reset();
      router.refresh();
    } catch (error) {
      setFeedback({ kind: "error", text: error instanceof Error ? error.message : "The record could not be saved." });
    } finally {
      setBusy(false);
    }
  }

  const feedbackNode = feedback ? <div className={`form-feedback ${feedback.kind}`}>{feedback.text}</div> : null;
  const submitButton = (label: string) => <button className="action-button" disabled={busy} type="submit">{busy ? "Saving…" : label}</button>;

  if (section === "inventory") {
    return (
      <section className="card entry-card">
        <div className="entry-head"><div><span className="eyebrow">Stock control</span><h2>Update inventory</h2></div><div className="segmented"><button type="button" className={inventoryMode === "create" ? "active" : ""} onClick={() => setInventoryMode("create")}>New material</button><button type="button" className={inventoryMode === "adjust" ? "active" : ""} onClick={() => setInventoryMode("adjust")}>Stock adjustment</button></div></div>
        {inventoryMode === "create" ? (
          <form className="entry-form" onSubmit={(event) => submit(event, "materials", (data) => ({ branch_id: optional(data, "branch_id"), code: text(data, "code"), name: text(data, "name"), category: text(data, "category"), unit: text(data, "unit"), reorder_level: numeric(data, "reorder_level") }), "Material created.") }>
            <BranchSelect branches={branches} />
            <label>Material code<input name="code" required placeholder="CEMENT-50KG" /></label>
            <label>Material name<input name="name" required placeholder="50kg Cement" /></label>
            <label>Category<input name="category" required placeholder="Cement / sand / glass" /></label>
            <label>Unit<input name="unit" required placeholder="bags, tonnes, litres, m²" /></label>
            <label>Reorder level<input name="reorder_level" type="number" min="0" step="0.001" defaultValue="0" /></label>
            {feedbackNode}<div className="form-actions">{submitButton("Create material")}</div>
          </form>
        ) : (
          <form className="entry-form" onSubmit={(event) => {
            const data = new FormData(event.currentTarget);
            const materialId = text(data, "material_id");
            return submit(event, `materials/${materialId}/adjust`, (fresh) => ({ quantity_delta: numeric(fresh, "quantity_delta"), reference: optional(fresh, "reference"), notes: optional(fresh, "notes") }), "Stock adjusted.");
          }}>
            <label className="span-2">Material<select name="material_id" required defaultValue=""><option value="">Select material</option>{materials.map((item) => <option key={item.id} value={item.id}>{item.name} · {item.quantity_on_hand ?? 0} {item.unit}</option>)}</select></label>
            <label>Quantity change<input name="quantity_delta" type="number" step="0.001" required placeholder="Use - for stock out" /></label>
            <label>Reference<input name="reference" placeholder="Stock count / transfer" /></label>
            <label className="span-2">Notes<textarea name="notes" rows={2} placeholder="Reason for adjustment" /></label>
            {feedbackNode}<div className="form-actions">{submitButton("Apply adjustment")}</div>
          </form>
        )}
      </section>
    );
  }

  if (section === "purchasing") {
    return (
      <section className="card entry-card"><div className="entry-head"><div><span className="eyebrow">Procurement</span><h2>Record purchase</h2></div><span className="entry-hint">Linked materials increase stock automatically</span></div>
        <form className="entry-form" onSubmit={(event) => submit(event, "purchases", (data) => ({ branch_id: optional(data, "branch_id"), material_id: optional(data, "material_id"), supplier_name: text(data, "supplier_name"), item_name: text(data, "item_name"), category: text(data, "category"), quantity: numeric(data, "quantity"), unit: text(data, "unit"), unit_cost: numeric(data, "unit_cost"), reference: optional(data, "reference"), purchase_date: text(data, "purchase_date") }), "Purchase recorded and stock updated where linked.") }>
          <BranchSelect branches={branches} />
          <label>Inventory material<select name="material_id" defaultValue=""><option value="">Expense-only / not stocked</option>{materials.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
          <label>Supplier<input name="supplier_name" required placeholder="Supplier name" /></label>
          <label>Item<input name="item_name" required placeholder="Rough sand / cement / glass" /></label>
          <label>Category<input name="category" required placeholder="Raw materials" /></label>
          <label>Quantity<input name="quantity" required type="number" min="0.0001" step="0.001" /></label>
          <label>Unit<input name="unit" required placeholder="tonnes / bags / m²" /></label>
          <label>Unit cost (M)<input name="unit_cost" required type="number" min="0" step="0.01" /></label>
          <label>Reference<input name="reference" placeholder="Invoice / receipt no." /></label>
          <label>Purchase date<input name="purchase_date" required type="date" defaultValue={today()} /></label>
          {feedbackNode}<div className="form-actions">{submitButton("Record purchase")}</div>
        </form>
      </section>
    );
  }

  if (section === "production") {
    return (
      <section className="card entry-card"><div className="entry-head"><div><span className="eyebrow">Manufacturing</span><h2>Create production batch</h2></div><span className="entry-hint">Raw materials are consumed and good bricks enter finished stock</span></div>
        <form className="entry-form" onSubmit={(event) => submit(event, "production", (data) => ({ branch_id: text(data, "branch_id"), product_id: text(data, "product_id"), batch_no: text(data, "batch_no"), produced_quantity: numeric(data, "produced_quantity"), rejected_quantity: numeric(data, "rejected_quantity"), electricity_cost: numeric(data, "electricity_cost"), water_cost: numeric(data, "water_cost"), labour_cost: numeric(data, "labour_cost"), machine_cost: numeric(data, "machine_cost"), fuel_cost: numeric(data, "fuel_cost"), other_cost: numeric(data, "other_cost"), notes: optional(data, "notes"), production_date: text(data, "production_date"), inputs: inputs.map((item) => ({ material_id: item.material_id, quantity: Number(item.quantity) })) }), "Production batch posted and inventory updated.") }>
          <BranchSelect branches={branches} required onChange={setBranchId} />
          <label>Finished product<select name="product_id" required defaultValue=""><option value="">Select brick product</option>{branchProducts.map((item) => <option key={item.id} value={item.id}>{item.name} · stock {item.quantity_on_hand ?? 0}</option>)}</select></label>
          <label>Batch number<input name="batch_no" required placeholder="BR-2026-001" /></label>
          <label>Production date<input name="production_date" required type="date" defaultValue={today()} /></label>
          <label>Produced quantity<input name="produced_quantity" required type="number" min="0.0001" step="1" /></label>
          <label>Rejected quantity<input name="rejected_quantity" type="number" min="0" step="1" defaultValue="0" /></label>
          <div className="span-2 input-builder"><div className="builder-head"><strong>Materials consumed</strong><button type="button" onClick={() => setInputs((items) => [...items, { material_id: "", quantity: "" }])}>+ Add material</button></div>{inputs.map((item, index) => <div className="input-row" key={index}><select required value={item.material_id} onChange={(event) => setInputs((items) => items.map((value, i) => i === index ? { ...value, material_id: event.target.value } : value))}><option value="">Select material</option>{branchMaterials.map((material) => <option key={material.id} value={material.id}>{material.name} · {material.quantity_on_hand ?? 0} {material.unit}</option>)}</select><input required type="number" min="0.0001" step="0.001" placeholder="Quantity used" value={item.quantity} onChange={(event) => setInputs((items) => items.map((value, i) => i === index ? { ...value, quantity: event.target.value } : value))} />{inputs.length > 1 ? <button type="button" className="remove-button" onClick={() => setInputs((items) => items.filter((_, i) => i !== index))}>Remove</button> : null}</div>)}</div>
          <label>Electricity cost (M)<input name="electricity_cost" type="number" min="0" step="0.01" defaultValue="0" /></label>
          <label>Water cost (M)<input name="water_cost" type="number" min="0" step="0.01" defaultValue="0" /></label>
          <label>Labour cost (M)<input name="labour_cost" type="number" min="0" step="0.01" defaultValue="0" /></label>
          <label>Machine cost (M)<input name="machine_cost" type="number" min="0" step="0.01" defaultValue="0" /></label>
          <label>Fuel cost (M)<input name="fuel_cost" type="number" min="0" step="0.01" defaultValue="0" /></label>
          <label>Other cost (M)<input name="other_cost" type="number" min="0" step="0.01" defaultValue="0" /></label>
          <label className="span-2">Notes<textarea name="notes" rows={2} /></label>
          {feedbackNode}<div className="form-actions">{submitButton("Post production batch")}</div>
        </form>
      </section>
    );
  }

  if (section === "aluminium") {
    return (
      <section className="card entry-card"><div className="entry-head"><div><span className="eyebrow">Job costing</span><h2>Create aluminium / glass job</h2></div><span className="entry-hint">Quoted value is compared with direct job costs</span></div>
        <form className="entry-form" onSubmit={(event) => submit(event, "aluminium-jobs", (data) => ({ branch_id: text(data, "branch_id"), job_no: text(data, "job_no"), customer_name: text(data, "customer_name"), description: text(data, "description"), quote_amount: numeric(data, "quote_amount"), material_cost: numeric(data, "material_cost"), labour_cost: numeric(data, "labour_cost"), transport_cost: numeric(data, "transport_cost"), other_cost: numeric(data, "other_cost"), status: text(data, "status"), opened_date: text(data, "opened_date"), due_date: optional(data, "due_date") }), "Aluminium job created.") }>
          <BranchSelect branches={branches} required />
          <label>Job number<input name="job_no" required placeholder="AL-2026-001" /></label>
          <label>Customer<input name="customer_name" required /></label>
          <label>Status<select name="status" defaultValue="quoted"><option value="quoted">Quoted</option><option value="approved">Approved</option><option value="fabrication">Fabrication</option><option value="installation">Installation</option><option value="completed">Completed</option></select></label>
          <label className="span-2">Job description<textarea name="description" required rows={3} placeholder="Doors, windows, glass type, site details…" /></label>
          <label>Quote amount (M)<input name="quote_amount" type="number" min="0" step="0.01" defaultValue="0" /></label>
          <label>Material cost (M)<input name="material_cost" type="number" min="0" step="0.01" defaultValue="0" /></label>
          <label>Labour cost (M)<input name="labour_cost" type="number" min="0" step="0.01" defaultValue="0" /></label>
          <label>Transport cost (M)<input name="transport_cost" type="number" min="0" step="0.01" defaultValue="0" /></label>
          <label>Other cost (M)<input name="other_cost" type="number" min="0" step="0.01" defaultValue="0" /></label>
          <label>Opened date<input name="opened_date" type="date" required defaultValue={today()} /></label>
          <label>Due date<input name="due_date" type="date" /></label>
          {feedbackNode}<div className="form-actions">{submitButton("Create job")}</div>
        </form>
      </section>
    );
  }

  if (section === "sales") {
    return (
      <section className="card entry-card"><div className="entry-head"><div><span className="eyebrow">Revenue</span><h2>Record product sale</h2></div><span className="entry-hint">Finished stock is reduced after a valid sale</span></div>
        <form className="entry-form" onSubmit={(event) => submit(event, "sales", (data) => ({ branch_id: text(data, "branch_id"), product_id: text(data, "product_id"), customer_name: text(data, "customer_name"), quantity: numeric(data, "quantity"), unit_price: numeric(data, "unit_price"), delivery_cost: numeric(data, "delivery_cost"), reference: optional(data, "reference"), sale_date: text(data, "sale_date") }), "Sale recorded and finished stock reduced.") }>
          <BranchSelect branches={branches} required onChange={setBranchId} />
          <label>Product<select name="product_id" required defaultValue=""><option value="">Select product</option>{branchProducts.map((item) => <option key={item.id} value={item.id}>{item.name} · {item.quantity_on_hand ?? 0} {item.unit}</option>)}</select></label>
          <label>Customer<input name="customer_name" required /></label>
          <label>Quantity<input name="quantity" type="number" min="0.0001" step="0.001" required /></label>
          <label>Unit price (M)<input name="unit_price" type="number" min="0.01" step="0.01" required /></label>
          <label>Delivery cost (M)<input name="delivery_cost" type="number" min="0" step="0.01" defaultValue="0" /></label>
          <label>Reference<input name="reference" placeholder="Invoice / order no." /></label>
          <label>Sale date<input name="sale_date" type="date" required defaultValue={today()} /></label>
          {feedbackNode}<div className="form-actions">{submitButton("Record sale")}</div>
        </form>
      </section>
    );
  }

  if (section === "finance") {
    return (
      <section className="card entry-card"><div className="entry-head"><div><span className="eyebrow">Cost control</span><h2>Record operating expense</h2></div><span className="entry-hint">Assign expenses to a division or keep them company-wide</span></div>
        <form className="entry-form" onSubmit={(event) => submit(event, "expenses", (data) => ({ branch_id: optional(data, "branch_id"), category: text(data, "category"), description: text(data, "description"), amount: numeric(data, "amount"), reference: optional(data, "reference"), expense_date: text(data, "expense_date") }), "Expense recorded.") }>
          <BranchSelect branches={branches} />
          <label>Category<input name="category" required placeholder="Electricity / salaries / tools" /></label>
          <label className="span-2">Description<input name="description" required /></label>
          <label>Amount (M)<input name="amount" type="number" min="0.01" step="0.01" required /></label>
          <label>Reference<input name="reference" placeholder="Receipt / voucher" /></label>
          <label>Expense date<input name="expense_date" type="date" required defaultValue={today()} /></label>
          {feedbackNode}<div className="form-actions">{submitButton("Record expense")}</div>
        </form>
      </section>
    );
  }

  if (section === "fleet") {
    return (
      <section className="card entry-card">
        <div className="entry-head"><div><span className="eyebrow">Fleet operations</span><h2>Update fleet</h2></div><div className="segmented"><button type="button" className={fleetMode === "vehicle" ? "active" : ""} onClick={() => setFleetMode("vehicle")}>Vehicle</button><button type="button" className={fleetMode === "fuel" ? "active" : ""} onClick={() => setFleetMode("fuel")}>Fuel</button><button type="button" className={fleetMode === "maintenance" ? "active" : ""} onClick={() => setFleetMode("maintenance")}>Maintenance</button></div></div>
        {fleetMode === "vehicle" ? <form className="entry-form" onSubmit={(event) => submit(event, "vehicles", (data) => ({ branch_id: optional(data, "branch_id"), registration: text(data, "registration"), make_model: text(data, "make_model"), vehicle_type: text(data, "vehicle_type"), status: text(data, "status"), odometer_km: numeric(data, "odometer_km") }), "Vehicle added.") }><BranchSelect branches={branches} /><label>Registration<input name="registration" required /></label><label>Make & model<input name="make_model" required /></label><label>Vehicle type<input name="vehicle_type" required placeholder="Truck / bakkie / car" /></label><label>Status<select name="status" defaultValue="active"><option value="active">Active</option><option value="maintenance">Maintenance</option><option value="inactive">Inactive</option></select></label><label>Odometer km<input name="odometer_km" type="number" min="0" step="0.1" defaultValue="0" /></label>{feedbackNode}<div className="form-actions">{submitButton("Add vehicle")}</div></form> : null}
        {fleetMode === "fuel" ? <form className="entry-form" onSubmit={(event) => submit(event, "fuel", (data) => ({ vehicle_id: text(data, "vehicle_id"), litres: numeric(data, "litres"), price_per_litre: numeric(data, "price_per_litre"), odometer_km: numeric(data, "odometer_km"), purpose: optional(data, "purpose"), log_date: text(data, "log_date") }), "Fuel entry recorded.") }><label className="span-2">Vehicle<select name="vehicle_id" required defaultValue=""><option value="">Select vehicle</option>{vehicles.map((vehicle) => <option key={vehicle.id} value={vehicle.id}>{vehicle.registration} · {vehicle.make_model}</option>)}</select></label><label>Litres<input name="litres" type="number" min="0.001" step="0.001" required /></label><label>Price / litre (M)<input name="price_per_litre" type="number" min="0.001" step="0.001" required /></label><label>Odometer km<input name="odometer_km" type="number" min="0" step="0.1" required /></label><label>Purpose<input name="purpose" placeholder="Brick delivery / site visit" /></label><label>Fuel date<input name="log_date" type="date" required defaultValue={today()} /></label>{feedbackNode}<div className="form-actions">{submitButton("Record fuel")}</div></form> : null}
        {fleetMode === "maintenance" ? <form className="entry-form" onSubmit={(event) => submit(event, "maintenance", (data) => ({ vehicle_id: text(data, "vehicle_id"), description: text(data, "description"), cost: numeric(data, "cost"), odometer_km: numeric(data, "odometer_km"), service_date: text(data, "service_date") }), "Maintenance entry recorded.") }><label className="span-2">Vehicle<select name="vehicle_id" required defaultValue=""><option value="">Select vehicle</option>{vehicles.map((vehicle) => <option key={vehicle.id} value={vehicle.id}>{vehicle.registration} · {vehicle.make_model}</option>)}</select></label><label className="span-2">Work performed<input name="description" required placeholder="Service / tyres / repair" /></label><label>Cost (M)<input name="cost" type="number" min="0.01" step="0.01" required /></label><label>Odometer km<input name="odometer_km" type="number" min="0" step="0.1" required /></label><label>Service date<input name="service_date" type="date" required defaultValue={today()} /></label>{feedbackNode}<div className="form-actions">{submitButton("Record maintenance")}</div></form> : null}
      </section>
    );
  }

  return null;
}
