import { Shell } from "@/components/Shell";
import { LedgerControl } from "@/components/LedgerControl";
import { apiGet, money } from "@/lib/api";

type Account={id:string;code:string;name:string;account_type:string;debit?:number|string;credit?:number|string;balance?:number|string};
type Bank={id:string;name:string;bank_name:string;balance?:number|string;unreconciled?:number};
type Transaction={id:string;description:string;reference?:string|null;amount:number|string;direction:string;reconciled:boolean;transaction_date:string};
type Trial={accounts:Account[];total_debit:number;total_credit:number;balanced:boolean};

export default async function LedgerPage(){
 const [accounts,banks,transactions,trial]=await Promise.all([apiGet<Account[]>("ledger-accounts",[]),apiGet<Bank[]>("bank-accounts",[]),apiGet<Transaction[]>("bank-transactions",[]),apiGet<Trial>("trial-balance",{accounts:[],total_debit:0,total_credit:0,balanced:true})]);
 const bankTotal=banks.reduce((s,b)=>s+Number(b.balance||0),0);
 return <Shell active="/ledger">
  <section className="page-head"><div><span className="eyebrow">Financial control</span><h1>General Ledger & Bank Reconciliation</h1><p>Post balanced journals, maintain the chart of accounts, record bank movement and prove which transactions have been reconciled.</p></div></section>
  <section className="metric-strip"><div className="card"><span>Total bank position</span><strong>{money(bankTotal)}</strong></div><div className="card"><span>Trial balance</span><strong>{trial.balanced?"Balanced":"Out of balance"}</strong></div><div className="card"><span>Unreconciled</span><strong>{transactions.filter(x=>!x.reconciled).length}</strong></div></section>
  <LedgerControl accounts={accounts} banks={banks} transactions={transactions}/>
  <section className="section-grid"><div className="card table-card"><div className="table-title"><h2>Trial balance</h2><span>Debit {money(trial.total_debit)} · Credit {money(trial.total_credit)}</span></div><div className="table-wrap"><table className="data-table"><thead><tr><th>Code</th><th>Account</th><th>Type</th><th>Debit</th><th>Credit</th><th>Net</th></tr></thead><tbody>{trial.accounts.map(a=><tr key={a.id}><td>{a.code}</td><td>{a.name}</td><td>{a.account_type}</td><td>{money(a.debit)}</td><td>{money(a.credit)}</td><td>{money(a.balance)}</td></tr>)}</tbody></table></div></div><div className="card table-card"><div className="table-title"><h2>Bank accounts</h2></div><div className="table-wrap"><table className="data-table"><thead><tr><th>Account</th><th>Bank</th><th>Balance</th><th>Open items</th></tr></thead><tbody>{banks.map(b=><tr key={b.id}><td>{b.name}</td><td>{b.bank_name}</td><td>{money(b.balance)}</td><td>{b.unreconciled||0}</td></tr>)}</tbody></table></div></div></section>
 </Shell>;
}
