"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

type Job={id:string;job_no:string;customer_name:string};

export function MeasurementControl({jobs}:{jobs:Job[]}){
 const router=useRouter();const [busy,setBusy]=useState(false);const [feedback,setFeedback]=useState("");
 async function submit(e:FormEvent<HTMLFormElement>){e.preventDefault();setBusy(true);setFeedback("");const d=new FormData(e.currentTarget);const body={job_id:String(d.get("job_id")),item_name:String(d.get("item_name")),width_mm:Number(d.get("width_mm")),height_mm:Number(d.get("height_mm")),quantity:Number(d.get("quantity")),glass_type:String(d.get("glass_type")||"")||null,notes:String(d.get("notes")||"")||null};
  try{const response=await fetch("/api/backend/aluminium-measurements",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});const payload=await response.json().catch(()=>null);if(!response.ok)throw new Error(typeof payload?.detail==="string"?payload.detail:"Could not save measurement.");e.currentTarget.reset();setFeedback(`Measurement saved · ${Number(payload.area_m2).toFixed(3)} m²`);router.refresh();}catch(error){setFeedback(error instanceof Error?error.message:"Could not save measurement.");}finally{setBusy(false)}
 }
 return <section className="card entry-card"><div className="entry-head"><div><span className="eyebrow">Site & fabrication measurements</span><h2>Add measured item</h2></div><span className="entry-hint">Area is calculated automatically from width × height × quantity</span></div><form className="entry-form" onSubmit={submit}>
  <label>Aluminium job<select name="job_id" required defaultValue=""><option value="">Select job</option>{jobs.map(x=><option key={x.id} value={x.id}>{x.job_no} · {x.customer_name}</option>)}</select></label><label>Item<input name="item_name" required placeholder="Kitchen window / front door"/></label><label>Width (mm)<input name="width_mm" type="number" min="1" step="0.01" required/></label><label>Height (mm)<input name="height_mm" type="number" min="1" step="0.01" required/></label><label>Quantity<input name="quantity" type="number" min="1" step="1" defaultValue="1" required/></label><label>Glass type<input name="glass_type" placeholder="6mm clear / tinted"/></label><label className="span-2">Notes<input name="notes" placeholder="Frame/profile or installation notes"/></label><div className="form-actions"><button className="action-button" disabled={busy}>{busy?"Saving…":"Save measurement"}</button></div>
 </form>{feedback?<div className="form-feedback success">{feedback}</div>:null}</section>;
}
