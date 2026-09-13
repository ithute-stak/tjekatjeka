import { Shell } from "@/components/Shell";
import { GovernanceControl } from "@/components/GovernanceControl";
import { apiGet } from "@/lib/api";

type Approval={id:string;title:string;entity_type:string;amount?:number|string|null;requested_by?:string|null;status:string};
type Profile={id:string;email_snapshot?:string|null;role:string};
type Document={id:string;title:string;document_type:string;entity_type:string;created_at:string};
type Notification={id:string;recipient:string;title:string;message:string;severity:string;read:boolean};
type Audit={id:string;actor?:string|null;action:string;entity_type:string;summary:string;occurred_at:string};
type Summary={pending_approvals:number;unread_notifications:number;documents:number;active_employees:number;draft_payroll_runs:number};

export default async function GovernancePage(){
 const [approvals,profiles,documents,notifications,audit,summary]=await Promise.all([
  apiGet<Approval[]>("approvals",[]),apiGet<Profile[]>("profiles",[]),apiGet<Document[]>("documents",[]),apiGet<Notification[]>("notifications",[]),apiGet<Audit[]>("audit-events",[]),apiGet<Summary>("governance-summary",{pending_approvals:0,unread_notifications:0,documents:0,active_employees:0,draft_payroll_runs:0})
 ]);
 return <Shell active="/governance">
  <section className="page-head"><div><span className="eyebrow">Enterprise governance</span><h1>Approvals, Roles, Documents & Audit</h1><p>Control who can act, require director decisions for sensitive workflows, preserve supporting files and retain an audit trail of enterprise actions.</p></div></section>
  <section className="kpi-grid"><div className="card kpi"><div className="kpi-head"><span>Pending approvals</span><span className="kpi-icon">A</span></div><strong>{summary.pending_approvals}</strong><small>Waiting for director/admin</small></div><div className="card kpi"><div className="kpi-head"><span>Unread notices</span><span className="kpi-icon">N</span></div><strong>{summary.unread_notifications}</strong><small>Governance notifications</small></div><div className="card kpi"><div className="kpi-head"><span>Documents</span><span className="kpi-icon">D</span></div><strong>{summary.documents}</strong><small>Persistent vault records</small></div><div className="card kpi"><div className="kpi-head"><span>Draft payroll</span><span className="kpi-icon">P</span></div><strong>{summary.draft_payroll_runs}</strong><small>Runs not yet approved</small></div></section>
  <GovernanceControl approvals={approvals} profiles={profiles} documents={documents} notifications={notifications}/>
  <section className="card table-card record-table"><div className="table-title"><h2>Audit trail</h2><span>Latest 500 governed actions</span></div><div className="table-wrap"><table className="data-table"><thead><tr><th>When</th><th>Actor</th><th>Action</th><th>Entity</th><th>Summary</th></tr></thead><tbody>{audit.map(x=><tr key={x.id}><td>{new Date(x.occurred_at).toLocaleString("en-LS")}</td><td>{x.actor||"System"}</td><td>{x.action}</td><td>{x.entity_type}</td><td>{x.summary}</td></tr>)}</tbody></table></div></section>
 </Shell>;
}
