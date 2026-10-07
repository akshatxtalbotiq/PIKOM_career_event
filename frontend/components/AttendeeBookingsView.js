import Link from "next/link";

export default function BookingsView({ schedule, action }) {
  const sessions = schedule?.sessions || [];
  const interviews = schedule?.interviews || [];
  const savedJobs = schedule?.saved_jobs || [];
  const promotions = schedule?.promotions || [];

  return (
    <div className="stack" style={{ gap: "2.5rem" }}>
      {/* 01 / Reserved Sessions */}
      <section>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem" }}>
          <div className="eyebrow muted">01 / RESERVED SESSIONS ({sessions.length})</div>
          <Link href="/sessions" className="mono-indicator" style={{ color: "var(--brick-red)", fontWeight: 700 }}>
            + BROWSE SESSIONS →
          </Link>
        </div>

        {!sessions.length ? (
          <div className="card" style={{ padding: "2rem", textAlign: "center" }}>
            <p className="muted" style={{ margin: "0 0 1rem" }}>
              You have not registered for any keynote or tech sessions yet.
            </p>
            <Link className="button secondary" href="/sessions" style={{ fontSize: "0.82rem" }}>
              Explore Stage Schedule
            </Link>
          </div>
        ) : (
          <div className="grid">
            {sessions.map((session) => (
              <article className="card" key={session.id} style={{ display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
                <div>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.5rem" }}>
                    <span className="badge">SESSION RESERVED</span>
                    <span className="mono-indicator">{session.start_time?.slice(0, 5)}</span>
                  </div>
                  <h3>{session.title}</h3>
                  <p className="muted" style={{ fontSize: "0.9rem", margin: "0.2rem 0 1rem" }}>
                    🗓️ {session.date} · ⏰ {session.start_time}
                  </p>
                </div>
                <button
                  className="secondary"
                  onClick={() => action(`sessions/${session.id}/registration/`, "DELETE")}
                  style={{ width: "100%", fontSize: "0.8rem", color: "var(--brick-red)" }}
                >
                  Cancel Reservation
                </button>
              </article>
            ))}
          </div>
        )}
      </section>

      {/* 02 / Interview Appointments */}
      <section>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem" }}>
          <div className="eyebrow muted">02 / 1-ON-1 INTERVIEW SLOTS ({interviews.length})</div>
          <Link href="/interviews" className="mono-indicator" style={{ color: "var(--brick-red)", fontWeight: 700 }}>
            + BOOK INTERVIEWS →
          </Link>
        </div>

        {!interviews.length ? (
          <div className="card" style={{ padding: "2rem", textAlign: "center" }}>
            <p className="muted" style={{ margin: "0 0 1rem" }}>
              No 1-on-1 interview slots booked yet.
            </p>
            <Link className="button secondary" href="/interviews" style={{ fontSize: "0.82rem" }}>
              View Interview Openings
            </Link>
          </div>
        ) : (
          <div className="grid">
            {interviews.map((booking) => (
              <article className="card" key={booking.booking_id} style={{ display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
                <div>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.5rem" }}>
                    <span className="badge brick">CONFIRMED INTERVIEW</span>
                    <span className="mono-indicator">{booking.start_time?.slice(0, 5)}</span>
                  </div>
                  <h3>{booking.employer}</h3>
                  <p className="muted" style={{ fontSize: "0.9rem", margin: "0.2rem 0 1rem" }}>
                    🗓️ {booking.date} · ⏰ {booking.start_time}
                  </p>
                </div>
                <button
                  className="secondary"
                  onClick={() => action(`interview-slots/${booking.slot_id}/booking/`, "DELETE")}
                  style={{ width: "100%", fontSize: "0.8rem", color: "var(--brick-red)" }}
                >
                  Cancel Interview Slot
                </button>
              </article>
            ))}
          </div>
        )}
      </section>

      {/* 03 / Saved Jobs */}
      <section>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem" }}>
          <div className="eyebrow muted">03 / SAVED JOBS ({savedJobs.length})</div>
          <Link href="/jobs" className="mono-indicator" style={{ color: "var(--brick-red)", fontWeight: 700 }}>
            + BROWSE JOBS →
          </Link>
        </div>

        {!savedJobs.length ? (
          <div className="card" style={{ padding: "2rem", textAlign: "center" }}>
            <p className="muted" style={{ margin: "0 0 1rem" }}>
              You haven&rsquo;t bookmarked any job listings yet.
            </p>
            <Link className="button secondary" href="/jobs" style={{ fontSize: "0.82rem" }}>
              Explore Vacancies
            </Link>
          </div>
        ) : (
          <div className="grid">
            {savedJobs.map((job) => (
              <article className="card" key={job.id} style={{ display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
                <div>
                  <span className="badge" style={{ marginBottom: "0.5rem" }}>BOOKMARKED</span>
                  <h3>{job.title}</h3>
                  <p className="muted" style={{ fontSize: "0.9rem", margin: "0.2rem 0 1rem" }}>
                    🏢 {job.employer}
                  </p>
                </div>
                <Link className="button secondary" href="/jobs" style={{ width: "100%", fontSize: "0.8rem" }}>
                  View in Job Directory →
                </Link>
              </article>
            ))}
          </div>
        )}
      </section>

      {/* 04 / Claimed Promotions */}
      <section>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem" }}>
          <div className="eyebrow muted">04 / CLAIMED PERKS & TRAINING ({promotions.length})</div>
          <Link href="/training-providers" className="mono-indicator" style={{ color: "var(--brick-red)", fontWeight: 700 }}>
            + VIEW PROMOTIONS →
          </Link>
        </div>

        {!promotions.length ? (
          <div className="card" style={{ padding: "2rem", textAlign: "center" }}>
            <p className="muted" style={{ margin: "0 0 1rem" }}>
              No training discounts or promotions claimed yet.
            </p>
            <Link className="button secondary" href="/training-providers" style={{ fontSize: "0.82rem" }}>
              Explore Training Offers
            </Link>
          </div>
        ) : (
          <div className="grid">
            {promotions.map((promotion) => (
              <article className="card" key={promotion.claim_id} style={{ display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
                <div>
                  <span className="badge brick" style={{ marginBottom: "0.5rem" }}>CLAIMED PERK</span>
                  <h3>{promotion.title}</h3>
                  <p className="muted" style={{ fontSize: "0.9rem", margin: "0.2rem 0 1rem" }}>
                    🎓 {promotion.provider}
                  </p>
                </div>
                <button
                  className="secondary"
                  onClick={() => action(`promotions/${promotion.promotion_id}/claim/`, "DELETE")}
                  style={{ width: "100%", fontSize: "0.8rem", color: "var(--brick-red)" }}
                >
                  Cancel Claim
                </button>
              </article>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

