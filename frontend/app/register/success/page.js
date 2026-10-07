"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

export default function Success() {
  const [number, setNumber] = useState("");

  useEffect(() => {
    setNumber(sessionStorage.getItem("pikom-registration-number") || "");
  }, []);

  return (
    <main className="shell">
      <header className="topbar">
        <Link className="brand-wrapper" href="/">
          <span className="brand">PIKOM</span>
          <span className="brand-tag">CAREER FESTIVAL · 2026</span>
        </Link>
        <nav>
          <Link className="button secondary" href="/">
            Festival Home
          </Link>
        </nav>
      </header>

      <div style={{ maxWidth: "620px", margin: "2rem auto" }}>
        <section className="card" style={{ padding: "clamp(2rem, 5vw, 3.5rem)", textAlign: "center" }}>
          <div className="eyebrow" style={{ marginBottom: "0.75rem" }}>
            CONFIRMATION · DELEGATE ADMISSION
          </div>

          <h1 className="display-title" style={{ fontSize: "clamp(2.2rem, 6vw, 3.6rem)", marginBottom: "0.5rem" }}>
            Registration Submitted
          </h1>

          <p className="muted" style={{ fontSize: "1rem", lineHeight: 1.6, maxWidth: "500px", margin: "0 auto 1.75rem" }}>
            Your registration is currently being verified by the PIKOM event team. A confirmation email has been dispatched to your inbox.
          </p>

          {number && (
            <div
              style={{
                background: "var(--surface-tint)",
                border: "1px dashed var(--border-cream-dark)",
                borderRadius: "var(--radius-md)",
                padding: "1.5rem",
                margin: "1.5rem 0 2rem",
              }}
            >
              <div className="mono-indicator" style={{ marginBottom: "0.25rem", color: "var(--ink-muted)" }}>
                DELEGATE REFERENCE CODE
              </div>
              <div
                style={{
                  fontFamily: "var(--font-display)",
                  fontSize: "clamp(2rem, 5vw, 2.8rem)",
                  color: "var(--brick-red)",
                  letterSpacing: "0.05em",
                }}
              >
                {number}
              </div>
            </div>
          )}

          <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem", alignItems: "center" }}>
            <Link className="button" href="/dashboard" style={{ width: "100%", maxWidth: "340px" }}>
              Open Attendee Portal →
            </Link>
            <p className="muted" style={{ fontSize: "0.85rem", marginTop: "0.5rem" }}>
              Your access code is saved to this browser for automatic sign-in.
            </p>
          </div>
        </section>
      </div>

      <footer className="footer">
        <div>PIKOM CAREER FESTIVAL · DELEGATE CONFIRMATION</div>
        <div>OFFICIAL RECEIPT</div>
      </footer>
    </main>
  );
}

