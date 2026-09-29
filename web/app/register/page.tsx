"use client";
import {FormEvent,useState} from "react";
import {useRouter} from "next/navigation";
import Link from "next/link";
export default function Page(){
 const[email,setEmail]=useState("");const[password,setPassword]=useState("");const[error,setError]=useState("");const[busy,setBusy]=useState(false);
 const router=useRouter();const api=process.env.NEXT_PUBLIC_API_URL||"http://localhost:8000";
 async function submit(e:FormEvent){e.preventDefault();setBusy(true);setError("");try{
  const r=await fetch(api+"/api/v1/auth/register",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({email,password})});
  const d=await r.json().catch(()=>({}));if(!r.ok)throw new Error(d.detail||`Request failed (${r.status})`);
  localStorage.setItem("cv_token",d.access_token);router.push("/dashboard");
 }catch(e:any){setError(e.message||"Unable to continue")}finally{setBusy(false)}}
 return <main className="shell"><div className="card authCard"><div className="brand"><img src="/contextvault-logo.svg" width="42" height="42" alt="ContextVault logo"/>ContextVault</div><h1>Register</h1>
 <form onSubmit={submit}><label>Email<input className="input" type="email" required autoComplete="email" value={email} onChange={e=>setEmail(e.target.value)}/></label>
 <label>Password<input className="input" type="password" required minLength={8} autoComplete="new-password" value={password} onChange={e=>setPassword(e.target.value)}/></label>
 {error&&<div className="notice errorNotice" role="alert">{error}</div>}<button className="button" disabled={busy}>{busy?"Working…":"Create account"}</button></form>
 <p className="muted"><Link href="/login">Already registered? Login</Link></p><div className="footer">Powered by Codyza</div></div></main>
}