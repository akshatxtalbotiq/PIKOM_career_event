import { CheckCircleIcon, ClockAlertIcon, PrinterIcon } from "./Icons";

export default function CheckInView({ checkin }) {
  const isCheckedIn = Boolean(checkin?.checked_in);
  const isApproved = checkin?.approval_status === "approved";

  return (
    <div style={{ maxWidth: "600px", margin: "1rem auto" }}>
      <article className="pass-ticket">
        {/* Ticket Header Banner */}
        <div className="pass-ticket-header">
          <div>
            <div className="eyebrow" style={{ color: "var(--brick-red-border)", marginBottom: "0.2rem" }}>
              OFFICIAL DELEGATE PASS
            </div>
            <div style={{ fontFamily: "var(--font-display)", fontSize: "1.4rem", letterSpacing: "0.04em", textTransform: "uppercase" }}>
              PIKOM Career Festival 2026
            </div>
          </div>
          <div className="mono-indicator" style={{ color: "var(--bg-cream)", fontSize: "0.72rem" }}>
            PASS ID #{checkin?.registration_number ? checkin.registration_number.slice(-6) : "PENDING"}
          </div>
        </div>

        {/* Ticket Body */}
        <div className="pass-ticket-body">
          <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", justifyContent: "center", marginBottom: "1rem" }}>
            <span className={`badge ${isCheckedIn ? "dark" : "brick"}`}>
              {isCheckedIn ? (
                <><CheckCircleIcon size={14} /> Venue Check-In Complete</>
              ) : (
                <><ClockAlertIcon size={14} /> Awaiting Venue Check-In</>
              )}
            </span>
            <span className="badge">
              Status: {checkin?.approval_status?.toUpperCase() || "PENDING"}
            </span>
          </div>

          <div className="eyebrow muted" style={{ fontSize: "0.72rem", marginBottom: "0.25rem" }}>
            DELEGATE REGISTRATION NUMBER
          </div>
          <h2
            style={{
              fontFamily: "var(--font-display)",
              fontSize: "clamp(2rem, 5.5vw, 2.8rem)",
              color: "var(--ink)",
              letterSpacing: "0.04em",
              margin: "0 0 1rem",
            }}
          >
            {checkin?.registration_number || "REGISTRATION PENDING"}
          </h2>

          {checkin?.qr_code ? (
            <>
              <div className="pass-qr-frame">
                <img
                  src={checkin.qr_code}
                  width="220"
                  height="220"
                  alt="Your event check-in QR code"
                  style={{ display: "block" }}
                />
              </div>
              <p className="muted" style={{ fontSize: "0.92rem", lineHeight: 1.5, maxWidth: "420px", margin: "0.5rem 0 1.5rem" }}>
                Present this QR code to the entrance reception desk for high-speed scanning and badge collection.
              </p>
              <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap", justifyContent: "center" }}>
                <button
                  type="button"
                  className="secondary"
                  onClick={() => window.print()}
                  style={{ fontSize: "0.82rem" }}
                >
                  <><PrinterIcon size={14} /> Print Physical Pass</>
                </button>
              </div>
            </>
          ) : (
            <div
              style={{
                padding: "2rem",
                margin: "1.5rem 0",
                background: "var(--surface-tint)",
                borderRadius: "var(--radius-md)",
                border: "1px dashed var(--border-cream-dark)",
                maxWidth: "440px",
              }}
            >
              <div className="eyebrow" style={{ marginBottom: "0.5rem" }}>
                QR GENERATION PENDING
              </div>
              <p className="muted" style={{ fontSize: "0.92rem", margin: 0, lineHeight: 1.6 }}>
                Your check-in QR code will appear here as soon as the organizers review and approve your registration.
              </p>
            </div>
          )}
        </div>
      </article>
    </div>
  );
}

