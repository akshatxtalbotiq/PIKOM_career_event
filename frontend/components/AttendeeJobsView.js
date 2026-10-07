"use client";

import { useState } from "react";
import { BuildingIcon, PinIcon, ArrowUpRightIcon, MailIcon, BookmarkIcon } from "./Icons";

export default function JobsView({ jobs = [], me, busy, action }) {
  const [search, setSearch] = useState("");
  const [selectedType, setSelectedType] = useState("ALL");

  const types = ["ALL", ...Array.from(new Set(jobs.map((j) => j.employment_type?.replaceAll("_", " ").toUpperCase()).filter(Boolean)))];

  const filtered = jobs.filter((job) => {
    const matchesSearch = `${job.title} ${job.employer} ${job.location} ${job.experience_level || ""} ${job.description || ""}`
      .toLowerCase()
      .includes(search.toLowerCase());
    const matchesType =
      selectedType === "ALL" ||
      job.employment_type?.replaceAll("_", " ").toUpperCase() === selectedType;
    return matchesSearch && matchesType;
  });

  const isApproved = me.approval_status === "approved";

  return (
    <div className="stack" style={{ gap: "1.5rem" }}>
      {/* Search & Horizontal Filter Bar */}
      <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between" }}>
        <div style={{ flex: "1 1 300px", maxWidth: "460px" }}>
          <input
            type="search"
            className="search-input"
            placeholder="Search job title, employer, skill..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        {types.length > 2 && (
          <div className="category-tabs" style={{ padding: 0 }}>
            {types.map((type) => (
              <button
                type="button"
                key={type}
                className={`category-tab ${selectedType === type ? "active" : ""}`}
                onClick={() => setSelectedType(type)}
                style={{ cursor: "pointer", border: "1px solid var(--border-cream)" }}
              >
                {type}
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="eyebrow muted">
        AVAILABLE OPENINGS · {filtered.length} POSITIONS
      </div>

      {!filtered.length && (
        <div className="card" style={{ textAlign: "center", padding: "3rem 1.5rem" }}>
          <p className="muted" style={{ margin: 0 }}>
            No jobs found matching your criteria.
          </p>
        </div>
      )}

      <div className="grid">
        {filtered.map((job) => (
          <article
            className="card"
            key={job.id}
            style={{ display: "flex", flexDirection: "column", justifyContent: "space-between" }}
          >
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "0.5rem", marginBottom: "0.75rem" }}>
                <span className="badge brick">
                  {job.employment_type?.replaceAll("_", " ")}
                </span>
                {job.experience_level && (
                  <span className="mono-indicator" style={{ fontSize: "0.72rem" }}>
                    {job.experience_level.toUpperCase()}
                  </span>
                )}
              </div>

              <h3>{job.title}</h3>

              <p className="muted" style={{ fontSize: "0.92rem", margin: "0.2rem 0 0.75rem", fontWeight: 600, display: "flex", alignItems: "center", gap: "0.4rem", flexWrap: "wrap" }}>
                <span style={{ display: "inline-flex", alignItems: "center", gap: "0.35rem" }}>
                  <BuildingIcon size={14} />
                  {job.employer}
                </span>
                {job.location && (
                  <span style={{ display: "inline-flex", alignItems: "center", gap: "0.35rem" }}>
                    · <PinIcon size={13} style={{ color: "var(--brick-red)" }} />
                    {job.location}
                  </span>
                )}
              </p>

              <p style={{ color: "var(--ink-muted)", fontSize: "0.94rem", lineHeight: 1.6, marginBottom: "0.75rem" }}>
                {job.description}
              </p>

              {job.requirements && (
                <div style={{ padding: "0.6rem 0.85rem", background: "var(--surface-tint)", borderRadius: "var(--radius-sm)", marginBottom: "1.25rem" }}>
                  <div className="eyebrow muted" style={{ fontSize: "0.68rem", marginBottom: "0.2rem" }}>
                    REQUIREMENTS
                  </div>
                  <p style={{ margin: 0, fontSize: "0.86rem", color: "var(--ink)" }}>{job.requirements}</p>
                </div>
              )}
            </div>

            <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", alignItems: "center", marginTop: "1rem" }}>
              {job.application_url && (
                <a
                  className="button"
                  href={job.application_url}
                  target="_blank"
                  rel="noreferrer"
                  style={{ flex: "1 1 auto", fontSize: "0.82rem", display: "inline-flex", alignItems: "center", justifyContent: "center", gap: "0.4rem" }}
                >
                  Apply Online <ArrowUpRightIcon size={13} />
                </a>
              )}

              {!job.application_url && job.application_email && (
                <a
                  className="button"
                  href={`mailto:${job.application_email}`}
                  style={{ flex: "1 1 auto", fontSize: "0.82rem", display: "inline-flex", alignItems: "center", justifyContent: "center", gap: "0.4rem" }}
                >
                  Email Application <MailIcon size={14} />
                </a>
              )}

              <button
                className="secondary"
                disabled={busy || !isApproved}
                onClick={() => action(`jobs/${job.id}/bookmark/`, job.saved ? "DELETE" : "POST")}
                title={!isApproved ? "Available after approval" : undefined}
                style={{
                  fontSize: "0.82rem",
                  background: job.saved ? "var(--surface-dark)" : "var(--surface-cream)",
                  color: job.saved ? "var(--bg-cream)" : "var(--ink)",
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "0.4rem",
                }}
              >
                <BookmarkIcon size={14} filled={Boolean(job.saved)} />
                {job.saved ? "Saved" : "Save"}
              </button>
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}

