"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { apiFetch, clearAuth, readError } from "@/lib/api";

type Overview = {
  total_learners: number;
  total_enrollments: number;
  completed_enrollments: number;
  completion_rate: number;
  certificates_issued: number;
  trained_learners: number;
  verified_employment_learners: number;
  employment_rate: number;
  self_employed_learners: number;
  milestone_employment_rates: Record<string, number>;
  retention_rates: Record<string, number>;
  average_training_relevance: number;
};

type SkillRow = {
  skill_id: string;
  skill: string;
  category: string;
  trained_learners: number;
  avg_proficiency: number;
  job_demand: number;
  demand_supply_ratio: number;
  gap: number;
  training_program_coverage: number;
  priority: string;
};

type ProgramRow = {
  program_id: string;
  program: string;
  category: string;
  enrolled: number;
  completed: number;
  completion_rate: number;
  certified: number;
  certification_rate: number;
  verified_employed: number;
  employment_rate: number;
  avg_assessment_score: number;
  skills_covered: string[];
};

type RegionRow = {
  region: string;
  learners: number;
  verified_employed: number;
  employment_rate: number;
  active_jobs: number;
  top_demand_skills: string[];
};

type Insight = {
  summary: string;
  observed_facts: string[];
  priority_skill_gaps: Array<{ skill: string; demand: number; supply: number; gap: number; priority: string; rationale?: string }>;
  recommended_actions: string[];
  caveat: string;
  ai_status?: string;
};

const priorityClass: Record<string, string> = {
  CRITICAL: "pill pill-critical",
  HIGH: "pill pill-high",
  MEDIUM: "pill pill-medium",
  LOW: "pill pill-low",
};

function Metric({ label, value, note }: { label: string; value: string | number; note?: string }) {
  return (
    <div className="metric-card">
      <span>{label}</span>
      <strong>{value}</strong>
      {note && <small>{note}</small>}
    </div>
  );
}

export default function AdminPage() {
  const router = useRouter();
  const [ready, setReady] = useState(false);
  const [overview, setOverview] = useState<Overview | null>(null);
  const [skills, setSkills] = useState<SkillRow[]>([]);
  const [programs, setPrograms] = useState<ProgramRow[]>([]);
  const [regions, setRegions] = useState<RegionRow[]>([]);
  const [insight, setInsight] = useState<Insight | null>(null);
  const [loading, setLoading] = useState(true);
  const [aiBusy, setAiBusy] = useState(false);
  const [question, setQuestion] = useState("Why do some training programs have high completion but lower employment conversion?");
  const [aiAnswer, setAiAnswer] = useState<any>(null);
  const [error, setError] = useState("");
  const [lastUpdated, setLastUpdated] = useState<string>("");

  async function loadDashboard() {
    setError("");
    setLoading(true);
    const responses = await Promise.all([
      apiFetch("/admin/analytics/overview"),
      apiFetch("/admin/analytics/skills/supply-demand"),
      apiFetch("/admin/analytics/training-effectiveness"),
      apiFetch("/admin/analytics/regions"),
      apiFetch("/admin/analytics/insights?use_ai=false"),
    ]);
    if (responses.some((response) => !response.ok)) {
      setError(await readError(responses.find((response) => !response.ok)!, "Could not load government analytics."));
      setLoading(false);
      return;
    }
    const [overviewRes, skillsRes, programsRes, regionsRes, insightRes] = responses;
    setOverview(await overviewRes.json());
    setSkills((await skillsRes.json()).skills);
    setPrograms((await programsRes.json()).programs);
    setRegions((await regionsRes.json()).regions);
    setInsight(await insightRes.json());
    setLastUpdated(new Date().toLocaleString());
    setLoading(false);
  }

  useEffect(() => {
    (async () => {
      const meRes = await apiFetch("/auth/me");
      if (!meRes.ok) {
        clearAuth();
        router.replace("/login");
        return;
      }
      const me = await meRes.json();
      if (me.role !== "GOVERNMENT_ADMIN") {
        router.replace("/dashboard");
        return;
      }
      setReady(true);
      await loadDashboard();
    })();
  }, [router]);

  const topSkillGaps = useMemo(() => skills.filter((row) => row.priority === "CRITICAL" || row.priority === "HIGH").slice(0, 8), [skills]);
  const maxDemand = Math.max(...skills.map((row) => row.job_demand), 1);
  const maxJobs = Math.max(...regions.map((row) => row.active_jobs), 1);

  async function generateAI() {
    setAiBusy(true);
    setAiAnswer(null);
    try {
      const res = await apiFetch("/admin/analytics/insights?use_ai=true");
      if (!res.ok) throw new Error(await readError(res, "Gemini insight failed"));
      setInsight(await res.json());
    } catch (err: any) {
      setError(err.message || "Gemini insight failed");
    } finally {
      setAiBusy(false);
    }
  }

  async function exportCsv() {
    try {
      const res = await apiFetch("/admin/analytics/export.csv");
      if (!res.ok) throw new Error(await readError(res, "Could not export analytics."));
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = "kaushalsetu-aggregate-analytics.csv";
      anchor.click();
      URL.revokeObjectURL(url);
    } catch (err: any) {
      setError(err.message || "Could not export analytics.");
    }
  }

  async function askAI() {
    setAiBusy(true);
    setAiAnswer(null);
    try {
      const res = await apiFetch("/admin/analytics/ai/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });
      if (!res.ok) throw new Error(await readError(res, "Could not answer the question"));
      setAiAnswer(await res.json());
    } catch (err: any) {
      setError(err.message || "AI request failed");
    } finally {
      setAiBusy(false);
    }
  }

  if (!ready || loading) {
    return <div className="page-shell"><div className="loading-panel">Loading government intelligence…</div></div>;
  }

  return (
    <main className="page-shell admin-shell">
      <nav className="topbar">
        <Link className="brand" href="/">KaushalSetu</Link>
        <div className="nav-actions">
          <Link href="/demo">Demo</Link>
          <Link href="/profile">Account</Link>
          <button className="link-button" onClick={() => { clearAuth(); router.push("/"); }}>Logout</button>
        </div>
      </nav>

      <section className="admin-hero">
        <div>
          <span className="eyebrow">Government Outcome Intelligence</span>
          <h1 className="page-title">From training data to decisions.</h1>
          <p className="subtitle admin-subtitle">
            Monitor employment outcomes, training effectiveness, regional demand, and skill gaps without exposing individual learner identities.
          </p><div className="data-freshness">Aggregate view · {lastUpdated ? `updated ${lastUpdated}` : "loading"}</div>
        </div>
        <div className="admin-hero-actions">
          <button className="button button-primary" onClick={loadDashboard}>Refresh data</button>
          <button className="button button-secondary" onClick={generateAI} disabled={aiBusy}>{aiBusy ? "Thinking…" : "Generate Gemini insight"}</button><button className="button button-secondary" onClick={exportCsv}>Export CSV</button><button className="button button-secondary" onClick={() => window.print()}>Print brief</button>
        </div>
      </section>

      {error && <div className="alert alert-error section-gap">{error}</div>}

      {overview && <>
        <section className="metrics-grid">
          <Metric label="Learners" value={overview.total_learners} note="tracked longitudinally" />
          <Metric label="Completion rate" value={`${overview.completion_rate}%`} note={`${overview.completed_enrollments} completed enrollments`} />
          <Metric label="Certificates" value={overview.certificates_issued} note="issued records" />
          <Metric label="Verified employment" value={`${overview.employment_rate}%`} note={`${overview.verified_employment_learners} learners`} />
          <Metric label="3-month employment" value={`${overview.milestone_employment_rates["3"] ?? 0}%`} note="outcome check-ins" />
          <Metric label="12-month retention" value={`${overview.retention_rates["12"] ?? 0}%`} note="same-employer signal" />
        </section>

        <section className="analytics-grid">
          <div className="card">
            <div className="section-heading compact-heading">
              <span className="eyebrow">Outcome funnel</span>
              <h2>Training → Employment</h2>
            </div>
            <div className="funnel">
              <div><span>Enrolled</span><strong>{overview.total_enrollments}</strong></div>
              <div><span>Completed</span><strong>{overview.completed_enrollments}</strong></div>
              <div><span>Certified</span><strong>{overview.certificates_issued}</strong></div>
              <div><span>Verified employed</span><strong>{overview.verified_employment_learners}</strong></div>
            </div>
          </div>

          <div className="card">
            <div className="section-heading compact-heading">
              <span className="eyebrow">Longitudinal signal</span>
              <h2>Employment & retention</h2>
            </div>
            <div className="milestone-grid">
              {[3, 6, 12].map((months) => (
                <div key={months} className="milestone-card">
                  <span>{months}-month</span>
                  <strong>{overview.milestone_employment_rates[String(months)] ?? 0}%</strong>
                  <small>employment</small>
                  <em>{overview.retention_rates[String(months)] ?? 0}% retention</em>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="card section-gap">
          <div className="section-heading compact-heading">
            <span className="eyebrow">Labour-market intelligence</span>
            <h2>Skill supply vs employer demand</h2>
            <p className="muted">Supply = learners with proficiency ≥60. Demand = active job postings requiring the skill.</p>
          </div>
          <div className="skill-table">
            {skills.slice(0, 12).map((row) => (
              <div className="skill-row" key={row.skill_id}>
                <div className="skill-name"><strong>{row.skill}</strong><span>{row.category}</span></div>
                <div className="bar-cell"><span>Supply {row.trained_learners}</span><div className="bar-track"><div className="bar bar-supply" style={{ width: `${Math.min(100, (row.trained_learners / Math.max(maxDemand, 1)) * 100)}%` }} /></div></div>
                <div className="bar-cell"><span>Demand {row.job_demand}</span><div className="bar-track"><div className="bar bar-demand" style={{ width: `${Math.min(100, (row.job_demand / maxDemand) * 100)}%` }} /></div></div>
                <div>{row.job_demand > 0 ? <span className={priorityClass[row.priority] || "pill"}>{row.priority}</span> : <span className="pill pill-low">LOW</span>}</div>
              </div>
            ))}
          </div>
        </section>

        <section className="analytics-grid section-gap">
          <div className="card">
            <div className="section-heading compact-heading">
              <span className="eyebrow">Program outcomes</span>
              <h2>Training effectiveness</h2>
            </div>
            <div className="simple-list">
              {programs.map((program) => (
                <div key={program.program_id}>
                  <strong>{program.program}</strong>
                  <span>{program.completed}/{program.enrolled} completed · {program.certification_rate}% certified · {program.employment_rate}% verified employed</span>
                  <small>Skills: {program.skills_covered.join(", ") || "not mapped"}</small>
                </div>
              ))}
            </div>
          </div>

          <div className="card">
            <div className="section-heading compact-heading">
              <span className="eyebrow">Regional intelligence</span>
              <h2>Demand hotspots</h2>
            </div>
            <div className="region-list">
              {regions.slice(0, 8).map((region) => (
                <div className="region-row" key={region.region}>
                  <div><strong>{region.region}</strong><span>{region.learners} learners · {region.verified_employed} verified employed</span></div>
                  <div className="region-metric"><strong>{region.active_jobs}</strong><span>jobs</span></div>
                  <div className="mini-track"><div className="bar bar-demand" style={{ width: `${Math.min(100, (region.active_jobs / maxJobs) * 100)}%` }} /></div>
                  <small>{region.top_demand_skills.slice(0, 3).join(" · ")}</small>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="card section-gap executive-brief">
          <div>
            <span className="eyebrow">Executive brief</span>
            <h2>What the data says right now</h2>
            <p className="muted">Use these signals to decide where to investigate, not as standalone causal conclusions.</p>
          </div>
          <div className="brief-grid">
            <div><strong>{topSkillGaps.length}</strong><span>priority skill gaps</span></div>
            <div><strong>{programs.filter((p) => p.completed > 0 && p.employment_rate < 50).length}</strong><span>programs under 50% verified employment</span></div>
            <div><strong>{regions.filter((r) => r.active_jobs > 0).length}</strong><span>regions with active jobs</span></div>
            <div><strong>{overview.average_training_relevance}%</strong><span>average reported training relevance</span></div>
          </div>
        </section>

        <section className="card section-gap ai-panel">
          <div className="section-heading compact-heading">
            <span className="eyebrow">Gemini decision support</span>
            <h2>Ask the dashboard</h2>
            <p className="muted">Gemini receives aggregate analytics, not raw APAAR IDs or individual records.</p>
          </div>
          <div className="ai-question-row">
            <input value={question} onChange={(e) => setQuestion(e.target.value)} />
            <button className="button button-primary" onClick={askAI} disabled={aiBusy || !question.trim()}>{aiBusy ? "Thinking…" : "Ask Gemini"}</button>
          </div>
          {aiAnswer && <div className="ai-result">
            <strong>{aiAnswer.answer}</strong>
            <div><span className="eyebrow">Observed facts</span>{aiAnswer.observed_facts?.map((item: string) => <p key={item}>• {item}</p>)}</div>
            <div><span className="eyebrow">Possible contributing factors</span>{aiAnswer.possible_contributing_factors?.map((item: string) => <p key={item}>• {item}</p>)}</div>
            <div><span className="eyebrow">Recommended investigation</span>{aiAnswer.recommended_investigation?.map((item: string) => <p key={item}>• {item}</p>)}</div>
            <small>{aiAnswer.caveat}</small>
          </div>}
        </section>

        {insight && <section className="card section-gap insight-card">
          <div className="section-heading compact-heading">
            <span className="eyebrow">Priority insight</span>
            <h2>{insight.summary}</h2>
          </div>
          <div className="insight-grid">
            <div><strong>Observed facts</strong>{insight.observed_facts.map((item) => <p key={item}>• {item}</p>)}</div>
            <div><strong>Priority skill gaps</strong>{insight.priority_skill_gaps.map((gap) => <p key={gap.skill}>• {gap.skill}: demand {gap.demand}, supply {gap.supply}, gap {gap.gap}</p>)}</div>
            <div><strong>Recommended actions</strong>{insight.recommended_actions.map((item) => <p key={item}>• {item}</p>)}</div>
          </div>
          <small>{insight.caveat} · Source: {insight.ai_status || "deterministic"}</small>
        </section>}
      </>}
    </main>
  );
}
