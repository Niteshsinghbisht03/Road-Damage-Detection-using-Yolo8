"""
Export utilities: CSV and PDF report generation for detection sessions.
"""
import csv
import io
from datetime import datetime


# ── CSV Export ────────────────────────────────────────────────────

def export_sessions_csv(sessions: list) -> bytes:
    """Export session list to CSV bytes."""
    output = io.StringIO()
    fieldnames = [
        "id", "session_type", "created_at", "source_filename",
        "location_name", "latitude", "longitude",
        "total_count", "overall_severity",
        "longitudinal_count", "transverse_count",
        "alligator_count", "pothole_count",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for s in sessions:
        writer.writerow({k: s.get(k, "") for k in fieldnames})
    return output.getvalue().encode("utf-8")


def export_detections_csv(detections: list) -> bytes:
    """Export raw detections list to CSV bytes."""
    output = io.StringIO()
    fieldnames = [
        "id", "session_id", "frame_index", "class_name",
        "confidence", "severity", "box_x1", "box_y1",
        "box_x2", "box_y2", "detected_at",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for d in detections:
        writer.writerow({k: d.get(k, "") for k in fieldnames})
    return output.getvalue().encode("utf-8")


# ── PDF Export (pure-Python, no external deps beyond stdlib) ──────

def export_session_pdf(session: dict, detections: list) -> bytes:
    """
    Generate a simple PDF report for one session.
    Uses only built-in string formatting — no reportlab required.
    Returns raw PDF bytes.
    """
    lines = []

    def add(text=""):
        lines.append(text)

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    add("ROAD DAMAGE DETECTION REPORT")
    add("=" * 60)
    add(f"Generated : {now}")
    add(f"Session ID: {session.get('id', 'N/A')}")
    add(f"Type      : {session.get('session_type', 'N/A').upper()}")
    add(f"Source    : {session.get('source_filename', 'N/A')}")
    add(f"Date/Time : {session.get('created_at', 'N/A')}")
    add()
    add("LOCATION")
    add("-" * 40)
    add(f"  Name     : {session.get('location_name') or 'Not specified'}")
    add(f"  Latitude : {session.get('latitude') or 'N/A'}")
    add(f"  Longitude: {session.get('longitude') or 'N/A'}")
    add()
    add("DAMAGE SUMMARY")
    add("-" * 40)
    add(f"  Total Detections  : {session.get('total_count', 0)}")
    add(f"  Overall Severity  : {session.get('overall_severity', 'None')}")
    add(f"  Longitudinal Crack: {session.get('longitudinal_count', 0)}")
    add(f"  Transverse Crack  : {session.get('transverse_count', 0)}")
    add(f"  Alligator Crack   : {session.get('alligator_count', 0)}")
    add(f"  Potholes          : {session.get('pothole_count', 0)}")
    add()

    if detections:
        add("DETECTION DETAILS")
        add("-" * 40)
        add(f"  {'#':<4} {'Class':<22} {'Confidence':>10}  {'Severity':<10}")
        add(f"  {'-'*4} {'-'*22} {'-'*10}  {'-'*10}")
        for i, d in enumerate(detections, 1):
            add(f"  {i:<4} {d.get('class_name',''):<22} "
                f"{d.get('confidence', 0):>10.2%}  {d.get('severity',''):<10}")
    add()
    add("=" * 60)
    add("Road Damage Detection Application — Powered by YOLOv8")

    # Encode as plain-text PDF (simple but universally readable)
    text_content = "\n".join(lines)

    # Build a minimal valid PDF containing the text
    pdf = _make_text_pdf(text_content)
    return pdf


def _make_text_pdf(text: str) -> bytes:
    """Produce a bare-bones but valid PDF with monospaced text."""
    # Escape special PDF characters
    safe = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    # Split into lines for the PDF stream
    text_lines = safe.split("\n")
    font_size = 9
    line_height = font_size * 1.4
    margin = 40
    page_height = 841  # A4
    page_width = 595

    streams = []
    pages = []
    y = page_height - margin

    current_stream_lines = [
        f"BT",
        f"/F1 {font_size} Tf",
        f"{margin} {y} Td",
        f"{line_height} TL",
    ]

    for line in text_lines:
        if y < margin + line_height:
            # New page
            current_stream_lines.append("ET")
            streams.append("\n".join(current_stream_lines))
            pages.append(streams[-1])
            y = page_height - margin
            current_stream_lines = [
                "BT",
                f"/F1 {font_size} Tf",
                f"{margin} {y} Td",
                f"{line_height} TL",
            ]
        current_stream_lines.append(f"({line}) '")
        y -= line_height

    current_stream_lines.append("ET")
    streams.append("\n".join(current_stream_lines))
    pages.append(streams[-1])

    # Build PDF objects
    obj_count = 0
    objects = {}

    def new_obj(content):
        nonlocal obj_count
        obj_count += 1
        objects[obj_count] = content
        return obj_count

    # Catalog, pages will be filled in
    catalog_id = new_obj(None)
    pages_id = new_obj(None)
    font_id = new_obj(
        "<< /Type /Font /Subtype /Type1 /BaseFont /Courier /Encoding /WinAnsiEncoding >>"
    )

    page_ids = []
    for stream_content in pages:
        encoded = stream_content.encode("latin-1", errors="replace")
        stream_id = new_obj(
            f"<< /Length {len(encoded)} >>\nstream\n"
            + stream_content
            + "\nendstream"
        )
        page_id = new_obj(
            f"<< /Type /Page /Parent {pages_id} 0 R "
            f"/MediaBox [0 0 {page_width} {page_height}] "
            f"/Contents {stream_id} 0 R "
            f"/Resources << /Font << /F1 {font_id} 0 R >> >> >>"
        )
        page_ids.append(page_id)

    kids = " ".join(f"{pid} 0 R" for pid in page_ids)
    objects[pages_id] = (
        f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>"
    )
    objects[catalog_id] = (
        f"<< /Type /Catalog /Pages {pages_id} 0 R >>"
    )

    # Serialize
    buf = io.BytesIO()
    buf.write(b"%PDF-1.4\n")
    offsets = {}
    for oid in range(1, obj_count + 1):
        offsets[oid] = buf.tell()
        content = objects[oid]
        buf.write(f"{oid} 0 obj\n{content}\nendobj\n".encode("latin-1", errors="replace"))

    xref_offset = buf.tell()
    buf.write(f"xref\n0 {obj_count + 1}\n".encode())
    buf.write(b"0000000000 65535 f \n")
    for oid in range(1, obj_count + 1):
        buf.write(f"{offsets[oid]:010d} 00000 n \n".encode())

    buf.write(
        f"trailer\n<< /Size {obj_count + 1} /Root {catalog_id} 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n".encode()
    )
    return buf.getvalue()


def export_all_sessions_pdf(sessions: list, stats: dict) -> bytes:
    """Generate a summary PDF for all sessions."""
    lines = []

    def add(text=""):
        lines.append(text)

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    add("ROAD DAMAGE DETECTION — FULL REPORT")
    add("=" * 60)
    add(f"Generated: {now}")
    add()
    add("OVERALL STATISTICS")
    add("-" * 40)
    add(f"  Total Sessions   : {stats.get('total_sessions', 0)}")
    add(f"  Total Detections : {stats.get('total_detections', 0)}")
    add(f"  Potholes         : {stats.get('pothole_count', 0)}")
    add(f"  Alligator Cracks : {stats.get('alligator_count', 0)}")
    add(f"  Longitudinal     : {stats.get('longitudinal_count', 0)}")
    add(f"  Transverse       : {stats.get('transverse_count', 0)}")
    add()
    add("SESSION LOG")
    add("-" * 60)
    add(f"  {'ID':<5} {'Date':<12} {'Type':<10} {'File':<20} {'Dmg':>4}  {'Severity'}")
    add(f"  {'-'*5} {'-'*12} {'-'*10} {'-'*20} {'-'*4}  {'-'*10}")
    for s in sessions:
        date = (s.get("created_at") or "")[:10]
        fname = (s.get("source_filename") or "—")[:18]
        add(f"  {s.get('id',''):<5} {date:<12} {s.get('session_type',''):<10} "
            f"{fname:<20} {s.get('total_count', 0):>4}  {s.get('overall_severity', 'None')}")
    add()
    add("=" * 60)
    add("Road Damage Detection Application — Powered by YOLOv8")

    return _make_text_pdf("\n".join(lines))
