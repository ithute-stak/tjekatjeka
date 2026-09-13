import { Shell } from "@/components/Shell";
import { DeliveryControl } from "@/components/DeliveryControl";
import { FormDialog } from "@/components/FormDialog";
import { apiGet, money, number } from "@/lib/api";

type Vehicle={id:string;registration:string;make_model:string};
type Branch={id:string;name:string};
type Delivery={id:string;delivery_no:string;customer_name:string;destination:string;load_description:string;quantity?:number|string|null;unit?:string|null;driver_name?:string|null;delivery_fee:number|string;status:string;scheduled_date:string;vehicle_id?:string|null};
type Summary={pending_deliveries:number};

export default async function DeliveriesPage(){
 const [vehicles,branches,deliveries,summary]=await Promise.all([
  apiGet<Vehicle[]>("vehicles",[]),apiGet<Branch[]>("branches",[]),apiGet<Delivery[]>("deliveries",[]),apiGet<Summary>("management-summary",{pending_deliveries:0})
 ]);
 return <Shell active="/deliveries">
  <section className="page-head"><div><span className="eyebrow">Logistics</span><h1>Deliveries & Dispatch</h1><p>Plan customer deliveries, assign trucks and drivers, and follow each load through to delivery.</p></div><FormDialog triggerLabel="Delivery action" title="Delivery & dispatch action" description="Schedule a customer delivery or update the status, vehicle and driver of an existing load." eyebrow="Dispatch" size="wide"><DeliveryControl vehicles={vehicles} branches={branches} deliveries={deliveries}/></FormDialog></section>
  <section className="metric-strip"><div className="card"><span>Pending deliveries</span><strong>{number(summary.pending_deliveries,0)}</strong></div><div className="card"><span>Total delivery records</span><strong>{number(deliveries.length,0)}</strong></div><div className="card"><span>Delivery fees tracked</span><strong>{money(deliveries.reduce((sum,x)=>sum+Number(x.delivery_fee||0),0))}</strong></div></section>
  <section className="card table-card"><div className="panel-head compact-head"><h2>Dispatch board</h2><span>Latest first</span></div><div className="table-wrap"><table className="data-table"><thead><tr><th>Delivery</th><th>Date</th><th>Customer</th><th>Destination</th><th>Load</th><th>Driver</th><th>Status</th><th>Fee</th></tr></thead><tbody>{deliveries.map(x=><tr key={x.id}><td>{x.delivery_no}</td><td>{x.scheduled_date}</td><td>{x.customer_name}</td><td>{x.destination}</td><td>{x.load_description}</td><td>{x.driver_name??"—"}</td><td>{x.status.replaceAll("_"," ")}</td><td>{money(x.delivery_fee)}</td></tr>)}</tbody></table></div></section>
 </Shell>;
}
