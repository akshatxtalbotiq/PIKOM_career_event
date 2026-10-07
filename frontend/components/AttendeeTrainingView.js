"use client";

import { useState } from "react";

export default function TrainingView({ providers = [], me, schedule, busy, action }) {
  const [search, setSearch] = useState("");
  const isApproved = me.approval_status === "approved";
  const claimedPromotions = new Map((schedule?.promotions || []).map((promotion) => [promotion.promotion_id, promotion]));

  const filtered = providers.filter((provider) =>
    `${provider.name} ${provider.description || ""} ${provider.promotions.map((p) => `${p.title} ${p.value || ""}`).join(" ")}`
      .toLowerCase()
      .includes(search.toLowerCase())
  );

  return (
    <div className="stack" style={{ gap: "2rem" }}>
      {/* Search Input Filter */}
      <div style={{ maxWidth: "480px" }}>
        <input
          type="search"
          className="search-input"
          placeholder="Search training provider, skills, or discount voucher..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      <div className="eyebrow muted">
        PROFESSIONAL UPSKILLING & TRAINING · {filtered.length} PROVIDERS
      </div>

      {!filtered.length && (
        <div className="card" style={{ textAlign: "center", padding: "3rem 1.5rem" }}>
          <p className="muted" style={{ margin: 0 }}>
            No training providers match your search &ldquo;{search}&rdquo;.
          </p>
        </div>
      )}

      <div className="grid">
        {filtered.map((provider) => (
          <article
            className="card"
            key={provider.id}
            style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}
          >
            <div>
              <div className="eyebrow muted" style={{ fontSize: "0.72rem", marginBottom: "0.3rem" }}>
                TRAINING ACADEMY
              </div>
              <h3>{provider.name}</h3>
              <p style={{ color: "var(--ink-muted)", fontSize: "0.94rem", lineHeight: 1.6, margin: "0.4rem 0 0" }}>
                {provider.description}
              </p>
            </div>

            {provider.promotions && provider.promotions.length > 0 && (
              <div style={{ display: "grid", gap: "1rem" }}>
                <div className="eyebrow muted" style={{ fontSize: "0.7rem" }}>
                  OFFERINGS & VOUCHERS ({provider.promotions.length})
                </div>
                {provider.promotions.map((promotion) => (
                  <div
                    key={promotion.id}
                    style={{
                      background: "var(--surface-tint)",
                      border: "1px solid var(--border-cream)",
                      borderRadius: "var(--radius-md)",
                      padding: "1.25rem",
                    }}
                  >
                    {claimedPromotions.has(promotion.id) && (
                      <div style={{ marginBottom: "0.65rem" }}>
                        <span className="badge dark" role="status">Claimed</span>
                      </div>
                    )}
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "0.5rem", marginBottom: "0.5rem" }}>
                      <span className="badge brick">
                        {promotion.value || "EXCLUSIVE PERK"}
                      </span>
                      {promotion.expires_at && (
                        <span className="mono-indicator" style={{ fontSize: "0.7rem" }}>
                          UNTIL {new Date(promotion.expires_at).toLocaleDateString()}
                        </span>
                      )}
                    </div>

                    <h4>{promotion.title}</h4>

                    <p style={{ color: "var(--ink-muted)", fontSize: "0.9rem", lineHeight: 1.5, margin: "0.3rem 0 0.75rem" }}>
                      {promotion.description}
                    </p>

                    {claimedPromotions.get(promotion.id)?.instructions && (
                      <p style={{ color: "var(--ink)", fontSize: "0.88rem", lineHeight: 1.5, margin: "0 0 0.75rem" }}>
                        <strong>Claim instructions:</strong> {claimedPromotions.get(promotion.id).instructions}
                      </p>
                    )}

                    <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", alignItems: "center" }}>
                      <button
                        disabled={busy || !isApproved || claimedPromotions.has(promotion.id)}
                        onClick={() => action(`promotions/${promotion.id}/claim/`)}
                        style={{ fontSize: "0.82rem", flex: "1 1 auto" }}
                      >
                        {claimedPromotions.has(promotion.id)
                          ? "Already claimed"
                          : isApproved ? "Claim Voucher →" : "Approval required"}
                      </button>

                      {promotion.document_url && (
                        <a
                          className="button secondary"
                          href={promotion.document_url}
                          target="_blank"
                          rel="noreferrer"
                          style={{ fontSize: "0.8rem" }}
                        >
                          Details ↗
                        </a>
                      )}
                    </div>
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

