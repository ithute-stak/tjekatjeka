import { Shell } from "@/components/Shell";
import { PeopleControl } from "@/components/PeopleControl";
import { apiGet, money } from "@/lib/api";

type Branch={id:string;name:string};
type Employee={id:string;employee_no:string;full_name:string;job_title:string;basic_salary:number|string;active:boolean};
type Payroll={id:string;period_label:string;pay_date:string;status:string;gross_total:number|string;deduction_total:number|string;net_total:number|string};

export default async function PeoplePage(){
 const [branches,employees,payrolls]=await Promise.all([apiGet<Branch[]>("branches",[]),apiGet<Employee[]>("employees",[]),apiGet<Payroll[]>("payroll-runs",[])]);
 const active=employees.filter(x=>x.active);const salary=active.reduce((s,x)=>s+Number(x.basic_salary||0),0);const pending=payrolls.filter(x=>x.status==="draft").length;
 return <Shell active="/people">
  <section className="page-head"><div><span className="eyebrow">People & payroll</span><h1>Employees, Salary Runs & Approval</h1><p>Maintain employee records and prepare payroll from salary snapshots without hard-coding statutory deductions into the software.</p></div></section>
  <section className="metric-strip"><div className="card"><span>Active employees</span><strong>{active.length}</strong></div><div className="card"><span>Basic salary base</span><strong>{money(salary)}</strong></div><div className="card"><span>Payroll awaiting approval</span><strong>{pending}</strong></div></section>
  <PeopleControl branches={branches} employees={employees} payrolls={payrolls}/>
  <section className="card table-card"><div className="table-title"><h2>Employee register</h2><span>{active.length} active</span></div><div className="table-wrap"><table className="data-table"><thead><tr><th>No.</th><th>Name</th><th>Job title</th><th>Basic salary</th><th>Status</th></tr></thead><tbody>{employees.map(x=><tr key={x.id}><td>{x.employee_no}</td><td>{x.full_name}</td><td>{x.job_title}</td><td>{money(x.basic_salary)}</td><td>{x.active?"Active":"Inactive"}</td></tr>)}</tbody></table></div></section>
 </Shell>;
}
