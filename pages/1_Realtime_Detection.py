import sys
import queue
from pathlib import Path
from typing import List, NamedTuple

import av
import cv2
import numpy as np
import streamlit as st
from streamlit_webrtc import WebRtcMode, webrtc_streamer

HERE = Path(__file__).parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))

from ultralytics import YOLO
from sample_utils.download import download_file
from sample_utils.get_STUNServer import getSTUNServer
from database.db import init_db, create_session, save_detections, upsert_damage_summary
from utils.severity import score_single_detection, score_session, severity_emoji
from utils.styles import inject_global_css, page_header, severity_badge

st.set_page_config(
    page_title="Realtime Detection — RDD",
    page_icon="📷",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_global_css()
init_db()

MODEL_URL = "https://github.com/oracl4/RoadDamageDetection/raw/main/models/YOLOv8_Small_RDD.pt"
MODEL_LOCAL_PATH = ROOT / "models" / "YOLOv8_Small_RDD.pt"
download_file(MODEL_URL, MODEL_LOCAL_PATH, expected_size=89569358)

cache_key = "yolov8smallrdd"
if cache_key in st.session_state:
    net = st.session_state[cache_key]
else:
    net = YOLO(MODEL_LOCAL_PATH)
    st.session_state[cache_key] = net

CLASSES      = ["Longitudinal Crack", "Transverse Crack", "Alligator Crack", "Potholes"]
CLASS_COLORS = ["#3b82f6", "#22c55e", "#f59e0b", "#ef4444"]

STUN_STRING = "stun:" + str(getSTUNServer())
STUN_SERVER = [{"urls": [STUN_STRING]}]

class Detection(NamedTuple):
    class_id: int
    label: str
    score: float
    box: np.ndarray
    severity: str

result_queue: "queue.Queue[List[Detection]]" = queue.Queue()

# ── Header ────────────────────────────────────────────────────────
page_header("REALTIME DETECTION", "Live Webcam · WebRTC · On-site Monitoring")

left, right = st.columns([1, 2], gap="large")

with left:
    st.markdown("""
    <div style="font-family:'DM Mono',monospace;font-size:0.68rem;letter-spacing:2px;
                color:#f59e0b;text-transform:uppercase;margin-bottom:0.8rem;">
    ◈ Stream Configuration
    </div>
    """, unsafe_allow_html=True)

    score_threshold = st.slider(
        "Confidence Threshold", min_value=0.0, max_value=1.0, value=0.5, step=0.05
    )
    st.markdown("""
    <div style="font-family:'DM Mono',monospace;font-size:0.67rem;color:#4a5a78;
                margin-top:-0.5rem;margin-bottom:1rem;">
    Adjust before starting the stream
    </div>
    """, unsafe_allow_html=True)

    with st.expander("◈ GPS / LOCATION TAGGING"):
        loc_name  = st.text_input("Location Name", placeholder="e.g. NH-58 KM 34, Rishikesh")
        c1, c2    = st.columns(2)
        with c1:
            latitude  = st.number_input("Latitude",  value=0.0, format="%.6f", step=0.000001)
        with c2:
            longitude = st.number_input("Longitude", value=0.0, format="%.6f", step=0.000001)
        use_location = st.checkbox("Attach location to session")

    st.markdown("<hr>", unsafe_allow_html=True)

    st.markdown("""
    <div style="font-family:'DM Mono',monospace;font-size:0.68rem;letter-spacing:2px;
                color:#f59e0b;text-transform:uppercase;margin-bottom:0.8rem;">
    ◈ Save Session
    </div>
    <div style="font-family:'Barlow',sans-serif;font-size:0.85rem;color:#8899b4;
                margin-bottom:1rem;line-height:1.6;">
    Stop the stream first, then save all queued detections to the database.
    </div>
    """, unsafe_allow_html=True)

    if st.button("◈  SAVE SESSION TO DATABASE", type="primary", use_container_width=True):
        all_dets = []
        try:
            while True:
                batch = result_queue.get_nowait()
                all_dets.extend(batch)
        except queue.Empty:
            pass

        counts = {0: 0, 1: 0, 2: 0, 3: 0}
        for d in all_dets:
            counts[d.class_id] += 1

        overall_sev = score_session(counts, "realtime")
        lat = latitude  if use_location else None
        lng = longitude if use_location else None
        lnm = loc_name  if use_location else None

        session_id = create_session(
            session_type="realtime",
            source_filename="webcam",
            latitude=lat, longitude=lng, location_name=lnm,
        )
        det_dicts = [
            {"class_id": d.class_id, "class_name": d.label,
             "confidence": d.score, "box": list(d.box), "severity": d.severity}
            for d in all_dets
        ]
        save_detections(session_id, det_dicts)
        upsert_damage_summary(session_id, counts, overall_sev)

        st.success(
            f"Session #{session_id} saved\n"
            f"{len(all_dets)} detections · {severity_emoji(overall_sev)} {overall_sev}"
        )
        if all_dets:
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Total",    len(all_dets))
            k2.metric("Potholes", counts[3])
            k3.metric("Alligator", counts[2])
            k4.metric("Severity", f"{severity_emoji(overall_sev)} {overall_sev}")

    st.markdown("<hr>", unsafe_allow_html=True)

    # Class reference
    st.markdown("""
    <div style="font-family:'DM Mono',monospace;font-size:0.65rem;letter-spacing:1.5px;
                color:#4a5a78;text-transform:uppercase;margin-bottom:0.6rem;">
    Detection Classes
    </div>
    """, unsafe_allow_html=True)
    for cls, color in zip(CLASSES, CLASS_COLORS):
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
          <div style="width:8px;height:8px;border-radius:50%;background:{color};flex-shrink:0;"></div>
          <span style="font-family:'DM Mono',monospace;font-size:0.72rem;color:#8899b4;">{cls}</span>
        </div>
        """, unsafe_allow_html=True)

with right:
    # ── WebRTC stream ──────────────────────────────────────────────
    def video_frame_callback(frame: av.VideoFrame) -> av.VideoFrame:
        image        = frame.to_ndarray(format="bgr24")
        h_ori, w_ori = image.shape[:2]
        img_resized  = cv2.resize(image, (640, 640), interpolation=cv2.INTER_AREA)
        results      = net.predict(img_resized, conf=score_threshold)

        for result in results:
            dets = []
            for _box in result.boxes.cpu().numpy():
                cid  = int(_box.cls)
                conf = float(_box.conf)
                sev  = score_single_detection(cid, conf)
                dets.append(Detection(
                    class_id=cid, label=CLASSES[cid],
                    score=conf, box=_box.xyxy[0].astype(int), severity=sev,
                ))
            result_queue.put(dets)

        annotated = results[0].plot()
        out = cv2.resize(annotated, (w_ori, h_ori), interpolation=cv2.INTER_AREA)
        return av.VideoFrame.from_ndarray(out, format="bgr24")

    st.markdown("""
    <div style="font-family:'DM Mono',monospace;font-size:0.68rem;letter-spacing:2px;
                color:#f59e0b;text-transform:uppercase;margin-bottom:0.6rem;">
    ◈ Live Feed
    </div>
    """, unsafe_allow_html=True)

    # Styled container for the WebRTC widget
    st.markdown("""
    <div style="background:var(--bg-raised);border:1px solid var(--border);
                border-radius:14px;padding:1rem;margin-bottom:1rem;">
    """, unsafe_allow_html=True)

    webrtc_ctx = webrtc_streamer(
        key="road-damage-detection",
        mode=WebRtcMode.SENDRECV,
        rtc_configuration={"iceServers": STUN_SERVER},
        video_frame_callback=video_frame_callback,
        media_stream_constraints={
            "video": {"width": {"ideal": 1280, "min": 800}},
            "audio": False,
        },
        async_processing=True,
    )

    st.markdown("</div>", unsafe_allow_html=True)

    # Status indicator
    if webrtc_ctx.state.playing:
        st.markdown("""
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:1rem;">
          <div style="width:8px;height:8px;border-radius:50%;background:#10b981;
                      box-shadow:0 0 8px #10b981;animation:pulse 1.5s infinite;"></div>
          <span style="font-family:'DM Mono',monospace;font-size:0.75rem;color:#34d399;
                       letter-spacing:1px;">STREAM ACTIVE</span>
        </div>
        <style>@keyframes pulse{0%,100%{opacity:1;}50%{opacity:0.4;}}</style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:1rem;">
          <div style="width:8px;height:8px;border-radius:50%;background:#4a5a78;"></div>
          <span style="font-family:'DM Mono',monospace;font-size:0.75rem;color:#4a5a78;
                       letter-spacing:1px;">STREAM OFFLINE — Click START to begin</span>
        </div>
        """, unsafe_allow_html=True)

    # Live predictions table
    if st.checkbox("Show Live Predictions Table"):
        if webrtc_ctx.state.playing:
            placeholder = st.empty()
            while True:
                result = result_queue.get()
                if result:
                    rows_html = ""
                    for d in result:
                        color = CLASS_COLORS[d.class_id]
                        badge = severity_badge(d.severity)
                        rows_html += f"""
                        <tr style="border-bottom:1px solid var(--border);">
                          <td style="padding:8px 12px;font-family:'Barlow',sans-serif;
                                      font-size:0.85rem;color:{color};">{d.label}</td>
                          <td style="padding:8px 12px;font-family:'DM Mono',monospace;
                                      font-size:0.75rem;color:#8899b4;">{d.score:.1%}</td>
                          <td style="padding:8px 12px;">{badge}</td>
                        </tr>
                        """
                    placeholder.markdown(f"""
                    <div style="background:var(--bg-surface);border:1px solid var(--border);
                                border-radius:10px;overflow:hidden;">
                      <table style="width:100%;border-collapse:collapse;">
                        <thead>
                          <tr style="background:var(--bg-raised);">
                            <th style="padding:8px 12px;text-align:left;font-family:'DM Mono',monospace;
                                        font-size:0.62rem;letter-spacing:1.5px;color:#4a5a78;">CLASS</th>
                            <th style="padding:8px 12px;text-align:left;font-family:'DM Mono',monospace;
                                        font-size:0.62rem;letter-spacing:1.5px;color:#4a5a78;">CONF</th>
                            <th style="padding:8px 12px;text-align:left;font-family:'DM Mono',monospace;
                                        font-size:0.62rem;letter-spacing:1.5px;color:#4a5a78;">SEVERITY</th>
                          </tr>
                        </thead>
                        <tbody>{rows_html}</tbody>
                      </table>
                    </div>
                    """, unsafe_allow_html=True)
