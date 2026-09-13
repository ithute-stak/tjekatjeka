import { Shell } from "@/components/Shell";
import { AccountsControl } from "@/components/AccountsControl";
import { apiGet, money } from "@/lib/api";

type Party={id:string;name:string;balance?:number|string;invoiced?:number|string;billed?:number|string;paid?:number|string};
type Invoice={id:string;customer_id:string;invoice_no:string;balance?:number|string};
type Bill={id:string;supplier_id:string;bill_no:string;balance?:number|string};
type Branch={id:string;name:string};
type Summary={receivables:number;payables:number;net_working_balance:number};

export default async function AccountsPage(){
 const [customers,suppliers,invoices,bills,branches,summary]=await Promise.all([
  apiGet<Party[]>("customers",[]),apiGet<Party[]>("suppliers",[]),apiGet<Invoice[]>("customer-invoices",[]),apiGet<Bill[]>("supplier-bills",[]),apiGet<Branch[]>("branches",[]),apiGet<Summary>("management-summary",{receivables:0,payables:0,net_working_balance:0})
 ]);
 return <Shell active="/accounts">
  <section className="page-head"><div><span className="eyebrow">Working capital</span><h1>Customer & Supplier Accounts</h1><p>Track invoices, payments, supplier bills and outstanding balances from one workspace.</p></div></section>
  <section className="metric-strip"><div className="card"><span>Receivables</span><strong>{money(summary.receivables)}</strong></div><div className="card"><span>Payables</span><strong>{money(summary.payables)}</strong></div><div className="card"><span>Net position</span><strong>{money(summary.net_working_balance)}</strong></div></section>
  <AccountsControl customers={customers} suppliers={suppliers} invoices={invoices} bills={bills} branches={branches}/>
  <section className="section-grid">
   <div className="card table-card"><div className="panel-head compact-head"><h2>Customers</h2></div><div className="table-wrap"><table className="data-table"><thead><tr><th>Name</th><th>Invoiced</th><th>Paid</th><th>Balance</th></tr></thead><tbody>{customers.map(x=><tr key={x.id}><td>{x.name}</td><td>{money(x.invoiced)}</td><td>{money(x.paid)}</td><td>{money(x.balance)}</td></tr>)}</tbody></table></div></div>
   <div className="card table-card"><div className="panel-head compact-head"><h2>Suppliers</h2></div><div className="table-wrap"><table className="data-table"><thead><tr><th>Name</th><th>Billed</th><th>Paid</th><th>Balance</th></tr></thead><tbody>{suppliers.map(x=><tr key={x.id}><td>{x.name}</td><td>{money(x.billed)}</td><td>{money(x.paid)}</td><td>{money(x.balance)}</td></tr>)}</tbody></table></div></div>
  </section>
 </Shell>;
}
