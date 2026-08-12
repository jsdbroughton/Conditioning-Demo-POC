"""Turner Uniformat code reference data and code-format detection.

Source: Turner - Uniformat Estimate Detail Structure.xlsx
Sections: A2010 (Subgrade Walls), B2010 (Exterior Walls), C1010 (Interior Partitions)

IMPORTANT: In Turner's system curtain walls are B2010.40 ("Fabricated Exterior Wall
Assemblies"), NOT B2050 ("Exterior Doors and Grilles"). This is a common mistake.

The hardcoded TURNER_CODES dict below is validated against the source
spreadsheet in tests/test_turner_codes_fixture.py (fixtures/Turner - Uniformat
Estimate Detail Structure.xlsx) — that test is the guardrail against drift,
not a switch to loading codes dynamically. Direction as of 2026-08-12 is to
keep this hardcoded for now.
"""

from __future__ import annotations

import re
from typing import Optional

TURNER_CODES: dict[str, str] = {
    # ── A2010 Subgrade / Basement Walls ─────────────────────────────────────
    "A2010":    "Walls for Subgrade Enclosures",
    "A2010.10": "Subgrade Enclosure Wall Construction",
    "A2010.20": "Subgrade Enclosure Wall Interior Skin",
    "A2010.90": "Subgrade Enclosure Wall Supplementary Components",
    # ── B2010 Exterior Walls ─────────────────────────────────────────────────
    "B2010":    "Exterior Walls",
    "B2010.10": "Exterior Wall Veneer",        # masonry, precast, metal panels, GFRC, stone
    "B2010.20": "Exterior Wall Back-up Construction",  # CMU/metal stud backup
    "B2010.30": "Exterior Wall Interior Skin",
    "B2010.40": "Fabricated Exterior Wall Assemblies",  # ← curtain walls go here
    "B2010.50": "Parapet Back-up Construction",
    "B2010.60": "Equipment Screens",
    "B2010.80": "Exterior Wall Supplementary Components",
    "B2010.90": "Exterior Wall Opening Supplementary Components",
    # ── C1010 Interior Partitions ────────────────────────────────────────────
    "C1010":    "Interior Partitions",
    "C1010.10": "Interior Fixed Partitions",   # CMU, rated/non-rated GWB
    "C1010.20": "Interior Glazed Partitions",  # interior storefront
    "C1010.40": "Interior Demountable Partitions",
    "C1010.50": "Interior Operable Partitions",
    "C1010.70": "Interior Screens",
    "C1010.90": "Interior Partition Supplementary Components",
}

# Primary prediction targets — sub-section codes applied directly to wall elements
# (the level at which a Revit Assembly Code is typically set)
TURNER_WALL_TARGETS: dict[str, str] = {
    "A2010.10": "Subgrade Enclosure Wall Construction",
    "B2010.10": "Exterior Wall Veneer",
    "B2010.40": "Fabricated Exterior Wall Assemblies (Curtain Wall)",
    "C1010.10": "Interior Fixed Partitions",
    "C1010.20": "Interior Glazed Partitions",
}

# ---------------------------------------------------------------------------
# Heuristic lookup
#
# Revit Function parameter is checked first (highest confidence), then keyword
# search across type name + family + function combined text.
# ---------------------------------------------------------------------------

# Revit Function parameter value → Turner code (most reliable signal)
FUNCTION_TO_CODE: dict[str, tuple[str, str]] = {
    "exterior":   ("B2010.10", "Exterior Wall Veneer"),
    "interior":   ("C1010.10", "Interior Fixed Partitions"),
    "retaining":  ("A2010.10", "Subgrade Enclosure Wall Construction"),
    "foundation": ("A2010.10", "Subgrade Enclosure Wall Construction"),
    "curtain":    ("B2010.40", "Fabricated Exterior Wall Assemblies (Curtain Wall)"),
}

# (keyword_in_combined_text, turner_code, description) — ordered by specificity
HEURISTIC_MAP: list[tuple[str, str, str]] = [
    ("curtain wall",  "B2010.40", "Fabricated Exterior Wall Assemblies (Curtain Wall)"),
    ("curtain",       "B2010.40", "Fabricated Exterior Wall Assemblies (Curtain Wall)"),
    ("glazing",       "B2010.40", "Fabricated Exterior Wall Assemblies (Curtain Wall)"),
    ("storefront",    "B2010.40", "Fabricated Exterior Wall Assemblies (Curtain Wall)"),
    ("084400",        "B2010.40", "Fabricated Exterior Wall Assemblies (Curtain Wall)"),
    ("retaining",     "A2010.10", "Subgrade Enclosure Wall Construction"),
    ("basement",      "A2010.10", "Subgrade Enclosure Wall Construction"),
    ("foundation",    "A2010.10", "Subgrade Enclosure Wall Construction"),
    ("below grade",   "A2010.10", "Subgrade Enclosure Wall Construction"),
    ("parapet",       "B2010.50", "Parapet Back-up Construction"),
    ("shear",         "B2010.10", "Exterior Wall Veneer"),
    ("exterior",      "B2010.10", "Exterior Wall Veneer"),
    ("facade",        "B2010.10", "Exterior Wall Veneer"),
    ("cmu",           "B2010.10", "Exterior Wall Veneer"),
    ("scmu",          "B2010.10", "Exterior Wall Veneer"),
    ("masonry",       "B2010.10", "Exterior Wall Veneer"),
    ("brick",         "B2010.10", "Exterior Wall Veneer"),
    ("gfrc",          "B2010.10", "Exterior Wall Veneer"),
    ("metal panel",   "B2010.10", "Exterior Wall Veneer"),
    ("precast",       "B2010.10", "Exterior Wall Veneer"),
    ("demising",      "C1010.10", "Interior Fixed Partitions"),
    ("firewall",      "C1010.10", "Interior Fixed Partitions"),
    ("partition",     "C1010.10", "Interior Fixed Partitions"),
    ("interior",      "C1010.10", "Interior Fixed Partitions"),
]

DEFAULT_CODE = ("B2010.10", "Exterior Wall Veneer (default fallback)")

# Confidence assigned to non-similarity predictions, keyed by method. These are
# fixed estimates of how much to trust each signal — NOT derived from the
# similarity score, which is meaningless when there's no reference wall to
# compare against (see predict.predict_codes). Ordering matches the
# reliability described in the module docstring: Revit's own Function param
# is the strongest signal, then keyword matching, then blind default.
METHOD_CONFIDENCE = {
    "heuristic_function": 0.75,
    "heuristic_name": 0.50,
    "default": 0.0,
}

# All conditioning output is written under this single namespaced key inside
# wall.properties, rather than as several flat sibling keys — keeps the
# viewer/report/PowerBI surface predictable (one place to look) and avoids
# ever colliding with a real Revit parameter name.
CONDITIONING_KEY = "Conditioning Results"

# Matches Turner Level 4 sub-section codes: one capital letter, 4 digits, dot, 1-2 digits
# e.g. B2010.10, C1010.40, A2010.10
LEVEL4_PATTERN = re.compile(r"^[A-Z]\d{4}\.\d{1,2}$")

# Matches codes that look like a Level 4 code with the period accidentally stripped:
# one capital letter, 4 digits, then exactly 2 digits (e.g. B201010, C101010).
# These are candidates for normalisation to B2010.10 form.
# NOTE: ASTM Uniformat II codes use a 3-digit suffix (e.g. B2010160) so they will
# NOT match this pattern — they are a different numbering scheme, not stripped Level 4.
COLLAPSED_LEVEL4_PATTERN = re.compile(r"^([A-Z]\d{4})(\d{2})$")

# Matches legacy ASTM Uniformat II codes: one capital letter, 4 digits, then a
# 3-digit sub-code (e.g. B2010160, C1010145). These already carry real
# classification signal via their type_name/family/function — they must NOT be
# treated as blank slates and overwritten by the heuristic fallback.
ASTM_CODE_PATTERN = re.compile(r"^[A-Z]\d{4}\d{3}$")


def try_normalise_to_level4(code: str) -> Optional[str]:
    """If `code` looks like a Level 4 code with the period stripped.

    e.g. 'B201010', return the normalised form ('B2010.10'). Otherwise return
    None.
    """
    m = COLLAPSED_LEVEL4_PATTERN.match(code.strip())
    if m:
        normalised = f"{m.group(1)}.{m.group(2)}"
        # Only accept if the normalised code is a known Turner Level 4 code
        if normalised in TURNER_CODES:
            return normalised
    return None
