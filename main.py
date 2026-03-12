"""
Micro-SaaS Idea Validator — Find SaaS ideas worth building

Setup:
  pip install -r requirements.txt
  cp .env.example .env          # add your GROQ_API_KEY
  uvicorn main:app --reload
  open http://localhost:8000
"""
import os, sqlite3
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import httpx
from dotenv import load_dotenv

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
DB_FILE      = "micro_saas_idea_validator.db"
SYSTEM_PROMPT = "You are a specialised AI tool: Micro-SaaS Idea Validator.\n\nYou are an experienced business strategist. Give advice that is specific to the user's situation, not generic.\n\nYour job: Describe a micro-SaaS idea. Get a validation framework with market size and competition analysis.\n\nThe user will provide: idea description, target customer, existing solutions, your edge. Use all of this information to personalise your response.\n\nOutput format: Structure your response as clear numbered steps. Each step on its own line, actionable and specific. Tell the user exactly what to do.\n\nQuality rules:\n- Be specific to what the user has actually provided \u2014 never give generic advice that ignores their inputs\n- Do not start with filler openers like Sure, Great, Certainly, or Of course\n- Do not explain what you are about to do \u2014 just do it\n- Do not add unnecessary disclaimers unless they are genuinely important\n- If the user's input is vague, make reasonable assumptions and state them briefly\n- Aim for depth over length \u2014 one specific, useful insight beats three generic ones"

app = FastAPI(title="Micro-SaaS Idea Validator")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


# ── Database ───────────────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS queries (
                id     INTEGER PRIMARY KEY AUTOINCREMENT,
                prompt TEXT NOT NULL,
                result TEXT,
                ts     TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.commit()

init_db()


# ── Frontend (injected HTML app) ───────────────────────────────────────────────

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Micro-SaaS Idea Validator</title>
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500;9..40,600&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box;margin:0;padding:0}
:root{--acc:#84cc16;--acc2:#a3e635;--bg:#050900;--s1:color-mix(in srgb,var(--bg) 60%,#111);--s2:color-mix(in srgb,var(--bg) 40%,#1a1a1a);--b1:rgba(255,255,255,.06);--b2:rgba(255,255,255,.11);--text:#e8eaef;--muted:#6b7280;--dim:#374151;--ok:#34d399;--err:#f87171}
html,body{height:100%;overflow:hidden}
body{font-family:'DM Sans',sans-serif;background:var(--bg);color:var(--text)}
#auth-overlay{position:fixed;inset:0;z-index:200;background:var(--bg);display:flex;align-items:center;justify-content:center;padding:24px}
.auth-box{width:100%;max-width:400px;background:var(--s1);border:1px solid var(--b2);border-radius:16px;padding:36px 32px}
.auth-logo{font-family:'Syne',sans-serif;font-size:22px;font-weight:800;color:var(--acc);margin-bottom:6px}
.auth-sub{color:var(--muted);font-size:13px;margin-bottom:28px;font-weight:300}
.auth-tabs{display:flex;margin-bottom:24px;background:var(--s2);border-radius:8px;padding:3px}
.auth-tab{flex:1;padding:8px;text-align:center;font-size:13px;font-weight:500;border-radius:6px;cursor:pointer;color:var(--muted)}
.auth-tab.active{background:var(--s1);color:var(--text);box-shadow:0 1px 4px rgba(0,0,0,.3)}
.auth-field{margin-bottom:14px}
.auth-field label{display:block;font-size:11px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin-bottom:6px}
.auth-field input{width:100%;background:var(--s2);border:1px solid var(--b1);border-radius:8px;color:var(--text);padding:11px 14px;font-size:14px;font-family:'DM Sans',sans-serif;outline:none;transition:border-color .2s}
.auth-field input:focus{border-color:var(--acc)}
.auth-btn{width:100%;background:var(--acc);color:var(--bg);border:none;border-radius:8px;padding:12px;font-weight:700;font-size:14px;font-family:'DM Sans',sans-serif;cursor:pointer;margin-top:4px}
.auth-btn:hover{filter:brightness(1.1)}
.auth-err{color:var(--err);font-size:12px;margin-top:10px;text-align:center}
#setup-overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,.85);backdrop-filter:blur(12px);z-index:200;align-items:center;justify-content:center}
#app-root{display:none;flex-direction:column;height:100vh}
#app-root.visible{display:flex}
/* App shell */
#main-app{display:none;grid-template-columns:220px 1fr;height:calc(100vh - 48px);overflow:hidden}
/* Sidebar nav */
.nav-sidebar{background:var(--s1);border-right:1px solid var(--b1);display:flex;flex-direction:column;overflow:hidden}
.nav-brand{padding:16px 16px 12px;border-bottom:1px solid var(--b1)}
.nav-logo{font-family:'Syne',sans-serif;font-size:14px;font-weight:800;color:var(--acc);letter-spacing:-.2px}
.nav-tagline{font-size:11px;color:var(--muted);margin-top:2px;font-weight:300;line-height:1.5}
.nav-section{padding:14px 10px 6px;flex:1;overflow-y:auto}
.nav-lbl{font-size:9px;font-weight:700;letter-spacing:.13em;text-transform:uppercase;color:var(--dim);padding:0 8px;margin-bottom:8px}
.nav-item{display:flex;align-items:center;gap:9px;padding:9px 10px;border-radius:8px;cursor:pointer;font-size:12px;color:var(--muted);border:1px solid transparent;margin-bottom:2px;transition:all .15s;font-weight:400}
.nav-item:hover{background:var(--s2);color:var(--text)}
.nav-item.active{background:color-mix(in srgb,var(--acc) 10%,transparent);border-color:color-mix(in srgb,var(--acc) 25%,transparent);color:var(--acc);font-weight:500}
.nav-icon{font-size:14px;width:18px;text-align:center;flex-shrink:0}
.nav-footer{padding:12px 10px;border-top:1px solid var(--b1);flex-shrink:0}
.user-chip{display:flex;align-items:center;gap:8px;font-size:11px;color:var(--muted)}
.user-avatar{width:24px;height:24px;border-radius:50%;background:var(--acc);color:var(--bg);display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:700}
.btn-logout{margin-left:auto;font-size:11px;color:var(--dim);cursor:pointer;background:none;border:none;font-family:'DM Sans',sans-serif}
.btn-logout:hover{color:var(--err)}
/* Main area */
.main-area{display:flex;flex-direction:column;overflow:hidden}
/* Header bar */
header#main-header{height:48px;padding:0 24px;background:var(--s1);border-bottom:1px solid var(--b1);display:none;align-items:center;justify-content:space-between;flex-shrink:0}
.hdr-left{display:flex;align-items:center;gap:10px}
.hdr-title{font-family:'Syne',sans-serif;font-size:15px;font-weight:800;letter-spacing:-.3px}
.mode-badge{font-size:9px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);border:1px solid var(--b2);border-radius:99px;padding:2px 8px}
.hdr-actions{display:flex;gap:6px}
.hdr-btn{background:none;border:1px solid var(--b1);border-radius:6px;padding:5px 12px;font-size:11px;font-weight:600;color:var(--muted);cursor:pointer;font-family:'DM Sans',sans-serif;transition:all .15s;display:inline-flex;align-items:center;gap:5px}
.hdr-btn:hover{border-color:var(--acc);color:var(--acc)}
/* Panels */
.panel{display:none;flex:1;overflow-y:auto}
.panel.active{display:block}
/* Input panel */
.input-panel-inner{max-width:640px;margin:0 auto;padding:28px 28px 60px}
.panel-head{margin-bottom:24px}
.panel-title{font-family:'Syne',sans-serif;font-size:20px;font-weight:800;letter-spacing:-.5px;margin-bottom:6px}
.panel-sub{font-size:13px;color:var(--muted);font-weight:300;line-height:1.7}
.card{background:var(--s1);border:1px solid var(--b1);border-radius:12px;padding:20px;margin-bottom:12px}
.card-lbl{font-size:10px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--dim);margin-bottom:14px}
.field{margin-bottom:14px}
.field:last-child{margin-bottom:0}
.field label{display:block;font-size:11px;font-weight:600;letter-spacing:.07em;text-transform:uppercase;color:var(--muted);margin-bottom:6px}
.field input[type=text],.field textarea,.field select{width:100%;background:var(--s2);border:1px solid var(--b1);border-radius:8px;color:var(--text);padding:10px 13px;font-size:13px;font-family:'DM Sans',sans-serif;font-weight:300;outline:none;transition:border-color .2s}
.field input[type=text]:focus,.field textarea:focus,.field select:focus{border-color:color-mix(in srgb,var(--acc) 60%,transparent)}
.field textarea{resize:vertical;min-height:80px;line-height:1.6}
.field select{cursor:pointer;appearance:none;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%236b7280' stroke-width='2'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E");background-repeat:no-repeat;background-position:right 12px center;padding-right:30px}
.field select option{background:var(--s2)}
.btn-row{display:flex;gap:8px;margin-top:16px;align-items:center}
.btn-primary{background:var(--acc);color:var(--bg);border:none;border-radius:8px;padding:10px 24px;font-weight:700;font-size:13px;cursor:pointer;font-family:'DM Sans',sans-serif;display:inline-flex;align-items:center;gap:7px;transition:all .15s;box-shadow:0 2px 12px color-mix(in srgb,var(--acc) 30%,transparent)}
.btn-primary:hover{filter:brightness(1.08);transform:translateY(-1px)}
.btn-primary:disabled{opacity:.4;cursor:not-allowed;transform:none;box-shadow:none}
.loading{display:none;align-items:center;gap:8px;color:var(--acc);font-size:12px}
.spin{width:13px;height:13px;flex-shrink:0;border:2px solid color-mix(in srgb,var(--acc) 20%,transparent);border-top-color:var(--acc);border-radius:50%;animation:spin .55s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
/* Report panel */
.report-panel-inner{max-width:760px;margin:0 auto;padding:28px 28px 80px}
.report-empty{display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:50vh;text-align:center;color:var(--dim);gap:12px;opacity:.5}
.report-empty-icon{font-size:52px}
.report-empty-text{font-size:13px;line-height:1.8}
/* KPI cards */
.kpi-row{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:10px;margin-bottom:20px}
.kpi-card{background:var(--s1);border:1px solid var(--b1);border-radius:10px;padding:14px 16px}
.kpi-label{font-size:10px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--dim);margin-bottom:6px}
.kpi-value{font-family:'Syne',sans-serif;font-size:22px;font-weight:800;color:var(--acc)}
.kpi-sub{font-size:11px;color:var(--muted);margin-top:3px}
/* Report sections */
.report-section{background:var(--s1);border:1px solid var(--b1);border-radius:10px;margin-bottom:10px;overflow:hidden}
.report-section-hdr{display:flex;align-items:center;justify-content:space-between;padding:14px 18px;cursor:pointer;user-select:none}
.section-title{font-size:13px;font-weight:700;display:flex;align-items:center;gap:8px}
.section-num{display:inline-flex;align-items:center;justify-content:center;width:20px;height:20px;border-radius:50%;background:color-mix(in srgb,var(--acc) 15%,transparent);color:var(--acc);font-size:10px;font-weight:700}
.section-chevron{color:var(--dim);transition:transform .2s;font-size:12px}
.section-chevron.open{transform:rotate(180deg)}
.section-body{padding:0 18px 16px;display:none;font-size:13px;line-height:1.8;color:var(--text);font-weight:300}
.section-body.open{display:block}
.section-body p{margin-bottom:10px}
.section-body ul,.section-body ol{padding-left:20px;margin-bottom:10px}
.section-body li{margin-bottom:4px}
.section-body strong{font-weight:600;color:var(--acc)}
.section-body table{width:100%;border-collapse:collapse;margin-bottom:10px;font-size:12px}
.section-body th{background:var(--s2);padding:8px 10px;text-align:left;font-weight:600;border-bottom:1px solid var(--b2)}
.section-body td{padding:7px 10px;border-bottom:1px solid var(--b1)}
/* Number highlight */
.num-highlight{color:var(--acc);font-weight:700}
#result-card,#history-section{display:none!important}
@keyframes fadeUp{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:translateY(0)}}
@media print{.nav-sidebar,.hdr-actions,header#main-header{display:none!important}.main-area{overflow:visible}.panel.active{overflow:visible}.report-section-hdr{cursor:default}.section-body{display:block!important}}
</style>
</head>
<body>
<div id="auth-overlay">
  <div class="auth-box">
    <div class="auth-logo">Micro-SaaS Idea Validator</div>
    <div class="auth-sub">Find SaaS ideas worth building</div>
    <div class="auth-tabs"><div class="auth-tab active" onclick="switchTab('login')">Log in</div><div class="auth-tab" onclick="switchTab('signup')">Sign up</div></div>
    <div id="login-form">
      <div class="auth-field"><label>Email</label><input type="email" id="login-email" placeholder="you@example.com"></div>
      <div class="auth-field"><label>Password</label><input type="password" id="login-pw" placeholder="••••••••"></div>
      <button class="auth-btn" onclick="login()">Log in</button>
    </div>
    <div id="signup-form" style="display:none">
      <div class="auth-field"><label>Name</label><input type="text" id="signup-name" placeholder="Jane Smith"></div>
      <div class="auth-field"><label>Email</label><input type="email" id="signup-email" placeholder="you@example.com"></div>
      <div class="auth-field"><label>Password</label><input type="password" id="signup-pw" placeholder="Min 6 chars"></div>
      <button class="auth-btn" onclick="signup()">Create account</button>
    </div>
    <div class="auth-err" id="auth-err"></div>
  </div>
</div>
<div id="setup-overlay">
  <div id="setup-local" style="background:var(--s1);border:1px solid var(--b2);border-radius:16px;padding:40px;max-width:460px;width:90%;text-align:center;display:none">
    <div style="font-size:36px;margin-bottom:12px">🔑</div>
    <h2 style="font-family:'Syne',sans-serif;font-size:20px;font-weight:800;margin-bottom:8px">One-time setup</h2>
    <p style="color:var(--muted);font-size:13px;line-height:1.7;margin-bottom:24px">Paste your Groq API key.<br><a href="https://console.groq.com" target="_blank" style="color:var(--acc);font-weight:600">Get free key →</a></p>
    <input id="setup-key-input" type="password" placeholder="gsk_..." style="width:100%;background:var(--s2);border:1px solid var(--b2);border-radius:8px;color:var(--text);padding:12px 16px;font-size:14px;outline:none;margin-bottom:12px;font-family:monospace;box-sizing:border-box">
    <div id="setup-err" style="color:#ff6b6b;font-size:12px;margin-bottom:10px;min-height:18px"></div>
    <button onclick="saveSetupKey()" style="width:100%;background:var(--acc);color:#fff;border:none;border-radius:8px;padding:12px;font-weight:700;font-size:14px;cursor:pointer;font-family:'Syne',sans-serif">Save & Start</button>
  </div>
  <div id="setup-deployed" style="background:var(--s1);border:1px solid var(--b2);border-radius:16px;padding:40px;max-width:460px;width:90%;text-align:center;display:none">
    <div style="font-size:36px;margin-bottom:12px">⚙️</div>
    <h2 style="font-family:'Syne',sans-serif;font-size:20px;font-weight:800;margin-bottom:8px">Not configured</h2>
    <p style="color:var(--muted);font-size:13px;line-height:1.7;margin-bottom:20px">Add <code style="background:var(--s2);padding:2px 6px;border-radius:4px">GROQ_API_KEY</code> as env var.</p>
    <a href="https://console.groq.com" target="_blank" style="display:inline-block;background:var(--acc);color:#fff;text-decoration:none;border-radius:8px;padding:10px 20px;font-weight:700;font-size:13px;font-family:'Syne',sans-serif">Get free key →</a>
  </div>
</div>
<div id="apikey-banner" style="display:none"></div>
<div id="app-root">
  <header id="main-header">
    <div class="hdr-left"><div class="hdr-title" id="hdr-title">Micro-SaaS Idea Validator</div><div class="mode-badge" id="mode-badge">HTML App</div></div>
    <div class="hdr-actions">
      <button class="hdr-btn" id="copy-btn" onclick="copyResult()">Copy</button>
      <button class="hdr-btn" onclick="regenerate()">↻ Redo</button>
      <button class="hdr-btn" onclick="improveResult()">✦ Improve</button>
      <button class="hdr-btn" onclick="window.print()">🖨 Print</button>
    </div>
  </header>
  <div id="main-app">
    <!-- Nav sidebar -->
    <div class="nav-sidebar">
      <div class="nav-brand">
        <div class="nav-logo">Micro-SaaS Idea Validator</div>
        <div class="nav-tagline">Find SaaS ideas worth building</div>
      </div>
      <div class="nav-section">
        <div class="nav-lbl">Workspace</div>
        <div class="nav-item active" onclick="showPanel('input')" id="nav-input"><span class="nav-icon">⚡</span>Generate</div>
        <div class="nav-item" onclick="showPanel('report')" id="nav-report"><span class="nav-icon">📊</span>Report</div>
        <div class="nav-item" onclick="showPanel('history')" id="nav-history"><span class="nav-icon">🕐</span>History</div>
      </div>
      <div class="nav-footer">
        <div class="user-chip"><div class="user-avatar" id="user-avatar">?</div><span id="user-name"></span><button class="btn-logout" onclick="logout()">Exit</button></div>
      </div>
    </div>
    <!-- Main content -->
    <div class="main-area">
      <!-- Input panel -->
      <div class="panel active" id="panel-input">
        <div class="input-panel-inner">
          <div class="panel-head">
            <div class="panel-title">Micro-SaaS Idea Validator</div>
            <div class="panel-sub">Describe a micro-SaaS idea. Get a validation framework with market size and competition analysis. Built for users.</div>
          </div>
          <div class="card">
            <div class="card-lbl">Your inputs</div>
                <div class="field">
      <label for="field-idea_description">Idea Description</label>
      <textarea id="field-idea_description" placeholder="Enter idea description..." required></textarea>
    </div>
    <div class="field">
      <label for="field-target_customer">Target Customer</label>
      <input type="text" id="field-target_customer" placeholder="e.g. your target customer">
    </div>
    <div class="field">
      <label for="field-existing_solutions">Existing Solutions</label>
      <input type="text" id="field-existing_solutions" placeholder="e.g. your existing solutions">
    </div>
    <div class="field">
      <label for="field-your_edge">Your Edge</label>
      <input type="text" id="field-your_edge" placeholder="e.g. your your edge">
    </div>
            <div class="btn-row">
              <button class="btn-primary" id="gen-btn" onclick="generate()"><svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><polygon points="5,3 19,12 5,21"/></svg>Generate Report</button>
              <div class="loading" id="loading"><div class="spin"></div><span id="loading-text">Analysing…</span></div>
            </div>
          </div>
        </div>
      </div>
      <!-- Report panel -->
      <div class="panel" id="panel-report">
        <div class="report-panel-inner">
          <div class="report-empty" id="report-empty">
            <div class="report-empty-icon">📋</div>
            <div class="report-empty-text">Fill in your inputs and generate<br>to see your report here</div>
          </div>
          <div id="result-content" style="display:none">
            <div id="kpi-row" class="kpi-row"></div>
            <div id="report-sections"></div>
          </div>
        </div>
      </div>
      <!-- History panel -->
      <div class="panel" id="panel-history">
        <div class="input-panel-inner">
          <div class="panel-head"><div class="panel-title">History</div></div>
          <div id="history-display"></div>
        </div>
      </div>
    </div>
  </div>
</div>
<div id="result-card" style="display:none"></div>
<div id="history-section" style="display:none"><div id="history-list"></div></div>
<script>
const APP={name:'Micro-SaaS Idea Validator',mode:'fastapi',auth:true,systemPrompt:"You are a specialised AI tool: Micro-SaaS Idea Validator.\\n\\nYou are an experienced business strategist. Give advice that is specific to the user's situation, not generic.\\n\\nYour job: Describe a micro-SaaS idea. Get a validation framework with market size and competition analysis.\\n\\nThe user will provide: idea description, target customer, existing solutions, your edge. Use all of this information to personalise your response.\\n\\nOutput format: Structure your response as clear numbered steps. Each step on its own line, actionable and specific. Tell the user exactly what to do.\\n\\nQuality rules:\\n- Be specific to what the user has actually provided \\u2014 never give generic advice that ignores their inputs\\n- Do not start with filler openers like Sure, Great, Certainly, or Of course\\n- Do not explain what you are about to do \\u2014 just do it\\n- Do not add unnecessary disclaimers unless they are genuinely important\\n- If the user's input is vague, make reasonable assumptions and state them briefly\\n- Aim for depth over length \\u2014 one specific, useful insight beats three generic ones",promptTemplate:"Idea Description: {{idea_description}}\\nTarget Customer: {{target_customer}}\\nExisting Solutions: {{existing_solutions}}\\nYour Edge: {{your_edge}}",resultFormat:'steps',resultConfig:{"label": "Result", "copyable": true},inputs:[{"id": "idea_description", "label": "Idea Description", "type": "textarea", "placeholder": "Enter idea description...", "required": true}, {"id": "target_customer", "label": "Target Customer", "type": "text", "placeholder": "e.g. your target customer", "required": false}, {"id": "existing_solutions", "label": "Existing Solutions", "type": "text", "placeholder": "e.g. your existing solutions", "required": false}, {"id": "your_edge", "label": "Your Edge", "type": "text", "placeholder": "e.g. your your edge", "required": false}]};
const UK=APP.name+':users',SK=APP.name+':session';
function getUsers(){try{return JSON.parse(localStorage.getItem(UK)||'{}')}catch{return {}}}
function getSession(){try{return JSON.parse(localStorage.getItem(SK)||'null')}catch{return null}}
function saveSession(s){localStorage.setItem(SK,JSON.stringify(s))}
function switchTab(t){document.getElementById('login-form').style.display=t==='login'?'':'none';document.getElementById('signup-form').style.display=t==='signup'?'':'none';document.querySelectorAll('.auth-tab').forEach((el,i)=>el.classList.toggle('active',i===(t==='login'?0:1)));document.getElementById('auth-err').textContent=''}
function signup(){const name=document.getElementById('signup-name').value.trim(),email=document.getElementById('signup-email').value.trim().toLowerCase(),pw=document.getElementById('signup-pw').value;if(!name||!email||!pw){setAuthErr('All fields required.');return}if(pw.length<6){setAuthErr('Password 6+ chars.');return}const users=getUsers();if(users[email]){setAuthErr('Account exists.');return}users[email]={name,pw};localStorage.setItem(UK,JSON.stringify(users));saveSession({email,name});onLoggedIn({email,name})}
function login(){const email=document.getElementById('login-email').value.trim().toLowerCase(),pw=document.getElementById('login-pw').value;if(!email||!pw){setAuthErr('Enter email and password.');return}const users=getUsers();if(!users[email]||users[email].pw!==pw){setAuthErr('Incorrect email or password.');return}const s={email,name:users[email].name};saveSession(s);onLoggedIn(s)}
function logout(){localStorage.removeItem(SK);document.getElementById('auth-overlay').style.display='flex';document.getElementById('app-root').classList.remove('visible')}
function setAuthErr(m){document.getElementById('auth-err').textContent=m}
function onLoggedIn(s){document.getElementById('auth-overlay').style.display='none';document.getElementById('app-root').classList.add('visible');document.getElementById('main-header').style.display='flex';document.getElementById('main-app').style.display='grid';document.getElementById('user-name').textContent=s.name.split(' ')[0];document.getElementById('user-avatar').textContent=s.name[0].toUpperCase();if(APP.mode==='fastapi')fetch('/api/health').then(r=>r.json()).then(d=>{if(!d.ai_ready)showSetup()}).catch(()=>{});renderHistoryPanel()}
function showPanel(name){document.querySelectorAll('.panel').forEach(p=>p.classList.remove('active'));document.querySelectorAll('.nav-item').forEach(n=>n.classList.remove('active'));document.getElementById('panel-'+name).classList.add('active');document.getElementById('nav-'+name).classList.add('active')}
function buildPrompt(){let p=APP.promptTemplate;for(const inp of APP.inputs){const el=document.getElementById('field-'+inp.id),val=el?el.value.trim():'';if(inp.required&&!val)throw new Error('Please fill in "'+inp.label+'"');p=p.replace(new RegExp('\\\\{\\\\{'+inp.id+'\\\\}\\\\}','g'),val||'(not specified)')}return p+'\\n\\nStructure your response with clearly labelled sections using ## headers. Highlight key numbers, percentages, and monetary values. Be specific and data-driven.'}
async function callGroq(up){if(APP.mode==='html'){const key=localStorage.getItem(APP.name+':apikey')||'';if(!key)throw new Error('No API key.');const r=await fetch('https://api.groq.com/openai/v1/chat/completions',{method:'POST',headers:{'Authorization':'Bearer '+key,'Content-Type':'application/json'},body:JSON.stringify({model:'llama-3.3-70b-versatile',messages:[{role:'system',content:APP.systemPrompt},{role:'user',content:up}],max_tokens:1500})});if(!r.ok){const e=await r.json().catch(()=>({}));throw new Error(e?.error?.message||'Groq error '+r.status)}return(await r.json()).choices[0].message.content}else{const r=await fetch('/api/generate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({prompt:up})});if(!r.ok){const e=await r.json().catch(()=>({}));if(e?.detail==='NO_KEY'){showSetup();throw new Error('__SILENT__')}throw new Error(e?.detail||'Server error '+r.status)}return(await r.json()).result}}
let lastResult='',lastPrompt='';
async function generate(){let prompt;try{prompt=buildPrompt()}catch(e){alert(e.message);return}lastPrompt=prompt;setLoading(true);try{const r=await callGroq(prompt);lastResult=r;renderResult(r);saveToHistory(prompt,r);showPanel('report')}catch(e){if(e.message!=='__SILENT__')alert(e.message)}finally{setLoading(false)}}
function renderResult(text){document.getElementById('report-empty').style.display='none';document.getElementById('result-content').style.display='block';// Extract KPI numbers
const kpiRow=document.getElementById('kpi-row');kpiRow.innerHTML='';const nums=text.match(/(\\$[\\d,]+[KMBkm]?|\\d+(?:\\.\\d+)?%|\\d+(?:\\.\\d+)?x)/g)||[];const kpiLabels=text.match(/([A-Z][a-z]+(?: [A-Z][a-z]+)*):?\\s*(?:\\$[\\d,]+[KMBkm]?|\\d+(?:\\.\\d+)?%|\\d+(?:\\.\\d+)?x)/g)||[];const seen=new Set();kpiLabels.slice(0,4).forEach(match=>{const parts=match.split(/:\\s*/);if(parts.length>=2&&!seen.has(parts[0])){seen.add(parts[0]);const numMatch=parts[1].match(/(\\$[\\d,]+[KMBkm]?|\\d+(?:\\.\\d+)?%|\\d+(?:\\.\\d+)?x)/);if(numMatch){kpiRow.innerHTML+=`<div class="kpi-card"><div class="kpi-label">${esc(parts[0])}</div><div class="kpi-value">${esc(numMatch[1])}</div></div>`}}});if(!kpiRow.innerHTML){nums.slice(0,4).forEach((n,i)=>{kpiRow.innerHTML+=`<div class="kpi-card"><div class="kpi-label">Metric ${i+1}</div><div class="kpi-value">${esc(n)}</div></div>`})}// Parse into sections
const secs=document.getElementById('report-sections');secs.innerHTML='';const sections=text.split(/\\n## /);const intro=sections[0].replace(/^## /,'');if(intro.trim()){secs.innerHTML+=renderSection('Overview',intro,0)}sections.slice(1).forEach((sec,i)=>{const nl=sec.indexOf('\\n');const title=nl>-1?sec.slice(0,nl):sec;const body=nl>-1?sec.slice(nl+1):'';secs.innerHTML+=renderSection(title,body,i+1)})}
function renderSection(title,body,idx){const id='sec-'+idx;return`<div class="report-section"><div class="report-section-hdr" onclick="toggleSection('${id}')"><div class="section-title"><span class="section-num">${idx+1}</span>${esc(title)}</div><span class="section-chevron ${idx===0?'open':''}">▼</span></div><div class="section-body ${idx===0?'open':''}">${formatBody(body)}</div></div>`}
function toggleSection(id){const sec=document.getElementById(id);if(!sec)return;const hdr=sec.querySelector('.section-chevron'),body=sec.querySelector('.section-body');body.classList.toggle('open');hdr.classList.toggle('open')}
// Override toggleSection to work without IDs
(function(){const orig=window.toggleSection;window.toggleSection=function(id){const sections=document.querySelectorAll('.report-section');sections.forEach(sec=>{const hdr=sec.querySelector('.report-section-hdr');if(hdr&&hdr.getAttribute('onclick')&&hdr.getAttribute('onclick').includes("'"+id+"'")){const ch=sec.querySelector('.section-chevron'),body=sec.querySelector('.section-body');body.classList.toggle('open');ch.classList.toggle('open')}})}}());
function formatBody(text){function e(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}function il(s){return s.replace(/\\*\\*(.+?)\\*\\*/g,'<strong>$1</strong>').replace(/(\\$[\\d,]+[KMBkm]?|\\d+(?:\\.\\d+)?%|\\d+(?:\\.\\d+)?x)/g,'<span class="num-highlight">$1</span>')}const lines=text.trim().split('\\n');let out='',inUl=false,inOl=false;function cl(){if(inUl){out+='</ul>';inUl=false}if(inOl){out+='</ol>';inOl=false}}for(const line of lines){if(!line.trim()){cl();out+='<br>';continue}if(/^[-*] (.+)/.test(line)){if(inOl){out+='</ol>';inOl=false}if(!inUl){out+='<ul>';inUl=true}out+='<li>'+il(e(line.slice(2)))+'</li>';continue}if(/^\\d+\\. (.+)/.test(line)){if(inUl){out+='</ul>';inUl=false}if(!inOl){out+='<ol>';inOl=true}out+='<li>'+il(e(line.replace(/^\\d+\\. /,'')))+'</li>';continue}cl();out+='<p>'+il(e(line))+'</p>'}cl();return out}
async function copyResult(){try{await navigator.clipboard.writeText(lastResult);const b=document.getElementById('copy-btn');b.textContent='✓ Copied!';setTimeout(()=>b.textContent='Copy',2000)}catch{}}
async function regenerate(){if(!lastPrompt)return;setLoading(true);try{const r=await callGroq(lastPrompt);lastResult=r;renderResult(r);saveToHistory(lastPrompt,r)}catch(e){if(e.message!=='__SILENT__')alert(e.message)}finally{setLoading(false)}}
async function improveResult(){if(!lastResult)return;setLoading(true);const p='Improve and expand this significantly, adding more specific data and insights:\\n\\n'+lastResult;try{const r=await callGroq(p);lastResult=r;renderResult(r);saveToHistory(p,r)}catch(e){if(e.message!=='__SILENT__')alert(e.message)}finally{setLoading(false)}}
async function differentStyle(){if(!lastResult)return;setLoading(true);const p='Rewrite in a different style:\\n\\n'+lastResult;try{const r=await callGroq(p);lastResult=r;renderResult(r);saveToHistory(p,r)}catch(e){if(e.message!=='__SILENT__')alert(e.message)}finally{setLoading(false)}}
const HK=APP.name+':history';
function loadHistory(){try{return JSON.parse(localStorage.getItem(HK)||'[]')}catch{return []}}
function saveToHistory(p,r){const h=loadHistory();h.unshift({id:Date.now(),prompt:p.slice(0,120),result:r,ts:new Date().toLocaleString()});localStorage.setItem(HK,JSON.stringify(h.slice(0,50)))}
function renderHistory(){renderHistoryPanel()}
function renderHistoryPanel(){const h=loadHistory(),el=document.getElementById('history-display');if(!el)return;if(!h.length){el.innerHTML='<div style="color:var(--dim);font-size:13px;text-align:center;padding:20px">No history yet.</div>';return}el.innerHTML=h.map(item=>`<div class="card" style="cursor:pointer;margin-bottom:10px" onclick="loadHistoryItem(${item.id})"><div style="font-size:12px;color:var(--muted);margin-bottom:4px">${esc(item.prompt)}</div><div style="font-size:11px;color:var(--dim)">${item.ts}</div></div>`).join('')}
function loadHistoryItem(id){const item=loadHistory().find(h=>h.id===id);if(!item)return;lastResult=item.result;lastPrompt=item.prompt;renderResult(item.result);showPanel('report')}
function deleteHistoryItem(id){localStorage.setItem(HK,JSON.stringify(loadHistory().filter(h=>h.id!==id)));renderHistoryPanel()}
function clearHistory(){localStorage.removeItem(HK);renderHistoryPanel()}
function esc(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}
function setLoading(on){document.getElementById('gen-btn').disabled=on;document.getElementById('loading').style.display=on?'flex':'none'}
function clearForm(){APP.inputs.forEach(inp=>{const el=document.getElementById('field-'+inp.id);if(el)el.value=''})}
document.addEventListener('keydown',e=>{if(e.ctrlKey&&e.key==='Enter')generate()});
function showSetup(){const isLocal=location.hostname==='localhost'||location.hostname==='127.0.0.1';document.getElementById('setup-local').style.display=isLocal?'block':'none';document.getElementById('setup-deployed').style.display=isLocal?'none':'block';document.getElementById('setup-overlay').style.display='flex'}
async function saveSetupKey(){const key=document.getElementById('setup-key-input').value.trim(),err=document.getElementById('setup-err');err.textContent='';if(!key){err.textContent='Paste your key.';return}if(!key.startsWith('gsk_')){err.textContent='Groq keys start with gsk_';return}try{const r=await fetch('/api/setup',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({api_key:key})});if(!r.ok){const e=await r.json().catch(()=>({}));err.textContent=e?.detail||'Error.';return}document.getElementById('setup-overlay').style.display='none'}catch(e){err.textContent='Error: '+e.message}}
(function init(){if(typeof __LP_PREVIEW__!=='undefined'&&__LP_PREVIEW__){const s={email:'preview@launchpad.app',name:'Preview'};saveSession(s);onLoggedIn(s);return}if(!APP.auth){document.getElementById('auth-overlay').style.display='none';document.getElementById('app-root').classList.add('visible');document.getElementById('main-header').style.display='flex';document.getElementById('main-app').style.display='grid';if(APP.mode==='fastapi')fetch('/api/health').then(r=>r.json()).then(d=>{if(!d.ai_ready)showSetup()}).catch(()=>{});renderHistoryPanel();return}const s=getSession();if(s)onLoggedIn(s)})();
</script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
def index():
    return HTML_PAGE


# ── API ────────────────────────────────────────────────────────────────────────

class GenerateRequest(BaseModel):
    prompt: str

class SetupRequest(BaseModel):
    api_key: str

@app.post("/api/setup")
def setup(req: SetupRequest):
    """Write the API key to .env so user never has to touch a file."""
    key = req.api_key.strip()
    if not key.startswith("gsk_"):
        raise HTTPException(400, detail="Invalid key. Groq keys start with gsk_")
    # Write .env file
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    with open(env_path, "w") as f:
        f.write("GROQ_API_KEY=" + key + chr(10))
    # Reload into current process
    os.environ["GROQ_API_KEY"] = key
    global GROQ_API_KEY
    GROQ_API_KEY = key
    return {"ok": True}

@app.post("/api/generate")
async def generate(req: GenerateRequest):
    if not GROQ_API_KEY:
        raise HTTPException(400, detail="NO_KEY")
    async with httpx.AsyncClient(timeout=40) as client:
        r = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user",   "content": req.prompt},
                ],
                "max_tokens": 1500,
            },
        )
        r.raise_for_status()
        result = r.json()["choices"][0]["message"]["content"]
    with get_db() as conn:
        conn.execute("INSERT INTO queries (prompt, result) VALUES (?, ?)", (req.prompt, result))
        conn.commit()
    return {"result": result}

@app.get("/api/history")
def history():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, prompt, result, ts FROM queries ORDER BY ts DESC LIMIT 20"
        ).fetchall()
    return [dict(r) for r in rows]

@app.get("/api/health")
def health():
    return {"status": "ok", "app": "Micro-SaaS Idea Validator", "ai_ready": bool(GROQ_API_KEY)}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
