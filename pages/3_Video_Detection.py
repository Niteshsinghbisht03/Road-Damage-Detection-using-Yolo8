import os
import sys
import time
from pathlib import Path
from typing import List, NamedTuple

import cv2
import numpy as np
import streamlit as st

HERE = Path(__file__).parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))

from ultralytics import YOLO
from sample_utils.download import download_file
from database.db import init_db, create_session, save_detections, upsert_damage_summary
from utils.severity import score_single_detection, score_session, severity_emoji
from utils.styles import inject_global_css, page_header, severity_badge, confidence_bar

st.set_page_config(
    page_title="Video Detection — RDD",
    page_icon="🎬",
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

os.makedirs("./temp", exist_ok=True)
temp_file_input = "./temp/video_input.mp4"
temp_file_infer = "./temp/video_infer.mp4"

if "processing_button" in st.session_state and st.session_state.processing_button:
    st.session_state.runningInference = True
else:
    st.session_state.runningInference = False

class Detection(NamedTuple):
    class_id: int
    label: str
    score: float
    box: np.ndarray
    severity: str

def write_bytesio_to_file(filename, bytesio):
    with open(filename, "wb") as f:
        f.write(bytesio.getbuffer())

def processVideo(video_file, score_threshold, session_id):
    write_bytesio_to_file(temp_file_input, video_file)
    cap = cv2.VideoCapture(temp_file_input)

    if not cap.isOpened():
        st.error("Error opening the video file.")
        return

    W           = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    H           = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps         = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration    = frame_count / fps
    dm, ds      = int(duration // 60), int(duration % 60)

    # Video info strip
    st.markdown(f"""
    <div style="display:flex;gap:24px;flex-wrap:wrap;margin-bottom:1.2rem;">
      <div style="background:var(--bg-raised);border:1px solid var(--border);
                  border-radius:8px;padding:8px 16px;">
        <div style="font-family:'DM Mono',monospace;font-size:0.62rem;color:#4a5a78;
                    letter-spacing:1.5px;text-transform:uppercase;">Duration</div>
        <div style="font-family:'Bebas Neue',sans-serif;font-size:1.3rem;
                    letter-spacing:2px;color:#e8edf5;">{dm:02d}:{ds:02d}</div>
      </div>
      <div style="background:var(--bg-raised);border:1px solid var(--border);
                  border-radius:8px;padding:8px 16px;">
        <div style="font-family:'DM Mono',monospace;font-size:0.62rem;color:#4a5a78;
                    letter-spacing:1.5px;text-transform:uppercase;">Resolution</div>
        <div style="font-family:'Bebas Neue',sans-serif;font-size:1.3rem;
                    letter-spacing:2px;color:#e8edf5;">{W}×{H}</div>
      </div>
      <div style="background:var(--bg-raised);border:1px solid var(--border);
                  border-radius:8px;padding:8px 16px;">
        <div style="font-family:'DM Mono',monospace;font-size:0.62rem;color:#4a5a78;
                    letter-spacing:1.5px;text-transform:uppercase;">FPS</div>
        <div style="font-family:'Bebas Neue',sans-serif;font-size:1.3rem;
                    letter-spacing:2px;color:#e8edf5;">{fps:.1f}</div>
      </div>
      <div style="background:var(--bg-raised);border:1px solid var(--border);
                  border-radius:8px;padding:8px 16px;">
        <div style="font-family:'DM Mono',monospace;font-size:0.62rem;color:#4a5a78;
                    letter-spacing:1.5px;text-transform:uppercase;">Total Frames</div>
        <div style="font-family:'Bebas Neue',sans-serif;font-size:1.3rem;
                    letter-spacing:2px;color:#e8edf5;">{frame_count:,}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Live view + progress
    progress_label = st.empty()
    progress_bar   = st.progress(0)
    live_frame     = st.empty()
    live_stats     = st.empty()

    fourcc    = cv2.VideoWriter_fourcc(*"mp4v")
    cv2writer = cv2.VideoWriter(temp_file_infer, fourcc, fps, (W, H))

    all_counts = {0: 0, 1: 0, 2: 0, 3: 0}
    frame_idx  = 0
    # Sample every N frames for both counting AND saving — avoids the same
    # damage being counted dozens of times while it stays in the camera view.
    SAMPLE_EVERY_N = max(1, int(fps))   # once per second
    start_time   = time.time()

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame_rgb   = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img_resized = cv2.resize(frame_rgb, (640, 640), interpolation=cv2.INTER_AREA)
        results     = net.predict(img_resized, conf=score_threshold)

        frame_dets = []
        for result in results:
            for _box in result.boxes.cpu().numpy():
                cid  = int(_box.cls)
                conf = float(_box.conf)
                sev  = score_single_detection(cid, conf)
                frame_dets.append({
                    "class_id": cid, "class_name": CLASSES[cid],
                    "confidence": conf, "box": list(_box.xyxy[0].astype(int)), "severity": sev,
                })

        # Only count and save on sampled frames to avoid inflating counts
        if frame_idx % SAMPLE_EVERY_N == 0:
            for d in frame_dets:
                all_counts[d["class_id"]] += 1
            if frame_dets:
                save_detections(session_id, frame_dets, frame_index=frame_idx)

        annotated = results[0].plot()
        out_frame = cv2.resize(annotated, (W, H), interpolation=cv2.INTER_AREA)
        cv2writer.write(cv2.cvtColor(out_frame, cv2.COLOR_RGB2BGR))
        live_frame.image(out_frame, width="stretch")

        # Progress with ETA
        pct      = frame_idx / frame_count
        elapsed  = time.time() - start_time
        eta      = (elapsed / max(frame_idx, 1)) * (frame_count - frame_idx)
        eta_str  = f"{int(eta//60):02d}:{int(eta%60):02d}"
        total    = sum(all_counts.values())

        progress_label.markdown(f"""
        <div style="display:flex;justify-content:space-between;align-items:center;
                    margin-bottom:4px;">
          <div style="font-family:'DM Mono',monospace;font-size:0.72rem;color:#8899b4;">
            ◈ PROCESSING FRAME {frame_idx:,} / {frame_count:,}
          </div>
          <div style="display:flex;gap:16px;">
            <span style="font-family:'DM Mono',monospace;font-size:0.7rem;color:#f59e0b;">
              {pct:.1%}
            </span>
            <span style="font-family:'DM Mono',monospace;font-size:0.7rem;color:#4a5a78;">
              ETA {eta_str}
            </span>
          </div>
        </div>
        """, unsafe_allow_html=True)
        progress_bar.progress(min(pct, 1.0))

        live_stats.markdown(f"""
        <div style="display:flex;gap:16px;flex-wrap:wrap;margin-top:8px;">
          <span style="font-family:'DM Mono',monospace;font-size:0.72rem;color:#3b82f6;">
            Long: {all_counts[0]}
          </span>
          <span style="font-family:'DM Mono',monospace;font-size:0.72rem;color:#22c55e;">
            Trans: {all_counts[1]}
          </span>
          <span style="font-family:'DM Mono',monospace;font-size:0.72rem;color:#f59e0b;">
            Allig: {all_counts[2]}
          </span>
          <span style="font-family:'DM Mono',monospace;font-size:0.72rem;color:#ef4444;">
            Potholes: {all_counts[3]}
          </span>
          <span style="font-family:'DM Mono',monospace;font-size:0.72rem;color:#8899b4;">
            Total: {total}
          </span>
        </div>
        """, unsafe_allow_html=True)

        frame_idx += 1

    cap.release()
    cv2writer.release()
    progress_bar.empty()
    progress_label.empty()

    # Final summary
    overall_sev = score_session(all_counts, "video")
    upsert_damage_summary(session_id, all_counts, overall_sev)

    st.success(f"✓ Processing complete — Session #{session_id} · {severity_emoji(overall_sev)} {overall_sev} severity")

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Total Detections", sum(all_counts.values()))
    k2.metric("Potholes",         all_counts[3])
    k3.metric("Alligator",        all_counts[2])
    k4.metric("Longitudinal",     all_counts[0])
    k5.metric("Severity",         f"{severity_emoji(overall_sev)} {overall_sev}")

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
    dl_col, rst_col = st.columns(2)
    with dl_col:
        with open(temp_file_infer, "rb") as f:
            st.download_button(
                label="⬇  DOWNLOAD ANNOTATED VIDEO",
                data=f,
                file_name="RDD_Prediction.mp4",
                mime="video/mp4",
                use_container_width=True,
            )
    with rst_col:
        if st.button("↺  RESTART", use_container_width=True, type="primary"):
            st.rerun()

# ── Page layout ───────────────────────────────────────────────────
page_header("VIDEO DETECTION", "Upload · Process · Download · Log")

left, right = st.columns([1, 2], gap="large")

with left:
    st.markdown("""
    <div style="font-family:'DM Mono',monospace;font-size:0.68rem;letter-spacing:2px;
                color:#f59e0b;text-transform:uppercase;margin-bottom:0.8rem;">
    ◈ Input Configuration
    </div>
    """, unsafe_allow_html=True)

    video_file = st.file_uploader(
        "DROP VIDEO HERE", type=["mp4"],
        disabled=st.session_state.runningInference,
        help="MP4 format · max 1 GB"
    )
    st.markdown("""
    <div style="font-family:'DM Mono',monospace;font-size:0.67rem;color:#4a5a78;margin-top:-0.4rem;">
    1 GB limit · .mp4 only · cut large files before uploading
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

    score_threshold = st.slider(
        "Confidence Threshold", min_value=0.0, max_value=1.0, value=0.5, step=0.05,
        disabled=st.session_state.runningInference,
    )

    with st.expander("◈ GPS / LOCATION TAGGING"):
        loc_name  = st.text_input("Location Name", placeholder="e.g. Ring Road, Delhi")
        c1, c2    = st.columns(2)
        with c1:
            latitude  = st.number_input("Latitude",  value=0.0, format="%.6f", step=0.000001)
        with c2:
            longitude = st.number_input("Longitude", value=0.0, format="%.6f", step=0.000001)
        use_location = st.checkbox("Attach location to this session")

    if video_file is not None:
        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
        process = st.button(
            "▶  PROCESS VIDEO",
            use_container_width=True,
            disabled=st.session_state.runningInference,
            type="primary",
            key="processing_button",
        )

with right:
    if video_file is None:
        st.markdown("""
        <div style="
          height:460px;display:flex;flex-direction:column;
          align-items:center;justify-content:center;
          background:var(--bg-raised);border:1px dashed var(--border-glow);
          border-radius:14px;gap:1rem;
        ">
          <div style="font-size:3.5rem;opacity:0.3;">🎬</div>
          <div style="font-family:'Bebas Neue',sans-serif;font-size:1.4rem;
                      letter-spacing:3px;color:#4a5a78;">AWAITING VIDEO</div>
          <div style="font-family:'DM Mono',monospace;font-size:0.72rem;color:#4a5a78;">
            Upload an MP4 file to begin processing
          </div>
        </div>
        """, unsafe_allow_html=True)
    elif "processing_button" in st.session_state and st.session_state.processing_button:
        lat = latitude  if use_location else None
        lng = longitude if use_location else None
        lnm = loc_name  if use_location else None

        session_id = create_session(
            session_type="video",
            source_filename=video_file.name,
            latitude=lat, longitude=lng, location_name=lnm,
        )
        processVideo(video_file, score_threshold, session_id)
