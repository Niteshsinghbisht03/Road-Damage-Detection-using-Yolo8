import sqlite3
import os
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "rdd.db"

def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize all database tables."""
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_type TEXT NOT NULL,
            created_at TEXT NOT NULL,
            source_filename TEXT,
            latitude REAL,
            longitude REAL,
            location_name TEXT,
            total_frames INTEGER DEFAULT 1,
            notes TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS detections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            frame_index INTEGER DEFAULT 0,
            class_id INTEGER NOT NULL,
            class_name TEXT NOT NULL,
            confidence REAL NOT NULL,
            box_x1 INTEGER, box_y1 INTEGER,
            box_x2 INTEGER, box_y2 INTEGER,
            severity TEXT NOT NULL,
            detected_at TEXT NOT NULL,
            annotated_image_path TEXT,
            FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS damage_summary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL UNIQUE,
            longitudinal_count INTEGER DEFAULT 0,
            transverse_count INTEGER DEFAULT 0,
            alligator_count INTEGER DEFAULT 0,
            pothole_count INTEGER DEFAULT 0,
            total_count INTEGER DEFAULT 0,
            overall_severity TEXT DEFAULT 'None',
            FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()

# ── Session helpers ───────────────────────────────────────────────

def create_session(session_type, source_filename=None, latitude=None,
                   longitude=None, location_name=None, total_frames=1, notes=None):
    conn = get_connection()
    c = conn.cursor()
    now = datetime.now().isoformat()
    c.execute("""
        INSERT INTO sessions
          (session_type, created_at, source_filename, latitude, longitude,
           location_name, total_frames, notes)
        VALUES (?,?,?,?,?,?,?,?)
    """, (session_type, now, source_filename, latitude, longitude,
          location_name, total_frames, notes))
    conn.commit()
    session_id = c.lastrowid
    conn.close()
    return session_id

def get_all_sessions(limit=200):
    conn = get_connection()
    rows = conn.execute("""
        SELECT s.*, ds.total_count, ds.overall_severity,
               ds.longitudinal_count, ds.transverse_count,
               ds.alligator_count, ds.pothole_count
        FROM sessions s
        LEFT JOIN damage_summary ds ON ds.session_id = s.id
        ORDER BY s.created_at DESC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_session_by_id(session_id):
    conn = get_connection()
    row = conn.execute("""
        SELECT s.*, ds.total_count, ds.overall_severity,
               ds.longitudinal_count, ds.transverse_count,
               ds.alligator_count, ds.pothole_count
        FROM sessions s
        LEFT JOIN damage_summary ds ON ds.session_id = s.id
        WHERE s.id = ?
    """, (session_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def delete_session(session_id):
    conn = get_connection()
    conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()

# ── Detection helpers ─────────────────────────────────────────────

def save_detections(session_id, detections_list, annotated_image_path=None, frame_index=0):
    conn = get_connection()
    c = conn.cursor()
    now = datetime.now().isoformat()
    for det in detections_list:
        box = det.get("box", [None, None, None, None])
        c.execute("""
            INSERT INTO detections
              (session_id, frame_index, class_id, class_name, confidence,
               box_x1, box_y1, box_x2, box_y2, severity, detected_at, annotated_image_path)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """, (session_id, frame_index,
              det["class_id"], det["class_name"], det["confidence"],
              int(box[0]) if box[0] is not None else None,
              int(box[1]) if box[1] is not None else None,
              int(box[2]) if box[2] is not None else None,
              int(box[3]) if box[3] is not None else None,
              det["severity"], now, annotated_image_path))
    conn.commit()
    conn.close()

def get_detections_for_session(session_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM detections WHERE session_id = ? ORDER BY detected_at",
        (session_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ── Summary helpers ───────────────────────────────────────────────

def upsert_damage_summary(session_id, counts: dict, overall_severity: str):
    """counts: {0: n, 1: n, 2: n, 3: n}  (class_id -> count)"""
    conn = get_connection()
    total = sum(counts.values())
    conn.execute("""
        INSERT INTO damage_summary
          (session_id, longitudinal_count, transverse_count,
           alligator_count, pothole_count, total_count, overall_severity)
        VALUES (?,?,?,?,?,?,?)
        ON CONFLICT(session_id) DO UPDATE SET
          longitudinal_count=excluded.longitudinal_count,
          transverse_count=excluded.transverse_count,
          alligator_count=excluded.alligator_count,
          pothole_count=excluded.pothole_count,
          total_count=excluded.total_count,
          overall_severity=excluded.overall_severity
    """, (session_id, counts.get(0, 0), counts.get(1, 0),
          counts.get(2, 0), counts.get(3, 0), total, overall_severity))
    conn.commit()
    conn.close()

# ── Analytics helpers ─────────────────────────────────────────────

def get_dashboard_stats():
    conn = get_connection()
    stats = {}

    row = conn.execute("SELECT COUNT(*) as c FROM sessions").fetchone()
    stats["total_sessions"] = row["c"]

    row = conn.execute("SELECT COUNT(*) as c FROM detections").fetchone()
    stats["total_detections"] = row["c"]

    row = conn.execute("""
        SELECT SUM(pothole_count) as p, SUM(alligator_count) as a,
               SUM(longitudinal_count) as l, SUM(transverse_count) as t
        FROM damage_summary
    """).fetchone()
    stats["pothole_count"]      = row["p"] or 0
    stats["alligator_count"]    = row["a"] or 0
    stats["longitudinal_count"] = row["l"] or 0
    stats["transverse_count"]   = row["t"] or 0

    rows = conn.execute("""
        SELECT DATE(created_at) as day, COUNT(*) as cnt
        FROM sessions
        GROUP BY day ORDER BY day DESC LIMIT 30
    """).fetchall()
    stats["daily_sessions"] = [dict(r) for r in rows]

    rows = conn.execute("""
        SELECT overall_severity, COUNT(*) as cnt
        FROM damage_summary GROUP BY overall_severity
    """).fetchall()
    stats["severity_dist"] = [dict(r) for r in rows]

    rows = conn.execute("""
        SELECT session_type, COUNT(*) as cnt
        FROM sessions GROUP BY session_type
    """).fetchall()
    stats["type_dist"] = [dict(r) for r in rows]

    rows = conn.execute("""
        SELECT s.latitude, s.longitude, s.location_name,
               ds.total_count, ds.overall_severity, s.created_at
        FROM sessions s
        JOIN damage_summary ds ON ds.session_id = s.id
        WHERE s.latitude IS NOT NULL AND s.longitude IS NOT NULL
          AND ds.total_count > 0
    """).fetchall()
    stats["map_points"] = [dict(r) for r in rows]

    conn.close()
    return stats
