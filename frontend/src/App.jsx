import { Link, Route, Routes } from "react-router-dom";
import { ArrowRight, BookOpen, BrainCircuit, Code2, Rocket, ShieldCheck } from "lucide-react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

function Logo() {
  return (
    <Link className="brand" to="/">
      <span className="brand-mark"><Code2 size={20} /></span>
      <span>Cod2Ship</span>
    </Link>
  );
}

function Landing() {
  return (
    <div className="site">
      <nav className="nav container">
        <Logo />
        <div className="nav-links">
          <a href="#learn">What you'll learn</a>
          <a href="#how">How it works</a>
          <Link className="nav-login" to="/login">Login</Link>
        </div>
      </nav>

      <main>
        <section className="hero container">
          <div className="hero-copy">
            <div className="eyebrow"><span className="pulse" /> Hands-on learning for the next generation</div>
            <h1>Turn your ideas into <span>real projects.</span></h1>
            <p>
              Learn programming, AI and modern technology through practical work.
              Learn the skill, write the code, build the project, and ship it.
            </p>
            <div className="hero-actions">
              <Link className="button primary" to="/login">Get Started <ArrowRight size={18} /></Link>
              <a className="button secondary" href="#how">See how it works</a>
            </div>
            <div className="trust-row"><ShieldCheck size={17} /> Built with privacy and role-based access in mind.</div>
          </div>
          <div className="hero-card">
            <div className="terminal-top"><span /><span /><span /></div>
            <div className="terminal">
              <div><span className="muted">$</span> learn --topic <b>python</b></div>
              <div><span className="muted">→</span> practice: <span className="cyan">loops.py</span></div>
              <div><span className="muted">→</span> project: <span className="cyan">calculator</span></div>
              <div><span className="muted">→</span> ship: <span className="green">deployed ✓</span></div>
              <div className="cursor">▌</div>
            </div>
          </div>
        </section>

        <section id="learn" className="section container">
          <div className="section-heading"><span>01</span><h2>Learn what matters.</h2></div>
          <div className="feature-grid">
            {[
              [BookOpen, "Programming", "Build a strong coding foundation with practical exercises."],
              [BrainCircuit, "AI", "Explore AI concepts by building useful, understandable projects."],
              [Code2, "Problem Solving", "Turn problems into algorithms, code and working solutions."],
              [Rocket, "Real Projects", "Create work you can actually demonstrate and ship."]
            ].map(([Icon, title, text]) => (
              <article className="feature-card" key={title}>
                <div className="icon-box"><Icon size={21} /></div>
                <h3>{title}</h3><p>{text}</p>
              </article>
            ))}
          </div>
        </section>

        <section id="how" className="section how container">
          <div className="section-heading"><span>02</span><h2>One simple loop.</h2></div>
          <div className="steps">
            {[
              ["01", "Learn", "Understand the fundamentals."],
              ["02", "Code", "Practice by writing real code."],
              ["03", "Build", "Create projects that solve problems."],
              ["04", "Ship", "Share and launch what you build."]
            ].map(([n, title, text]) => (
              <div className="step" key={n}><span>{n}</span><h3>{title}</h3><p>{text}</p></div>
            ))}
          </div>
        </section>

        <section className="cta container">
          <div><span className="eyebrow">Ready to build?</span><h2>Start your Cod2Ship journey.</h2></div>
          <Link className="button primary" to="/login">Join Cod2Ship <ArrowRight size={18} /></Link>
        </section>
      </main>

      <footer className="footer container"><Logo /><span>Learn • Code • Build • Ship</span></footer>
    </div>
  );
}

function Login() {
  const login = () => {
    window.location.href = `${API_URL}/auth/google/login`;
  };
  return (
    <div className="auth-page">
      <div className="auth-card">
        <Logo />
        <div className="auth-icon"><Code2 size={25} /></div>
        <h1>Welcome to Cod2Ship</h1>
        <p>Learn • Code • Build</p>
        <button className="google-button" onClick={login}>
          <span className="google-g">G</span> Continue with Google
        </button>
        <Link className="back-link" to="/">← Back to Cod2Ship</Link>
      </div>
    </div>
  );
}

function Dashboard() {
  return (
    <div className="dashboard-shell">
      <nav className="nav container"><Logo /><Link className="nav-login" to="/">Home</Link></nav>
      <main className="dashboard container">
        <div className="dashboard-head"><div><span className="eyebrow">Student space</span><h1>Welcome to Cod2Ship 👋</h1><p>Your learning workspace will appear here after registration and approval.</p></div></div>
        <div className="status-card"><div><span className="status-dot" /> Registration status</div><strong>Pending</strong><p>Complete the registration form. An admin will review your request before activating your student account.</p><a className="button primary" href={API_URL + "/config/registration-form"}>Register Now <ArrowRight size={18} /></a></div>
      </main>
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/dashboard" element={<Dashboard />} />
    </Routes>
  );
}
