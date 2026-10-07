"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import Navigation from "./Navigation";
import { clearToken } from "../lib/api";

const CATEGORIES = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/employers", label: "Employers" },
  { href: "/jobs", label: "Jobs" },
  { href: "/interviews", label: "Interviews" },
  { href: "/universities", label: "Universities" },
  { href: "/training-providers", label: "Training" },
  { href: "/sessions", label: "Sessions" },
  { href: "/floor-map", label: "Floor Map" },
  { href: "/dashboard/bookings", label: "My Schedule" },
  { href: "/check-in", label: "Check-in Pass" },
];

export default function AttendeePageLayout({ title, attendee, children }) {
  const { me, data, error, loadingMore, loadMore } = attendee;
  const pathname = usePathname();

  if (error && !me) {
    return (
      <main className="shell">
        <Navigation />
        <section className="card access-card">
          <div className="eyebrow" style={{ marginBottom: "0.5rem" }}>00 / Authorization</div>
          <h1>Attendee Access Needed</h1>
          <p className="muted" style={{ margin: "1rem 0 1.5rem" }}>{error}</p>
          <Link className="button" href="/login">
            Sign In with Access Code
          </Link>
        </section>
      </main>
    );
  }

  if (!data || !me) {
    return (
      <main className="shell">
        <Navigation />
        <div style={{ padding: "4rem 0", textAlign: "center" }}>
          <div className="eyebrow">PORTAL LOADING</div>
          <h2 style={{ fontFamily: "var(--font-display)", textTransform: "uppercase", fontSize: "2rem", margin: "0.5rem 0" }}>
            Synchronizing Event Data…
          </h2>
          <p className="muted">Retrieving your attendee itinerary and event directory.</p>
        </div>
      </main>
    );
  }

  const isPending = me.approval_status !== "approved";

  return (
    <main className="shell">
      <Navigation />

      {/* Editorial Header Furniture (Section 5) */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "0.5rem", marginBottom: "0.75rem" }}>
        <span className="eyebrow muted">{data.event.title}</span>
        <span className="mono-indicator">
          STATUS: <span style={{ color: isPending ? "var(--brick-red)" : "inherit", fontWeight: 700 }}>{me.approval_status?.toUpperCase()}</span>
        </span>
      </div>

      <div className="section-title attendee-title">
        <div>
          <h1>{title}</h1>
          <p>
            {isPending
              ? "Your registration is currently waiting for event team review. Booking features and check-in pass activate upon approval."
              : "Explore career pathways, schedule interviews, and manage your festival itinerary."}
          </p>
        </div>
        <div className="attendee-actions-row">
          <button
            className="secondary"
            onClick={() => {
              clearToken();
              location.href = "/login";
            }}
          >
            Sign out
          </button>
        </div>
      </div>

      {/* Section 12: Horizontally scrollable editorial category tabs for fast swiping */}
      <div className="category-tabs-wrapper">
        <div className="category-tabs" role="tablist" aria-label="Directory sections">
          {CATEGORIES.map((tab) => {
            const isActive = pathname === tab.href;
            return (
              <Link
                key={tab.href}
                href={tab.href}
                className={`category-tab ${isActive ? "active" : ""}`}
                role="tab"
                aria-selected={isActive}
              >
                {tab.label}
              </Link>
            );
          })}
        </div>
      </div>

      {error && (
        <p className="error" role="alert" style={{ marginBottom: "1.5rem" }}>
          {error}
        </p>
      )}

      <section className="attendee-content">{children}</section>

      {Object.values(data.pagination?.has_more || {}).some(Boolean) && (
        <div className="attendee-load-more">
          <button className="secondary" disabled={loadingMore} onClick={loadMore}>
            {loadingMore ? "Loading more records…" : "Load More"}
          </button>
        </div>
      )}
    </main>
  );
}
