"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

const navLinks = [
  { href: "/dashboard", label: "Dashboard", icon: "home" },
  { href: "/employers", label: "Employers", icon: "building" },
  { href: "/jobs", label: "Jobs", icon: "briefcase" },
  { href: "/interviews", label: "Interviews", icon: "calendar" },
  { href: "/universities", label: "Universities", icon: "academic" },
  { href: "/training-providers", label: "Training", icon: "training" },
  { href: "/sessions", label: "Sessions", icon: "sessions" },
  { href: "/floor-map", label: "Floor Map", icon: "map" },
  { href: "/dashboard/bookings", label: "My Schedule", icon: "schedule" },
  { href: "/check-in", label: "Check-in Pass", icon: "ticket" },
];

const desktopPrimaryLinks = ["/dashboard", "/jobs", "/sessions", "/dashboard/bookings"];
const mobilePrimaryLinks = ["/dashboard", "/jobs", "/check-in", "/sessions"];

function isCurrentRoute(pathname, href) {
  return pathname === href ||
    (href === "/dashboard" && pathname.startsWith("/dashboard/") && pathname !== "/dashboard/bookings");
}

function NavIcon({ name }) {
  const paths = {
    home: <><path d="m3 10 9-7 9 7" /><path d="M5 9v12h14V9M9 21v-7h6v7" /></>,
    building: <><rect x="4" y="2" width="16" height="20" rx="2" /><path d="M9 22v-4h6v4M8 6h.01M16 6h.01M8 10h.01M16 10h.01M8 14h.01M16 14h.01" /></>,
    briefcase: <><rect x="3" y="7" width="18" height="14" rx="2" /><path d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M3 12h18M10 12v2h4v-2" /></>,
    calendar: <><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M16 3v4M8 3v4M3 10h18M8 14h2M14 14h2M8 17h2" /></>,
    academic: <><path d="m2 10 10-5 10 5-10 5-10-5Z" /><path d="M6 12v5c3 3 9 3 12 0v-5M22 10v6" /></>,
    training: <><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" /><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2ZM8 7h8M8 11h8" /></>,
    sessions: <><rect x="3" y="4" width="18" height="16" rx="2" /><path d="m10 9 5 3-5 3V9Z" /></>,
    map: <><path d="m3 6 6-3 6 3 6-3v15l-6 3-6-3-6 3V6Z" /><path d="M9 3v15M15 6v15" /></>,
    schedule: <><path d="M5 3h14v18l-7-4-7 4V3Z" /><path d="M9 8h6M9 12h6" /></>,
    ticket: <><path d="M3 7a2 2 0 0 0 0 4v2a2 2 0 0 0 0 4v2h18v-2a2 2 0 0 1 0-4v-2a2 2 0 0 1 0-4V5H3v2Z" /><path d="M13 5v2M13 11v2M13 17v2" /></>,
  };
  return <svg className="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{paths[name]}</svg>;
}

export default function Navigation({ signOutAction }) {
  const pathname = usePathname();
  const [moreOpen, setMoreOpen] = useState(false);
  const desktopMoreLinks = navLinks.filter((item) => !desktopPrimaryLinks.includes(item.href));
  const mobileMoreLinks = navLinks.filter((item) => !mobilePrimaryLinks.includes(item.href));
  const desktopMoreActive = desktopMoreLinks.some((item) => isCurrentRoute(pathname, item.href));
  const mobileMoreActive = mobileMoreLinks.some((item) => isCurrentRoute(pathname, item.href));

  useEffect(() => setMoreOpen(false), [pathname]);

  useEffect(() => {
    if (!moreOpen) return undefined;
    const closeOnEscape = (event) => {
      if (event.key === "Escape") setMoreOpen(false);
    };
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, [moreOpen]);

  const renderMoreLinks = (className, id, links, mobile = false) => (
    <div className={className} id={id} aria-label="More attendee destinations">
      {mobile && (
        <div className="mobile-more-heading">
          <span>More sections</span>
          <button type="button" className="mobile-more-close" onClick={() => setMoreOpen(false)} aria-label="Close more sections">×</button>
        </div>
      )}
      {links.map((item) => {
        const active = isCurrentRoute(pathname, item.href);
        return (
          <Link key={item.href} href={item.href} className={active ? "active" : ""} aria-current={active ? "page" : undefined}>
            <NavIcon name={item.icon} />
            <span>{item.label}</span>
          </Link>
        );
      })}
    </div>
  );

  return (
    <>
      <header className="topbar">
        <Link className="brand-wrapper" href="/">
          <span className="brand">PIKOM</span>
          <span className="brand-tag">CAREER FESTIVAL · 2026</span>
        </Link>
        <nav className="desktop-nav" aria-label="Attendee sections">
          {navLinks.filter((item) => desktopPrimaryLinks.includes(item.href)).map((item) => {
            const isActive = isCurrentRoute(pathname, item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={isActive ? "active" : ""}
                aria-current={isActive ? "page" : undefined}
              >
                {item.label}
              </Link>
            );
          })}
          <div className="desktop-more-wrap">
            <button type="button" className={`desktop-more-trigger ${desktopMoreActive ? "active" : ""}`} aria-expanded={moreOpen} aria-controls="attendee-more-desktop" onClick={() => setMoreOpen((open) => !open)}>
              More <span className={`more-chevron ${moreOpen ? "open" : ""}`} aria-hidden="true">⌄</span>
            </button>
            {moreOpen && renderMoreLinks("desktop-more-menu", "attendee-more-desktop", desktopMoreLinks)}
          </div>
        </nav>
        {signOutAction && (
          <div className="topbar-actions">
            <button type="button" className="secondary topbar-signout" onClick={signOutAction}>Sign out</button>
          </div>
        )}
      </header>

      <div className={`mobile-nav-backdrop ${moreOpen ? "visible" : ""}`} onClick={() => setMoreOpen(false)} aria-hidden="true" />
      {moreOpen && renderMoreLinks("mobile-more-sheet", "attendee-more-mobile", mobileMoreLinks, true)}
      <nav className="mobile-bottom-bar" aria-label="Primary attendee navigation">
        {mobilePrimaryLinks.map((href) => navLinks.find((item) => item.href === href)).map((item) => {
          const active = isCurrentRoute(pathname, item.href);
          return (
            <Link key={item.href} href={item.href} className={`mobile-bottom-link ${item.href === "/check-in" ? "mobile-checkin-link" : ""} ${active ? "active" : ""}`} aria-current={active ? "page" : undefined}>
              {item.href === "/check-in" ? <span className="mobile-checkin-icon"><NavIcon name={item.icon} /></span> : <NavIcon name={item.icon} />}
              <span>{item.href === "/dashboard" ? "Home" : item.href === "/dashboard/bookings" ? "Schedule" : item.href === "/check-in" ? "Check-in" : item.label}</span>
            </Link>
          );
        })}
        <button type="button" className={`mobile-bottom-link mobile-more-trigger ${moreOpen || mobileMoreActive ? "active" : ""}`} aria-expanded={moreOpen} aria-controls="attendee-more-mobile" onClick={() => setMoreOpen((open) => !open)}>
          <span className="more-dots" aria-hidden="true">•••</span>
          <span>More</span>
        </button>
      </nav>
    </>
  );
}

