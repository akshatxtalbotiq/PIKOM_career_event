"use client";

import { useState } from "react";
import { PinIcon, ArrowUpRightIcon } from "./Icons";

export default function EmployersView({ employers = [] }) {
  const [search, setSearch] = useState("");

  const filtered = employers.filter((employer) =>
    `${employer.name} ${employer.description || ""} ${employer.booth?.number || ""} ${employer.booth?.name || ""}`
      .toLowerCase()
      .includes(search.toLowerCase())
  );

  return (
    <div className="stack" style={{ gap: "1.5rem" }}>
      {/* Search Input Filter */}
      <div style={{ maxWidth: "480px" }}>
        <input
          type="search"
          className="search-input"
          placeholder="Search employer name, technology, or booth..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      <div className="eyebrow muted">
        EXHIBITING EMPLOYERS · {filtered.length} COMPANIES
      </div>

      {!filtered.length && (
        <div className="card" style={{ textAlign: "center", padding: "3rem 1.5rem" }}>
          <p className="muted" style={{ margin: 0 }}>
            No employers matched your search &ldquo;{search}&rdquo;.
          </p>
        </div>
      )}

      <div className="grid">
        {filtered.map((employer) => (
          <article
            className="card"
            key={employer.id}
            style={{ display: "flex", flexDirection: "column", justifyContent: "space-between" }}
          >
            <div>
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "flex-start",
                  gap: "0.75rem",
                  marginBottom: "1rem",
                }}
              >
                {employer.logo_url ? (
                  <div
                    style={{
                      width: "60px",
                      height: "60px",
                      borderRadius: "12px",
                      overflow: "hidden",
                      background: "#fff",
                      border: "1px solid var(--border-cream)",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      padding: "4px",
                    }}
                  >
                    <img
                      src={employer.logo_url}
                      alt={`${employer.name} logo`}
                      style={{ maxHeight: "100%", maxWidth: "100%", objectFit: "contain" }}
                    />
                  </div>
                ) : (
                  <div
                    style={{
                      width: "52px",
                      height: "52px",
                      borderRadius: "12px",
                      background: "var(--surface-tint)",
                      border: "1px solid var(--border-cream)",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      fontFamily: "var(--font-display)",
                      fontSize: "1.3rem",
                      color: "var(--ink)",
                    }}
                  >
                    {employer.name?.slice(0, 2).toUpperCase()}
                  </div>
                )}

                {employer.booth && (
                  <span className="badge brick">
                    Booth {employer.booth.number}
                  </span>
                )}
              </div>

              <h3>{employer.name}</h3>

              {employer.booth?.name && (
                <p className="muted" style={{ fontSize: "0.85rem", margin: "-0.2rem 0 0.5rem", fontWeight: 600, display: "flex", alignItems: "center", gap: "0.35rem" }}>
                  <PinIcon size={13} style={{ color: "var(--brick-red)" }} />
                  {employer.booth.name}
                </p>
              )}

              <p style={{ color: "var(--ink-muted)", fontSize: "0.94rem", lineHeight: 1.6, marginBottom: "1.25rem" }}>
                {employer.description}
              </p>
            </div>

            {employer.website && (
              <div style={{ paddingTop: "0.5rem" }}>
                <a
                  className="button secondary"
                  href={employer.website}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{ width: "100%", fontSize: "0.8rem", display: "inline-flex", alignItems: "center", justifyContent: "center", gap: "0.4rem" }}
                >
                  Visit Website <ArrowUpRightIcon size={13} />
                </a>
              </div>
            )}
          </article>
        ))}
      </div>
    </div>
  );
}

