import Link from "next/link";
import { ArrowRight, BriefcaseBusiness, GraduationCap, Landmark, ShieldCheck, BarChart3 } from "lucide-react";

const journeys = [
  {
    href: "/login",
    title: "Learner Journey",
    description: "Login, view training progress, certificates, employment records, and submit outcome check-ins.",
    icon: GraduationCap,
    cta: "Open learner login",
  },
  {
    href: "/employer",
    title: "Employer Verification",
    description: "Verify a learner's employment using the one-time code and submit skill feedback.",
    icon: BriefcaseBusiness,
    cta: "Open employer dashboard",
  },
  {
    href: "/provider",
    title: "Training Provider",
    description: "Manage programs, learner completion, assessments, and certificate issuance.",
    icon: ShieldCheck,
    cta: "Open provider dashboard",
  },
  {
    href: "/verify",
    title: "Certificate Verification",
    description: "Verify a KaushalSetu certificate without exposing APAAR information.",
    icon: Landmark,
    cta: "Verify a certificate",
  },
  {
    href: "/login",
    title: "Government Intelligence",
    description: "View aggregate employment outcomes, training effectiveness, regional demand, skill gaps, and Gemini decision support.",
    icon: BarChart3,
    cta: "Open government login",
  },
];

export default function Home() {
  return (
    <main className="page-shell home-shell">
      <nav className="topbar">
        <Link className="brand" href="/">KaushalSetu</Link>
        <div className="nav-actions">
          <Link href="/demo">Demo guide</Link>
          <Link href="/login">Login</Link>
          <Link className="button button-primary button-small" href="/register">Create account</Link>
        </div>
      </nav>

      <section className="hero hero-home">
        <div>
          <p className="eyebrow">Smart India Hackathon • Skill Outcome Intelligence</p>
          <h1>From training records to real employment outcomes.</h1>
          <p className="subtitle">
            KaushalSetu connects training, assessments, certificates, employment verification,
            employer feedback, and longitudinal career outcomes in one platform.
          </p>
          <div className="hero-actions">
            <Link className="button button-primary" href="/demo">
              Run demo <ArrowRight size={18} />
            </Link>
            <Link className="button button-secondary" href="/login">
              Sign in
            </Link>
            <Link className="button button-secondary" href="/verify">
              Verify certificate
            </Link>
          </div>
        </div>
      </section>

      <section className="demo-strip">
        <div>
          <span className="dot" />
          <strong>Backend connected</strong>
          <span className="muted">Phase 5 government intelligence and Gemini decision support are available for testing.</span>
        </div>
        <Link href="/demo">Open demo guide →</Link>
      </section>

      <section className="section-heading">
        <p className="eyebrow">Test the platform</p>
        <h2>Five role-based journeys</h2>
        <p className="muted">Use the guided flow instead of jumping into role screens without authentication.</p>
      </section>

      <section className="journey-grid">
        {journeys.map(({ href, title, description, icon: Icon, cta }) => (
          <article className="journey-card" key={href}>
            <div className="icon-wrap"><Icon size={22} /></div>
            <h3>{title}</h3>
            <p>{description}</p>
            <Link className="card-link" href={href}>
              {cta} <ArrowRight size={16} />
            </Link>
          </article>
        ))}
      </section>

      <section className="workflow-card">
        <div>
          <p className="eyebrow">End-to-end intelligence loop</p>
          <h2>Training → Employment → Verified evidence → Skill gaps → Government action</h2>
          <p className="muted">
            Report employment as a learner, share the generated code with an authenticated employer, verify the employment,
            collect skill feedback, then inspect aggregate supply-demand gaps and training outcomes from the government dashboard.
          </p>
        </div>
        <div className="workflow-steps">
          <span>1. Learner reports employment</span>
          <span>2. Employer verifies</span>
          <span>3. Employer rates skills</span>
          <span>4. Timeline and skill evidence update</span>
          <span>5. Government dashboard turns evidence into action</span>
        </div>
      </section>

      <footer className="footer">
        <Link href="/demo">Demo guide</Link>
        <Link href="/login">Login</Link>
        <Link href="/register">Register</Link>
        <Link href="/provider">Provider</Link>
        <Link href="/employer">Employer</Link>
        <Link href="/verify">Certificate verification</Link>
      </footer>
    </main>
  );
}
