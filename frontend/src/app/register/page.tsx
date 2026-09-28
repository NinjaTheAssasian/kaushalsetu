"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { API, readError, roleHome } from "@/lib/api";

export default function Register() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("TRAINEE");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const router = useRouter();

  const submit = async (e: React.FormEvent) => {
    e.preventDefault(); setError(""); setBusy(true);
    try {
      const res = await fetch(`${API}/auth/register`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ email, password, role }) });
      if (!res.ok) throw new Error(await readError(res, "Registration failed"));
      const form = new URLSearchParams({ username: email, password });
      const loginRes = await fetch(`${API}/auth/login`, { method: "POST", headers: { "Content-Type": "application/x-www-form-urlencoded" }, body: form });
      if (!loginRes.ok) { router.push("/login"); return; }
      const token = await loginRes.json(); localStorage.setItem("token", token.access_token);
      router.push(roleHome(role));
    } catch (err: any) { setError(err.message || "Registration failed"); }
    finally { setBusy(false); }
  };

  return <div className="page-shell narrow-shell">
    <div className="nav"><Link href="/">Home</Link><Link href="/login">Login</Link></div>
    <form className="auth-card stack" onSubmit={submit}>
      <span className="eyebrow">Create an account</span><h1 className="auth-title">Join KaushalSetu</h1>
      {error && <div className="alert alert-error">{error}</div>}
      <label>Email<input type="email" value={email} onChange={e => setEmail(e.target.value)} required /></label>
      <label>Password<input type="password" minLength={6} value={password} onChange={e => setPassword(e.target.value)} required /></label>
      <label>Role<select value={role} onChange={e => setRole(e.target.value)}><option value="TRAINEE">Learner</option><option value="TRAINING_PROVIDER">Training Provider</option><option value="EMPLOYER">Employer</option><option value="GOVERNMENT_ADMIN">Government Admin (demo)</option></select></label>
      <button className="button button-primary full-button" disabled={busy}>{busy ? "Creating…" : "Create account"}</button>
    </form>
  </div>;
}
