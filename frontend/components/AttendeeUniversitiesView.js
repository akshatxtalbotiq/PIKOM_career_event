"use client";

import { useState } from "react";

export default function UniversitiesView({ universities = [] }) {
  const [search, setSearch] = useState("");

  const filtered = universities.filter((u) =>
    `${u.name} ${u.description || ""} ${(u.programs || []).map((p) => `${p.name} ${p.description || ""} ${p.eligibility || ""}`).join(" ")}`
      .toLowerCase()
      .includes(search.toLowerCase())
  );

  return (
    <div className="stack" style={{ gap: "2rem" }}>
      {/* Search Bar */}
      <div style={{ maxWidth: "480px" }}>
        <input
          type="search"
          className="search-input"
          placeholder="Search university, program, degree, eligibility..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      <div className="eyebrow muted">
        ACADEMIC INSTITUTIONS & HIGHER EDUCATION · {filtered.length} UNIVERSITIES
      </div>

      {!filtered.length && (
        <div className="card" style={{ textAlign: "center", padding: "3rem 1.5rem" }}>
          <p className="muted" style={{ margin: 0 }}>
            No universities match your search &ldquo;{search}&rdquo;.
          </p>
        </div>
      )}

      <div className="grid">
        {filtered.map((university) => (
          <article
            className="card"
            key={university.id}
            style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}
          >
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "0.5rem", marginBottom: "0.3rem" }}>
                <span className="eyebrow muted" style={{ fontSize: "0.72rem" }}>
                  HIGHER EDUCATION
                </span>
                {university.website && (
                  <a
                    className="button secondary"
                    href={university.website}
                    target="_blank"
                    rel="noreferrer"
                    style={{ fontSize: "0.75rem", padding: "0.4rem 0.8rem", minHeight: "34px" }}
                  >
                    Campus Website ↗
                  </a>
                )}
              </div>

              <h3>{university.name}</h3>

              <p style={{ color: "var(--ink-muted)", fontSize: "0.94rem", lineHeight: 1.6, margin: "0.4rem 0 0" }}>
                {university.description}
              </p>
            </div>

            {university.programs && university.programs.length > 0 && (
              <div style={{ display: "grid", gap: "0.85rem" }}>
                <div className="eyebrow muted" style={{ fontSize: "0.7rem" }}>
                  ACCREDITED DEGREE PROGRAMS ({university.programs.length})
                </div>
                {university.programs.map((program) => (
                  <div
                    key={program.id}
                    style={{
                      background: "var(--surface-tint)",
                      border: "1px solid var(--border-cream)",
                      borderRadius: "var(--radius-md)",
                      padding: "1.25rem",
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.4rem" }}>
                      <span className="badge" style={{ fontSize: "0.7rem" }}>
                        ACADEMIC PROGRAM
                      </span>
                      {program.upcoming_batch_info && (
                        <span className="mono-indicator" style={{ fontSize: "0.7rem" }}>
                          INTAKE: {program.upcoming_batch_info}
                        </span>
                      )}
                    </div>

                    <h4>{program.name}</h4>

                    <p style={{ color: "var(--ink-muted)", fontSize: "0.9rem", lineHeight: 1.5, margin: "0.3rem 0 0.6rem" }}>
                      {program.description}
                    </p>

                    {program.eligibility && (
                      <p className="muted" style={{ fontSize: "0.82rem", margin: "0.4rem 0 0", fontStyle: "italic" }}>
                        <strong>Eligibility:</strong> {program.eligibility}
                      </p>
                    )}

                    {program.internship_fresher_info && (
                      <p className="muted" style={{ fontSize: "0.82rem", margin: "0.2rem 0 0" }}>
                        <strong>Placement & Freshers:</strong> {program.internship_fresher_info}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </article>
        ))}
      </div>
    </div>
  );
}

