"use client";
import { useState } from "react";
import Link from "next/link";
import { API } from "@/lib/api";

export default function VerifyCertificatePage() {
  const [code, setCode] = useState("");
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const verify = async () => { const value = code.trim(); if (!value) return; setLoading(true); setResult(null); try { const res = await fetch(`${API}/certificates/verify/${encodeURIComponent(value)}`); const data = await res.json(); setResult(res.ok ? data : { valid: false, error: data?.detail || "Certificate could not be verified." }); } catch { setResult({ valid: false, error: "Unable to reach KaushalSetu API." }); } finally { setLoading(false); } };
  return <div className="page-shell narrow-shell"><div className="nav"><Link href="/">Home</Link><Link href="/login">Login</Link></div><div className="auth-card"><span className="eyebrow">Public verification</span><h1 className="auth-title">Verify a training certificate</h1><p className="muted">This page is intentionally public. Employers and third parties can verify a certificate without receiving or entering an APAAR ID.</p><div className="verify-row"><input value={code} onChange={e => setCode(e.target.value)} placeholder="Paste certificate verification code"/><button className="button button-primary" onClick={verify} disabled={loading}>{loading ? "Checking…" : "Verify"}</button></div>{result && <div className={`verification-result ${result.valid ? "valid" : "invalid"}`}><h3>{result.valid ? "Certificate verified" : "Verification failed"}</h3>{result.valid ? <><p><strong>{result.certificate_name}</strong></p><p>Program: {result.program_name}</p><p>Certificate: {result.certificate_number}</p><p>Issued: {result.issued_on}</p><p>Status: {result.status}</p><p>Skills: {result.skills?.join(", ") || "None listed"}</p></> : <p>{result.error}</p>}</div>}</div></div>;
}
