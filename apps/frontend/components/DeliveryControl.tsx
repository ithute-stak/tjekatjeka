"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

type Vehicle={id:string;registration:string;make_model:string};
type Branch={id:string;name:string};
type Delivery={id:string;delivery_no:string;customer_name:string;status:string;vehicle_id?:string|null;driver_name?:string|null};
const today=()=>new Date().toISOString().slice(0,10);
const text=(d:FormData,k:string)=>String(d.get(k)??"").trim();
const optional=(d:FormData,k:string)=>text(d,k)||null;
const numeric=(d:FormData,k:string)=>Number(d.get(k)??0);

async function request(endpoint:string,method:"POST"|"PATCH",body:unknown){
 const response=await fetch(`/api/backend/${endpoint}`,{method,headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});
 const payload=await response.json().catch(()=>null);
 if(!response.ok)throw new Error(typeof payload?.detail==="string"?payload.detail:"Could not save delivery.");
}

export function DeliveryControl({vehicles,branches,deliveries}:{vehicles:Vehicle[];branches:Branch[];deliveries:Delivery[]}){
 const router=useRouter();const [mode,setMode]=useState<"create"|"status">("create");const [busy,setBusy]=useState(false);const [feedback,setFeedback]=useState("");
 async function submit(e:FormEvent<HTMLFormElement>){e.preventDefault();setBusy(true);setFeedback("");const d=new FormData(e.currentTarget);try{
  if(mode==="create")await request("deliveries","POST",{branch_id:optional(d,"branch_id"),vehicle_id:optional(d,"vehicle_id"),delivery_no:text(d,"delivery_no"),customer_name:text(d,"customer_name"),destination:text(d,"destination"),load_description:text(d,"load_description"),quantity:text(d,"quantity")?numeric(d,"quantity"):null,unit:optional(d,"unit"),driver_name:optional(d,"driver_name"),delivery_fee:numeric(d,"delivery_fee"),status:"scheduled",scheduled_date:text(d,"scheduled_date"),notes:optional(d,"notes")});
  else await request(`deliveries/${text(d,"delivery_id")}`,"PATCH",{status:text(d,"status"),delivered_date:optional(d,"delivered_date"),vehicle_id:optional(d,"vehicle_id"),driver_name:optional(d,"driver_name")});
  e.currentTarget.reset();setFeedback(mode==="create"?"Delivery scheduled.":"Delivery status updated.");router.refresh();
 }catch(error){setFeedback(error instanceof Error?error.message:"Could not save delivery.");}finally{setBusy(false)}}
 return <section className="card entry-card"><div className="entry-head"><div><span className="eyebrow">Dispatch control</span><h2>Plan and update deliveries</h2></div><div className="segmented"><button type="button" className={mode==="create"?"active":""} onClick={()=>setMode("create")}>New delivery</button><button type="button" className={mode==="status"?"active":""} onClick={()=>setMode("status")}>Update status</button></div></div>
  <form className="entry-form" onSubmit={submit}>
   {mode==="create"?<>
    <label>Delivery no.<input name="delivery_no" required placeholder="DEL-2026-001"/></label><label>Customer<input name="customer_name" required/></label><label>Destination<input name="destination" required/></label><label>Branch<select name="branch_id" defaultValue=""><option value="">Company / shared</option>{branches.map(x=><option key={x.id} value={x.id}>{x.name}</option>)}</select></label>
    <label className="span-2">Load description<input name="load_description" required placeholder="5,000 6-inch blocks"/></label><label>Quantity<input name="quantity" type="number" min="0.001" step="0.001"/></label><label>Unit<input name="unit" placeholder="bricks / units"/></label>
    <label>Vehicle<select name="vehicle_id" defaultValue=""><option value="">Assign later</option>{vehicles.map(x=><option key={x.id} value={x.id}>{x.registration} · {x.make_model}</option>)}</select></label><label>Driver<input name="driver_name"/></label><label>Delivery fee (M)<input name="delivery_fee" type="number" min="0" step="0.01" defaultValue="0"/></label><label>Scheduled date<input name="scheduled_date" type="date" defaultValue={today()} required/></label><label className="span-2">Notes<input name="notes"/></label>
   </>:<>
    <label>Delivery<select name="delivery_id" required defaultValue=""><option value="">Select delivery</option>{deliveries.filter(x=>!['delivered','cancelled'].includes(x.status)).map(x=><option key={x.id} value={x.id}>{x.delivery_no} · {x.customer_name}</option>)}</select></label><label>Status<select name="status" required defaultValue="in_transit"><option value="scheduled">Scheduled</option><option value="loaded">Loaded</option><option value="in_transit">In transit</option><option value="delivered">Delivered</option><option value="cancelled">Cancelled</option></select></label>
    <label>Vehicle<select name="vehicle_id" defaultValue=""><option value="">Keep / unassigned</option>{vehicles.map(x=><option key={x.id} value={x.id}>{x.registration} · {x.make_model}</option>)}</select></label><label>Driver<input name="driver_name"/></label><label>Delivered date<input name="delivered_date" type="date"/></label>
   </>}
   <div className="form-actions"><button className="action-button" disabled={busy}>{busy?"Saving…":mode==="create"?"Schedule delivery":"Update delivery"}</button></div>
  </form>{feedback?<div className="form-feedback success">{feedback}</div>:null}
 </section>;
}
