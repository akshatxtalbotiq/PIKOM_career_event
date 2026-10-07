"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { api, saveToken } from "../../lib/api";

function LoginForm() {
  const router = useRouter();
  const [token, setValue] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    const supplied = new URLSearchParams(location.search).get("token");
    if (supplied) setValue(supplied);
  }, []);

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      saveToken(token.trim());
      await api("me/");
      router.push("/dashboard");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="shell">
      <header className="topbar">
        <Link className="brand-wrapper" href="/">
          <span className="brand">PIKOM</span>
          <span className="brand-tag">CAREER FESTIVAL · 2026</span>
        </Link>
        <nav>
          <Link className="button secondary" href="/">
            ← Back to Festivals
          </Link>
        </nav>
      </header>

      <div style={{ maxWidth: "560px", margin: "2rem auto" }}>
        <section className="card" style={{ padding: "clamp(1.75rem, 5vw, 3rem)" }}>
          <div className="eyebrow" style={{ marginBottom: "0.5rem" }}>
            00 / AUTHORIZATION GATE
          </div>
          <h1 className="display-title" style={{ fontSize: "clamp(2rem, 5vw, 3rem)", marginBottom: "0.5rem" }}>
            Attendee Access
          </h1>
          <p className="muted" style={{ marginBottom: "1.75rem", fontSize: "0.98rem", lineHeight: 1.6 }}>
            Open your private attendee access link from your registration confirmation email, or enter your personal access code below.
          </p>

          <form className="form" onSubmit={submit} style={{ maxWidth: "100%" }}>
            <label>
              <span className="editorial-label muted" style={{ fontSize: "0.75rem" }}>
                Attendee Access Code
              </span>
              <input
                required
                placeholder="e.g. reg_xyz789..."
                value={token}
                onChange={(e) => setValue(e.target.value)}
                autoComplete="off"
                spellCheck="false"
              />
            </label>

            {error && (
              <p className="error" role="alert" style={{ margin: "0.25rem 0" }}>
                {error}
              </p>
            )}

            <button disabled={busy} style={{ width: "100%", marginTop: "0.5rem" }}>
              {busy ? "Verifying Credentials…" : "Enter Attendee Portal →"}
            </button>
          </form>

          <div style={{ marginTop: "2rem", paddingTop: "1.5rem", borderTop: "1px solid var(--border-cream)", textAlign: "center" }}>
            <p className="muted" style={{ fontSize: "0.88rem", margin: 0 }}>
              Need to register? <Link href="/" style={{ color: "var(--brick-red)", fontWeight: 700 }}>Browse upcoming festivals</Link>
            </p>
          </div>
        </section>
      </div>

      <footer className="footer">
        <div>PIKOM CAREER FESTIVAL · ATTENDEE GATEWAY</div>
        <div>SECURE ACCESS</div>
      </footer>
    </main>
  );
}

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <main className="shell">
          <p className="muted" style={{ textAlign: "center", padding: "4rem 0" }}>
            Loading login portal…
          </p>
        </main>
      }
    >
      <LoginForm />
    </Suspense>
  );
}

