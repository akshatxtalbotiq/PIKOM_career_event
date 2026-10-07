"use client";

import Link from "next/link";
import { useSearchParams, useRouter } from "next/navigation";
import { Suspense, useState, useEffect } from "react";
import { api, saveToken } from "../../lib/api";

function RegistrationForm() {
  const params = useSearchParams();
  const router = useRouter();
  const eventId = params.get("event");
  const [schema, setSchema] = useState(null);
  const [answers, setAnswers] = useState({});
  const [basic, setBasic] = useState({ name: "", email: "", phone: "", organization: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (eventId) {
      api(`events/${eventId}/registration-form/`)
        .then(setSchema)
        .catch((e) => setError(e.message));
    }
  }, [eventId]);

  const update = (id, value) => setAnswers((current) => ({ ...current, [id]: value }));

  function renderQuestion(q) {
    const value = answers[q.id] ?? (q.type === "checkbox" ? [] : "");
    const options = Array.isArray(q.choices) ? q.choices : [];
    const label = (
      <span className="editorial-label muted" style={{ fontSize: "0.78rem", color: "var(--ink)", display: "block", marginBottom: "0.25rem" }}>
        {q.text}
        {q.required && <span aria-hidden="true" style={{ color: "var(--brick-red)" }}> *</span>}
      </span>
    );

    if (q.type === "checkbox") {
      return (
        <fieldset key={q.id} className="card" style={{ padding: "1.25rem", margin: "0.5rem 0", background: "var(--surface-cream)" }}>
          <legend style={{ padding: "0 0.5rem" }}>{label}</legend>
          {q.help_text && <p className="muted" style={{ fontSize: "0.85rem", margin: "0 0 0.75rem" }}>{q.help_text}</p>}
          <div style={{ display: "grid", gap: "0.6rem" }}>
            {[...options, ...(q.allow_other ? ["Other"] : [])].map((option) => (
              <label
                key={option}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "0.75rem",
                  minHeight: "44px",
                  padding: "0.4rem 0.6rem",
                  borderRadius: "8px",
                  cursor: "pointer",
                  background: value.includes(option) ? "var(--surface-tint)" : "transparent",
                  transition: "background 150ms ease",
                }}
              >
                <input
                  type="checkbox"
                  style={{ width: "18px", height: "18px", accentColor: "var(--brick-red)" }}
                  checked={value.includes(option)}
                  onChange={(e) =>
                    update(
                      q.id,
                      e.target.checked ? [...value, option] : value.filter((v) => v !== option)
                    )
                  }
                />
                <span style={{ fontSize: "0.92rem", fontWeight: 500 }}>{option}</span>
              </label>
            ))}
          </div>
          {value.filter((option) => q.choice_followups?.[option]).map((option) => (
            <label key={option + "followup"} style={{ marginTop: "0.75rem" }}>
              <span className="muted" style={{ fontSize: "0.85rem" }}>{q.choice_followups[option]}</span>
              <input
                value={answers[`${q.id}_followup_${option}`] || ""}
                onChange={(e) => update(`${q.id}_followup_${option}`, e.target.value)}
              />
            </label>
          ))}
          {q.allow_other && value.includes("Other") && (
            <input
              aria-label="Other answer"
              placeholder="Please specify other..."
              style={{ marginTop: "0.75rem" }}
              value={answers[`${q.id}_other`] || ""}
              onChange={(e) => update(`${q.id}_other`, e.target.value)}
            />
          )}
        </fieldset>
      );
    }

    if (q.type === "radio" || q.type === "select" || q.type === "identity_participant_type") {
      const selectOptions = q.type === "identity_participant_type"
        ? ["Delegate", "Organizer", "Sponsor", "Exhibitor", "Speaker"]
        : options;

      return (
        <label key={q.id}>
          {label}
          {q.help_text && <span className="muted" style={{ fontSize: "0.82rem" }}>{q.help_text}</span>}
          <select required={q.required} value={value} onChange={(e) => update(q.id, e.target.value)}>
            <option value="">Select option…</option>
            {selectOptions.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
            {q.allow_other && <option value="Other">Other</option>}
          </select>
          {q.allow_other && value === "Other" && (
            <input
              placeholder="Please specify..."
              style={{ marginTop: "0.5rem" }}
              value={answers[`${q.id}_other`] || ""}
              onChange={(e) => update(`${q.id}_other`, e.target.value)}
            />
          )}
          {q.choice_followups?.[value] && (
            <div style={{ marginTop: "0.5rem" }}>
              <span className="muted" style={{ fontSize: "0.82rem" }}>{q.choice_followups[value]}</span>
              <input
                value={answers[`${q.id}_followup_${value}`] || ""}
                onChange={(e) => update(`${q.id}_followup_${value}`, e.target.value)}
              />
            </div>
          )}
        </label>
      );
    }

    const inputType = q.type === "identity_email" ? "email" : q.type === "identity_phone" ? "tel" : "text";
    const long = q.type === "textarea" || q.type === "matrix_roles" || q.type === "identity_organization";

    return (
      <label key={q.id}>
        {label}
        {q.help_text && <span className="muted" style={{ fontSize: "0.82rem" }}>{q.help_text}</span>}
        {long ? (
          <textarea
            required={q.required}
            rows={q.type === "matrix_roles" ? 4 : 3}
            value={value}
            onChange={(e) => update(q.id, e.target.value)}
          />
        ) : (
          <input
            type={inputType}
            required={q.required}
            value={value}
            onChange={(e) => update(q.id, e.target.value)}
          />
        )}
      </label>
    );
  }

  function renderMissingIdentityFields() {
    const presentTypes = new Set((schema?.questions || []).map((question) => question.type));
    const fields = [
      ["identity_name", "name", "Full Name", "text", true],
      ["identity_email", "email", "Email Address", "email", true],
      ["identity_phone", "phone", "Phone Number", "tel", false],
      ["identity_organization", "organization", "Organization / Institution", "text", false],
    ];
    return fields
      .filter(([type]) => !presentTypes.has(type))
      .map(([, key, label, type, required]) => (
        <label key={`basic-${key}`}>
          <span className="editorial-label muted" style={{ fontSize: "0.78rem", color: "var(--ink)", display: "block", marginBottom: "0.25rem" }}>
            {label}
            {required && <span aria-hidden="true" style={{ color: "var(--brick-red)" }}> *</span>}
          </span>
          <input
            type={type}
            required={required}
            value={basic[key]}
            onChange={(e) => setBasic((current) => ({ ...current, [key]: e.target.value }))}
          />
        </label>
      ));
  }

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const formatted = {};
      for (const q of schema.questions) {
        const value = answers[q.id] ?? (q.type === "checkbox" ? [] : "");
        const other = answers[`${q.id}_other`] || "";
        const followups = {};
        for (const selected of Array.isArray(value) ? value : [value]) {
          if (answers[`${q.id}_followup_${selected}`]) {
            followups[selected] = answers[`${q.id}_followup_${selected}`];
          }
        }
        formatted[q.id] = other || Object.keys(followups).length ? { value, other, followups } : value;
      }
      const result = await api(`events/${eventId}/register/`, {
        method: "POST",
        body: { ...basic, answers: formatted },
      });
      saveToken(result.registration_code);
      sessionStorage.setItem("pikom-registration-number", result.registration_number);
      router.push("/register/success");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="shell">
      <header className="topbar">
        <Link className="brand-wrapper" href="/">
          <span className="brand">PIKOM</span>
          <span className="brand-tag">CAREER FESTIVAL · 2026</span>
        </Link>
        <nav>
          <Link className="button secondary" href="/">
            ← All Events
          </Link>
        </nav>
      </header>

      <div style={{ maxWidth: "680px", margin: "1.5rem auto" }}>
        <section className="card" style={{ padding: "clamp(1.75rem, 5vw, 3rem)" }}>
          <div className="eyebrow" style={{ marginBottom: "0.5rem" }}>
            01 / EVENT REGISTRATION
          </div>
          <h1 className="display-title" style={{ fontSize: "clamp(2rem, 5vw, 3.2rem)", marginBottom: "0.5rem" }}>
            {schema?.event?.title || "Attendee Registration"}
          </h1>
          <p className="muted" style={{ marginBottom: "2rem", fontSize: "0.98rem", lineHeight: 1.6 }}>
            Please fill in your details to reserve your delegate pass. Your registration will be reviewed and verified by the PIKOM event team.
          </p>

          {!schema && !error && (
            <p className="muted" style={{ textAlign: "center", padding: "2rem 0" }}>
              Loading registration questionnaire…
            </p>
          )}

          {error && !schema && (
            <p className="error" role="alert" style={{ marginBottom: "1.5rem" }}>
              {error}
            </p>
          )}

          {schema && (
            <form className="form" onSubmit={submit} style={{ maxWidth: "100%" }}>
              {renderMissingIdentityFields()}
              {schema.questions.map(renderQuestion)}
              {error && (
                <p className="error" role="alert" style={{ margin: "0.5rem 0" }}>
                  {error}
                </p>
              )}
              <button disabled={busy} style={{ width: "100%", marginTop: "1rem" }}>
                {busy ? "Submitting Registration…" : "Complete Registration →"}
              </button>
            </form>
          )}
        </section>
      </div>

      <footer className="footer">
        <div>PIKOM CAREER FESTIVAL · OFFICIAL DELEGATE REGISTRATION</div>
        <div>CONFIDENTIAL & SECURE</div>
      </footer>
    </main>
  );
}

export default function RegisterPage() {
  return (
    <Suspense
      fallback={
        <main className="shell">
          <p className="muted" style={{ textAlign: "center", padding: "4rem 0" }}>
            Loading registration…
          </p>
        </main>
      }
    >
      <RegistrationForm />
    </Suspense>
  );
}
