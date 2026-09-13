import { cookies } from "next/headers";
import { redirect } from "next/navigation";

type PageProps = { searchParams: Promise<{ auth_error?: string }> };

const messages: Record<string, string> = {
  missing_credentials: "Enter your email address and password.",
  invalid_credentials: "The email address or password is incorrect.",
  mfa_required: "This account requires an MFA code.",
  too_many_attempts: "Too many sign-in attempts. Please wait and try again.",
  client_unavailable: "Tjekatjeka is not registered with central Ithute Auth yet.",
  auth_unavailable: "Central Ithute Auth is temporarily unavailable.",
  auth_response_invalid: "The sign-in service returned an invalid response.",
  session_expired: "Your session expired. Sign in again.",
};

export default async function LoginPage({ searchParams }: PageProps) {
  const store = await cookies();
  if (store.get("tjekatjeka_access")?.value) redirect("/dashboard");
  const query = await searchParams;
  const error = query.auth_error ? messages[query.auth_error] ?? "Sign in failed. Please try again." : "";

  return (
    <main className="login-shell">
      <section className="login-brand-panel">
        <div className="login-brand-lockup"><span className="login-mark">TJ</span><div><strong>Tjekatjeka Holdings</strong><small>Enterprise Operations Control Centre</small></div></div>
        <div className="login-brand-copy"><span className="eyebrow">One company. One control centre.</span><h1>Manage production, aluminium, finance, people and fleet operations from one place.</h1><p>Tjekatjeka uses central !thute Auth for identity while keeping its business data in its own protected database.</p></div>
        <div className="login-brand-footer">Powered by <strong>!thute</strong></div>
      </section>
      <section className="login-form-panel">
        <div className="login-card">
          <span className="eyebrow">Secure access</span>
          <h2>Sign in to Tjekatjeka</h2>
          <p>Use your Tjekatjeka owner or staff account.</p>
          {error ? <div className="login-error" role="alert">{error}</div> : null}
          <form action="/api/auth/password" method="post" className="login-form">
            <label>Email address<input name="identifier" type="email" defaultValue="thekoetlisi@tjekatjeka.co.ls" autoComplete="username" required /></label>
            <label>Password<input name="password" type="password" autoComplete="current-password" required /></label>
            <label>MFA code <span>(only if enabled)</span><input name="mfa_code" inputMode="numeric" autoComplete="one-time-code" /></label>
            <button type="submit">Sign in</button>
          </form>
          <small className="login-security-note">Your password is sent only to central Ithute Auth and is not stored in the Tjekatjeka database.</small>
        </div>
      </section>
    </main>
  );
}
