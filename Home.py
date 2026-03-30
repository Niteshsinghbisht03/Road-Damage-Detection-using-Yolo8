import sys
from pathlib import Path
import streamlit as st

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

from database.db import init_db
from utils.styles import inject_global_css



st.set_page_config(
    page_title="RDD — Road Damage Detection",
    page_icon="🛣️",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_db()

inject_global_css()

# ── Hero section ──────────────────────────────────────────────────
st.markdown("""
<div style="
  min-height: 38vh;
  display: flex; flex-direction: column; justify-content: center;
  padding: 4rem 0 3rem;
  position: relative;
">
  <div style="
    font-family:'DM Mono',monospace; font-size:0.72rem; letter-spacing:3px;
    color:#f59e0b; text-transform:uppercase; margin-bottom:1rem;
  ">
    ◈ Ministry of Public Works &amp; Housing &nbsp;·&nbsp; CRDDC2022 Dataset &nbsp;·&nbsp; YOLOv8
  </div>
  <div style="
    font-family:'Bebas Neue',sans-serif; font-size:clamp(3.5rem,8vw,7rem);
    letter-spacing:6px; line-height:0.92; color:#e8edf5; margin-bottom:1.2rem;
  ">
    ROAD DAMAGE<br>
    <span style="
      -webkit-text-stroke: 1px #2a3f6b; color: transparent;
      font-size:clamp(3rem,6vw,5.5rem);
    ">DETECTION</span>
  </div>
  <div style="
    font-family:'Barlow',sans-serif; font-size:1.05rem; color:#8899b4;
    max-width:560px; line-height:1.7; margin-bottom:2rem;
  ">
    AI-powered infrastructure monitoring system. Identifies and classifies
    road surface damage in real-time, from images, and video footage.
    Every detection is logged, scored, and mapped.
  </div>
  <div style="display:flex; gap:12px; flex-wrap:wrap;">
    <div style="
      background:linear-gradient(135deg,#b45309,#f59e0b);
      color:#0a0f1e; font-family:'DM Mono',monospace; font-size:0.78rem;
      letter-spacing:1.5px; padding:10px 24px; border-radius:8px;
      font-weight:600; text-transform:uppercase;
    ">↳ Select a mode from the sidebar</div>
    <div style="
      background:transparent; border:1px solid #1e2d4a;
      color:#8899b4; font-family:'DM Mono',monospace; font-size:0.78rem;
      letter-spacing:1px; padding:10px 24px; border-radius:8px;
    ">v2.0 · SQLite · GPS · Severity Scoring</div>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

# ── Detection modes grid ──────────────────────────────────────────
st.markdown("""
<div style="font-family:'Bebas Neue',sans-serif;font-size:1.6rem;letter-spacing:3px;
            color:#e8edf5;margin-bottom:1.2rem;">DETECTION MODES</div>
""", unsafe_allow_html=True)

cards = [
    ("📷", "REALTIME", "pages/1_Realtime_Detection.py",
     "Live webcam stream via WebRTC. On-site monitoring with instant bounding-box overlay.",
     "#3b82f6"),
    ("🖼️", "IMAGE", "pages/2_Image_Detection.py",
     "Upload PNG/JPG. Side-by-side original vs annotated output with download.",
     "#f59e0b"),
    ("🎬", "VIDEO", "pages/3_Video_Detection.py",
     "Process MP4 frame-by-frame. Download the fully annotated output video.",
     "#10b981"),
    ("🛡️", "ADMIN", "pages/4_Admin_Dashboard.py",
     "Charts, detection logs, GPS map, and PDF/CSV export reports.",
     "#a855f7"),
]

# Style the nav buttons to be invisible so the card looks clickable
st.markdown("""
<style>
.card-nav-btn > div > button {
    position: absolute !important;
    top: 0; left: 0; right: 0; bottom: 0;
    width: 100% !important;
    height: 100% !important;
    opacity: 0 !important;
    cursor: pointer !important;
    z-index: 10 !important;
    border: none !important;
    background: transparent !important;
    padding: 0 !important;
    margin: 0 !important;
}
.card-wrapper {
    position: relative;
    cursor: pointer;
    transition: transform 0.15s ease;
}
.card-wrapper:hover {
    transform: translateY(-3px);
}
</style>
""", unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)

for col, (icon, label, page, desc, color) in zip([c1, c2, c3, c4], cards):
    with col:
        st.markdown(f"""
        <div class="card-wrapper">
          <div class="glass-card" style="border-top:3px solid {color};min-height:180px;">
            <div style="font-size:2rem;margin-bottom:0.6rem;">{icon}</div>
            <div style="font-family:'Bebas Neue',sans-serif;font-size:1.3rem;
                        letter-spacing:3px;color:#e8edf5;margin-bottom:0.5rem;">{label}</div>
            <div style="font-family:'Barlow',sans-serif;font-size:0.85rem;
                        color:#8899b4;line-height:1.6;">{desc}</div>
            <div style="margin-top:0.8rem;font-family:'DM Mono',monospace;font-size:0.68rem;
                        letter-spacing:1.5px;color:{color};">→ OPEN {label}</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="card-nav-btn">', unsafe_allow_html=True)
        if st.button(label, key=f"nav_{label}"):
            st.switch_page(page)
        st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("<hr>", unsafe_allow_html=True)

# ── Damage classes ────────────────────────────────────────────────
st.markdown("""
<div style="font-family:'Bebas Neue',sans-serif;font-size:1.6rem;letter-spacing:3px;
            color:#e8edf5;margin-bottom:1.2rem;">DAMAGE CLASSIFICATION</div>
""", unsafe_allow_html=True)

d1, d2, d3, d4 = st.columns(4)
damage_types = [
    ("D-00", "LONGITUDINAL CRACK",
     "Crack running parallel to the road direction. Early-stage structural fatigue.",
     "#3b82f6", "Low"),
    ("D-01", "TRANSVERSE CRACK",
     "Crack running perpendicular to road direction. Common in aging asphalt.",
     "#22c55e", "Low"),
    ("D-10", "ALLIGATOR CRACK",
     "Interconnected network of cracks. Indicates deep structural failure.",
     "#f59e0b", "Medium"),
    ("D-40", "POTHOLE",
     "Bowl-shaped depression. Immediate hazard requiring urgent repair.",
     "#ef4444", "High"),
]

for col, (code, name, desc, color, sev) in zip([d1, d2, d3, d4], damage_types):
    with col:
        st.markdown(f"""
        <div class="glass-card" style="min-height:160px;">
          <div style="font-family:'DM Mono',monospace;font-size:0.65rem;
                      color:{color};letter-spacing:2px;margin-bottom:0.4rem;">{code}</div>
          <div style="font-family:'Bebas Neue',sans-serif;font-size:1rem;
                      letter-spacing:2px;color:#e8edf5;margin-bottom:0.4rem;">{name}</div>
          <div style="font-family:'Barlow',sans-serif;font-size:0.82rem;
                      color:#8899b4;line-height:1.5;margin-bottom:0.8rem;">{desc}</div>
          <div style="display:inline-block;padding:2px 10px;border-radius:20px;
                      background:rgba(255,255,255,0.04);border:1px solid {color}33;
                      font-family:'DM Mono',monospace;font-size:0.68rem;color:{color};">
            Base: {sev}
          </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("<hr>", unsafe_allow_html=True)

# ── What's new ────────────────────────────────────────────────────
st.markdown("""
<div style="font-family:'Bebas Neue',sans-serif;font-size:1.6rem;letter-spacing:3px;
            color:#e8edf5;margin-bottom:1.2rem;">WHAT'S NEW IN V2</div>
<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;">
""", unsafe_allow_html=True)

features = [
    ("🗄️", "SQLite Database", "All detections auto-saved with full session history"),
    ("📍", "GPS Tagging", "Attach lat/lng to every session and view on map"),
    ("🟡", "Severity Scoring", "Per-detection scoring: Low → Medium → High → Critical"),
    ("📊", "Admin Dashboard", "Charts, logs, Folium map, PDF & CSV exports"),
]
fc = st.columns(4)
for col, (icon, title, desc) in zip(fc, features):
    with col:
        st.markdown(f"""
        <div style="background:var(--bg-raised);border:1px solid var(--border);
                    border-radius:10px;padding:1rem 1.1rem;">
          <div style="font-size:1.4rem;margin-bottom:0.4rem;">{icon}</div>
          <div style="font-family:'DM Mono',monospace;font-size:0.78rem;
                      color:#f59e0b;margin-bottom:0.3rem;letter-spacing:1px;">{title}</div>
          <div style="font-family:'Barlow',sans-serif;font-size:0.82rem;color:#8899b4;">{desc}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("""
<div style="font-family:'DM Mono',monospace;font-size:0.68rem;color:#4a5a78;
            letter-spacing:1px;text-align:center;padding-bottom:2rem;">
  CRDDC2022 Dataset &nbsp;·&nbsp; YOLOv8s by Ultralytics &nbsp;·&nbsp; Streamlit &nbsp;·&nbsp;
  <a href="https://github.com/oracl4/RoadDamageDetection" style="color:#3b82f6;text-decoration:none;">
    GitHub
  </a>
</div>
""", unsafe_allow_html=True)