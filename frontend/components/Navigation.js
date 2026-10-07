"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export default function Navigation() {
  const pathname = usePathname();

  const navLinks = [
    { href: "/dashboard", label: "Dashboard" },
    { href: "/employers", label: "Employers" },
    { href: "/jobs", label: "Jobs" },
    { href: "/interviews", label: "Interviews" },
    { href: "/universities", label: "Universities" },
    { href: "/training-providers", label: "Training" },
    { href: "/sessions", label: "Sessions" },
    { href: "/floor-map", label: "Floor Map" },
    { href: "/dashboard/bookings", label: "My Schedule" },
    { href: "/check-in", label: "Check-in" },
  ];

  return (
    <>
      <header className="topbar">
        <Link className="brand-wrapper" href="/">
          <span className="brand">PIKOM</span>
          <span className="brand-tag">CAREER FESTIVAL · 2026</span>
        </Link>
        <nav className="desktop-nav">
          {navLinks.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={isActive ? "active" : ""}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>
      </header>

      {/* Modern Floating Bottom Navigation Bar for Mobile (Section 11) */}
      <nav className="mobile-bottom-bar" aria-label="Mobile Navigation">
        <Link
          href="/dashboard"
          className={`mobile-bottom-link ${pathname === "/dashboard" ? "active" : ""}`}
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
          </svg>
          <span>Home</span>
        </Link>

        <Link
          href="/jobs"
          className={`mobile-bottom-link ${pathname === "/jobs" ? "active" : ""}`}
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
          <span>Jobs</span>
        </Link>

        {/* Floating circular primary action button for Check-In Pass */}
        <Link
          href="/check-in"
          className="mobile-bottom-action"
          title="Digital Pass & Check-in"
          aria-label="Digital Pass and Check-in"
        >
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
            <rect x="3" y="3" width="7" height="7" rx="1.5" />
            <rect x="14" y="3" width="7" height="7" rx="1.5" />
            <rect x="3" y="14" width="7" height="7" rx="1.5" />
            <path d="M14 14h3v3h-3zM17 17h4v4h-4zM14 20h3" />
          </svg>
        </Link>

        <Link
          href="/sessions"
          className={`mobile-bottom-link ${pathname === "/sessions" ? "active" : ""}`}
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          <span>Sessions</span>
        </Link>

        <Link
          href="/dashboard/bookings"
          className={`mobile-bottom-link ${pathname === "/dashboard/bookings" ? "active" : ""}`}
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
          </svg>
          <span>Schedule</span>
        </Link>
      </nav>
    </>
  );
}

