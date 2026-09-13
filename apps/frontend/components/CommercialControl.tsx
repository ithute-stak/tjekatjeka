"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

type Customer={id:string;name:string};
type Branch={id:string;name:string};
type Quote={id:string;quote_no:string;customer_name?:string;status:string;total_amount:number|string;converted_invoice_id?:string|null};
type Line={description:string;quantity:string;unit:string;unit_price:string};

async function request(path:string,method:string,body?:unknown){
 const response=await fetch(`/api/backend/${path}`,{method,headers:{"Content-Type":"application/json"},body:body===undefined?undefined:JSON.stringify(body)});
 const payload=await response.json().catch(()=>null);
 if(!response.ok) throw new Error(typeof payload?.detail==="string"?payload.detail:"Request failed");
 return payload;
}

export function CommercialControl({customers,branches,quotes}:{customers:Customer[];branches:Branch[];quotes:Quote[]}){
 const router=useRouter();
 const [lines,setLines]=useState<Line[]>([{description:"",quantity:"1",unit:"each",unit_price:""}]);
 const [message,setMessage]=useState("");
 const [busy,setBusy]=useState(false);
 async function create(event:FormEvent<HTMLFormElement>){
  event.preventDefault();setBusy(true);setMessage("");
  const form=new FormData(event.currentTarget);
  try{
   await request("quotes","POST",{branch_id:String(form.get("branch_id")||"")||null,customer_id:String(form.get("customer_id")||""),quote_no:String(form.get("quote_no")||""),description:String(form.get("description")||"")||null,tax_amount:Number(form.get("tax_amount")||0),quote_date:String(form.get("quote_date")||""),valid_until:String(form.get("valid_until")||"")||null,lines:lines.map(x=>({description:x.description,quantity:Number(x.quantity),unit:x.unit,unit_price:Number(x.unit_price)}))});
   setMessage("Quotation created.");event.currentTarget.reset();setLines([{description:"",quantity:"1",unit:"each",unit_price:""}]);router.refresh();
  }catch(error){setMessage(error instanceof Error?error.message:"Could not create quote");}finally{setBusy(false);}
 }
 async function change(id:string,status:string){try{await request(`quotes/${id}`,"PATCH",{status});router.refresh();}catch(error){setMessage(error instanceof Error?error.message:"Could not update quote");}}
 async function convert(id:string,quoteNo:string){const invoice=window.prompt("Invoice number",`INV-${quoteNo}`);if(!invoice)return;try{await request(`quotes/${id}/convert`,"POST",{invoice_no:invoice,due_date:null});setMessage("Quote converted to customer invoice.");router.refresh();}catch(error){setMessage(error instanceof Error?error.message:"Could not convert quote");}}
 return <>
  <section className="card entry-card"><div className="entry-head"><div><span className="eyebrow">Commercial workflow</span><h2>Create quotation</h2></div><span className="entry-hint">Accepted quotes can be converted directly into receivables invoices</span></div>
   <form className="entry-form" onSubmit={create}>
    <label>Customer<select name="customer_id" required defaultValue=""><option value="">Select customer</option>{customers.map(x=><option key={x.id} value={x.id}>{x.name}</option>)}</select></label>
    <label>Branch<select name="branch_id" defaultValue=""><option value="">Company / shared</option>{branches.map(x=><option key={x.id} value={x.id}>{x.name}</option>)}</select></label>
    <label>Quote number<input name="quote_no" required placeholder="Q-2026-001"/></label>
    <label>Quote date<input name="quote_date" required type="date" defaultValue={new Date().toISOString().slice(0,10)}/></label>
    <label>Valid until<input name="valid_until" type="date"/></label>
    <label>Tax amount (M)<input name="tax_amount" type="number" min="0" step="0.01" defaultValue="0"/></label>
    <label className="span-2">Description<textarea name="description" rows={2}/></label>
    <div className="span-2 input-builder"><div className="builder-head"><strong>Quotation lines</strong><button type="button" onClick={()=>setLines(v=>[...v,{description:"",quantity:"1",unit:"each",unit_price:""}])}>+ Add line</button></div>{lines.map((line,index)=><div className="quote-line" key={index}><input required placeholder="Description" value={line.description} onChange={e=>setLines(v=>v.map((x,i)=>i===index?{...x,description:e.target.value}:x))}/><input required type="number" min="0.0001" step="0.001" value={line.quantity} onChange={e=>setLines(v=>v.map((x,i)=>i===index?{...x,quantity:e.target.value}:x))}/><input required placeholder="Unit" value={line.unit} onChange={e=>setLines(v=>v.map((x,i)=>i===index?{...x,unit:e.target.value}:x))}/><input required type="number" min="0" step="0.01" placeholder="Unit price" value={line.unit_price} onChange={e=>setLines(v=>v.map((x,i)=>i===index?{...x,unit_price:e.target.value}:x))}/>{lines.length>1?<button type="button" className="remove-button" onClick={()=>setLines(v=>v.filter((_,i)=>i!==index))}>Remove</button>:null}</div>)}</div>
    {message?<div className="form-feedback success">{message}</div>:null}<div className="form-actions"><button className="action-button" disabled={busy}>{busy?"Saving…":"Create quotation"}</button></div>
   </form>
  </section>
  <section className="card table-card"><div className="table-title"><h2>Quotation pipeline</h2><span>{quotes.length} quotes</span></div><div className="table-wrap"><table className="data-table"><thead><tr><th>Quote</th><th>Customer</th><th>Status</th><th>Total</th><th>Actions</th></tr></thead><tbody>{quotes.map(q=><tr key={q.id}><td>{q.quote_no}</td><td>{q.customer_name||"—"}</td><td>{q.status}</td><td>M {Number(q.total_amount||0).toLocaleString("en-LS",{minimumFractionDigits:2})}</td><td><div className="inline-actions">{!q.converted_invoice_id?<><button onClick={()=>change(q.id,"sent")}>Sent</button><button onClick={()=>change(q.id,"accepted")}>Accept</button><button onClick={()=>convert(q.id,q.quote_no)}>Invoice</button></>:<span>Invoiced</span>}</div></td></tr>)}</tbody></table></div></section>
 </>;
}
