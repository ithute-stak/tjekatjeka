"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

type Party = { id: string; name: string };
type Invoice = { id: string; customer_id: string; invoice_no: string; balance?: number | string };
type Bill = { id: string; supplier_id: string; bill_no: string; balance?: number | string };
type Branch = { id: string; name: string };

type Props = { customers: Party[]; suppliers: Party[]; invoices: Invoice[]; bills: Bill[]; branches: Branch[] };

type Mode = "customer" | "customer-invoice" | "customer-payment" | "supplier" | "supplier-bill" | "supplier-payment";

const today = () => new Date().toISOString().slice(0, 10);
const text = (data: FormData, key: string) => String(data.get(key) ?? "").trim();
const optional = (data: FormData, key: string) => text(data, key) || null;
const numeric = (data: FormData, key: string) => Number(data.get(key) ?? 0);

async function send(endpoint: string, body: unknown) {
  const response = await fetch(`/api/backend/${endpoint}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  const payload = await response.json().catch(() => null);
  if (!response.ok) throw new Error(typeof payload?.detail === "string" ? payload.detail : "Could not save this account entry.");
}

export function AccountsControl({ customers, suppliers, invoices, bills, branches }: Props) {
  const router = useRouter();
  const [mode, setMode] = useState<Mode>("customer-invoice");
  const [busy, setBusy] = useState(false);
  const [feedback, setFeedback] = useState("");
  const [customerId, setCustomerId] = useState("");
  const [supplierId, setSupplierId] = useState("");

  async function submit(event: FormEvent<HTMLFormElement>, endpoint: string, body: (data: FormData) => unknown, success: string) {
    event.preventDefault(); setBusy(true); setFeedback("");
    try { await send(endpoint, body(new FormData(event.currentTarget))); event.currentTarget.reset(); setFeedback(success); router.refresh(); }
    catch (error) { setFeedback(error instanceof Error ? error.message : "Could not save this entry."); }
    finally { setBusy(false); }
  }

  const customerInvoices = invoices.filter((item) => !customerId || item.customer_id === customerId);
  const supplierBills = bills.filter((item) => !supplierId || item.supplier_id === supplierId);

  return (
    <section className="card entry-card">
      <div className="entry-head"><div><span className="eyebrow">Accounts control</span><h2>Post receivables and payables</h2></div></div>
      <div className="segmented wrap-segmented">
        {[
          ["customer-invoice","Customer invoice"],["customer-payment","Customer payment"],["supplier-bill","Supplier bill"],["supplier-payment","Supplier payment"],["customer","New customer"],["supplier","New supplier"],
        ].map(([value,label]) => <button key={value} type="button" className={mode === value ? "active" : ""} onClick={() => setMode(value as Mode)}>{label}</button>)}
      </div>

      {mode === "customer" ? <form className="entry-form" onSubmit={(e) => submit(e, "customers", (d) => ({ name:text(d,"name"), phone:optional(d,"phone"), email:optional(d,"email") }), "Customer created.")}>
        <label>Customer name<input name="name" required /></label><label>Phone<input name="phone" /></label><label>Email<input name="email" type="email" /></label><div className="form-actions"><button className="action-button" disabled={busy}>Create customer</button></div>
      </form> : null}

      {mode === "supplier" ? <form className="entry-form" onSubmit={(e) => submit(e, "suppliers", (d) => ({ name:text(d,"name"), phone:optional(d,"phone"), email:optional(d,"email") }), "Supplier created.")}>
        <label>Supplier name<input name="name" required /></label><label>Phone<input name="phone" /></label><label>Email<input name="email" type="email" /></label><div className="form-actions"><button className="action-button" disabled={busy}>Create supplier</button></div>
      </form> : null}

      {mode === "customer-invoice" ? <form className="entry-form" onSubmit={(e) => submit(e, "customer-invoices", (d) => ({ customer_id:text(d,"customer_id"), branch_id:optional(d,"branch_id"), invoice_no:text(d,"invoice_no"), description:text(d,"description"), amount:numeric(d,"amount"), invoice_date:text(d,"invoice_date"), due_date:optional(d,"due_date") }), "Customer invoice posted.")}>
        <label>Customer<select name="customer_id" required defaultValue=""><option value="">Select customer</option>{customers.map((x)=><option key={x.id} value={x.id}>{x.name}</option>)}</select></label>
        <label>Branch<select name="branch_id" defaultValue=""><option value="">Company / shared</option>{branches.map((x)=><option key={x.id} value={x.id}>{x.name}</option>)}</select></label>
        <label>Invoice no.<input name="invoice_no" required placeholder="INV-2026-001" /></label><label>Amount (M)<input name="amount" type="number" min="0.01" step="0.01" required /></label>
        <label className="span-2">Description<input name="description" required placeholder="Brick sale / aluminium installation" /></label><label>Invoice date<input name="invoice_date" type="date" defaultValue={today()} required /></label><label>Due date<input name="due_date" type="date" /></label>
        <div className="form-actions"><button className="action-button" disabled={busy}>Post invoice</button></div>
      </form> : null}

      {mode === "customer-payment" ? <form className="entry-form" onSubmit={(e) => submit(e, "customer-payments", (d) => ({ customer_id:text(d,"customer_id"), invoice_id:optional(d,"invoice_id"), amount:numeric(d,"amount"), method:text(d,"method"), reference:optional(d,"reference"), payment_date:text(d,"payment_date"), notes:optional(d,"notes") }), "Customer payment recorded.")}>
        <label>Customer<select name="customer_id" required value={customerId} onChange={(e)=>setCustomerId(e.target.value)}><option value="">Select customer</option>{customers.map((x)=><option key={x.id} value={x.id}>{x.name}</option>)}</select></label>
        <label>Invoice<select name="invoice_id" defaultValue=""><option value="">Unallocated payment</option>{customerInvoices.map((x)=><option key={x.id} value={x.id}>{x.invoice_no} · balance M{x.balance ?? 0}</option>)}</select></label>
        <label>Amount (M)<input name="amount" type="number" min="0.01" step="0.01" required /></label><label>Method<select name="method" defaultValue="bank"><option value="bank">Bank</option><option value="cash">Cash</option><option value="mobile_money">Mobile money</option><option value="card">Card</option></select></label>
        <label>Reference<input name="reference" /></label><label>Payment date<input name="payment_date" type="date" defaultValue={today()} required /></label><label className="span-2">Notes<input name="notes" /></label>
        <div className="form-actions"><button className="action-button" disabled={busy}>Record payment</button></div>
      </form> : null}

      {mode === "supplier-bill" ? <form className="entry-form" onSubmit={(e) => submit(e, "supplier-bills", (d) => ({ supplier_id:text(d,"supplier_id"), branch_id:optional(d,"branch_id"), bill_no:text(d,"bill_no"), description:text(d,"description"), amount:numeric(d,"amount"), bill_date:text(d,"bill_date"), due_date:optional(d,"due_date") }), "Supplier bill posted.")}>
        <label>Supplier<select name="supplier_id" required defaultValue=""><option value="">Select supplier</option>{suppliers.map((x)=><option key={x.id} value={x.id}>{x.name}</option>)}</select></label><label>Branch<select name="branch_id" defaultValue=""><option value="">Company / shared</option>{branches.map((x)=><option key={x.id} value={x.id}>{x.name}</option>)}</select></label>
        <label>Bill no.<input name="bill_no" required /></label><label>Amount (M)<input name="amount" type="number" min="0.01" step="0.01" required /></label><label className="span-2">Description<input name="description" required /></label><label>Bill date<input name="bill_date" type="date" defaultValue={today()} required /></label><label>Due date<input name="due_date" type="date" /></label>
        <div className="form-actions"><button className="action-button" disabled={busy}>Post supplier bill</button></div>
      </form> : null}

      {mode === "supplier-payment" ? <form className="entry-form" onSubmit={(e) => submit(e, "supplier-payments", (d) => ({ supplier_id:text(d,"supplier_id"), bill_id:optional(d,"bill_id"), amount:numeric(d,"amount"), method:text(d,"method"), reference:optional(d,"reference"), payment_date:text(d,"payment_date"), notes:optional(d,"notes") }), "Supplier payment recorded.")}>
        <label>Supplier<select name="supplier_id" required value={supplierId} onChange={(e)=>setSupplierId(e.target.value)}><option value="">Select supplier</option>{suppliers.map((x)=><option key={x.id} value={x.id}>{x.name}</option>)}</select></label><label>Bill<select name="bill_id" defaultValue=""><option value="">Unallocated payment</option>{supplierBills.map((x)=><option key={x.id} value={x.id}>{x.bill_no} · balance M{x.balance ?? 0}</option>)}</select></label>
        <label>Amount (M)<input name="amount" type="number" min="0.01" step="0.01" required /></label><label>Method<select name="method" defaultValue="bank"><option value="bank">Bank</option><option value="cash">Cash</option><option value="mobile_money">Mobile money</option></select></label><label>Reference<input name="reference" /></label><label>Payment date<input name="payment_date" type="date" defaultValue={today()} required /></label><label className="span-2">Notes<input name="notes" /></label>
        <div className="form-actions"><button className="action-button" disabled={busy}>Record supplier payment</button></div>
      </form> : null}

      {feedback ? <div className="form-feedback success">{feedback}</div> : null}
    </section>
  );
}
