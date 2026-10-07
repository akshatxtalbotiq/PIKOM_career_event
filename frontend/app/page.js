"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { PinIcon, ArrowUpRightIcon, CalendarIcon } from "../components/Icons";

export default function Home() {
  const [events, setEvents] = useState([]);
  const [error, setError] = useState("");
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    api("events/")
      .then(setEvents)
      .catch((e) => setError(e.message))
      .finally(() => setLoaded(true));
  }, []);

  return (
    <main className="shell">
      <header className="topbar">
        <Link className="brand-wrapper" href="/">
          <span className="brand">PIKOM</span>
          <span className="brand-tag">CAREER FESTIVAL · 2026</span>
        </Link>
        <nav>
          <Link className="button secondary" href="/login">
            Attendee Login
          </Link>
        </nav>
      </header>

      {/* Hero Section (Section 7) */}
      <section className="hero">
        <div className="eyebrow">NATIONAL TALENT INITIATIVE · 2026</div>
        <h1>
          Find
          <br />
          Your Next
          <br />
          Move.
        </h1>
        <p>
          Connect directly with top technology employers, schedule 1-on-1 interviews, attend industry keynotes, and discover university degree pathways across Malaysia.
        </p>
        <div className="hero-actions">
          <a className="button" href="#events">
            Explore Events
          </a>
          <Link className="button secondary" href="/login" style={{ background: "rgba(255,255,255,0.08)", color: "#fff", borderColor: "rgba(255,255,255,0.2)" }}>
            Access Portal <ArrowUpRightIcon size={14} />
          </Link>
        </div>
      </section>

      {/* Metrics Section (Section 9) */}
      <div className="metrics-grid">
        <div className="metric-card">
          <span className="metric-number">120+</span>
          <span className="metric-label">Companies Attending</span>
        </div>
        <div className="metric-card">
          <span className="metric-number">50+</span>
          <span className="metric-label">Keynotes & Sessions</span>
        </div>
        <div className="metric-card">
          <span className="metric-number">1-ON-1</span>
          <span className="metric-label">Direct Interviews</span>
        </div>
        <div className="metric-card">
          <span className="metric-number">FREE</span>
          <span className="metric-label">Delegate Pass</span>
        </div>
      </div>

      {/* Editorial Chapter Break (Section 15) */}
      <section className="chapter-break" id="events">
        <div className="chapter-number">01 / CALENDAR</div>
        <h2>Upcoming Festivals & Career Fairs</h2>
        <p>
          Select an event below to register your delegate attendance. Approved attendees unlock digital fast-track check-in and 1-on-1 interview scheduling.
        </p>
      </section>

      {error && (
        <p className="error" role="alert" style={{ margin: "2rem 0" }}>
          {error}
        </p>
      )}

      {!loaded && !error && (
        <p className="muted" style={{ padding: "2rem 0", textAlign: "center" }}>
          Loading scheduled events…
        </p>
      )}

      {loaded && !events.length && !error && (
        <p className="muted" style={{ padding: "2rem 0", textAlign: "center" }}>
          No upcoming events are available yet. Please check back soon.
        </p>
      )}

      <div className="grid">
        {events.map((event) => (
          <article className="card" key={event.id} style={{ display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem" }}>
                <span className={`badge ${event.registration_open ? "brick" : ""}`}>
                  {event.registration_open ? "Registration Open" : "Registration Closed"}
                </span>
                <span className="mono-indicator" style={{ display: "inline-flex", alignItems: "center", gap: "0.35rem" }}>
                  <CalendarIcon size={13} />
                  {new Date(event.start_date).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" })}
                </span>
              </div>
              <h2>{event.title}</h2>
              <p className="muted" style={{ fontSize: "0.92rem", marginBottom: "0.75rem", fontWeight: 600, display: "flex", alignItems: "center", gap: "0.4rem" }}>
                <PinIcon size={14} style={{ color: "var(--brick-red)" }} /> {event.venue}
              </p>
              <p style={{ color: "var(--ink-muted)", fontSize: "0.95rem", lineHeight: 1.6, marginBottom: "1.5rem" }}>
                {event.description}
              </p>
            </div>
            <div>
              <Link className="button" href={`/register?event=${event.id}`} style={{ width: "100%" }}>
                Register for Event <ArrowUpRightIcon size={14} />
              </Link>
            </div>
          </article>
        ))}
      </div>

      <footer className="footer">
        <div>PIKOM CAREER FESTIVAL · 2026 EDITION</div>
        <div>ALL RIGHTS RESERVED</div>
      </footer>
    </main>
  );
}
