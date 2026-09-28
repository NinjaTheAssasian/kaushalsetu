"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { apiFetch, clearAuth, readError } from "@/lib/api";

type Skill = { id: string; name: string; category: string };

export default function EmployerDashboard() {
  const [records, setRecords] = useState<any[]>([]);
  const [skills, setSkills] = useState<Skill[]>([]);
  const [code, setCode] = useState("");
  const [message, setMessage] = useState("");
  const [feedbackMessage, setFeedbackMessage] = useState("");
  const [selectedRecord, setSelectedRecord] = useState<any | null>(null);
  const [feedback, setFeedback] = useState({ skill_id: "", rating: "80", comments: "" });
  const [busy, setBusy] = useState(false);
  const [feedbackBusy, setFeedbackBusy] = useState(false);
  const router = useRouter();

  const load = async () => {
    const meRes = await apiFetch("/auth/me");
    if (!meRes.ok) { clearAuth(); router.replace("/login"); return; }
    const me = await meRes.json();
    if (me.role !== "EMPLOYER") { router.replace("/dashboard"); return; }
    const [recordsRes, skillsRes] = await Promise.all([apiFetch("/employers/me/employments"), apiFetch("/skills")]);
    if (recordsRes.ok) setRecords(await recordsRes.json());
    if (skillsRes.ok) setSkills(await skillsRes.json());
  };

  useEffect(() => { void load(); }, [router]);

  const verifyEmployment = async (event: FormEvent) => {
    event.preventDefault(); if (!code.trim()) return;
    setMessage(""); setBusy(true);
    try {
      const res = await apiFetch("/employment/verify", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ verification_code: code.trim() }) });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.detail || "Verification failed");
      setMessage(`${data.role_title} is now employer-verified.`); setCode(""); await load();
    } catch (e: any) { setMessage(e.message || "Verification failed"); }
    finally { setBusy(false); }
  };

  const submitFeedback = async (event: FormEvent) => {
    event.preventDefault(); if (!selectedRecord) return;
    setFeedbackMessage(""); setFeedbackBusy(true);
    try {
      const res = await apiFetch(`/employment/${selectedRecord.id}/feedback`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ skill_id: feedback.skill_id, rating: Number(feedback.rating), comments: feedback.comments || undefined }) });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.detail || "Could not save feedback");
      setFeedbackMessage(`Feedback saved for ${data.skill_name}.`);
      setFeedback({ skill_id: "", rating: "80", comments: "" });
    } catch (e: any) { setFeedbackMessage(e.message || "Could not save feedback"); }
    finally { setFeedbackBusy(false); }
  };

  return <div className="page-shell">
    <div className="nav"><Link href="/">Home</Link><Link href="/employer">Employer Dashboard</Link><Link href="/profile">Account</Link><button className="link-button" onClick={() => { clearAuth(); router.push("/"); }}>Logout</button></div>

    <div className="card hero-card"><span className="eyebrow">Employer workspace</span><h1 className="page-title">Verify employment outcomes</h1><p className="muted">Employer actions require an authenticated employer account. The learner gives you a one-time code after reporting a job.</p></div>

    <div className="workflow-card employer-flow"><div><p className="eyebrow">How verification works</p><h2>Report → share code → verify → rate skills</h2></div><div className="workflow-steps"><span>1. Learner reports employment</span><span>2. Learner shares the one-time code</span><span>3. You sign in and verify it</span><span>4. You add practical skill feedback</span></div></div>

    <div className="grid">
      <div className="card"><h2>Verify a learner</h2><p className="muted">Paste the code the learner received. You must be logged in as the employer organization that is attesting to the employment.</p>
        <form onSubmit={verifyEmployment} className="stack"><label>Employment verification code<input value={code} onChange={e => setCode(e.target.value)} placeholder="Paste one-time code" required /></label><button className="button button-primary" disabled={busy}>{busy ? "Verifying…" : "Verify employment"}</button></form>
        {message && <div className="alert alert-info">{message}</div>}
      </div>
      <div className="card"><h2>Verified employment</h2>{records.length === 0 ? <div className="empty-state"><strong>No records yet</strong><p>Once you verify one, it will appear here for skill feedback.</p></div> : records.map(record => <button className={`record-card ${selectedRecord?.id === record.id ? "record-selected" : ""}`} key={record.id} onClick={() => setSelectedRecord(record)}><strong>{record.role_title}</strong><span>{record.reported_employer_name || record.employer_name}</span><span>{record.verification_status.replaceAll("_", " ")}</span></button>)}</div>
    </div>

    <div className="card section-gap"><h2>Employer skill feedback</h2>{!selectedRecord ? <p className="muted">Select a verified employment record above to rate the learner's practical skill level.</p> : <><div className="selected-record"><strong>{selectedRecord.role_title}</strong><span>Learner record: {selectedRecord.learner_id.slice(0, 8)}…</span></div><form onSubmit={submitFeedback} className="stack feedback-form"><label>Skill<select value={feedback.skill_id} onChange={e => setFeedback({ ...feedback, skill_id: e.target.value })} required><option value="">Choose a skill</option>{skills.map(s => <option key={s.id} value={s.id}>{s.name} · {s.category}</option>)}</select></label><label>Proficiency<input type="range" min="0" max="100" value={feedback.rating} onChange={e => setFeedback({ ...feedback, rating: e.target.value })}/><span className="range-value">{feedback.rating}/100</span></label><label>Comments<textarea rows={4} value={feedback.comments} onChange={e => setFeedback({ ...feedback, comments: e.target.value })} placeholder="What did the learner demonstrate well? What should they improve?"/></label><button className="button button-primary" disabled={feedbackBusy}>{feedbackBusy ? "Saving…" : "Save skill feedback"}</button></form>{feedbackMessage && <div className="alert alert-info">{feedbackMessage}</div>}</>}</div>

    <div className="card demo-note"><strong>Demo credentials</strong><span className="muted">hr@techcorp.com / emp123</span><span className="muted">Use the Login page to switch roles during the SIH demo.</span></div>
  </div>;
}
