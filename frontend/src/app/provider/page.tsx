"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { apiFetch, clearAuth } from "@/lib/api";

const today = new Date().toISOString().slice(0, 10);

export default function ProviderDashboard() {
  const [programs, setPrograms] = useState<any[]>([]);
  const [skills, setSkills] = useState<any[]>([]);
  const [selectedProgram, setSelectedProgram] = useState<any>(null);
  const [enrollments, setEnrollments] = useState<any[]>([]);
  const [assessments, setAssessments] = useState<any[]>([]);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [assessmentForm, setAssessmentForm] = useState({ name: "Final Assessment", assessment_type: "FINAL", max_score: "100", passing_score: "60", assessment_date: today });
  const [resultForm, setResultForm] = useState({ assessment_id: "", learner_id: "", score: "", attempt_number: "1", remarks: "" });
  const [attendanceEnrollment, setAttendanceEnrollment] = useState("");
  const router = useRouter();

  const loadPrograms = async () => {
    const meRes = await apiFetch("/auth/me");
    if (!meRes.ok) { clearAuth(); router.push("/login"); return; }
    const me = await meRes.json();
    if (me.role !== "TRAINING_PROVIDER") { router.push("/dashboard"); return; }
    const [programRes, skillRes] = await Promise.all([apiFetch("/training-programs/programs"), apiFetch("/skills")]);
    if (programRes.ok) setPrograms(await programRes.json());
    if (skillRes.ok) setSkills(await skillRes.json());
  };

  const loadProgramData = async (programId: string) => {
    const [enrollmentRes, assessmentRes] = await Promise.all([
      apiFetch(`/training-programs/${programId}/enrollments`),
      apiFetch(`/training-programs/${programId}/assessments`),
    ]);
    setEnrollments(enrollmentRes.ok ? await enrollmentRes.json() : []);
    setAssessments(assessmentRes.ok ? await assessmentRes.json() : []);
  };

  useEffect(() => {
    (async () => { try { await loadPrograms(); } finally { setLoading(false); } })();
  }, []);

  const selectProgram = async (program: any) => {
    setSelectedProgram(program); setMessage(""); await loadProgramData(program.id);
  };

  const updateProgress = async (enrollment: any) => {
    const res = await apiFetch(`/enrollments/${enrollment.id}/progress`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ status: "COMPLETED", completion_percentage: 100 }) });
    const data = await res.json().catch(() => ({}));
    setMessage(res.ok ? "Enrollment marked completed." : (data.detail || "Could not update enrollment."));
    if (selectedProgram) await loadProgramData(selectedProgram.id);
  };

  const markPresent = async (enrollmentId: string) => {
    setAttendanceEnrollment(enrollmentId);
    const res = await apiFetch(`/enrollments/${enrollmentId}/attendance`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ attendance_date: today, status: "PRESENT", hours_attended: 8 }) });
    const data = await res.json().catch(() => ({}));
    setMessage(res.ok ? "Today's attendance marked present." : (data.detail || "Could not record attendance."));
    setAttendanceEnrollment("");
    if (selectedProgram) await loadProgramData(selectedProgram.id);
  };

  const createAssessment = async (event: FormEvent) => {
    event.preventDefault(); if (!selectedProgram) return;
    const res = await apiFetch(`/training-programs/${selectedProgram.id}/assessments`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ ...assessmentForm, max_score: Number(assessmentForm.max_score), passing_score: Number(assessmentForm.passing_score) }) });
    const data = await res.json().catch(() => ({}));
    setMessage(res.ok ? `Assessment created: ${data.name}` : (data.detail || "Could not create assessment."));
    if (res.ok) await loadProgramData(selectedProgram.id);
  };

  const recordResult = async (event: FormEvent) => {
    event.preventDefault(); if (!resultForm.assessment_id || !resultForm.learner_id) return;
    const res = await apiFetch(`/assessments/${resultForm.assessment_id}/results`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ learner_id: resultForm.learner_id, score: Number(resultForm.score), attempt_number: Number(resultForm.attempt_number), remarks: resultForm.remarks || undefined }) });
    const data = await res.json().catch(() => ({}));
    setMessage(res.ok ? `Result recorded: ${data.percentage}% ${data.passed ? "Passed" : "Needs improvement"}.` : (data.detail || "Could not record result."));
    if (res.ok) setResultForm({ ...resultForm, score: "", remarks: "" });
  };

  const issueCertificate = async (enrollment: any) => {
    const chosenSkills = skills.slice(0, 3).map((s) => s.id);
    const res = await apiFetch(`/enrollments/${enrollment.id}/certificate`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ certificate_name: `${selectedProgram.name} Certificate`, skill_ids: chosenSkills }) });
    const data = await res.json().catch(() => ({}));
    setMessage(res.ok ? `Certificate issued: ${data.certificate_number}` : (data.detail || "Certificate cannot be issued yet. Complete the training and pass required assessments first."));
  };

  if (loading) return <div className="page-shell"><div className="loading-panel">Loading provider workspace…</div></div>;

  return <div className="page-shell">
    <div className="nav"><Link href="/">Home</Link><Link href="/provider">Provider Dashboard</Link><Link href="/profile">Account</Link><button className="link-button" onClick={() => { clearAuth(); router.push("/"); }}>Logout</button></div>
    <div className="hero-card card"><span className="eyebrow">Training provider workspace</span><h1 className="page-title">Run the training-to-certificate workflow</h1><p className="muted">Select a program, manage learner completion, create assessments, record results, mark attendance, and issue certificates only when the learner is eligible.</p></div>
    {message && <div className="alert alert-info">{message}</div>}

    <div className="grid">
      <div className="card"><h2>Your programs</h2>{programs.length === 0 ? <p className="muted">No programs found.</p> : programs.map(p => <button className={`record-card ${selectedProgram?.id === p.id ? "record-selected" : ""}`} key={p.id} onClick={() => void selectProgram(p)}><strong>{p.name}</strong><span>{p.category} · {p.duration_hours} hours · capacity {p.capacity}</span></button>)}</div>
      <div className="card"><h2>{selectedProgram ? `${selectedProgram.name} · learners` : "Select a program"}</h2>{!selectedProgram ? <p className="muted">Choose a program on the left.</p> : enrollments.length === 0 ? <p className="muted">No learners enrolled.</p> : enrollments.map(e => <div className="list-row" key={e.id}><strong>Learner {e.learner_id.slice(0, 8)}…</strong><span>Status: {e.status}</span><span>Completion: {e.completion_percentage ?? 0}% · Attendance: {Number(e.attendance_percentage ?? 0).toFixed(1)}%</span><div className="button-row">{e.status !== "COMPLETED" && <button className="button button-primary button-small" onClick={() => void updateProgress(e)}>Mark complete</button>}<button className="button button-secondary button-small" disabled={attendanceEnrollment === e.id} onClick={() => void markPresent(e.id)}>{attendanceEnrollment === e.id ? "Saving…" : "Mark present today"}</button><button className="button button-secondary button-small" onClick={() => void issueCertificate(e)}>Issue certificate</button></div></div>)}</div>
    </div>

    {selectedProgram && <div className="grid section-gap">
      <div className="card"><h2>Create assessment</h2><form className="stack" onSubmit={createAssessment}><label>Name<input value={assessmentForm.name} onChange={e => setAssessmentForm({ ...assessmentForm, name: e.target.value })}/></label><label>Type<select value={assessmentForm.assessment_type} onChange={e => setAssessmentForm({ ...assessmentForm, assessment_type: e.target.value })}><option>QUIZ</option><option>PRACTICAL</option><option>PROJECT</option><option>FINAL</option><option>OTHER</option></select></label><div className="two-col"><label>Max score<input type="number" value={assessmentForm.max_score} onChange={e => setAssessmentForm({ ...assessmentForm, max_score: e.target.value })}/></label><label>Passing score<input type="number" value={assessmentForm.passing_score} onChange={e => setAssessmentForm({ ...assessmentForm, passing_score: e.target.value })}/></label></div><button className="button button-primary">Create assessment</button></form></div>
      <div className="card"><h2>Record result</h2>{assessments.length === 0 ? <p className="muted">Create an assessment first.</p> : <form className="stack" onSubmit={recordResult}><label>Assessment<select value={resultForm.assessment_id} onChange={e => setResultForm({ ...resultForm, assessment_id: e.target.value })} required><option value="">Choose assessment</option>{assessments.map(a => <option key={a.id} value={a.id}>{a.name} · pass {a.passing_score}/{a.max_score}</option>)}</select></label><label>Learner<select value={resultForm.learner_id} onChange={e => setResultForm({ ...resultForm, learner_id: e.target.value })} required><option value="">Choose learner</option>{enrollments.map(e => <option key={e.learner_id} value={e.learner_id}>Learner {e.learner_id.slice(0, 8)}…</option>)}</select></label><label>Score<input type="number" value={resultForm.score} onChange={e => setResultForm({ ...resultForm, score: e.target.value })} required min="0"/></label><label>Remarks<textarea rows={3} value={resultForm.remarks} onChange={e => setResultForm({ ...resultForm, remarks: e.target.value })}/></label><button className="button button-primary">Record result</button></form>}</div>
    </div>}

    {selectedProgram && <div className="card section-gap"><h2>Assessments in this program</h2>{assessments.length === 0 ? <p className="muted">No assessments yet.</p> : <div className="simple-list">{assessments.map(a => <div key={a.id}><strong>{a.name}</strong><span>{a.assessment_type} · pass mark {a.passing_score}/{a.max_score} · {a.assessment_date || "No date"}</span></div>)}</div>}</div>}
  </div>;
}
