"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "../lib/api";

export default function Home() {
  const [events, setEvents] = useState([]);
  const [error, setError] = useState("");
  useEffect(() => { api("events/").then(setEvents).catch(e => setError(e.message)); }, []);
  return <main className="shell"><header className="topbar"><Link className="brand" href="/">PIKOM</Link><nav><Link href="/login">Attendee login</Link></nav></header>
    <section className="hero"><div className="eyebrow">Connect · Learn · Grow</div><h1>Find your next opportunity.</h1><p>Explore employers, sessions, education and training at PIKOM career events.</p></section>
    <div className="section-title"><div><div className="eyebrow muted">Discover</div><h2>Upcoming events</h2></div></div>
    {error && <p className="error">{error}</p>}{!events.length && !error && <p className="muted">Loading events…</p>}
    <div className="grid">{events.map(event => <article className="card" key={event.id}><span className="badge">Registration {event.registration_open ? "open" : "closed"}</span><h2>{event.title}</h2><p className="muted">{new Date(event.start_date).toLocaleDateString()} · {event.venue}</p><p>{event.description}</p><Link className="button" href={`/register?event=${event.id}`}>Register</Link></article>)}</div>
    <footer className="footer">PIKOM Career Festival</footer></main>;
}
