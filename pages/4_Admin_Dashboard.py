"""
Admin Dashboard — Road Damage Detection v2
"""
import sys
import json
from pathlib import Path
from datetime import datetime

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

HERE = Path(__file__).parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))

from database.db import (
    init_db, get_dashboard_stats, get_all_sessions,
    get_session_by_id, get_detections_for_session, delete_session,
)
from utils.severity import severity_color, severity_emoji
from utils.export import (
    export_sessions_csv, export_detections_csv,
    export_session_pdf, export_all_sessions_pdf,
)
from utils.styles import inject_global_css, severity_badge, confidence_bar

st.set_page_config(
    page_title="Admin Dashboard — RDD",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_global_css()
init_db()

# ── Extra dashboard-specific CSS ──────────────────────────────────
st.markdown("""
<style>
/* Login page full-screen centering */
.login-wrap {
  display: flex; align-items: center; justify-content: center;
  min-height: 80vh;
}
.login-card {
  background: linear-gradient(160deg, #0f1729 0%, #070b14 100%);
  border: 1px solid #1e2d4a;
  border-radius: 20px;
  padding: 3rem 2.8rem 2.5rem;
  width: 100%; max-width: 420px;
  position: relative; overflow: hidden;
}
.login-card::before {
  content: '';
  position: absolute; top: 0; left: 0; right: 0; height: 2px;
  background: linear-gradient(90deg, transparent, #f59e0b, #3b82f6, transparent);
}
.login-title {
  font-family: 'Bebas Neue', sans-serif;
  font-size: 2.2rem; letter-spacing: 4px;
  color: #e8edf5; margin-bottom: 0.2rem;
}
.login-sub {
  font-family: 'DM Mono', monospace;
  font-size: 0.7rem; letter-spacing: 2px;
  color: #4a5a78; text-transform: uppercase; margin-bottom: 2rem;
}
/* Stat number glow */
.stat-glow {
  font-family: 'Bebas Neue', sans-serif;
  font-size: 3rem; letter-spacing: 2px;
  color: #e8edf5;
  text-shadow: 0 0 30px rgba(245,158,11,0.3);
}
/* Section label */
.section-label {
  font-family: 'DM Mono', monospace;
  font-size: 0.65rem; letter-spacing: 2.5px;
  color: #f59e0b; text-transform: uppercase;
  margin-bottom: 0.8rem;
}
/* Table row hover */
.det-table tr:hover td { background: rgba(30,45,74,0.4) !important; }
/* Sidebar nav item active */
.nav-active {
  background: rgba(245,158,11,0.1) !important;
  border-left: 3px solid #f59e0b !important;
  color: #f59e0b !important;
}
</style>
""", unsafe_allow_html=True)

# ── Auth ──────────────────────────────────────────────────────────
ADMIN_USER = "admin"
ADMIN_PASS = "rdd@2024"

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    # Centered login card
    _, mid, _ = st.columns([1, 1.2, 1])
    with mid:
        st.markdown("<div style='height:8vh'></div>", unsafe_allow_html=True)
        st.markdown("""
        <div class="login-card">
          <div style="font-size:2rem;margin-bottom:0.8rem;">🛡️</div>
          <div class="login-title">ADMIN ACCESS</div>
          <div class="login-sub">Road Damage Detection System</div>
        </div>
        """, unsafe_allow_html=True)

        with st.form("login_form"):
            username = st.text_input("Username", placeholder="admin")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            submitted = st.form_submit_button(
                "◈  AUTHENTICATE", use_container_width=True, type="primary"
            )

        if submitted:
            if username == ADMIN_USER and password == ADMIN_PASS:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Authentication failed. Check credentials.")

        st.markdown("""
        <div style="font-family:'DM Mono',monospace;font-size:0.65rem;color:#4a5a78;
                    text-align:center;margin-top:1.5rem;letter-spacing:1px;">
        Default: admin / rdd@2024
        </div>
        """, unsafe_allow_html=True)
    st.stop()

# ── Sidebar ───────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sidebar-logo">
      <div style="font-size:1.5rem;margin-bottom:0.3rem;">🛣️</div>
      <div class="sidebar-logo-text">RDD ADMIN</div>
      <div class="sidebar-logo-sub">Road Damage Detection v2</div>
    </div>
    """, unsafe_allow_html=True)

    page = st.radio(
        "nav",
        ["📊  Overview", "📋  Detection Logs", "🗺️  Map View", "📤  Export Reports"],
        label_visibility="collapsed",
    )

    st.markdown("<div style='flex:1'></div>", unsafe_allow_html=True)
    st.markdown("<div style='position:absolute;bottom:2rem;left:0;right:0;padding:0 0.8rem;'>", unsafe_allow_html=True)

    # System status
    st.markdown(f"""
    <div style="background:var(--bg-raised);border:1px solid var(--border);
                border-radius:8px;padding:10px 12px;margin-bottom:10px;">
      <div style="font-family:'DM Mono',monospace;font-size:0.62rem;
                  color:#4a5a78;letter-spacing:1.5px;margin-bottom:4px;">SYSTEM</div>
      <div style="display:flex;align-items:center;gap:6px;">
        <div style="width:6px;height:6px;border-radius:50%;background:#10b981;
                    box-shadow:0 0 6px #10b981;"></div>
        <span style="font-family:'DM Mono',monospace;font-size:0.72rem;color:#34d399;">
          ONLINE
        </span>
      </div>
      <div style="font-family:'DM Mono',monospace;font-size:0.62rem;color:#4a5a78;
                  margin-top:4px;">{datetime.now().strftime('%H:%M:%S')}</div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("◈  LOGOUT", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

stats    = get_dashboard_stats()
sessions = get_all_sessions()

# ── Plotly dark theme helper ──────────────────────────────────────
def dark_layout(fig, height=300):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(7,11,20,0.6)",
        font=dict(family="DM Mono, monospace", color="#8899b4", size=11),
        margin=dict(l=8, r=8, t=16, b=8),
        height=height,
        legend=dict(
            bgcolor="rgba(0,0,0,0)", bordercolor="#1e2d4a",
            font=dict(size=10, color="#8899b4"),
        ),
    )
    fig.update_xaxes(gridcolor="#0f1729", linecolor="#1e2d4a", tickfont=dict(size=10))
    fig.update_yaxes(gridcolor="#0f1729", linecolor="#1e2d4a", tickfont=dict(size=10))
    return fig


# ═══════════════════════════════════════════════════════════════════
# PAGE 1 — OVERVIEW
# ═══════════════════════════════════════════════════════════════════
if "Overview" in page:

    # Page header
    st.markdown(f"""
    <div style="display:flex;justify-content:space-between;align-items:flex-end;
                padding-bottom:1.2rem;border-bottom:1px solid var(--border);margin-bottom:1.8rem;">
      <div>
        <div class="section-label">◈ Admin Dashboard</div>
        <div style="font-family:'Bebas Neue',sans-serif;font-size:2.8rem;
                    letter-spacing:4px;color:#e8edf5;line-height:1;">OVERVIEW</div>
      </div>
      <div style="font-family:'DM Mono',monospace;font-size:0.7rem;color:#4a5a78;text-align:right;">
        Last updated<br>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
      </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("↺  REFRESH", type="primary"):
        st.rerun()

    # ── KPI cards ─────────────────────────────────────────────────
    k1, k2, k3, k4, k5 = st.columns(5)
    kpis = [
        (k1, "📁", "SESSIONS",     stats["total_sessions"],    "#3b82f6"),
        (k2, "🎯", "DETECTIONS",   stats["total_detections"],  "#f59e0b"),
        (k3, "🕳️", "POTHOLES",     stats["pothole_count"],     "#ef4444"),
        (k4, "🕸️", "ALLIGATOR",    stats["alligator_count"],   "#f59e0b"),
        (k5, "〰️", "LONGITUDINAL", stats["longitudinal_count"], "#3b82f6"),
    ]
    for col, icon, label, value, color in kpis:
        with col:
            col.markdown(f"""
            <div class="glass-card" style="border-top:2px solid {color};text-align:center;
                                           padding:1.2rem 0.8rem;">
              <div style="font-size:1.6rem;margin-bottom:0.3rem;">{icon}</div>
              <div style="font-family:'DM Mono',monospace;font-size:0.62rem;letter-spacing:2px;
                          color:#4a5a78;text-transform:uppercase;">{label}</div>
              <div style="font-family:'Bebas Neue',sans-serif;font-size:2.6rem;
                          letter-spacing:2px;color:{color};line-height:1.1;
                          text-shadow:0 0 20px {color}44;">{value}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

    # ── Charts ────────────────────────────────────────────────────
    c_left, c_mid, c_right = st.columns([2.2, 1.4, 1.4], gap="medium")

    with c_left:
        st.markdown('<div class="section-label">◈ Daily Detection Sessions — Last 30 Days</div>',
                    unsafe_allow_html=True)
        daily = stats.get("daily_sessions", [])
        if daily:
            df_daily = pd.DataFrame(daily).sort_values("day")
            fig = go.Figure(go.Bar(
                x=df_daily["day"], y=df_daily["cnt"],
                marker=dict(
                    color=df_daily["cnt"],
                    colorscale=[[0, "#1e2d4a"], [0.5, "#3b82f6"], [1, "#f59e0b"]],
                    line=dict(width=0),
                ),
                hovertemplate="<b>%{x}</b><br>Sessions: %{y}<extra></extra>",
            ))
            dark_layout(fig, 260)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.markdown("""
            <div style="height:260px;display:flex;align-items:center;justify-content:center;
                        background:var(--bg-raised);border-radius:12px;
                        font-family:'DM Mono',monospace;font-size:0.75rem;color:#4a5a78;">
              No session data yet
            </div>
            """, unsafe_allow_html=True)

    with c_mid:
        st.markdown('<div class="section-label">◈ Damage Type Breakdown</div>',
                    unsafe_allow_html=True)
        labels = ["Longitudinal", "Transverse", "Alligator", "Potholes"]
        values = [
            stats["longitudinal_count"], stats["transverse_count"],
            stats["alligator_count"],    stats["pothole_count"],
        ]
        if sum(values) > 0:
            fig2 = go.Figure(go.Pie(
                labels=labels, values=values, hole=0.62,
                marker=dict(
                    colors=["#3b82f6", "#22c55e", "#f59e0b", "#ef4444"],
                    line=dict(color="#070b14", width=2),
                ),
                textfont=dict(family="DM Mono, monospace", size=10),
                hovertemplate="<b>%{label}</b><br>Count: %{value}<br>%{percent}<extra></extra>",
            ))
            fig2.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(family="DM Mono, monospace", color="#8899b4"),
                margin=dict(l=0, r=0, t=10, b=0),
                height=260,
                legend=dict(
                    bgcolor="rgba(0,0,0,0)", font=dict(size=10),
                    orientation="v", x=1.0, y=0.5,
                ),
                annotations=[dict(
                    text=f'<b>{sum(values)}</b><br><span style="font-size:9px">total</span>',
                    x=0.5, y=0.5, font=dict(family="Bebas Neue", size=22, color="#e8edf5"),
                    showarrow=False,
                )],
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.markdown("""
            <div style="height:260px;display:flex;align-items:center;justify-content:center;
                        background:var(--bg-raised);border-radius:12px;
                        font-family:'DM Mono',monospace;font-size:0.75rem;color:#4a5a78;">
              No damage data yet
            </div>
            """, unsafe_allow_html=True)

    with c_right:
        st.markdown('<div class="section-label">◈ Severity Distribution</div>',
                    unsafe_allow_html=True)
        sev_data = stats.get("severity_dist", [])
        if sev_data:
            df_sev = pd.DataFrame(sev_data)
            sev_order  = ["None", "Low", "Medium", "High", "Critical"]
            sev_colors_map = {
                "None": "#1e2d4a", "Low": "#10b981",
                "Medium": "#f59e0b", "High": "#ef4444", "Critical": "#a855f7",
            }
            df_sev = df_sev.set_index("overall_severity").reindex(sev_order).fillna(0).reset_index()
            colors = [sev_colors_map.get(s, "#1e2d4a") for s in df_sev["overall_severity"]]
            fig3 = go.Figure(go.Bar(
                x=df_sev["overall_severity"], y=df_sev["cnt"],
                marker=dict(color=colors, line=dict(width=0)),
                hovertemplate="<b>%{x}</b><br>Sessions: %{y}<extra></extra>",
            ))
            dark_layout(fig3, 260)
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.markdown("""
            <div style="height:260px;display:flex;align-items:center;justify-content:center;
                        background:var(--bg-raised);border-radius:12px;
                        font-family:'DM Mono',monospace;font-size:0.75rem;color:#4a5a78;">
              No severity data yet
            </div>
            """, unsafe_allow_html=True)

    # ── Recent sessions ───────────────────────────────────────────
    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    st.markdown('<div class="section-label">◈ Recent Sessions</div>', unsafe_allow_html=True)

    if sessions:
        rows_html = ""
        for s in sessions[:10]:
            sev   = s.get("overall_severity") or "None"
            badge = severity_badge(sev)
            stype = s.get("session_type", "").upper()
            date  = (s.get("created_at") or "")[:19]
            fname = (s.get("source_filename") or "—")[:22]
            loc   = s.get("location_name") or "—"
            total = s.get("total_count") or 0
            type_color = {"IMAGE": "#3b82f6", "VIDEO": "#10b981", "REALTIME": "#f59e0b"}.get(stype, "#8899b4")

            rows_html += (
                f'<tr style="border-bottom:1px solid var(--border);">'
                f'<td style="padding:10px 14px;font-family:\'DM Mono\',monospace;font-size:0.7rem;color:#4a5a78;">#{s["id"]:04d}</td>'
                f'<td style="padding:10px 14px;"><span style="font-family:\'DM Mono\',monospace;font-size:0.7rem;color:{type_color};background:rgba(255,255,255,0.04);padding:2px 8px;border-radius:4px;border:1px solid {type_color}33;">{stype}</span></td>'
                f'<td style="padding:10px 14px;font-family:\'DM Mono\',monospace;font-size:0.72rem;color:#8899b4;">{date}</td>'
                f'<td style="padding:10px 14px;font-family:\'Barlow\',sans-serif;font-size:0.85rem;color:#e8edf5;">{fname}</td>'
                f'<td style="padding:10px 14px;font-family:\'Barlow\',sans-serif;font-size:0.82rem;color:#8899b4;">{loc}</td>'
                f'<td style="padding:10px 14px;text-align:center;font-family:\'Bebas Neue\',sans-serif;font-size:1.1rem;color:#e8edf5;">{total}</td>'
                f'<td style="padding:10px 14px;">{badge}</td>'
                f'</tr>'
            )

        table_html = (
            '<div style="background:var(--bg-surface);border:1px solid var(--border);border-radius:14px;overflow:hidden;">'
            '<table style="width:100%;border-collapse:collapse;">'
            '<thead><tr style="background:var(--bg-raised);border-bottom:1px solid var(--border);">'
            '<th style="padding:10px 14px;text-align:left;font-family:\'DM Mono\',monospace;font-size:0.62rem;letter-spacing:2px;color:#4a5a78;">ID</th>'
            '<th style="padding:10px 14px;text-align:left;font-family:\'DM Mono\',monospace;font-size:0.62rem;letter-spacing:2px;color:#4a5a78;">TYPE</th>'
            '<th style="padding:10px 14px;text-align:left;font-family:\'DM Mono\',monospace;font-size:0.62rem;letter-spacing:2px;color:#4a5a78;">DATE</th>'
            '<th style="padding:10px 14px;text-align:left;font-family:\'DM Mono\',monospace;font-size:0.62rem;letter-spacing:2px;color:#4a5a78;">FILE</th>'
            '<th style="padding:10px 14px;text-align:left;font-family:\'DM Mono\',monospace;font-size:0.62rem;letter-spacing:2px;color:#4a5a78;">LOCATION</th>'
            '<th style="padding:10px 14px;text-align:center;font-family:\'DM Mono\',monospace;font-size:0.62rem;letter-spacing:2px;color:#4a5a78;">DETECTIONS</th>'
            '<th style="padding:10px 14px;text-align:left;font-family:\'DM Mono\',monospace;font-size:0.62rem;letter-spacing:2px;color:#4a5a78;">SEVERITY</th>'
            '</tr></thead>'
            f'<tbody>{rows_html}</tbody>'
            '</table></div>'
        )
        st.markdown(table_html, unsafe_allow_html=True)
    else:
        st.info("No sessions recorded yet. Run a detection from Image / Video / Realtime pages.")


# ═══════════════════════════════════════════════════════════════════
# PAGE 2 — DETECTION LOGS
# ═══════════════════════════════════════════════════════════════════
elif "Logs" in page:
    st.markdown("""
    <div style="padding-bottom:1.2rem;border-bottom:1px solid var(--border);margin-bottom:1.8rem;">
      <div class="section-label">◈ Admin Dashboard</div>
      <div style="font-family:'Bebas Neue',sans-serif;font-size:2.8rem;
                  letter-spacing:4px;color:#e8edf5;line-height:1;">DETECTION LOGS</div>
    </div>
    """, unsafe_allow_html=True)

    if not sessions:
        st.info("No sessions recorded yet.")
        st.stop()

    # Filters
    f1, f2, f3 = st.columns([1, 1, 2])
    with f1:
        type_filter = st.selectbox("SESSION TYPE", ["All", "image", "video", "realtime"])
    with f2:
        sev_filter  = st.selectbox("SEVERITY",     ["All", "Critical", "High", "Medium", "Low", "None"])
    with f3:
        search_term = st.text_input("SEARCH", placeholder="filename or location…")

    filtered = sessions
    if type_filter != "All":
        filtered = [s for s in filtered if s.get("session_type") == type_filter]
    if sev_filter != "All":
        filtered = [s for s in filtered if s.get("overall_severity") == sev_filter]
    if search_term:
        q = search_term.lower()
        filtered = [
            s for s in filtered
            if q in (s.get("source_filename") or "").lower()
            or q in (s.get("location_name") or "").lower()
        ]

    st.markdown(f"""
    <div style="font-family:'DM Mono',monospace;font-size:0.7rem;color:#4a5a78;
                margin-bottom:1rem;letter-spacing:1px;">
      ◈ {len(filtered)} session{"s" if len(filtered) != 1 else ""} found
    </div>
    """, unsafe_allow_html=True)

    for s in filtered:
        sev   = s.get("overall_severity") or "None"
        badge = severity_badge(sev)
        total = s.get("total_count") or 0
        date  = (s.get("created_at") or "")[:19]
        stype = s.get("session_type", "").upper()
        type_color = {"IMAGE": "#3b82f6", "VIDEO": "#10b981", "REALTIME": "#f59e0b"}.get(stype, "#8899b4")

        with st.expander(
            f"#{s['id']:04d}  ·  {stype}  ·  {total} detections  ·  {sev}  ·  {date}"
        ):
            col_a, col_b, col_c = st.columns([1.5, 1.5, 1])

            with col_a:
                st.markdown(f"""
                <div style="font-family:'DM Mono',monospace;font-size:0.72rem;
                            color:#8899b4;line-height:2.2;">
                  <span style="color:#4a5a78;">FILE</span>&nbsp;&nbsp;&nbsp;
                    {s.get('source_filename') or '—'}<br>
                  <span style="color:#4a5a78;">LOC&nbsp;</span>&nbsp;&nbsp;&nbsp;
                    {s.get('location_name') or '—'}<br>
                  <span style="color:#4a5a78;">GPS&nbsp;</span>&nbsp;&nbsp;&nbsp;
                    {s.get('latitude', 'N/A')} / {s.get('longitude', 'N/A')}
                </div>
                """, unsafe_allow_html=True)

            with col_b:
                vals = [
                    ("Longitudinal", s.get('longitudinal_count', 0), "#3b82f6"),
                    ("Transverse",   s.get('transverse_count',   0), "#22c55e"),
                    ("Alligator",    s.get('alligator_count',    0), "#f59e0b"),
                    ("Potholes",     s.get('pothole_count',      0), "#ef4444"),
                ]
                for name, count, color in vals:
                    pct = min(count / max(total, 1) * 100, 100)
                    st.markdown(f"""
                    <div style="margin-bottom:6px;">
                      <div style="display:flex;justify-content:space-between;
                                  font-family:'DM Mono',monospace;font-size:0.68rem;margin-bottom:2px;">
                        <span style="color:#8899b4;">{name}</span>
                        <span style="color:{color};">{count}</span>
                      </div>
                      <div style="background:var(--bg-raised);border-radius:3px;height:4px;overflow:hidden;">
                        <div style="width:{pct}%;height:100%;background:{color};border-radius:3px;
                                    transition:width 0.6s;"></div>
                      </div>
                    </div>
                    """, unsafe_allow_html=True)

            with col_c:
                st.markdown(f"""
                <div style="text-align:center;padding:0.5rem 0;">
                  {badge}
                  <div style="font-family:'Bebas Neue',sans-serif;font-size:2.5rem;
                              color:#e8edf5;margin-top:0.3rem;">{total}</div>
                  <div style="font-family:'DM Mono',monospace;font-size:0.62rem;
                              color:#4a5a78;letter-spacing:1px;">TOTAL DETECTIONS</div>
                </div>
                """, unsafe_allow_html=True)

            dets = get_detections_for_session(s["id"])
            st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

            b1, b2, b3 = st.columns(3)
            with b1:
                if dets:
                    st.download_button(
                        "⬇  CSV", export_detections_csv(dets),
                        f"session_{s['id']}_detections.csv", "text/csv",
                        use_container_width=True,
                    )
            with b2:
                st.download_button(
                    "⬇  PDF REPORT", export_session_pdf(s, dets),
                    f"session_{s['id']}_report.pdf", "application/pdf",
                    use_container_width=True,
                )
            with b3:
                if st.button(f"🗑  DELETE", key=f"del_{s['id']}", use_container_width=True):
                    delete_session(s["id"])
                    st.success(f"Session #{s['id']} deleted.")
                    st.rerun()

            if dets:
                st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
                rows_html = ""
                for i, d in enumerate(dets, 1):
                    color  = ["#3b82f6","#22c55e","#f59e0b","#ef4444"][d.get("class_id", 0) % 4]
                    badge2 = severity_badge(d.get("severity","None"))
                    bar    = confidence_bar(d.get("confidence", 0), color)
                    ts     = str(d.get("detected_at",""))[:19]
                    rows_html += (
                        f'<tr style="border-bottom:1px solid var(--border);">'
                        f'<td style="padding:8px 12px;font-family:\'DM Mono\',monospace;font-size:0.68rem;color:#4a5a78;">#{i:03d}</td>'
                        f'<td style="padding:8px 12px;font-family:\'Barlow\',sans-serif;font-size:0.85rem;color:{color};">{d.get("class_name","")}</td>'
                        f'<td style="padding:8px 12px;min-width:100px;">{bar}</td>'
                        f'<td style="padding:8px 12px;">{badge2}</td>'
                        f'<td style="padding:8px 12px;font-family:\'DM Mono\',monospace;font-size:0.68rem;color:#4a5a78;">{ts}</td>'
                        f'</tr>'
                    )
                table_html = (
                    '<div style="background:var(--bg-deep);border:1px solid var(--border);border-radius:10px;overflow:hidden;">'
                    '<table style="width:100%;border-collapse:collapse;">'
                    '<thead><tr style="background:var(--bg-raised);">'
                    '<th style="padding:8px 12px;text-align:left;font-family:\'DM Mono\',monospace;font-size:0.6rem;letter-spacing:1.5px;color:#4a5a78;">#</th>'
                    '<th style="padding:8px 12px;text-align:left;font-family:\'DM Mono\',monospace;font-size:0.6rem;letter-spacing:1.5px;color:#4a5a78;">CLASS</th>'
                    '<th style="padding:8px 12px;text-align:left;font-family:\'DM Mono\',monospace;font-size:0.6rem;letter-spacing:1.5px;color:#4a5a78;">CONFIDENCE</th>'
                    '<th style="padding:8px 12px;text-align:left;font-family:\'DM Mono\',monospace;font-size:0.6rem;letter-spacing:1.5px;color:#4a5a78;">SEVERITY</th>'
                    '<th style="padding:8px 12px;text-align:left;font-family:\'DM Mono\',monospace;font-size:0.6rem;letter-spacing:1.5px;color:#4a5a78;">TIME</th>'
                    '</tr></thead>'
                    f'<tbody>{rows_html}</tbody>'
                    '</table></div>'
                )
                st.markdown(table_html, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
# PAGE 3 — MAP VIEW
# ═══════════════════════════════════════════════════════════════════
elif "Map" in page:
    st.markdown("""
    <div style="padding-bottom:1.2rem;border-bottom:1px solid var(--border);margin-bottom:1.8rem;">
      <div class="section-label">◈ Admin Dashboard</div>
      <div style="font-family:'Bebas Neue',sans-serif;font-size:2.8rem;
                  letter-spacing:4px;color:#e8edf5;line-height:1;">DAMAGE MAP</div>
    </div>
    """, unsafe_allow_html=True)

    map_points = stats.get("map_points", [])

    if not map_points:
        st.markdown("""
        <div style="background:var(--bg-raised);border:1px solid var(--border);
                    border-radius:12px;padding:3rem;text-align:center;">
          <div style="font-size:3rem;margin-bottom:1rem;opacity:0.3;">🗺️</div>
          <div style="font-family:'Bebas Neue',sans-serif;font-size:1.4rem;
                      letter-spacing:3px;color:#4a5a78;margin-bottom:0.5rem;">
            NO GPS DATA
          </div>
          <div style="font-family:'DM Mono',monospace;font-size:0.75rem;color:#4a5a78;">
            Add latitude/longitude when saving Image or Video detections.
          </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        try:
            import folium
            from streamlit_folium import st_folium

            lats   = [p["latitude"]  for p in map_points]
            lngs   = [p["longitude"] for p in map_points]
            centre = [sum(lats)/len(lats), sum(lngs)/len(lngs)]

            m = folium.Map(location=centre, zoom_start=12, tiles="CartoDB dark_matter")

            sev_color_map = {
                "None": "gray", "Low": "green",
                "Medium": "orange", "High": "red", "Critical": "purple",
            }

            for p in map_points:
                sev   = p.get("overall_severity") or "None"
                color = sev_color_map.get(sev, "gray")
                popup_html = f"""
                <div style="font-family:monospace;font-size:12px;background:#0f172a;
                             color:#e8edf5;padding:12px;border-radius:8px;min-width:160px;">
                  <b style="color:#f59e0b;">{p.get('location_name') or 'Unknown Location'}</b><br>
                  <span style="color:#8899b4;">Severity:</span> {sev}<br>
                  <span style="color:#8899b4;">Detections:</span> {p.get('total_count', 0)}<br>
                  <span style="color:#8899b4;">Date:</span> {(p.get('created_at') or '')[:10]}
                </div>
                """
                folium.CircleMarker(
                    location=[p["latitude"], p["longitude"]],
                    radius=12, color=color, fill=True,
                    fill_color=color, fill_opacity=0.75,
                    popup=folium.Popup(popup_html, max_width=240),
                    tooltip=f"{'★' if sev=='Critical' else '●'} {sev} — {p.get('location_name') or 'Location'}",
                ).add_to(m)

            legend = """
            <div style='position:fixed;bottom:30px;left:30px;z-index:9999;
                        background:#070b14;border:1px solid #1e2d4a;border-radius:10px;
                        padding:12px 16px;font-family:monospace;font-size:12px;color:#8899b4;'>
              <div style="color:#f59e0b;font-weight:bold;margin-bottom:6px;
                           letter-spacing:2px;font-size:11px;">SEVERITY</div>
              <div>🟣 Critical &nbsp; 🔴 High</div>
              <div>🟠 Medium &nbsp; 🟢 Low &nbsp; ⚫ None</div>
            </div>
            """
            m.get_root().html.add_child(folium.Element(legend))
            st_folium(m, width=None, height=540, returned_objects=[])

        except ImportError:
            st.warning("Install `folium streamlit-folium` for map view. Showing table instead.")
            st.dataframe(pd.DataFrame(map_points), use_container_width=True)

    # Tagged sessions table
    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    st.markdown('<div class="section-label">◈ GPS-Tagged Sessions</div>', unsafe_allow_html=True)
    tagged = [s for s in sessions if s.get("latitude") and s.get("longitude")]
    if tagged:
        df_t = pd.DataFrame(tagged)[[
            "id","session_type","created_at","location_name",
            "latitude","longitude","total_count","overall_severity",
        ]]
        df_t.columns = ["ID","Type","Date","Location","Lat","Lng","Detections","Severity"]
        df_t["Date"] = df_t["Date"].str[:10]
        st.dataframe(df_t, use_container_width=True, hide_index=True)
    else:
        st.info("No GPS-tagged sessions yet.")


# ═══════════════════════════════════════════════════════════════════
# PAGE 4 — EXPORT REPORTS
# ═══════════════════════════════════════════════════════════════════
elif "Export" in page:
    st.markdown("""
    <div style="padding-bottom:1.2rem;border-bottom:1px solid var(--border);margin-bottom:1.8rem;">
      <div class="section-label">◈ Admin Dashboard</div>
      <div style="font-family:'Bebas Neue',sans-serif;font-size:2.8rem;
                  letter-spacing:4px;color:#e8edf5;line-height:1;">EXPORT REPORTS</div>
    </div>
    """, unsafe_allow_html=True)

    # Full export cards
    st.markdown('<div class="section-label">◈ Full Database Export</div>', unsafe_allow_html=True)
    e1, e2 = st.columns(2, gap="medium")

    with e1:
        st.markdown("""
        <div class="glass-card glass-card-blue" style="margin-bottom:0.5rem;">
          <div style="font-size:1.8rem;margin-bottom:0.5rem;">📊</div>
          <div style="font-family:'Bebas Neue',sans-serif;font-size:1.2rem;
                      letter-spacing:2px;color:#e8edf5;margin-bottom:0.3rem;">ALL SESSIONS CSV</div>
          <div style="font-family:'Barlow',sans-serif;font-size:0.83rem;color:#8899b4;">
            Complete session log with damage counts, severity, GPS, and timestamps.
          </div>
        </div>
        """, unsafe_allow_html=True)
        st.download_button(
            label="⬇  DOWNLOAD CSV",
            data=export_sessions_csv(sessions),
            file_name=f"rdd_sessions_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with e2:
        st.markdown("""
        <div class="glass-card glass-card-accent" style="margin-bottom:0.5rem;">
          <div style="font-size:1.8rem;margin-bottom:0.5rem;">📄</div>
          <div style="font-family:'Bebas Neue',sans-serif;font-size:1.2rem;
                      letter-spacing:2px;color:#e8edf5;margin-bottom:0.3rem;">FULL REPORT PDF</div>
          <div style="font-family:'Barlow',sans-serif;font-size:0.83rem;color:#8899b4;">
            Session log with overall statistics. Monospaced, printable format.
          </div>
        </div>
        """, unsafe_allow_html=True)
        st.download_button(
            label="⬇  DOWNLOAD PDF",
            data=export_all_sessions_pdf(sessions, stats),
            file_name=f"rdd_report_{datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)

    # Single session export
    st.markdown('<div class="section-label">◈ Single Session Export</div>', unsafe_allow_html=True)

    if not sessions:
        st.info("No sessions to export yet.")
    else:
        session_options = {
            f"#{s['id']:04d}  ·  {s.get('session_type','').upper()}  ·  "
            f"{(s.get('created_at') or '')[:10]}  ·  "
            f"{s.get('overall_severity','None')} severity": s["id"]
            for s in sessions
        }
        selected_label = st.selectbox("SELECT SESSION", list(session_options.keys()))
        selected_id    = session_options[selected_label]
        selected       = get_session_by_id(selected_id)
        dets           = get_detections_for_session(selected_id)

        if selected:
            sev = selected.get("overall_severity", "None")
            st.markdown(f"""
            <div class="glass-card" style="margin:1rem 0;">
              <div style="display:flex;gap:2rem;flex-wrap:wrap;align-items:center;">
                <div>
                  <div style="font-family:'DM Mono',monospace;font-size:0.62rem;
                              color:#4a5a78;letter-spacing:1.5px;">SESSION</div>
                  <div style="font-family:'Bebas Neue',sans-serif;font-size:1.8rem;
                              color:#e8edf5;">#{selected_id:04d}</div>
                </div>
                <div>
                  <div style="font-family:'DM Mono',monospace;font-size:0.62rem;
                              color:#4a5a78;letter-spacing:1.5px;">DETECTIONS</div>
                  <div style="font-family:'Bebas Neue',sans-serif;font-size:1.8rem;
                              color:#f59e0b;">{selected.get('total_count',0)}</div>
                </div>
                <div>
                  <div style="font-family:'DM Mono',monospace;font-size:0.62rem;
                              color:#4a5a78;letter-spacing:1.5px;margin-bottom:4px;">SEVERITY</div>
                  {severity_badge(sev)}
                </div>
                <div>
                  <div style="font-family:'DM Mono',monospace;font-size:0.62rem;
                              color:#4a5a78;letter-spacing:1.5px;">TYPE</div>
                  <div style="font-family:'DM Mono',monospace;font-size:0.85rem;
                              color:#8899b4;">{selected.get('session_type','').upper()}</div>
                </div>
                <div>
                  <div style="font-family:'DM Mono',monospace;font-size:0.62rem;
                              color:#4a5a78;letter-spacing:1.5px;">FILE</div>
                  <div style="font-family:'DM Mono',monospace;font-size:0.78rem;
                              color:#8899b4;">{selected.get('source_filename') or '—'}</div>
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)

            d1, d2 = st.columns(2)
            with d1:
                if dets:
                    st.download_button(
                        "⬇  DETECTIONS CSV",
                        export_detections_csv(dets),
                        f"session_{selected_id}_detections.csv",
                        "text/csv",
                        use_container_width=True,
                    )
            with d2:
                st.download_button(
                    "⬇  SESSION PDF REPORT",
                    export_session_pdf(selected, dets),
                    f"session_{selected_id}_report.pdf",
                    "application/pdf",
                    use_container_width=True,
                )
