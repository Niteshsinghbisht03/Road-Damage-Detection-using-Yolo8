import os
import sys
import logging
from pathlib import Path
from typing import NamedTuple

import cv2
import numpy as np
import streamlit as st
from PIL import Image
from io import BytesIO

HERE = Path(__file__).parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))

from ultralytics import YOLO
from sample_utils.download import download_file
from database.db import init_db, create_session, save_detections, upsert_damage_summary
from utils.severity import score_single_detection, score_session, severity_emoji
from utils.styles import inject_global_css, page_header, severity_badge, confidence_bar

st.set_page_config(
    page_title="Image Detection — RDD",
    page_icon="🖼️",
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

CLASSES = ["Longitudinal Crack", "Transverse Crack", "Alligator Crack", "Potholes"]
CLASS_COLORS = ["#3b82f6", "#22c55e", "#f59e0b", "#ef4444"]

class Detection(NamedTuple):
    class_id: int
    label: str
    score: float
    box: np.ndarray
    severity: str

# ── Header ────────────────────────────────────────────────────────
page_header("IMAGE DETECTION", "Upload · Analyze · Log · Export")

# ── Two-column layout: controls left, results right ───────────────
left, right = st.columns([1, 2], gap="large")

with left:
    st.markdown("""
    <div style="font-family:'DM Mono',monospace;font-size:0.68rem;letter-spacing:2px;
                color:#f59e0b;text-transform:uppercase;margin-bottom:0.8rem;">
    ◈ Input Configuration
    </div>
    """, unsafe_allow_html=True)

    image_file = st.file_uploader(
        "DROP IMAGE HERE", type=["png", "jpg", "jpeg"],
        help="PNG or JPG — any resolution"
    )

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

    score_threshold = st.slider(
        "Confidence Threshold", min_value=0.0, max_value=1.0, value=0.5, step=0.05
    )
    st.markdown("""
    <div style="font-family:'DM Mono',monospace;font-size:0.68rem;color:#4a5a78;
                margin-top:-0.5rem;margin-bottom:1rem;">
    ↑ Lower = more detections &nbsp;·&nbsp; Higher = fewer false positives
    </div>
    """, unsafe_allow_html=True)

    # GPS expander
    with st.expander("◈ GPS / LOCATION TAGGING"):
        st.markdown("""
        <div style="font-family:'DM Mono',monospace;font-size:0.7rem;color:#8899b4;
                    margin-bottom:0.8rem;">
        Tag this session with coordinates to appear on the damage map.
        </div>
        """, unsafe_allow_html=True)
        loc_name  = st.text_input("Location Name", placeholder="e.g. NH-58, Dehradun")
        col_lat, col_lng = st.columns(2)
        with col_lat:
            latitude  = st.number_input("Latitude",  value=0.0, format="%.6f", step=0.000001)
        with col_lng:
            longitude = st.number_input("Longitude", value=0.0, format="%.6f", step=0.000001)
        use_location = st.checkbox("Attach location to this session")

with right:
    if image_file is None:
        st.markdown("""
        <div style="
          height:420px; display:flex; flex-direction:column;
          align-items:center; justify-content:center;
          background:var(--bg-raised); border:1px dashed var(--border-glow);
          border-radius:14px; gap:1rem;
        ">
          <div style="font-size:3.5rem;opacity:0.3;">🖼️</div>
          <div style="font-family:'Bebas Neue',sans-serif;font-size:1.4rem;
                      letter-spacing:3px;color:#4a5a78;">AWAITING INPUT</div>
          <div style="font-family:'DM Mono',monospace;font-size:0.72rem;
                      color:#4a5a78;">Upload an image to begin analysis</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # ── Run inference ─────────────────────────────────────────
        image    = Image.open(image_file)
        _image   = np.array(image)
        h_ori, w_ori = _image.shape[:2]

        with st.spinner("Running YOLOv8 inference…"):
            image_resized = cv2.resize(_image, (640, 640), interpolation=cv2.INTER_AREA)
            results       = net.predict(image_resized, conf=score_threshold)

        detections = []
        counts = {0: 0, 1: 0, 2: 0, 3: 0}

        for result in results:
            for _box in result.boxes.cpu().numpy():
                cid  = int(_box.cls)
                conf = float(_box.conf)
                sev  = score_single_detection(cid, conf)
                counts[cid] += 1
                detections.append(Detection(
                    class_id=cid, label=CLASSES[cid],
                    score=conf, box=_box.xyxy[0].astype(int), severity=sev,
                ))

        overall_sev = score_session(counts, "image")
        annotated   = results[0].plot()
        _image_pred = cv2.resize(annotated, (w_ori, h_ori), interpolation=cv2.INTER_AREA)

        # ── KPI strip ─────────────────────────────────────────────
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Total Detections", len(detections))
        k2.metric("Potholes",         counts[3])
        k3.metric("Alligator Cracks", counts[2])
        k4.metric("Severity",         f"{severity_emoji(overall_sev)} {overall_sev}")

        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

        # ── Image comparison ──────────────────────────────────────
        img_col1, img_col2 = st.columns(2, gap="small")
        with img_col1:
            st.markdown("""
            <div style="font-family:'DM Mono',monospace;font-size:0.7rem;letter-spacing:2px;
                        color:#8899b4;text-transform:uppercase;margin-bottom:0.5rem;">
            ◈ Original
            </div>
            """, unsafe_allow_html=True)
            st.image(_image, width="stretch")

        with img_col2:
            st.markdown("""
            <div style="font-family:'DM Mono',monospace;font-size:0.7rem;letter-spacing:2px;
                        color:#f59e0b;text-transform:uppercase;margin-bottom:0.5rem;">
            ◈ Annotated Output
            </div>
            """, unsafe_allow_html=True)
            st.image(_image_pred, width="stretch")

            buffer = BytesIO()
            Image.fromarray(_image_pred).save(buffer, format="PNG")
            st.download_button(
                label="⬇  DOWNLOAD ANNOTATED IMAGE",
                data=buffer.getvalue(),
                file_name="RDD_Prediction.png",
                mime="image/png",
                use_container_width=True,
            )

        # ── Detection details table ───────────────────────────────
        if detections:
            st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
            st.markdown("""
            <div style="font-family:'Bebas Neue',sans-serif;font-size:1.3rem;
                        letter-spacing:3px;color:#e8edf5;margin-bottom:0.8rem;">
            DETECTION DETAILS
            </div>
            """, unsafe_allow_html=True)

            # Build HTML table
            rows_html = ""
            for i, d in enumerate(detections, 1):
                color = CLASS_COLORS[d.class_id]
                badge = severity_badge(d.severity)
                bar   = confidence_bar(d.score, color)
                bbox  = f"[{d.box[0]},{d.box[1]}] → [{d.box[2]},{d.box[3]}]"
                rows_html += (
                    f'<tr style="border-bottom:1px solid var(--border);">'
                    f'<td style="padding:10px 12px;font-family:\'DM Mono\',monospace;font-size:0.72rem;color:#4a5a78;">#{i:02d}</td>'
                    f'<td style="padding:10px 12px;font-family:\'Barlow\',sans-serif;font-size:0.88rem;color:{color};font-weight:500;">{d.label}</td>'
                    f'<td style="padding:10px 12px;min-width:120px;">{bar}</td>'
                    f'<td style="padding:10px 12px;">{badge}</td>'
                    f'<td style="padding:10px 12px;font-family:\'DM Mono\',monospace;font-size:0.68rem;color:#4a5a78;">{bbox}</td>'
                    f'</tr>'
                )

            table_html = (
                '<div style="background:var(--bg-surface);border:1px solid var(--border);border-radius:12px;overflow:hidden;">'
                '<table style="width:100%;border-collapse:collapse;">'
                '<thead><tr style="background:var(--bg-raised);border-bottom:1px solid var(--border);">'
                '<th style="padding:10px 12px;text-align:left;font-family:\'DM Mono\',monospace;font-size:0.65rem;letter-spacing:1.5px;color:#4a5a78;">#</th>'
                '<th style="padding:10px 12px;text-align:left;font-family:\'DM Mono\',monospace;font-size:0.65rem;letter-spacing:1.5px;color:#4a5a78;">CLASS</th>'
                '<th style="padding:10px 12px;text-align:left;font-family:\'DM Mono\',monospace;font-size:0.65rem;letter-spacing:1.5px;color:#4a5a78;">CONFIDENCE</th>'
                '<th style="padding:10px 12px;text-align:left;font-family:\'DM Mono\',monospace;font-size:0.65rem;letter-spacing:1.5px;color:#4a5a78;">SEVERITY</th>'
                '<th style="padding:10px 12px;text-align:left;font-family:\'DM Mono\',monospace;font-size:0.65rem;letter-spacing:1.5px;color:#4a5a78;">BOUNDING BOX</th>'
                '</tr></thead>'
                f'<tbody>{rows_html}</tbody>'
                '</table></div>'
            )
            st.markdown(table_html, unsafe_allow_html=True)

        # ── Save to DB ────────────────────────────────────────────
        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
        if st.button("◈  SAVE SESSION TO DATABASE", type="primary", use_container_width=True):
            lat = latitude  if use_location else None
            lng = longitude if use_location else None
            lnm = loc_name  if use_location else None

            session_id = create_session(
                session_type="image",
                source_filename=image_file.name,
                latitude=lat, longitude=lng, location_name=lnm,
            )
            det_dicts = [
                {"class_id": d.class_id, "class_name": d.label,
                 "confidence": d.score, "box": list(d.box), "severity": d.severity}
                for d in detections
            ]
            save_detections(session_id, det_dicts)
            upsert_damage_summary(session_id, counts, overall_sev)

            st.success(
                f"Session #{session_id} saved — {len(detections)} detections "
                f"· {severity_emoji(overall_sev)} {overall_sev} severity"
            )
