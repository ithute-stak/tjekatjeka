import { Shell } from "@/components/Shell";
import { MeasurementControl } from "@/components/MeasurementControl";
import { apiGet, number } from "@/lib/api";

type Job={id:string;job_no:string;customer_name:string};
type Measurement={id:string;job_id:string;item_name:string;width_mm:number|string;height_mm:number|string;quantity:number|string;area_m2:number|string;glass_type?:string|null;notes?:string|null};
type Summary={aluminium_measured_area_m2:number};

export default async function MeasurementsPage(){
 const [jobs,measurements,summary]=await Promise.all([
  apiGet<Job[]>("aluminium-jobs",[]),apiGet<Measurement[]>("aluminium-measurements",[]),apiGet<Summary>("management-summary",{aluminium_measured_area_m2:0})
 ]);
 return <Shell active="/measurements">
  <section className="page-head"><div><span className="eyebrow">Aluminium & glass production</span><h1>Measurements</h1><p>Capture real site and fabrication sizes, calculate glass area automatically, and keep measurements attached to the correct customer job.</p></div></section>
  <section className="metric-strip"><div className="card"><span>Total measured area</span><strong>{number(summary.aluminium_measured_area_m2,2)} m²</strong></div><div className="card"><span>Measurement lines</span><strong>{number(measurements.length,0)}</strong></div><div className="card"><span>Jobs available</span><strong>{number(jobs.length,0)}</strong></div></section>
  <MeasurementControl jobs={jobs}/>
  <section className="card table-card"><div className="panel-head compact-head"><h2>Measurement register</h2><span>Fabrication reference</span></div><div className="table-wrap"><table className="data-table"><thead><tr><th>Item</th><th>Width</th><th>Height</th><th>Qty</th><th>Area</th><th>Glass</th><th>Notes</th></tr></thead><tbody>{measurements.map(x=><tr key={x.id}><td>{x.item_name}</td><td>{number(x.width_mm,0)} mm</td><td>{number(x.height_mm,0)} mm</td><td>{number(x.quantity,0)}</td><td>{number(x.area_m2,3)} m²</td><td>{x.glass_type??"—"}</td><td>{x.notes??"—"}</td></tr>)}</tbody></table></div></section>
 </Shell>;
}
