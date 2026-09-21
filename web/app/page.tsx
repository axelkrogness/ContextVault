'use client';

import {useEffect,useState} from 'react';
import {
  Brain,
  KeyRound,
  Database,
  Search,
  ShieldCheck,
  Activity,
  Plus,
  Archive,
  Download,
  LogOut,
  ChevronRight,
  Copy,
  Check
} from 'lucide-react';

const API=process.env.NEXT_PUBLIC_API_URL||'http://localhost:8000';

async function call(path:string,opts:any={},token?:string){
  const r=await fetch(API+path,{
    ...opts,
    headers:{
      'Content-Type':'application/json',
      ...(token?{Authorization:`Bearer ${token}`}:{})
    }
  });

  const d=await r.json();

  if(!r.ok) throw new Error(d.detail||'Request failed');

  return d;
}

export default function Home(){
  const [token,setToken]=useState('');
  const [mode,setMode]=useState<'login'|'register'>('login');
  const [email,setEmail]=useState('');
  const [password,setPassword]=useState('');
  const [apps,setApps]=useState<any[]>([]);
  const [agents,setAgents]=useState<any[]>([]);
  const [selected,setSelected]=useState('');
  const [query,setQuery]=useState('');
  const [results,setResults]=useState<any[]>([]);
  const [memory,setMemory]=useState('');
  const [namespace,setNamespace]=useState('default');
  const [stats,setStats]=useState<any>({});
  const [key,setKey]=useState('');
  const [notice,setNotice]=useState('');
  const [loading,setLoading]=useState(false);

  async function refresh(t=token){
    if(!t)return;

    setApps(await call('/api/v1/applications',{},t));

    const ag=await call('/api/v1/agents',{},t);

    setAgents(ag);
    setSelected(s=>s||ag[0]?.id||'');

    setStats(await call('/api/v1/usage',{},t));
  }

  useEffect(()=>{
    const t=localStorage.getItem('cv_token');

    if(t){
      setToken(t);
      refresh(t);
    }
  },[]);

  async function auth(){
    setLoading(true);

    try{
      const d=await call(
        `/api/v1/auth/${mode==='login'?'login':'register'}/`,
        {
          method:'POST',
          body:JSON.stringify({
            email,
            password
          })
        }
      );

      localStorage.setItem('cv_token',d.access_token);
      setToken(d.access_token);
      setNotice('Welcome to ContextVault');

      await refresh(d.access_token);
    }catch(e:any){
      setNotice(e.message);
    }finally{
      setLoading(false);
    }
  }

  async function logout(){
    localStorage.removeItem('cv_token');
    setToken('');
    setApps([]);
    setAgents([]);
    setResults([]);
    setNotice('');
  }

  async function addMemory(){
    if(!memory.trim()||!selected)return;

    setLoading(true);

    try{
      await call(
        '/api/v1/memories',
        {
          method:'POST',
          body:JSON.stringify({
            agent_id:selected,
            namespace,
            content:memory
          })
        },
        token
      );

      setMemory('');
      setNotice('Memory saved');
      await refresh();
    }catch(e:any){
      setNotice(e.message);
    }finally{
      setLoading(false);
    }
  }

  async function searchMemory(){
    if(!query.trim()||!selected)return;

    setLoading(true);

    try{
      const d=await call(
        '/api/v1/search',
        {
          method:'POST',
          body:JSON.stringify({
            agent_id:selected,
            namespace,
            query
          })
        },
        token
      );

      setResults(d);
    }catch(e:any){
      setNotice(e.message);
    }finally{
      setLoading(false);
    }
  }

  async function createKey(){
    if(!selected)return;

    setLoading(true);

    try{
      const d=await call(
        '/api/v1/api-keys',
        {
          method:'POST',
          body:JSON.stringify({
            agent_id:selected
          })
        },
        token
      );

      setKey(d.key||d.token||'');
      setNotice('API key created');
    }catch(e:any){
      setNotice(e.message);
    }finally{
      setLoading(false);
    }
  }

  async function exportData(){
    setLoading(true);

    try{
      const d=await call(
        '/api/v1/export',
        {},
        token
      );

      const blob=new Blob(
        [JSON.stringify(d,null,2)],
        {type:'application/json'}
      );

      const url=URL.createObjectURL(blob);
      const a=document.createElement('a');

      a.href=url;
      a.download='contextvault-export.json';
      a.click();

      URL.revokeObjectURL(url);

      setNotice('Export downloaded');
    }catch(e:any){
      setNotice(e.message);
    }finally{
      setLoading(false);
    }
  }

  if(!token){
    return (
      <main className="min-h-screen bg-slate-950 text-white flex items-center justify-center p-6">
        <div className="w-full max-w-md">
          <div className="mb-8 text-center">
            <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-indigo-600">
              <Brain size={32}/>
            </div>

            <h1 className="text-3xl font-bold">
              ContextVault
            </h1>

            <p className="mt-2 text-slate-400">
              AI memory infrastructure
            </p>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-xl">
            <div className="mb-6 flex rounded-xl bg-slate-800 p-1">
              <button
                onClick={()=>setMode('login')}
                className={`flex-1 rounded-lg px-4 py-2 text-sm font-medium ${
                  mode==='login'
                    ? 'bg-indigo-600 text-white'
                    : 'text-slate-400'
                }`}
              >
                Login
              </button>

              <button
                onClick={()=>setMode('register')}
                className={`flex-1 rounded-lg px-4 py-2 text-sm font-medium ${
                  mode==='register'
                    ? 'bg-indigo-600 text-white'
                    : 'text-slate-400'
                }`}
              >
                Register
              </button>
            </div>

            <div className="space-y-4">
              <input
                type="email"
                placeholder="Email"
                value={email}
                onChange={e=>setEmail(e.target.value)}
                className="w-full rounded-xl border border-slate-700 bg-slate-800 px-4 py-3 text-white outline-none focus:border-indigo-500"
              />

              <input
                type="password"
                placeholder="Password"
                value={password}
                onChange={e=>setPassword(e.target.value)}
                onKeyDown={e=>{
                  if(e.key==='Enter') auth();
                }}
                className="w-full rounded-xl border border-slate-700 bg-slate-800 px-4 py-3 text-white outline-none focus:border-indigo-500"
              />

              <button
                onClick={auth}
                disabled={loading}
                className="w-full rounded-xl bg-indigo-600 px-4 py-3 font-semibold transition hover:bg-indigo-500 disabled:opacity-50"
              >
                {loading
                  ? 'Please wait...'
                  : mode==='login'
                    ? 'Login'
                    : 'Create account'
                }
              </button>
            </div>

            {notice && (
              <div className="mt-4 rounded-xl border border-slate-700 bg-slate-800 p-3 text-sm text-slate-300">
                {notice}
              </div>
            )}
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-slate-950 text-white">
      <header className="border-b border-slate-800 bg-slate-900">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-600">
              <Brain size={22}/>
            </div>

            <div>
              <h1 className="font-bold">
                ContextVault
              </h1>

              <p className="text-xs text-slate-400">
                AI memory infrastructure
              </p>
            </div>
          </div>

          <button
            onClick={logout}
            className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-slate-400 hover:bg-slate-800 hover:text-white"
          >
            <LogOut size={16}/>
            Logout
          </button>
        </div>
      </header>

      <div className="mx-auto max-w-7xl p-6">
        {notice && (
          <div className="mb-6 rounded-xl border border-slate-800 bg-slate-900 p-4 text-sm text-slate-300">
            {notice}
          </div>
        )}

        <div className="mb-6 grid gap-4 md:grid-cols-4">
          <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
            <div className="mb-3 flex items-center justify-between">
              <span className="text-sm text-slate-400">
                Applications
              </span>
              <Database size={18}/>
            </div>

            <div className="text-2xl font-bold">
              {apps.length}
            </div>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
            <div className="mb-3 flex items-center justify-between">
              <span className="text-sm text-slate-400">
                Agents
              </span>
              <Brain size={18}/>
            </div>

            <div className="text-2xl font-bold">
              {agents.length}
            </div>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
            <div className="mb-3 flex items-center justify-between">
              <span className="text-sm text-slate-400">
                Usage
              </span>
              <Activity size={18}/>
            </div>

            <div className="text-2xl font-bold">
              {stats.total_memories||0}
            </div>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
            <div className="mb-3 flex items-center justify-between">
              <span className="text-sm text-slate-400">
                Security
              </span>
              <ShieldCheck size={18}/>
            </div>

            <div className="text-sm font-semibold text-green-400">
              JWT protected
            </div>
          </div>
        </div>

        <div className="grid gap-6 lg:grid-cols-3">
          <section className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
            <div className="mb-5 flex items-center gap-3">
              <Brain size={20}/>
              <h2 className="font-semibold">
                Memory
              </h2>
            </div>

            <label className="mb-2 block text-sm text-slate-400">
              Agent
            </label>

            <select
              value={selected}
              onChange={e=>setSelected(e.target.value)}
              className="mb-4 w-full rounded-xl border border-slate-700 bg-slate-800 px-4 py-3 text-white"
            >
              {agents.map(agent=>(
                <option
                  key={agent.id}
                  value={agent.id}
                >
                  {agent.name||agent.id}
                </option>
              ))}
            </select>

            <label className="mb-2 block text-sm text-slate-400">
              Namespace
            </label>

            <input
              value={namespace}
              onChange={e=>setNamespace(e.target.value)}
              className="mb-4 w-full rounded-xl border border-slate-700 bg-slate-800 px-4 py-3 text-white"
            />

            <label className="mb-2 block text-sm text-slate-400">
              Memory
            </label>

            <textarea
              value={memory}
              onChange={e=>setMemory(e.target.value)}
              placeholder="Write something for your agent to remember..."
              rows={6}
              className="mb-4 w-full resize-none rounded-xl border border-slate-700 bg-slate-800 px-4 py-3 text-white outline-none focus:border-indigo-500"
            />

            <button
              onClick={addMemory}
              disabled={loading||!memory.trim()}
              className="flex w-full items-center justify-center gap-2 rounded-xl bg-indigo-600 px-4 py-3 font-semibold hover:bg-indigo-500 disabled:opacity-50"
            >
              <Plus size={18}/>
              Save memory
            </button>
          </section>

          <section className="rounded-2xl border border-slate-800 bg-slate-900 p-6 lg:col-span-2">
            <div className="mb-5 flex items-center gap-3">
              <Search size={20}/>
              <h2 className="font-semibold">
                Semantic search
              </h2>
            </div>

            <div className="mb-6 flex gap-3">
              <input
                value={query}
                onChange={e=>setQuery(e.target.value)}
                onKeyDown={e=>{
                  if(e.key==='Enter') searchMemory();
                }}
                placeholder="Search your agent's memory..."
                className="flex-1 rounded-xl border border-slate-700 bg-slate-800 px-4 py-3 text-white outline-none focus:border-indigo-500"
              />

              <button
                onClick={searchMemory}
                disabled={loading||!query.trim()}
                className="rounded-xl bg-indigo-600 px-5 py-3 font-semibold hover:bg-indigo-500 disabled:opacity-50"
              >
                Search
              </button>
            </div>

            <div className="space-y-3">
              {results.length===0 ? (
                <div className="rounded-xl border border-dashed border-slate-700 p-8 text-center text-slate-500">
                  No search results yet.
                </div>
              ) : (
                results.map((result,index)=>(
                  <div
                    key={result.id||index}
                    className="rounded-xl border border-slate-800 bg-slate-800/50 p-4"
                  >
                    <div className="mb-2 flex items-center justify-between">
                      <span className="text-xs text-slate-500">
                        {result.namespace||namespace}
                      </span>

                      {result.score!==undefined && (
                        <span className="text-xs text-slate-500">
                          Score: {Number(result.score).toFixed(3)}
                        </span>
                      )}
                    </div>

                    <p className="text-sm leading-6 text-slate-200">
                      {result.content||result.text||JSON.stringify(result)}
                    </p>
                  </div>
                ))
              )}
            </div>
          </section>
        </div>

        <div className="mt-6 grid gap-6 md:grid-cols-3">
          <section className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
            <div className="mb-4 flex items-center gap-3">
              <KeyRound size={20}/>
              <h2 className="font-semibold">
                API Keys
              </h2>
            </div>

            <button
              onClick={createKey}
              disabled={loading}
              className="mb-4 flex w-full items-center justify-center gap-2 rounded-xl bg-slate-800 px-4 py-3 font-medium hover:bg-slate-700 disabled:opacity-50"
            >
              <Plus size={16}/>
              Create API key
            </button>

            {key && (
              <div className="rounded-xl border border-slate-700 bg-slate-800 p-3">
                <div className="break-all font-mono text-xs text-slate-300">
                  {key}
                </div>

                <button
                  onClick={()=>{
                    navigator.clipboard.writeText(key);
                    setNotice('API key copied');
                  }}
                  className="mt-3 flex items-center gap-2 text-xs text-indigo-400 hover:text-indigo-300"
                >
                  <Copy size={14}/>
                  Copy key
                </button>
              </div>
            )}
          </section>

          <section className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
            <div className="mb-4 flex items-center gap-3">
              <Archive size={20}/>
              <h2 className="font-semibold">
                Memory management
              </h2>
            </div>

            <p className="mb-4 text-sm leading-6 text-slate-400">
              Manage namespaces, archive memories, and maintain long-term agent context.
            </p>

            <button
              onClick={()=>setNotice('Memory management tools are ready for API integration.')}
              className="flex w-full items-center justify-center gap-2 rounded-xl bg-slate-800 px-4 py-3 font-medium hover:bg-slate-700"
            >
              Manage memories
              <ChevronRight size={16}/>
            </button>
          </section>

          <section className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
            <div className="mb-4 flex items-center gap-3">
              <Download size={20}/>
              <h2 className="font-semibold">
                Data export
              </h2>
            </div>

            <p className="mb-4 text-sm leading-6 text-slate-400">
              Export your ContextVault data as JSON.
            </p>

            <button
              onClick={exportData}
              disabled={loading}
              className="flex w-full items-center justify-center gap-2 rounded-xl bg-slate-800 px-4 py-3 font-medium hover:bg-slate-700 disabled:opacity-50"
            >
              <Download size={16}/>
              Export data
            </button>
          </section>
        </div>
      </div>
    </main>
  );
}