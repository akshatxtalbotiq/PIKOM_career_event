import { CalendarIcon } from "./Icons";

export default function InterviewsView({ slots = [], schedule, me, busy, action }) {
  const isApproved = me.approval_status === "approved";
  const bookingsBySlot = new Map((schedule?.interviews || []).map((booking) => [booking.slot_id, booking]));

  return (
    <div className="stack" style={{ gap: "1.5rem" }}>
      <div className="eyebrow muted">
        INTERVIEW SLOTS · {slots.length} EMPLOYERS SCHEDULING
      </div>

      {!slots.length && (
        <div className="card" style={{ textAlign: "center", padding: "3rem 1.5rem" }}>
          <p className="muted" style={{ margin: 0 }}>
            No interview sessions are currently open for booking. Please check back later.
          </p>
        </div>
      )}

      <div className="grid">
        {slots.map((slot) => (
          <article
            className="card"
            key={slot.id}
            style={{ display: "flex", flexDirection: "column", justifyContent: "space-between" }}
          >
            {bookingsBySlot.has(slot.id) && (
              <div style={{ marginBottom: "0.75rem" }}>
                <span className="badge dark" role="status">Appointment booked</span>
              </div>
            )}
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem" }}>
                <span className="badge">1-ON-1 INTERVIEW</span>
                <span className="mono-indicator">
                  {slot.start_time.slice(0, 5)}–{slot.end_time.slice(0, 5)}
                </span>
              </div>

              <h3>{slot.employer}</h3>

              <p className="muted" style={{ fontSize: "0.9rem", margin: "0.2rem 0 0.5rem", fontWeight: 600, display: "flex", alignItems: "center", gap: "0.4rem" }}>
                <CalendarIcon size={14} />
                {new Date(`${slot.date}T00:00:00`).toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" })}
              </p>

              {slot.interviewer_info && (
                <div style={{ padding: "0.6rem 0.85rem", background: "var(--surface-tint)", borderRadius: "var(--radius-sm)", margin: "0.75rem 0 1.25rem" }}>
                  <div className="eyebrow muted" style={{ fontSize: "0.68rem", marginBottom: "0.2rem" }}>
                    INTERVIEWER BRIEF
                  </div>
                  <p style={{ margin: 0, fontSize: "0.88rem", color: "var(--ink)" }}>{slot.interviewer_info}</p>
                </div>
              )}
            </div>

            <div>
              <div className="eyebrow muted" style={{ fontSize: "0.72rem", marginBottom: "0.5rem" }}>
                SELECT TIME APPOINTMENT
              </div>
              <div style={{ display: "grid", gap: "0.5rem" }}>
                {slot.options.map((option) => {
                  const isAvailable = Boolean(option.remaining);
                  const booking = bookingsBySlot.get(slot.id);
                  const isBookedTime = booking?.start_time === option.start_time;
                  return (
                    <button
                      key={option.start_time}
                      className={isBookedTime ? "secondary" : undefined}
                      disabled={busy || (booking ? !isBookedTime : !isApproved || !isAvailable)}
                      onClick={() =>
                        booking
                          ? action(`interview-slots/${slot.id}/booking/`, "DELETE")
                          : action(`interview-slots/${slot.id}/booking/`, "POST", { start_time: option.start_time })
                      }
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        fontSize: "0.82rem",
                        padding: "0.65rem 1rem",
                        background: !isAvailable ? "var(--surface-tint)" : undefined,
                        color: !isAvailable ? "var(--ink-muted)" : undefined,
                      }}
                    >
                      <span style={{ fontWeight: 700 }}>{option.start_time}</span>
                      <span
                        style={{
                          fontSize: "0.72rem",
                          letterSpacing: "0.04em",
                          textTransform: "uppercase",
                          opacity: isAvailable ? 0.9 : 0.6,
                        }}
                      >
                          {isBookedTime ? "Your appointment · Cancel" : booking ? "Unavailable while booked" : isAvailable ? `${option.remaining} spots left` : "Filled"}
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}

