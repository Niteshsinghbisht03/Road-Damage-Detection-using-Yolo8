"""
Severity scoring for Road Damage Detection.

Severity rules (per single detection):
  - Potholes      → always starts at High (most dangerous)
  - Alligator     → Medium (structural failure pattern)
  - Longitudinal  → Low-Medium
  - Transverse    → Low

Overall session severity is elevated by count and mix of types.
"""

# Per-class base severity
CLASS_BASE_SEVERITY = {
    0: "Low",      # Longitudinal Crack
    1: "Low",      # Transverse Crack
    2: "Medium",   # Alligator Crack
    3: "High",     # Pothole
}

SEVERITY_RANK = {"None": 0, "Low": 1, "Medium": 2, "High": 3, "Critical": 4}
RANK_SEVERITY = {v: k for k, v in SEVERITY_RANK.items()}


def score_single_detection(class_id: int, confidence: float) -> str:
    """Return severity for a single bounding-box detection."""
    base = CLASS_BASE_SEVERITY.get(class_id, "Low")
    rank = SEVERITY_RANK[base]

    # Boost severity for high-confidence detections
    if confidence >= 0.85:
        rank = min(rank + 1, 4)

    return RANK_SEVERITY[rank]


def score_session(counts: dict, session_type: str = "image") -> str:
    """
    Compute overall session severity.

    counts: {class_id (int): count (int)}
    """
    total = sum(counts.values())

    if total == 0:
        return "None"

    # Start from the worst individual class present
    max_rank = 0
    for class_id, cnt in counts.items():
        if cnt > 0:
            base_rank = SEVERITY_RANK[CLASS_BASE_SEVERITY.get(class_id, "Low")]
            max_rank = max(max_rank, base_rank)

    # Escalate by total volume
    if total >= 15:
        max_rank = min(max_rank + 2, 4)
    elif total >= 7:
        max_rank = min(max_rank + 1, 4)

    # Potholes + alligator together → Critical
    if counts.get(3, 0) > 0 and counts.get(2, 0) > 0:
        max_rank = min(max_rank + 1, 4)

    return RANK_SEVERITY[max_rank]


def severity_color(severity: str) -> str:
    """Return a hex color for display."""
    return {
        "None":     "#6b7280",
        "Low":      "#22c55e",
        "Medium":   "#f59e0b",
        "High":     "#ef4444",
        "Critical": "#7c3aed",
    }.get(severity, "#6b7280")


def severity_emoji(severity: str) -> str:
    return {
        "None":     "⚪",
        "Low":      "🟢",
        "Medium":   "🟡",
        "High":     "🔴",
        "Critical": "🟣",
    }.get(severity, "⚪")
