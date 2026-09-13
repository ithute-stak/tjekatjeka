"use client";

import { FormEvent, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

type Product={id:string;name:string};
type Material={id:string;name:string;unit:string};
type Batch={id:string;batch_no:string;product_id:string;good_quantity:number|string};
type RecipeInput={material_id:string;quantity:string};
type Recipe={id:string;name:string;product_id:string;standard_output:number|string};
type Variance={batch_no:string;recipe_name:string;reject_rate_pct:number;total_variance_cost:number;materials:{material_name:string;unit:string;expected:number;actual:number;variance:number;variance_pct:number|null;cost_impact:number}[]};

export function ProductionStandards({products,materials,batches,recipes}:{products:Product[];materials:Material[];batches:Batch[];recipes:Recipe[]}){
 const router=useRouter();
 const [inputs,setInputs]=useState<RecipeInput[]>([{material_id:"",quantity:""}]);
 const [productId,setProductId]=useState("");
 const [batchId,setBatchId]=useState("");
 const [recipeId,setRecipeId]=useState("");
 const [variance,setVariance]=useState<Variance|null>(null);
 const [message,setMessage]=useState("");
 const [busy,setBusy]=useState(false);
 const batch=useMemo(()=>batches.find(x=>x.id===batchId),[batches,batchId]);
 const matchingRecipes=recipes.filter(x=>!batch||x.product_id===batch.product_id);

 async function createRecipe(event:FormEvent<HTMLFormElement>){
  event.preventDefault();setBusy(true);setMessage("");const data=new FormData(event.currentTarget);
  const body={product_id:String(data.get("product_id")),name:String(data.get("name")),standard_output:Number(data.get("standard_output")),notes:String(data.get("notes")||"")||null,inputs:inputs.map(x=>({material_id:x.material_id,quantity:Number(x.quantity)}))};
  const response=await fetch("/api/backend/brick-recipes",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});
  const payload=await response.json().catch(()=>null);setBusy(false);
  if(!response.ok){setMessage(typeof payload?.detail==="string"?payload.detail:"Could not save recipe.");return;}
  setMessage("Production recipe saved.");setInputs([{material_id:"",quantity:""}]);event.currentTarget.reset();setProductId("");router.refresh();
 }

 async function analyse(){
  if(!batchId||!recipeId)return;setBusy(true);setMessage("");
  const response=await fetch(`/api/backend/production/${batchId}/variance?recipe_id=${encodeURIComponent(recipeId)}`);
  const payload=await response.json().catch(()=>null);setBusy(false);
  if(!response.ok){setMessage(typeof payload?.detail==="string"?payload.detail:"Could not calculate variance.");return;}
  setVariance(payload as Variance);
 }

 return <>
  <section className="card entry-card"><div className="entry-head"><div><span className="eyebrow">Production standard</span><h2>Create brick recipe</h2></div><span className="entry-hint">Define expected material use for a standard good-output quantity</span></div>
   <form className="entry-form" onSubmit={createRecipe}>
    <label>Finished product<select name="product_id" required value={productId} onChange={e=>setProductId(e.target.value)}><option value="">Select product</option>{products.map(x=><option key={x.id} value={x.id}>{x.name}</option>)}</select></label>
    <label>Recipe name<input name="name" required placeholder="6-inch block standard mix" /></label><label>Standard good output<input name="standard_output" type="number" min="1" step="1" required placeholder="1000" /></label><label>Notes<input name="notes" placeholder="Approved production standard" /></label>
    <div className="span-2 input-builder"><div className="builder-head"><strong>Expected materials</strong><button type="button" onClick={()=>setInputs(v=>[...v,{material_id:"",quantity:""}])}>+ Add material</button></div>{inputs.map((x,i)=><div className="input-row" key={i}><select required value={x.material_id} onChange={e=>setInputs(v=>v.map((item,n)=>n===i?{...item,material_id:e.target.value}:item))}><option value="">Select material</option>{materials.map(m=><option key={m.id} value={m.id}>{m.name} · {m.unit}</option>)}</select><input required type="number" min="0.0001" step="0.001" value={x.quantity} placeholder="Standard quantity" onChange={e=>setInputs(v=>v.map((item,n)=>n===i?{...item,quantity:e.target.value}:item))}/>{inputs.length>1?<button className="remove-button" type="button" onClick={()=>setInputs(v=>v.filter((_,n)=>n!==i))}>Remove</button>:null}</div>)}</div>
    <div className="form-actions"><button className="action-button" disabled={busy}>Save production standard</button></div>
   </form>{message?<div className="form-feedback success">{message}</div>:null}
  </section>

  <section className="card entry-card"><div className="entry-head"><div><span className="eyebrow">Variance analysis</span><h2>Compare batch with recipe</h2></div></div>
   <div className="entry-form"><label>Production batch<select value={batchId} onChange={e=>{setBatchId(e.target.value);setRecipeId("");setVariance(null)}}><option value="">Select batch</option>{batches.map(x=><option key={x.id} value={x.id}>{x.batch_no} · {x.good_quantity} good units</option>)}</select></label><label>Standard recipe<select value={recipeId} onChange={e=>setRecipeId(e.target.value)}><option value="">Select recipe</option>{matchingRecipes.map(x=><option key={x.id} value={x.id}>{x.name}</option>)}</select></label><div className="form-actions"><button type="button" className="action-button" disabled={busy||!batchId||!recipeId} onClick={analyse}>Analyse variance</button></div></div>
   {variance?<div className="table-wrap"><table className="data-table"><thead><tr><th>Material</th><th>Expected</th><th>Actual</th><th>Variance</th><th>Variance %</th><th>Cost impact</th></tr></thead><tbody>{variance.materials.map(x=><tr key={x.material_name}><td>{x.material_name}</td><td>{x.expected.toFixed(3)} {x.unit}</td><td>{x.actual.toFixed(3)} {x.unit}</td><td>{x.variance.toFixed(3)}</td><td>{x.variance_pct===null?"—":`${x.variance_pct.toFixed(1)}%`}</td><td>M {x.cost_impact.toFixed(2)}</td></tr>)}</tbody></table><div className="note">Reject rate: {variance.reject_rate_pct.toFixed(2)}% · Material variance cost impact: M {variance.total_variance_cost.toFixed(2)}</div></div>:null}
  </section>
 </>;
}
