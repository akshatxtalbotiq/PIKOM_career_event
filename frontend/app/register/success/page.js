"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
export default function Success(){const [number,setNumber]=useState("");useEffect(()=>setNumber(sessionStorage.getItem("pikom-registration-number")||""),[]);return <main className="shell"><section className="card"><span className="badge">Submitted</span><h1>Thanks for registering</h1><p>Your registration is pending event team approval. A confirmation email is on its way, and this browser can already open your attendee dashboard.</p>{number&&<p>Reference: <strong>{number}</strong></p>}<Link className="button" href="/dashboard">Open attendee dashboard</Link></section></main>}
