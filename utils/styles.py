"""
Shared CSS design system for Road Damage Detection App.
Import and call inject_global_css() at the top of every page.
"""

import streamlit as st

GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Mono:ital,wght@0,300;0,400;0,500;1,300&family=Barlow:wght@300;400;500;600;700&display=swap');

/* ── CSS Variables ─────────────────────────────────────── */
:root {
  --bg-deep:     #070b14;
  --bg-base:     #0a0f1e;
  --bg-surface:  #0f1729;
  --bg-raised:   #141d35;
  --bg-card:     #151e33;
  --border:      #1e2d4a;
  --border-glow: #2a3f6b;
  --accent:      #f59e0b;
  --accent-dim:  #92610a;
  --accent-glow: rgba(245,158,11,0.15);
  --blue:        #3b82f6;
  --blue-dim:    #1d4ed8;
  --blue-glow:   rgba(59,130,246,0.12);
  --green:       #10b981;
  --red:         #ef4444;
  --purple:      #a855f7;
  --text-primary:   #e8edf5;
  --text-secondary: #8899b4;
  --text-muted:     #4a5a78;
  --font-display: 'Bebas Neue', sans-serif;
  --font-body:    'Barlow', sans-serif;
  --font-mono:    'DM Mono', monospace;
}

/* ── Base resets ───────────────────────────────────────── */
html, body, [class*="css"], .stApp {
  background-color: var(--bg-base) !important;
  font-family: var(--font-body) !important;
  color: var(--text-primary) !important;
}

/* ── Hide Streamlit chrome ─────────────────────────────── */
#MainMenu, footer { visibility: hidden; }
.stDeployButton { display: none; }
/* Hide top toolbar but keep sidebar toggle visible */
header[data-testid="stHeader"] { visibility: hidden; }
[data-testid="stSidebarCollapsedControl"] { visibility: visible !important; }
[data-testid="stSidebarCollapsedControl"] * { visibility: visible !important; }

/* ── Main content padding ──────────────────────────────── */
.block-container {
  padding: 2rem 2.5rem 4rem !important;
  max-width: 1400px;
}

/* ── Page header scan-line effect ──────────────────────── */
.page-header {
  position: relative;
  padding: 2.5rem 0 1.5rem;
  margin-bottom: 2rem;
  border-bottom: 1px solid var(--border);
}
.page-header::before {
  content: '';
  position: absolute;
  top: 0; left: -2.5rem; right: -2.5rem; height: 1px;
  background: linear-gradient(90deg, transparent, var(--accent), transparent);
  animation: scanline 3s ease-in-out infinite;
}
@keyframes scanline {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 1; }
}
.page-title {
  font-family: var(--font-display) !important;
  font-size: 3.2rem !important;
  letter-spacing: 3px !important;
  color: var(--text-primary) !important;
  margin: 0 !important;
  line-height: 1 !important;
}
.page-subtitle {
  font-family: var(--font-mono) !important;
  font-size: 0.78rem !important;
  color: var(--accent) !important;
  letter-spacing: 2px !important;
  text-transform: uppercase !important;
  margin-top: 0.4rem !important;
}

/* ── Sidebar ───────────────────────────────────────────── */
section[data-testid="stSidebar"] {
  background: var(--bg-deep) !important;
  border-right: 1px solid var(--border) !important;
  width: 240px !important;
}
section[data-testid="stSidebar"] > div {
  padding: 0 !important;
}
section[data-testid="stSidebar"] * {
  color: var(--text-secondary) !important;
}
/* Sidebar logo area */
.sidebar-logo {
  padding: 1.8rem 1.4rem 1.2rem;
  border-bottom: 1px solid var(--border);
  margin-bottom: 0.5rem;
}
.sidebar-logo-text {
  font-family: var(--font-display);
  font-size: 1.5rem;
  letter-spacing: 3px;
  color: var(--text-primary) !important;
}
.sidebar-logo-sub {
  font-family: var(--font-mono);
  font-size: 0.65rem;
  color: var(--accent) !important;
  letter-spacing: 1.5px;
  text-transform: uppercase;
  margin-top: 2px;
}
/* Sidebar radio nav */
section[data-testid="stSidebar"] .stRadio > label { display: none !important; }
section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] {
  gap: 2px !important;
  padding: 0 0.8rem;
}
section[data-testid="stSidebar"] .stRadio label[data-baseweb="radio"] {
  background: transparent !important;
  padding: 0.65rem 1rem !important;
  border-radius: 8px !important;
  transition: all 0.15s ease !important;
  border: 1px solid transparent !important;
  cursor: pointer;
}
section[data-testid="stSidebar"] .stRadio label[data-baseweb="radio"]:hover {
  background: var(--bg-raised) !important;
  border-color: var(--border) !important;
}
section[data-testid="stSidebar"] [aria-checked="true"] {
  background: var(--accent-glow) !important;
  border-color: var(--accent-dim) !important;
  color: var(--accent) !important;
}

/* ── Glassmorphism card ────────────────────────────────── */
.glass-card {
  background: linear-gradient(135deg, rgba(21,30,51,0.9) 0%, rgba(15,23,42,0.95) 100%);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 1.4rem 1.6rem;
  position: relative;
  overflow: hidden;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.glass-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0; height: 1px;
  background: linear-gradient(90deg, transparent, var(--border-glow), transparent);
}
.glass-card:hover {
  border-color: var(--border-glow);
  box-shadow: 0 8px 32px rgba(0,0,0,0.4);
}
.glass-card-accent {
  border-left: 3px solid var(--accent) !important;
}
.glass-card-blue {
  border-left: 3px solid var(--blue) !important;
}

/* ── KPI metric cards ──────────────────────────────────── */
[data-testid="metric-container"] {
  background: linear-gradient(135deg, var(--bg-card) 0%, var(--bg-surface) 100%) !important;
  border: 1px solid var(--border) !important;
  border-radius: 12px !important;
  padding: 1.2rem 1.4rem !important;
  position: relative;
  overflow: hidden;
  transition: all 0.2s;
}
[data-testid="metric-container"]::after {
  content: '';
  position: absolute;
  top: 0; right: 0;
  width: 60px; height: 60px;
  background: radial-gradient(circle at top right, var(--accent-glow), transparent);
  border-radius: 0 12px 0 60px;
}
[data-testid="metric-container"]:hover {
  border-color: var(--accent-dim) !important;
  box-shadow: 0 0 20px var(--accent-glow);
}
[data-testid="metric-container"] label {
  font-family: var(--font-mono) !important;
  font-size: 0.7rem !important;
  letter-spacing: 1.5px !important;
  text-transform: uppercase !important;
  color: var(--text-muted) !important;
}
[data-testid="stMetricValue"] {
  font-family: var(--font-display) !important;
  font-size: 2.2rem !important;
  letter-spacing: 1px !important;
  color: var(--text-primary) !important;
}
[data-testid="stMetricDelta"] { font-family: var(--font-mono) !important; font-size: 0.75rem !important; }

/* ── Severity badges ───────────────────────────────────── */
.sev-badge {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 3px 12px; border-radius: 20px;
  font-family: var(--font-mono); font-size: 0.72rem;
  font-weight: 500; letter-spacing: 1px; text-transform: uppercase;
}
.sev-none     { background: rgba(74,90,120,0.25); color: var(--text-muted); border: 1px solid #2a3a56; }
.sev-low      { background: rgba(16,185,129,0.12); color: #34d399; border: 1px solid rgba(16,185,129,0.3); }
.sev-medium   { background: rgba(245,158,11,0.12); color: #fbbf24; border: 1px solid rgba(245,158,11,0.3); }
.sev-high     { background: rgba(239,68,68,0.12); color: #f87171; border: 1px solid rgba(239,68,68,0.3); }
.sev-critical { background: rgba(168,85,247,0.12); color: #c084fc; border: 1px solid rgba(168,85,247,0.3); }

/* ── Buttons ───────────────────────────────────────────── */
.stButton > button {
  font-family: var(--font-mono) !important;
  font-size: 0.8rem !important;
  letter-spacing: 1px !important;
  border-radius: 8px !important;
  transition: all 0.15s ease !important;
  border: 1px solid var(--border) !important;
  background: var(--bg-raised) !important;
  color: var(--text-secondary) !important;
}
.stButton > button:hover {
  background: var(--bg-card) !important;
  border-color: var(--border-glow) !important;
  color: var(--text-primary) !important;
}
.stButton > button[kind="primary"] {
  background: linear-gradient(135deg, #b45309, var(--accent)) !important;
  border-color: var(--accent) !important;
  color: #0a0f1e !important;
  font-weight: 600 !important;
  box-shadow: 0 0 20px rgba(245,158,11,0.25) !important;
}
.stButton > button[kind="primary"]:hover {
  box-shadow: 0 0 30px rgba(245,158,11,0.45) !important;
  transform: translateY(-1px) !important;
}

/* ── Download buttons ──────────────────────────────────── */
.stDownloadButton > button {
  font-family: var(--font-mono) !important;
  font-size: 0.78rem !important;
  letter-spacing: 0.8px !important;
  border-radius: 8px !important;
  background: var(--bg-raised) !important;
  border: 1px solid var(--border-glow) !important;
  color: var(--blue) !important;
  transition: all 0.15s !important;
}
.stDownloadButton > button:hover {
  background: var(--blue-glow) !important;
  border-color: var(--blue) !important;
  color: #93c5fd !important;
}

/* ── Form inputs ───────────────────────────────────────── */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stSelectbox > div > div,
.stTextArea > div > div > textarea {
  background: var(--bg-raised) !important;
  border: 1px solid var(--border) !important;
  border-radius: 8px !important;
  color: var(--text-primary) !important;
  font-family: var(--font-mono) !important;
  font-size: 0.85rem !important;
}
.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus {
  border-color: var(--accent-dim) !important;
  box-shadow: 0 0 0 2px var(--accent-glow) !important;
}
.stTextInput label, .stNumberInput label,
.stSelectbox label, .stSlider label,
.stFileUploader label, .stCheckbox label {
  font-family: var(--font-mono) !important;
  font-size: 0.75rem !important;
  letter-spacing: 1px !important;
  text-transform: uppercase !important;
  color: var(--text-muted) !important;
}

/* ── Slider ────────────────────────────────────────────── */
.stSlider > div > div > div > div {
  background: var(--accent) !important;
}
.stSlider > div > div > div {
  background: var(--border) !important;
}

/* ── File uploader ─────────────────────────────────────── */
[data-testid="stFileUploader"] {
  background: var(--bg-raised) !important;
  border: 1px dashed var(--border-glow) !important;
  border-radius: 12px !important;
  padding: 1rem !important;
  transition: all 0.2s !important;
}
[data-testid="stFileUploader"]:hover {
  border-color: var(--accent-dim) !important;
  background: rgba(245,158,11,0.04) !important;
}

/* ── Expander ──────────────────────────────────────────── */
.streamlit-expanderHeader {
  background: var(--bg-raised) !important;
  border: 1px solid var(--border) !important;
  border-radius: 8px !important;
  font-family: var(--font-mono) !important;
  font-size: 0.8rem !important;
  letter-spacing: 0.8px !important;
  color: var(--text-secondary) !important;
}
.streamlit-expanderContent {
  background: var(--bg-surface) !important;
  border: 1px solid var(--border) !important;
  border-top: none !important;
  border-radius: 0 0 8px 8px !important;
}

/* ── Dataframe / table ─────────────────────────────────── */
.stDataFrame {
  border-radius: 10px !important;
  overflow: hidden !important;
  border: 1px solid var(--border) !important;
}
iframe[title="st_aggrid"] { border-radius: 10px; }

/* ── Alerts ────────────────────────────────────────────── */
.stAlert {
  border-radius: 10px !important;
  font-family: var(--font-mono) !important;
  font-size: 0.82rem !important;
  border: 1px solid !important;
}
.stAlert[data-baseweb="notification"][kind="info"] {
  background: rgba(59,130,246,0.08) !important;
  border-color: rgba(59,130,246,0.3) !important;
}
.stAlert[data-baseweb="notification"][kind="success"] {
  background: rgba(16,185,129,0.08) !important;
  border-color: rgba(16,185,129,0.3) !important;
}
.stAlert[data-baseweb="notification"][kind="warning"] {
  background: rgba(245,158,11,0.08) !important;
  border-color: rgba(245,158,11,0.3) !important;
}
.stAlert[data-baseweb="notification"][kind="error"] {
  background: rgba(239,68,68,0.08) !important;
  border-color: rgba(239,68,68,0.3) !important;
}

/* ── Progress bar ──────────────────────────────────────── */
.stProgress > div > div > div > div {
  background: linear-gradient(90deg, var(--accent-dim), var(--accent)) !important;
  border-radius: 4px !important;
}
.stProgress > div > div > div {
  background: var(--bg-raised) !important;
  border-radius: 4px !important;
}

/* ── Checkbox ──────────────────────────────────────────── */
.stCheckbox > label > span[data-testid="stMarkdownContainer"] {
  font-family: var(--font-mono) !important;
  font-size: 0.82rem !important;
}

/* ── Divider ───────────────────────────────────────────── */
hr {
  border: none !important;
  border-top: 1px solid var(--border) !important;
  margin: 1.5rem 0 !important;
}

/* ── Caption ───────────────────────────────────────────── */
.stCaption {
  font-family: var(--font-mono) !important;
  font-size: 0.72rem !important;
  color: var(--text-muted) !important;
  letter-spacing: 0.5px !important;
}

/* ── Subheader ─────────────────────────────────────────── */
h2, h3 {
  font-family: var(--font-display) !important;
  letter-spacing: 2px !important;
  color: var(--text-primary) !important;
}

/* ── Scrollbar ─────────────────────────────────────────── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: var(--bg-deep); }
::-webkit-scrollbar-thumb { background: var(--border-glow); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--accent-dim); }

/* ── Animated grid bg ──────────────────────────────────── */
.stApp::before {
  content: '';
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background-image:
    linear-gradient(rgba(30,45,74,0.25) 1px, transparent 1px),
    linear-gradient(90deg, rgba(30,45,74,0.25) 1px, transparent 1px);
  background-size: 40px 40px;
  pointer-events: none;
  z-index: 0;
}

/* ── Confidence bar ────────────────────────────────────── */
.conf-bar-wrap {
  background: var(--bg-raised);
  border-radius: 4px;
  height: 6px;
  width: 100%;
  overflow: hidden;
  margin-top: 3px;
}
.conf-bar-fill {
  height: 100%;
  border-radius: 4px;
  background: linear-gradient(90deg, var(--accent-dim), var(--accent));
  transition: width 0.6s ease;
}
</style>
"""

def inject_global_css():
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

def page_header(title: str, subtitle: str = ""):
    st.markdown(f"""
    <div class="page-header">
      <div class="page-title">{title}</div>
      {"<div class='page-subtitle'>" + subtitle + "</div>" if subtitle else ""}
    </div>
    """, unsafe_allow_html=True)

def severity_badge(severity: str) -> str:
    cls_map = {
        "None":     ("sev-none",     "●"),
        "Low":      ("sev-low",      "▲"),
        "Medium":   ("sev-medium",   "◆"),
        "High":     ("sev-high",     "■"),
        "Critical": ("sev-critical", "★"),
    }
    cls, icon = cls_map.get(severity, ("sev-none", "●"))
    return f'<span class="sev-badge {cls}">{icon} {severity}</span>'

def confidence_bar(conf: float, color: str = "#f59e0b") -> str:
    pct = int(conf * 100)
    return (
        f'<div style="font-family:\'DM Mono\',monospace;font-size:0.78rem;color:#8899b4;">'
        f'{pct}%'
        f'<div class="conf-bar-wrap">'
        f'<div class="conf-bar-fill" style="width:{pct}%;background:linear-gradient(90deg,#92610a,{color});"></div>'
        f'</div></div>'
    )

def glass_card(content: str, accent: str = "") -> str:
    extra = f"glass-card-{accent}" if accent else ""
    return f'<div class="glass-card {extra}">{content}</div>'