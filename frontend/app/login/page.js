"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { api, saveToken } from "../../lib/api";

function LoginForm() {
  const router = useRouter(); const [token, setValue] = useState(""); const [error, setError] = useState(""); const [busy, setBusy] = useState(false);
  useEffect(() => { const supplied = new URLSearchParams(location.search).get("token"); if (supplied) setValue(supplied); }, []);
  async function submit(e) { e.preventDefault(); setBusy(true); setError(""); try { saveToken(token.trim()); await api("me/"); router.push("/dashboard"); } catch (err) { setError(err.message); } finally { setBusy(false); } }
  return <main className="shell"><header className="topbar"><Link className="brand" href="/">PIKOM</Link><Link href="/">Home</Link></header><section className="card"><h1>Attendee login</h1><p className="muted">Open your private attendee access link from the registration confirmation email, or enter your access code.</p><form className="form" onSubmit={submit}><label>Attendee access code<input required value={token} onChange={e=>setValue(e.target.value)} autoComplete="off" /></label>{error&&<p className="error">{error}</p>}<button disabled={busy}>{busy?"Checking…":"Continue"}</button></form></section></main>;
}
export default function LoginPage() { return <Suspense fallback={<main className="shell">Loading…</main>}><LoginForm/></Suspense>; }
