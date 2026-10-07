"use client";

import { useState } from "react";

export default function FloorMapView({ floorMaps = [] }) {
  const [search, setSearch] = useState("");
  const [activeBoothId, setActiveBoothId] = useState(null);

  return (
    <div className="stack" style={{ gap: "2rem" }}>
      {/* Search Bar */}
      <div style={{ maxWidth: "520px" }}>
        <input
          type="search"
          className="search-input"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Search booth number, organization, hall, category..."
        />
      </div>

      {!floorMaps.length && (
        <div className="card" style={{ textAlign: "center", padding: "3rem 1.5rem" }}>
          <p className="muted" style={{ margin: 0 }}>
            Floor maps are not currently available for this event.
          </p>
        </div>
      )}

      {floorMaps.map((map) => {
        const booths = (map.booths || []).filter((booth) =>
          `${booth.number} ${booth.name} ${booth.organization_name || ""} ${booth.category || ""}`
            .toLowerCase()
            .includes(search.toLowerCase())
        );

        return (
          <article
            className="card"
            key={map.id}
            style={{ padding: "clamp(1.5rem, 4vw, 2.5rem)" }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "1rem", marginBottom: "0.5rem" }}>
              <div>
                <div className="eyebrow muted">VENUE BLUEPRINT // 01</div>
                <h3 style={{ fontSize: "1.8rem", margin: "0.2rem 0" }}>
                  {map.name}{" "}
                  {map.version && (
                    <small className="mono-indicator" style={{ fontSize: "0.8rem", color: "var(--ink-muted)" }}>
                      · {map.version}
                    </small>
                  )}
                </h3>
              </div>
              <span className="badge">
                {booths.length} BOOTHS INDEXED
              </span>
            </div>

            {map.description && (
              <p style={{ color: "var(--ink-muted)", fontSize: "0.95rem", lineHeight: 1.6, margin: "0 0 1.5rem" }}>
                {map.description}
              </p>
            )}

            {/* Map Canvas with Interactive Pins */}
            <div className="boothmap">
              <img src={map.image_url} alt={`${map.name} event blueprint map`} />
              {booths.map((booth) => {
                const isHighlighted = activeBoothId === booth.id;
                return (
                  <div
                    key={booth.id}
                    className="booth-pin"
                    title={`${booth.number} · ${booth.organization_name || booth.name}`}
                    onClick={() => setActiveBoothId(booth.id)}
                    style={{
                      left: `${booth.x_percent}%`,
                      top: `${booth.y_percent}%`,
                      width: `${booth.width_percent}%`,
                      height: `${booth.height_percent}%`,
                      background: isHighlighted ? "var(--surface-dark)" : "var(--brick-red)",
                      transform: isHighlighted ? "scale(1.2)" : undefined,
                      zIndex: isHighlighted ? 20 : 2,
                    }}
                  >
                    {booth.number}
                  </div>
                );
              })}
            </div>

            {/* Booth Directory Grid */}
            <div style={{ marginTop: "2rem" }}>
              <div className="eyebrow muted" style={{ marginBottom: "0.75rem" }}>
                BOOTH DIRECTORY
              </div>
              <div className="grid">
                {booths.map((booth) => {
                  const isHighlighted = activeBoothId === booth.id;
                  return (
                    <div
                      className="card"
                      key={booth.id}
                      onClick={() => setActiveBoothId(booth.id)}
                      style={{
                        padding: "1.2rem",
                        cursor: "pointer",
                        borderColor: isHighlighted ? "var(--brick-red)" : "var(--border-cream)",
                        background: isHighlighted ? "var(--surface-tint)" : "var(--surface-cream)",
                      }}
                    >
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.4rem" }}>
                        <span className="badge brick" style={{ fontSize: "0.72rem" }}>
                          Booth {booth.number}
                        </span>
                        {booth.category && (
                          <span className="mono-indicator" style={{ fontSize: "0.7rem" }}>
                            {booth.category}
                          </span>
                        )}
                      </div>
                      <b style={{ fontSize: "1.05rem", color: "var(--ink)", display: "block" }}>
                        {booth.organization_name || booth.name}
                      </b>
                      {booth.description && (
                        <p className="muted" style={{ fontSize: "0.88rem", margin: "0.4rem 0 0", lineHeight: 1.5 }}>
                          {booth.description}
                        </p>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </article>
        );
      })}
    </div>
  );
}
