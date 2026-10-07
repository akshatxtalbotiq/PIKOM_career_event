"use client";

import { useState } from "react";

export default function SessionsView({ sessions = [], me, busy, action }) {
  const [search, setSearch] = useState("");
  const isApproved = me.approval_status === "approved";

  const filtered = sessions.filter((session) =>
    `${session.title} ${session.speaker} ${session.location} ${session.description || ""}`
      .toLowerCase()
      .includes(search.toLowerCase())
  );

  return (
    <div className="stack" style={{ gap: "1.5rem" }}>
      {/* Search Input Filter */}
      <div style={{ maxWidth: "480px" }}>
        <input
          type="search"
          className="search-input"
          placeholder="Search session title, speaker, or stage..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      <div className="eyebrow muted">
        SCHEDULED PROGRAMME · {filtered.length} SESSIONS
      </div>

      {!filtered.length && (
        <div className="card" style={{ textAlign: "center", padding: "3rem 1.5rem" }}>
          <p className="muted" style={{ margin: 0 }}>
            No sessions match your search &ldquo;{search}&rdquo;.
          </p>
        </div>
      )}

      <div className="grid">
        {filtered.map((session) => {
          const isFull = session.remaining === 0;
          return (
            <article
              className="card"
              key={session.id}
              style={{ display: "flex", flexDirection: "column", justifyContent: "space-between" }}
            >
              <div>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "0.5rem", marginBottom: "0.75rem" }}>
                  <span className={`badge ${session.remaining !== null && session.remaining < 15 ? "brick" : ""}`}>
                    {session.remaining === null ? "Open Seating" : isFull ? "Sold Out / Full" : `${session.remaining} Seats Left`}
                  </span>
                  <span className="mono-indicator" style={{ fontSize: "0.72rem" }}>
                    📍 {session.location}
                  </span>
                </div>

                <h3>{session.title}</h3>

                {session.speaker && (
                  <p className="editorial-serif" style={{ fontSize: "1.05rem", color: "var(--ink)", margin: "0.2rem 0 0.6rem" }}>
                    Presented by {session.speaker}
                  </p>
                )}

                <p className="muted" style={{ fontSize: "0.88rem", fontWeight: 600, margin: "0 0 0.75rem" }}>
                  🗓️ {new Date(`${session.date}T00:00:00`).toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" })} · ⏰ {session.start_time.slice(0, 5)}–{session.end_time.slice(0, 5)}
                </p>

                <p style={{ color: "var(--ink-muted)", fontSize: "0.94rem", lineHeight: 1.6, marginBottom: "1.25rem" }}>
                  {session.description}
                </p>
              </div>

              <div>
                <button
                  disabled={busy || !isApproved || isFull}
                  onClick={() => action(`sessions/${session.id}/registration/`)}
                  style={{ width: "100%", fontSize: "0.84rem" }}
                >
                  {isFull ? "Session Full" : "Reserve Seat in Schedule →"}
                </button>
              </div>
            </article>
          );
        })}
      </div>
    </div>
  );
}

