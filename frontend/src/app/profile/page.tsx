"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { apiFetch, API, clearAuth, roleHome } from "@/lib/api";

type UserProfile = { id: string; email: string; role: string };

type OutcomeForm = {
  milestone_months: string;
  employment_status: string;
  employer_name: string;
  role_title: string;
  income_band: string;
  training_relevance_score: string;
  using_training_skills: string;
  skill_gap_notes: string;
};

export default function Profile() {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [apaarStatus, setApaarStatus] = useState<any>(null);
  const [enrollments, setEnrollments] = useState<any[]>([]);
  const [assessments, setAssessments] = useState<any[]>([]);
  const [certificates, setCertificates] = useState<any[]>([]);
  const [outcomes, setOutcomes] = useState<any[]>([]);
  const [timeline, setTimeline] = useState<any[]>([]);
  const [employment, setEmployment] = useState<any[]>([]);
  const [employmentForm, setEmploymentForm] = useState({
    reported_employer_name: "",
    role_title: "",
    employment_type: "FULL_TIME",
    industry: "",
    district: "",
    state: "",
    start_date: new Date().toISOString().slice(0, 10),
    salary_band: "",
  });
  const [employmentMessage, setEmploymentMessage] = useState("");
  const [verificationCode, setVerificationCode] = useState("");
  const [loading, setLoading] = useState(true);
  const [outcomeSubmitting, setOutcomeSubmitting] = useState(false);
  const [outcomeMessage, setOutcomeMessage] = useState("");
  const [outcomeForm, setOutcomeForm] = useState<OutcomeForm>({
    milestone_months: "3",
    employment_status: "EMPLOYED",
    employer_name: "",
    role_title: "",
    income_band: "",
    training_relevance_score: "80",
    using_training_skills: "true",
    skill_gap_notes: "",
  });
  const router = useRouter();

  const loadLearnerData = async (token: string) => {
    const headers = { Authorization: `Bearer ${token}` };
    const [enrRes, assRes, certRes, outcomesRes, timelineRes, employmentRes] = await Promise.all([
      apiFetch(`/enrollments/me`, { headers }),
      apiFetch(`/learners/me/assessments`, { headers }),
      apiFetch(`/certificates/me`, { headers }),
      apiFetch(`/learners/me/outcomes`, { headers }),
      apiFetch(`/learners/me/timeline`, { headers }),
      apiFetch(`/learners/me/employment`, { headers }),
    ]);

    if (enrRes.ok) setEnrollments(await enrRes.json());
    if (assRes.ok) setAssessments(await assRes.json());
    if (certRes.ok) setCertificates(await certRes.json());
    if (outcomesRes.ok) setOutcomes(await outcomesRes.json());
    if (timelineRes.ok) setTimeline(await timelineRes.json());
    if (employmentRes.ok) setEmployment(await employmentRes.json());
  };

  useEffect(() => {
    const fetchProfile = async () => {
      const token = localStorage.getItem("token");
      if (!token) {
        router.push("/login");
        return;
      }

      try {
        const res = await fetch(`${API}/auth/me`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!res.ok) throw new Error("Session expired");

        const userData = await res.json();
        setUser(userData);

        const apaarRes = await fetch(`${API}/apaar/status`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (apaarRes.ok) setApaarStatus(await apaarRes.json());

        if (userData.role === "TRAINEE") await loadLearnerData(token);
      } catch (err) {
        console.error(err);
        localStorage.removeItem("token");
        router.push("/login");
      } finally {
        setLoading(false);
      }
    };

    fetchProfile();
  }, [router]);

  const handleLogout = () => {
    clearAuth();
    router.push("/");
  };

  const [apaarBusy, setApaarBusy] = useState(false);
  const [apaarMessage, setApaarMessage] = useState("");
  const handleVerifyApaar = async () => {
    setApaarMessage("");
    setApaarBusy(true);
    try {
      const apaarId = Array.from(crypto.getRandomValues(new Uint8Array(12)), (n) => n % 10).join("");
      const res = await apiFetch(`/apaar/verify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ apaar_id: apaarId }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.detail || `APAAR verification failed (${res.status})`);
      setApaarStatus({ masked_apaar_id: data.masked_apaar_id, verification_status: data.verification_status });
      setApaarMessage("Demo APAAR verification successful.");
    } catch (e: any) {
      setApaarMessage(e.message || "APAAR verification failed");
    } finally { setApaarBusy(false); }
  };

  const createEmployment = async (event: FormEvent) => {
    event.preventDefault();
    setEmploymentMessage("");
    const token = localStorage.getItem("token");
    try {
      const payload = {
        ...employmentForm,
        industry: employmentForm.industry || undefined,
        district: employmentForm.district || undefined,
        state: employmentForm.state || undefined,
        salary_band: employmentForm.salary_band || undefined,
      };
      const res = await fetch(`${API}/learners/me/employment`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Could not report employment");
      setVerificationCode(data.verification_code || "");
      setEmploymentMessage(`Employment reported. Share this verification code with your employer.`);
      setEmploymentForm({ ...employmentForm, reported_employer_name: "", role_title: "", salary_band: "" });
      await loadLearnerData(token!);
    } catch (error: any) {
      setEmploymentMessage(error.message || "Could not report employment");
    }
  };

  const endEmployment = async (employmentId: string) => {
    const token = localStorage.getItem("token");
    const res = await fetch(`${API}/learners/me/employment/${employmentId}/end`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    });
    const data = await res.json();
    setEmploymentMessage(res.ok ? "Employment marked as ended." : (data.detail || "Could not end employment"));
    if (res.ok) await loadLearnerData(token!);
  };

  const submitOutcome = async (event: FormEvent) => {
    event.preventDefault();
    setOutcomeSubmitting(true);
    setOutcomeMessage("");
    const token = localStorage.getItem("token");
    try {
      const payload = {
        milestone_months: Number(outcomeForm.milestone_months),
        employment_status: outcomeForm.employment_status,
        employer_name: outcomeForm.employer_name || undefined,
        role_title: outcomeForm.role_title || undefined,
        income_band: outcomeForm.income_band || undefined,
        training_relevance_score: Number(outcomeForm.training_relevance_score),
        using_training_skills: outcomeForm.using_training_skills === "true",
        skill_gap_notes: outcomeForm.skill_gap_notes || undefined,
      };
      const res = await fetch(`${API}/learners/me/outcomes`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Could not submit check-in");
      setOutcomeMessage(`${data.milestone_months}-month check-in saved.`);
      await loadLearnerData(token!);
    } catch (error: any) {
      setOutcomeMessage(error.message || "Could not submit check-in");
    } finally {
      setOutcomeSubmitting(false);
    }
  };

  if (loading) return <div className="page-shell">Loading...</div>;
  if (!user) return null;

  return (
    <div className="page-shell">
      <div className="nav">
        <Link href="/">Home</Link>
        {user.role === "TRAINING_PROVIDER" && <Link href="/provider">Provider Dashboard</Link>}
        {user.role === "EMPLOYER" && <Link href="/employer">Employer Dashboard</Link>}
        {user.role === "GOVERNMENT_ADMIN" && <Link href="/admin">Government Dashboard</Link>}
        {user.role === "TRAINEE" && <Link href="/verify">Verify Certificate</Link>}
        <button onClick={handleLogout} style={{ background: "none", border: "none", color: "var(--accent)", cursor: "pointer", fontWeight: 500, padding: 0 }}>
          Logout
        </button>
      </div>

      <div className="card">
        <h2>User Profile</h2>
        <p><strong>Email:</strong> {user.email}</p>
        <p><strong>Role:</strong> {user.role}</p>
{user.role === "TRAINEE" && (
          <div style={{ marginTop: 24, padding: 16, background: "#f9fafb", borderRadius: 8 }}>
          <h3>APAAR Identity Status</h3>
          {apaarStatus?.verification_status === "VERIFIED" ? (
            <>
              <p><strong>Status:</strong> <span style={{ color: "#12b76a" }}>VERIFIED</span></p>
              <p><strong>APAAR ID:</strong> {apaarStatus.masked_apaar_id}</p>
            </>
          ) : (
            <>
              <p><strong>Status:</strong> {apaarStatus?.verification_status || "UNVERIFIED"}</p>
              <button onClick={handleVerifyApaar} style={{ padding: "8px 16px", background: "var(--accent)", color: "white", border: 0, borderRadius: 4, cursor: "pointer", marginTop: 8 }}>
                {apaarBusy ? "Verifying…" : "Demo Verify APAAR"}
              </button>
              {apaarMessage && <p className="small" style={{ marginTop: 10 }}>{apaarMessage}</p>}
            </>
          )}
          </div>
        )}
      </div>

      {user.role === "TRAINEE" && (
        <>
          <section className="grid">
            <div className="card">
              <h2>Training Journey</h2>
              {enrollments.length === 0 ? <p>No enrollments found.</p> : enrollments.map((e) => (
                <div key={e.id} style={{ padding: "14px 0", borderBottom: "1px solid var(--border)" }}>
                  <strong>{e.training_program_id}</strong>
                  <p style={{ margin: "6px 0" }}>Status: {e.status}</p>
                  <p style={{ margin: "6px 0" }}>Attendance: {e.attendance_percentage?.toFixed?.(1) ?? e.attendance_percentage ?? 0}%</p>
                  <p style={{ margin: "6px 0" }}>Completion: {e.completion_percentage ?? 0}%</p>
                </div>
              ))}
            </div>

            <div className="card">
              <h2>Assessment Results</h2>
              {assessments.length === 0 ? <p>No assessments yet.</p> : assessments.map((a) => (
                <div key={a.id} style={{ padding: "14px 0", borderBottom: "1px solid var(--border)" }}>
                  <p style={{ margin: 0 }}><strong>{a.percentage}%</strong> · {a.passed ? <span style={{ color: "#12b76a" }}>Passed</span> : <span style={{ color: "#d92d20" }}>Needs improvement</span>}</p>
                  <p style={{ margin: "6px 0" }}>Score: {a.score} · Attempt {a.attempt_number}</p>
                  <small>{new Date(a.assessed_at).toLocaleDateString()}</small>
                </div>
              ))}
            </div>
          </section>

          <div className="card" style={{ marginTop: 24 }}>
            <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
              <div>
                <h2 style={{ marginBottom: 4 }}>Certificates</h2>
                <p style={{ marginTop: 0 }}>Verified evidence of completed training.</p>
              </div>
              <Link href="/verify">Open certificate verifier →</Link>
            </div>
            {certificates.length === 0 ? <p>No certificates yet.</p> : certificates.map((certificate) => (
              <div key={certificate.id} style={{ padding: "16px 0", borderTop: "1px solid var(--border)" }}>
                <strong>{certificate.certificate_name}</strong>
                <p style={{ margin: "6px 0" }}>Certificate: {certificate.certificate_number}</p>
                <p style={{ margin: "6px 0" }}>Issued: {new Date(certificate.issue_date).toLocaleDateString()} · {certificate.status}</p>
                <p style={{ margin: "6px 0" }}>Verification code: <code>{certificate.verification_code}</code></p>
              </div>
            ))}
          </div>

          <div className="card" style={{ marginTop: 24 }}>
            <h2>Employment Outcomes</h2>
            <p>Report a job outcome, then share the verification code with the employer so they can attest to it.</p>
            <form onSubmit={createEmployment} style={{ display: "grid", gap: 10, marginBottom: 20 }}>
              <input required placeholder="Employer / organization" value={employmentForm.reported_employer_name} onChange={(e) => setEmploymentForm({ ...employmentForm, reported_employer_name: e.target.value })} />
              <input required placeholder="Role title" value={employmentForm.role_title} onChange={(e) => setEmploymentForm({ ...employmentForm, role_title: e.target.value })} />
              <select value={employmentForm.employment_type} onChange={(e) => setEmploymentForm({ ...employmentForm, employment_type: e.target.value })}>
                <option value="FULL_TIME">Full time</option>
                <option value="PART_TIME">Part time</option>
                <option value="CONTRACT">Contract</option>
                <option value="INTERNSHIP">Internship</option>
                <option value="APPRENTICESHIP">Apprenticeship</option>
              </select>
              <input placeholder="Industry" value={employmentForm.industry} onChange={(e) => setEmploymentForm({ ...employmentForm, industry: e.target.value })} />
              <input placeholder="District" value={employmentForm.district} onChange={(e) => setEmploymentForm({ ...employmentForm, district: e.target.value })} />
              <input placeholder="State" value={employmentForm.state} onChange={(e) => setEmploymentForm({ ...employmentForm, state: e.target.value })} />
              <input type="date" value={employmentForm.start_date} onChange={(e) => setEmploymentForm({ ...employmentForm, start_date: e.target.value })} />
              <input placeholder="Salary / income band" value={employmentForm.salary_band} onChange={(e) => setEmploymentForm({ ...employmentForm, salary_band: e.target.value })} />
              <button type="submit" style={{ padding: 10, background: "var(--accent)", color: "white", border: 0, borderRadius: 6, cursor: "pointer" }}>Report employment</button>
            </form>
            {employmentMessage && <div className="alert alert-info">
              <p style={{ marginTop: 0 }}>{employmentMessage}</p>
              {verificationCode && <div className="verification-code-box"><code>{verificationCode}</code><button className="button button-secondary button-small" type="button" onClick={async () => { await navigator.clipboard.writeText(verificationCode); setEmploymentMessage("Verification code copied. Share it with the employer now."); }}>Copy code</button></div>}
            </div>}
            {employment.length === 0 ? <p>No employment records yet.</p> : employment.map((e) => (
              <div key={e.id} style={{ padding: "14px 0", borderTop: "1px solid var(--border)" }}>
                <strong>{e.role_title}</strong> · {e.reported_employer_name}
                <p style={{ margin: "6px 0" }}>Status: {e.status} · Verification: {e.verification_status.replaceAll("_", " ")}</p>
                <p style={{ margin: "6px 0" }}>Started: {new Date(e.start_date).toLocaleDateString()} {e.salary_band ? `· ${e.salary_band}` : ""}</p>
                {e.verification_status === "EMPLOYER_VERIFIED" && <span style={{ color: "#12b76a", fontWeight: 600 }}>Employer verified</span>}
                {e.status === "ACTIVE" && <button onClick={() => endEmployment(e.id)} style={{ marginLeft: 12, padding: "7px 10px", border: "1px solid var(--border)", background: "white", borderRadius: 6, cursor: "pointer" }}>Mark ended</button>}
              </div>
            ))}
          </div>

          <div className="grid" style={{ marginTop: 24 }}>
            <div className="card">
              <h2>Longitudinal Outcome Check-in</h2>
              <p>Submit a lightweight 3, 6, or 12-month update. It is stored as self-reported until a later verification step.</p>
              <form onSubmit={submitOutcome} style={{ display: "grid", gap: 10 }}>
                <label>Milestone
                  <select value={outcomeForm.milestone_months} onChange={(e) => setOutcomeForm({ ...outcomeForm, milestone_months: e.target.value })} style={{ width: "100%", padding: 10, marginTop: 4 }}>
                    <option value="3">3 months</option>
                    <option value="6">6 months</option>
                    <option value="12">12 months</option>
                  </select>
                </label>
                <label>Status
                  <select value={outcomeForm.employment_status} onChange={(e) => setOutcomeForm({ ...outcomeForm, employment_status: e.target.value })} style={{ width: "100%", padding: 10, marginTop: 4 }}>
                    <option value="EMPLOYED">Employed</option>
                    <option value="SELF_EMPLOYED">Self-employed</option>
                    <option value="FREELANCER">Freelancer</option>
                    <option value="ENTREPRENEUR">Entrepreneur</option>
                    <option value="APPRENTICESHIP">Apprenticeship</option>
                    <option value="HIGHER_STUDIES">Higher studies</option>
                    <option value="SEEKING_EMPLOYMENT">Seeking employment</option>
                    <option value="NOT_CURRENTLY_WORKING">Not currently working</option>
                  </select>
                </label>
                <input placeholder="Employer / organization" value={outcomeForm.employer_name} onChange={(e) => setOutcomeForm({ ...outcomeForm, employer_name: e.target.value })} />
                <input placeholder="Current role" value={outcomeForm.role_title} onChange={(e) => setOutcomeForm({ ...outcomeForm, role_title: e.target.value })} />
                <input placeholder="Income range, e.g. ₹20k–₹30k" value={outcomeForm.income_band} onChange={(e) => setOutcomeForm({ ...outcomeForm, income_band: e.target.value })} />
                <input type="number" min={0} max={100} placeholder="Training relevance (0-100)" value={outcomeForm.training_relevance_score} onChange={(e) => setOutcomeForm({ ...outcomeForm, training_relevance_score: e.target.value })} />
                <textarea placeholder="What skills are still difficult?" value={outcomeForm.skill_gap_notes} onChange={(e) => setOutcomeForm({ ...outcomeForm, skill_gap_notes: e.target.value })} rows={3} />
                <button type="submit" disabled={outcomeSubmitting} style={{ padding: 10, background: "var(--accent)", color: "white", border: 0, borderRadius: 6, cursor: "pointer" }}>
                  {outcomeSubmitting ? "Saving…" : "Save check-in"}
                </button>
              </form>
              {outcomeMessage && <p style={{ marginTop: 12 }}>{outcomeMessage}</p>}
            </div>

            <div className="card">
              <h2>Outcome History</h2>
              {outcomes.length === 0 ? <p>No check-ins yet.</p> : outcomes.map((o) => (
                <div key={o.id} style={{ padding: "12px 0", borderBottom: "1px solid var(--border)" }}>
                  <strong>{o.milestone_months}-month</strong> · {o.employment_status.replaceAll("_", " ")}
                  <p style={{ margin: "6px 0" }}>{o.role_title || "Role not provided"}</p>
                  <small>{o.verification_status.replaceAll("_", " ")}</small>
                </div>
              ))}
            </div>
          </div>

          <div className="card" style={{ marginTop: 24 }}>
            <h2>Career Timeline</h2>
            {timeline.length === 0 ? <p>Your timeline will appear here as outcomes accumulate.</p> : (
              <div style={{ borderLeft: "2px solid var(--border)", marginLeft: 8, paddingLeft: 20 }}>
                {timeline.map((item, idx) => (
                  <div key={`${item.event_type}-${item.event_date}-${idx}`} style={{ position: "relative", paddingBottom: 18 }}>
                    <span style={{ position: "absolute", left: -27, top: 3, width: 10, height: 10, borderRadius: "50%", background: "var(--accent)" }} />
                    <strong>{item.title}</strong>
                    <p style={{ margin: "4px 0" }}>{item.description || item.status || ""}</p>
                    <small>{new Date(item.event_date).toLocaleDateString()} {item.status ? `· ${item.status}` : ""}</small>
                  </div>
                ))}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
