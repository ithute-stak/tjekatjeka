import { Shell } from "@/components/Shell";
import { CommercialControl } from "@/components/CommercialControl";
import { apiGet, money } from "@/lib/api";

type Customer={id:string;name:string};
type Branch={id:string;name:string};
type Quote={id:string;quote_no:string;customer_name?:string;status:string;total_amount:number|string;converted_invoice_id?:string|null};

export default async function CommercialPage(){
 const [customers,branches,quotes]=await Promise.all([apiGet<Customer[]>("customers",[]),apiGet<Branch[]>("branches",[]),apiGet<Quote[]>("quotes",[])]);
 const pipeline=quotes.filter(x=>!x.converted_invoice_id&&!['rejected','expired'].includes(x.status));
 const value=pipeline.reduce((sum,x)=>sum+Number(x.total_amount||0),0);
 return <Shell active="/commercial">
  <section className="page-head"><div><span className="eyebrow">Commercial control</span><h1>Quotations → Invoices</h1><p>Create customer quotations with line items, manage their status, and convert accepted work into receivables without retyping the transaction.</p></div></section>
  <section className="metric-strip"><div className="card"><span>Open pipeline</span><strong>{pipeline.length}</strong></div><div className="card"><span>Pipeline value</span><strong>{money(value)}</strong></div><div className="card"><span>Converted</span><strong>{quotes.filter(x=>Boolean(x.converted_invoice_id)).length}</strong></div></section>
  <CommercialControl customers={customers} branches={branches} quotes={quotes}/>
 </Shell>;
}
