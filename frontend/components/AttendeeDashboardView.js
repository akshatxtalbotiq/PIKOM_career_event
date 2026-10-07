import Link from "next/link";
import { PinIcon, CalendarIcon, ClockIcon } from "./Icons";

export default function DashboardView({ me, event, schedule }) {
  const isPending = me.approval_status !== "approved";

  return (
    <div className="stack" style={{ gap: "2rem" }}>
      {/* Attendee Dossier Welcome Card */}
      <article
        className="card"
        style={{
          padding: "clamp(1.75rem, 5vw, 3rem)",
          background: "var(--surface-cream)",
          border: "1px solid var(--border-cream)",
          borderRadius: "var(--radius-xl)",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "1rem", marginBottom: "1rem" }}>
          <div className="eyebrow">
            01 / ATTENDEE DOSSIER {me.registration_number ? `· REF: ${me.registration_number}` : ""}
          </div>
          <span className={`badge ${isPending ? "brick" : "dark"}`}>
            REGISTRATION {me.approval_status?.toUpperCase()}
          </span>
        </div>

        <h2 style={{ fontSize: "clamp(2.4rem, 6vw, 4rem)", marginBottom: "0.5rem" }}>
          Welcome, {me.name}
        </h2>

        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", flexWrap: "wrap", margin: "0.5rem 0 1.25rem", color: "var(--ink-muted)", fontSize: "1rem" }}>
          <span style={{ fontWeight: 700, color: "var(--ink)" }}>{event.title}</span>
          <span>·</span>
          <span style={{ display: "inline-flex", alignItems: "center", gap: "0.35rem" }}>
            <PinIcon size={15} style={{ color: "var(--brick-red)" }} />
            {event.venue}
          </span>
          <span>·</span>
          <span style={{ display: "inline-flex", alignItems: "center", gap: "0.35rem" }}>
            <CalendarIcon size={15} />
            {new Date(event.start_date).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" })}
          </span>
          <span>·</span>
          <span style={{ display: "inline-flex", alignItems: "center", gap: "0.35rem" }}>
            <ClockIcon size={14} />
            {event.event_time}
          </span>
        </div>

        <p style={{ color: "var(--ink-muted)", fontSize: "1.05rem", lineHeight: 1.65, maxWidth: "780px", margin: "0 0 1.5rem" }}>
          {event.description}
        </p>

        {isPending && (
          <div
            style={{
              padding: "1rem 1.25rem",
              background: "var(--brick-red-light)",
              border: "1px solid var(--brick-red-border)",
              borderRadius: "var(--radius-sm)",
              color: "var(--brick-red)",
              fontSize: "0.92rem",
              fontWeight: 500,
            }}
          >
            <strong>Note:</strong> Your registration is currently awaiting organizer verification. Once approved, you can immediately book 1-on-1 interviews and access your check-in entry pass.
          </div>
        )}
      </article>

      {/* Metrics & Statistics (Section 9) */}
      <div>
        <div className="eyebrow muted" style={{ marginBottom: "0.5rem" }}>
          02 / YOUR EVENT ENGAGEMENT
        </div>
        <div className="metrics-grid" style={{ margin: "0.5rem 0 0" }}>
          <div className="metric-card">
            <span className="metric-number">{schedule ? schedule.interviews?.length : 0}</span>
            <span className="metric-label">Interviews Booked</span>
          </div>
          <div className="metric-card">
            <span className="metric-number">{schedule ? schedule.sessions?.length : 0}</span>
            <span className="metric-label">Sessions Reserved</span>
          </div>
          <div className="metric-card">
            <span className="metric-number">{schedule ? schedule.saved_jobs?.length : 0}</span>
            <span className="metric-label">Saved Jobs</span>
          </div>
          <div className="metric-card">
            <span className="metric-number">{schedule ? schedule.promotions?.length : 0}</span>
            <span className="metric-label">Perks Claimed</span>
          </div>
        </div>
      </div>

      {/* Action Pathways */}
      <div>
        <div className="eyebrow muted" style={{ marginBottom: "0.75rem" }}>
          03 / PORTAL DIRECTORY
        </div>
        <div className="grid">
          <article className="card" style={{ display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
            <div>
              <span className="badge" style={{ marginBottom: "0.75rem" }}>ITINERARY</span>
              <h3>My Schedule</h3>
              <p className="muted" style={{ fontSize: "0.92rem", marginBottom: "1.25rem" }}>
                {schedule
                  ? `${schedule.interviews?.length || 0} interviews · ${schedule.sessions?.length || 0} sessions reserved`
                  : "Loading your schedule…"}
              </p>
            </div>
            <Link className="button secondary" href="/dashboard/bookings" style={{ width: "100%" }}>
              Manage Schedule →
            </Link>
          </article>

          <article className="card" style={{ display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
            <div>
              <span className="badge brick" style={{ marginBottom: "0.75rem" }}>FAST-TRACK</span>
              <h3>Digital Check-in Pass</h3>
              <p className="muted" style={{ fontSize: "0.92rem", marginBottom: "1.25rem" }}>
                Access your personalized delegate QR code to present at venue reception.
              </p>
            </div>
            <Link className="button" href="/check-in" style={{ width: "100%" }}>
              Open Pass →
            </Link>
          </article>

          <article className="card" style={{ display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
            <div>
              <span className="badge" style={{ marginBottom: "0.75rem" }}>OPPORTUNITIES</span>
              <h3>Explore Jobs</h3>
              <p className="muted" style={{ fontSize: "0.92rem", marginBottom: "1.25rem" }}>
                Browse tech positions and graduate roles posted by attending employers.
              </p>
            </div>
            <Link className="button secondary" href="/jobs" style={{ width: "100%" }}>
              View Jobs →
            </Link>
          </article>

          <article className="card" style={{ display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
            <div>
              <span className="badge" style={{ marginBottom: "0.75rem" }}>NAVIGATION</span>
              <h3>Venue Floor Map</h3>
              <p className="muted" style={{ fontSize: "0.92rem", marginBottom: "1.25rem" }}>
                Locate employer booths, stage halls, and interview suites with interactive map.
              </p>
            </div>
            <Link className="button secondary" href="/floor-map" style={{ width: "100%" }}>
              Explore Map →
            </Link>
          </article>
        </div>
      </div>
    </div>
  );
}
