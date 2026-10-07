"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import Navigation from "./Navigation";
import { clearToken } from "../lib/api";
import { resetAttendeeCache } from "../hooks/useAttendeeData";

const PAGE_DESCRIPTIONS = {
  "Participating Employers": "Explore participating organizations and locate their festival booths.",
  "Jobs & Opportunities": "Browse roles from event employers and save opportunities to your schedule.",
  "Interview Availability": "Choose an available time for a one-to-one employer conversation.",
  "Universities & Programs": "Compare programs and connect with higher education providers.",
  "Training & Promotions": "Claim training offers and find your claimed vouchers here.",
  "Keynotes & Sessions": "Explore the event program and reserve or cancel a seat.",
  "Floor Map & Booths": "Find exhibitors, stages, and facilities across the venue.",
  "My Schedule & Itinerary": "Review and manage your sessions, interviews, saved jobs, and claimed offers.",
  "Check-in Pass": "Open your approved QR pass for entry and badge collection.",
};

export default function AttendeePageLayout({ title, attendee, children, showLoadMore = false }) {
  const { me, data, error, loadingMore, loadMore } = attendee;
  const router = useRouter();

  const handleSignOut = () => {
    resetAttendeeCache();
    clearToken();
    router.push("/login");
  };

  if (error && !me) {
    return (
      <main className="shell">
        <Navigation signOutAction={handleSignOut} />
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
        <Navigation signOutAction={handleSignOut} />
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
      <Navigation signOutAction={handleSignOut} />

      <div className="section-title attendee-title">
        <div>
          <h1>{title}</h1>
          {(isPending || PAGE_DESCRIPTIONS[title]) && (
            <p>
              {isPending
                ? "Your registration is currently waiting for event team review. Booking features and check-in pass activate upon approval."
                : PAGE_DESCRIPTIONS[title]}
            </p>
          )}
        </div>
      </div>

      {error && (
        <p className="error" role="alert" style={{ marginBottom: "1.5rem" }}>
          {error}
        </p>
      )}

      <section className="attendee-content">{children}</section>

      {showLoadMore && Object.values(data.pagination?.has_more || {}).some(Boolean) && (
        <div className="attendee-load-more">
          <button className="secondary" disabled={loadingMore} onClick={loadMore}>
            {loadingMore ? "Loading more records…" : "Load More"}
          </button>
        </div>
      )}
    </main>
  );
}
