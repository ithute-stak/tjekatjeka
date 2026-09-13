import { Shell } from "@/components/Shell";
import { ProductionStandards } from "@/components/ProductionStandards";
import { apiGet, money, number } from "@/lib/api";

type Product={id:string;name:string};
type Material={id:string;name:string;unit:string};
type Batch={id:string;batch_no:string;product_id:string;good_quantity:number|string};
type Recipe={id:string;name:string;product_id:string;standard_output:number|string};
type Summary={production_reject_rate_pct:number;average_brick_cost:number;active_recipes:number};

export default async function StandardsPage(){
 const [products,materials,batches,recipes,summary]=await Promise.all([
  apiGet<Product[]>("products",[]),apiGet<Material[]>("materials",[]),apiGet<Batch[]>("production",[]),apiGet<Recipe[]>("brick-recipes",[]),apiGet<Summary>("management-summary",{production_reject_rate_pct:0,average_brick_cost:0,active_recipes:0})
 ]);
 return <Shell active="/standards">
  <section className="page-head"><div><span className="eyebrow">Manufacturing discipline</span><h1>Brick Recipes & Variance</h1><p>Set the approved mix for each brick product and compare actual production against the standard to expose waste and cost drift.</p></div></section>
  <section className="metric-strip"><div className="card"><span>Active recipes</span><strong>{number(summary.active_recipes,0)}</strong></div><div className="card"><span>Overall reject rate</span><strong>{number(summary.production_reject_rate_pct,2)}%</strong></div><div className="card"><span>Average production cost</span><strong>{money(summary.average_brick_cost)}</strong></div></section>
  <ProductionStandards products={products} materials={materials} batches={batches} recipes={recipes}/>
 </Shell>;
}
