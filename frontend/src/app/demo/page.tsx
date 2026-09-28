"use client";

import Link from "next/link";

const steps = [
  { n: "1", title: "Learner", text: "Sign in, verify demo APAAR, report a job and copy the one-time employment code.", href: "/login?role=TRAINEE", label: "Open learner login" },
  { n: "2", title: "Employer", text: "Sign in as an employer, paste the learner's code, verify the job, then provide skill feedback.", href: "/login?role=EMPLOYER", label: "Sign in as employer" },
  { n: "3", title: "Learner", text: "Return to the learner profile and see the employer-verified outcome and longitudinal record.", href: "/profile", label: "Open learner profile" },
  { n: "4", title: "Public verifier", text: "Certificate verification is deliberately public. It does not expose or require APAAR information.", href: "/verify", label: "Open verifier" },
  { n: "5", title: "Government", text: "Sign in as a government administrator to inspect aggregate outcomes, skill gaps, training effectiveness, and Gemini decision support.", href: "/login?role=GOVERNMENT_ADMIN", label: "Open government login" },
];

export default function DemoPage() {
  return (
    <div className="page-shell">
      <div className="nav"><Link href="/">Home</Link><Link href="/login">Login</Link></div>
      <div className="hero-card card">
        <span className="eyebrow">SIH demo center</span>
        <h1 className="page-title">Run the KaushalSetu story end to end.</h1>
        <p className="muted">Authentication and role boundaries are explicit. Government analytics are aggregate-only and employer verification remains authenticated. Employment verification is an authenticated employer action; certificate verification is intentionally public.</p>
      </div>
      <div className="demo-flow-grid">
        {steps.map((s) => (
          <div className="card demo-step" key={s.n}>
            <div className="step-number">{s.n}</div>
            <span className="eyebrow">{s.title}</span>
            <h2>{s.text}</h2>
            <Link className="button button-primary" href={s.href}>{s.label}</Link>
          </div>
        ))}
      </div>
      <div className="card section-gap">
        <h2>Seeded demo accounts</h2>
        <div className="credential-grid">
          <div><strong>Learner</strong><code>learner1@example.com / learner123</code></div>
          <div><strong>Employer</strong><code>hr@techcorp.com / emp123</code></div>
          <div><strong>Training Provider</strong><code>provider@training.com / provider123</code></div>
          <div><strong>Government</strong><code>admin@gov.in / admin123</code></div>
        </div>
      </div>
    </div>
  );
}
