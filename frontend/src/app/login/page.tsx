"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { apiFetch, API, roleHome, readError } from "@/lib/api";

const DEMOS = [
  ["Learner", "TRAINEE", "learner1@example.com", "learner123"],
  ["Employer", "EMPLOYER", "hr@techcorp.com", "emp123"],
  ["Training Provider", "TRAINING_PROVIDER", "provider@training.com", "provider123"],
  ["Government", "GOVERNMENT_ADMIN", "admin@gov.in", "admin123"],
] as const;

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const router = useRouter();

  useEffect(() => {
    const role = new URLSearchParams(window.location.search).get("role");
    const demo = DEMOS.find((item) => item[1] === role);
    if (demo) {
      setEmail(demo[2]);
      setPassword(demo[3]);
    }
  }, []);

  const doLogin = async (loginEmail = email, loginPassword = password) => {
    setError("");
    setBusy(true);
    try {
      const body = new URLSearchParams({ username: loginEmail, password: loginPassword });
      const res = await fetch(`${API}/auth/login`, { method: "POST", headers: { "Content-Type": "application/x-www-form-urlencoded" }, body });
      if (!res.ok) throw new Error(await readError(res, "Login failed"));
      const data = await res.json();
      localStorage.setItem("token", data.access_token);
      const meRes = await apiFetch("/auth/me");
      const me = meRes.ok ? await meRes.json() : null;
      router.push(roleHome(me?.role));
    } catch (err: any) {
      setError(err.message || "Login failed");
    } finally { setBusy(false); }
  };

  return <div className="page-shell narrow-shell">
    <div className="nav"><Link href="/">Home</Link><Link href="/register">Create account</Link></div>
    <div className="auth-card">
      <span className="eyebrow">Secure sign-in</span>
      <h1 className="auth-title">Welcome back</h1>
      <p className="muted">Your role determines which dashboard and actions you can access.</p>{email && <div className="demo-mode-note">Demo account loaded. Click <strong>Sign in</strong> to continue.</div>}
      {error && <div className="alert alert-error">{error}</div>}
      <form className="stack" onSubmit={(e) => { e.preventDefault(); void doLogin(); }}>
        <label>Email<input type="email" value={email} onChange={e => setEmail(e.target.value)} autoComplete="email" required /></label>
        <label>Password<input type="password" value={password} onChange={e => setPassword(e.target.value)} autoComplete="current-password" required /></label>
        <button className="button button-primary full-button" disabled={busy}>{busy ? "Signing in…" : "Sign in"}</button>
      </form>
    </div>

    <div className="card demo-card">
      <div className="section-heading"><p className="eyebrow">Hackathon demo</p><h2>Use a seeded account</h2><p className="muted">No need to type credentials during your live demo.</p></div>
      <div className="demo-account-grid">
        {DEMOS.map(([label, , demoEmail, demoPassword]) => <div className="demo-account" key={demoEmail}>
          <div><strong>{label}</strong><div className="muted small">{demoEmail}</div></div>
          <button className="button button-secondary button-small" onClick={() => { setEmail(demoEmail); setPassword(demoPassword); void doLogin(demoEmail, demoPassword); }} disabled={busy}>Use</button>
        </div>)}
      </div>
    </div>
  </div>;
}
