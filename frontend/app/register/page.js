"use client";
import Link from "next/link";
import { useSearchParams, useRouter } from "next/navigation";
import { Suspense, useState } from "react";
import { useEffect } from "react";
import { api, saveToken } from "../../lib/api";

function RegistrationForm() {
  const params=useSearchParams(); const router=useRouter(); const eventId=params.get("event");
  const [schema,setSchema]=useState(null);const [answers,setAnswers]=useState({});const [basic,setBasic]=useState({name:"",email:"",phone:"",organization:""});const [error,setError]=useState("");const [busy,setBusy]=useState(false);
  useEffect(()=>{if(eventId)api(`events/${eventId}/registration-form/`).then(setSchema).catch(e=>setError(e.message))},[eventId]);
  const update=(id,value)=>setAnswers(current=>({...current,[id]:value}));
  function renderQuestion(q){const value=answers[q.id]??(q.type==="checkbox"?[]:"");const identity=q.type.startsWith("identity_");const options=Array.isArray(q.choices)?q.choices:[];const label=<>{q.text}{q.required&&<span aria-hidden="true"> *</span>}</>;
    if(q.type==="checkbox")return <fieldset key={q.id} className="card"><legend>{label}</legend>{q.help_text&&<small className="muted">{q.help_text}</small>}{[...options,...(q.allow_other?["Other"]:[])].map(option=><label key={option} style={{display:"flex",gridTemplateColumns:"auto 1fr",alignItems:"center"}}><input type="checkbox" checked={value.includes(option)} onChange={e=>update(q.id,e.target.checked?[...value,option]:value.filter(v=>v!==option))}/>{option}</label>)}{value.filter(option=>q.choice_followups?.[option]).map(option=><label key={option+"followup"}>{q.choice_followups[option]}<input value={answers[`${q.id}_followup_${option}`]||""} onChange={e=>update(`${q.id}_followup_${option}`,e.target.value)}/></label>)}{q.allow_other&&value.includes("Other")&&<input aria-label="Other answer" placeholder="Please specify" value={answers[`${q.id}_other`]||""} onChange={e=>update(`${q.id}_other`,e.target.value)}/>}</fieldset>;
    if(q.type==="radio"||q.type==="select"||q.type==="identity_participant_type")return <label key={q.id}>{label}{q.help_text&&<small className="muted">{q.help_text}</small>}<select required={q.required} value={value} onChange={e=>update(q.id,e.target.value)}><option value="">Choose…</option>{(q.type==="identity_participant_type"?["Delegate","Organizer","Sponsor","Exhibitor","Speaker"]:options).map(option=><option key={option} value={option}>{option}</option>)}{q.allow_other&&<option value="Other">Other</option>}</select>{q.allow_other&&value==="Other"&&<input placeholder="Please specify" value={answers[`${q.id}_other`]||""} onChange={e=>update(`${q.id}_other`,e.target.value)}/> }{q.choice_followups?.[value]&&<><small className="muted">{q.choice_followups[value]}</small><input value={answers[`${q.id}_followup_${value}`]||""} onChange={e=>update(`${q.id}_followup_${value}`,e.target.value)}/></>}</label>;
    const inputType=q.type==="identity_email"?"email":q.type==="identity_phone"?"tel":"text";const long=q.type==="textarea"||q.type==="matrix_roles"||q.type==="identity_organization";
    return <label key={q.id}>{label}{q.help_text&&<small className="muted">{q.help_text}</small>}{long?<textarea required={q.required} rows={q.type==="matrix_roles"?5:3} value={value} onChange={e=>update(q.id,e.target.value)}/>:<input type={inputType} required={q.required} value={value} onChange={e=>update(q.id,e.target.value)}/>}</label>;
  }
  function renderMissingIdentityFields(){
    const presentTypes=new Set((schema?.questions||[]).map(question=>question.type));
    const fields=[
      ["identity_name","name","Full name","text",true],
      ["identity_email","email","Email address","email",true],
      ["identity_phone","phone","Phone","tel",false],
      ["identity_organization","organization","Organization","text",false],
    ];
    return fields.filter(([type])=>!presentTypes.has(type)).map(([,key,label,type,required])=><label key={`basic-${key}`}>{label}{required&&<span aria-hidden="true"> *</span>}<input type={type} required={required} value={basic[key]} onChange={e=>setBasic(current=>({...current,[key]:e.target.value}))}/></label>);
  }
  async function submit(e){e.preventDefault();setBusy(true);setError("");try{const formatted={};for(const q of schema.questions){const value=answers[q.id]??(q.type==="checkbox"?[]:"");const other=answers[`${q.id}_other`]||"";const followups={};for(const selected of (Array.isArray(value)?value:[value]))if(answers[`${q.id}_followup_${selected}`])followups[selected]=answers[`${q.id}_followup_${selected}`];formatted[q.id]=other||Object.keys(followups).length?{value,other,followups}:value;}const result=await api(`events/${eventId}/register/`,{method:"POST",body:{...basic,answers:formatted}});saveToken(result.registration_code);sessionStorage.setItem("pikom-registration-number",result.registration_number);router.push("/register/success");}catch(err){setError(err.message)}finally{setBusy(false)}}
  return <main className="shell"><header className="topbar"><Link className="brand" href="/">PIKOM</Link><Link href="/">Events</Link></header><section className="card"><div className="eyebrow muted">Join the event</div><h1>{schema?.event?.title||"Attendee registration"}</h1><p className="muted">Your registration will be reviewed by the event team.</p>{!schema&&!error&&<p>Loading registration form…</p>}{error&&!schema&&<p className="error">{error}</p>}{schema&&<form className="form" onSubmit={submit}>{renderMissingIdentityFields()}{schema.questions.map(renderQuestion)}{error&&<p className="error">{error}</p>}<button disabled={busy}>{busy?"Submitting…":"Submit registration"}</button></form>}</section></main>;
}
export default function RegisterPage(){return <Suspense fallback={<main className="shell">Loading registration…</main>}><RegistrationForm/></Suspense>}
