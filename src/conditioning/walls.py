"""Extracting WallRecord data from raw Speckle DataObjects, and classifying
a wall list into coded/level4/uncoded buckets.

"WallRecord" is the umbrella term for any Uniformat-conditionable envelope
element — that's Revit's "Walls" category, plus curtain wall's separate
"Curtain Systems", "Curtain Panels", and "Curtain Wall Mullions" categories.
Turner's own B2010 ("Exterior Walls") Uniformat section already treats
curtain walls as a wall sub-type (B2010.40), so grouping them under one
WallRecord model matches the target taxonomy, even though Revit models them
as distinct categories from plain "Walls" — see TARGET_CATEGORIES below.

Data structure verified against Henry Ford Hospital shell model (project 0b23109140):
  - wall.category         → top-level str, e.g. "Walls", "Curtain Systems"
  - wall.type             → top-level str, Revit type name
  - wall.family            → top-level str, Revit family name
  - wall.level            → top-level str, e.g. "LEVEL 01"
  - Assembly Code         → properties["Parameters"]["Type Parameters"]
                              ["Identity Data"]["Assembly Code"]["value"]
  - Function              → properties["Parameters"]["Type Parameters"]
                              ["Construction"]["Function"]["value"]
  - Width (feet)          → properties["Parameters"]["Type Parameters"]
                              ["Construction"]["Width"]["value"]
  - Type Mark             → properties["Parameters"]["Type Parameters"]
                              ["Identity Data"]["Type Mark"]["value"]
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from conditioning.codes import ASTM_CODE_PATTERN, LEVEL4_PATTERN, try_normalise_to_level4

FEET_TO_MM = 304.8


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class WallRecord:
    """Extracted metadata for one Revit wall or curtain-wall-family element."""

    obj: object             # the DataObject (Base subclass)
    object_id: str          # wall.id
    category: str           # "Walls" | "Curtain Systems" | "Curtain Panels" | "Curtain Wall Mullions"
    type_name: str          # wall.type
    family: str             # wall.family
    function: str           # Construction > Function param value
    type_mark: str          # Identity Data > Type Mark param value
    width_mm: float         # Construction > Width (feet) × 304.8
    level: str              # wall.level (plain string in v3)
    assembly_code: Optional[str]  # Identity Data > Assembly Code; None if absent

    @property
    def is_coded(self) -> bool:
        """True if this wall already has an Assembly Code (any format)."""
        return bool(self.assembly_code and self.assembly_code.strip())

    @property
    def is_level4_coded(self) -> bool:
        """True if the Assembly Code is a Turner Level 4 sub-section code (e.g. B2010.10)."""
        return bool(self.assembly_code and LEVEL4_PATTERN.match(self.assembly_code.strip()))

    @property
    def is_astm_coded(self) -> bool:
        """True if the Assembly Code is a legacy ASTM Uniformat II code (e.g. B2010160).

        These carry real classification signal (they're not blank) but aren't in
        Turner's dot-notation format, so they need a human crosswalk decision —
        they must never be silently overwritten by the prediction heuristic.
        """
        return bool(self.assembly_code and ASTM_CODE_PATTERN.match(self.assembly_code.strip()))


@dataclass
class WallClassification:
    """Walls bucketed by code status — the same split is needed by both the
    report and the orchestrator, so it's computed once and shared."""

    coded: list[WallRecord] = field(default_factory=list)
    level4: list[WallRecord] = field(default_factory=list)
    non_level4_coded: list[WallRecord] = field(default_factory=list)
    uncoded: list[WallRecord] = field(default_factory=list)


def classify_walls(walls: list[WallRecord]) -> WallClassification:
    """Bucket walls by code status: coded/level4/non_level4_coded/uncoded."""
    return WallClassification(
        coded=[w for w in walls if w.is_coded],
        level4=[w for w in walls if w.is_level4_coded],
        non_level4_coded=[w for w in walls if w.is_coded and not w.is_level4_coded],
        uncoded=[w for w in walls if not w.is_coded],
    )


# ---------------------------------------------------------------------------
# Parameter extraction
# ---------------------------------------------------------------------------


def _type_params(wall_obj) -> dict:
    """Return the Type Parameters dict from properties["Parameters"]["Type Parameters"]."""
    props = getattr(wall_obj, "properties", None)
    if not props:
        return {}
    params = props.get("Parameters", {}) if isinstance(props, dict) else getattr(props, "Parameters", {}) or {}
    if isinstance(params, dict):
        tp = params.get("Type Parameters", {})
    else:
        tp = getattr(params, "Type Parameters", {}) or {}
    return tp if isinstance(tp, dict) else {}


def _pval(group: dict, name: str):
    """Pull the .value out of a parameter entry in a group dict."""
    entry = group.get(name) if isinstance(group, dict) else None
    if entry is None:
        return None
    return entry.get("value") if isinstance(entry, dict) else getattr(entry, "value", None)


def get_assembly_code(wall_obj) -> Optional[str]:
    """Extract Assembly Code from Identity Data > Type Parameters, or None.

    If the code looks like a Turner Level 4 code with the period accidentally
    stripped (e.g. 'B201010' → 'B2010.10'), normalise it on the way in so it
    is treated as already-coded Level 4 rather than needing upgrade.
    ASTM Uniformat II codes (3-digit suffix, e.g. 'B2010160') are NOT affected.
    """
    identity = _type_params(wall_obj).get("Identity Data", {})
    val = _pval(identity, "Assembly Code")
    if not val:
        return None
    raw = str(val).strip()
    if not raw:
        return None
    return try_normalise_to_level4(raw) or raw


def get_wall_metadata(wall_obj) -> dict:
    """Extract all fingerprinting fields from a wall DataObject."""
    # Core identity is on top-level attributes (confirmed in v3 connector data)
    type_name = str(getattr(wall_obj, "type",   "") or "").strip()
    family    = str(getattr(wall_obj, "family", "") or "").strip()
    level     = str(getattr(wall_obj, "level",  "") or "").strip()

    tp           = _type_params(wall_obj)
    identity     = tp.get("Identity Data", {})
    construction = tp.get("Construction", {})

    function  = str(_pval(construction, "Function")  or "").strip()
    type_mark = str(_pval(identity,     "Type Mark") or "").strip()

    width_raw = _pval(construction, "Width") or 0.0
    try:
        width_mm = float(width_raw) * FEET_TO_MM
    except (TypeError, ValueError):
        width_mm = 0.0

    return {
        "type_name": type_name,
        "family":    family,
        "function":  function,
        "type_mark": type_mark,
        "width_mm":  width_mm,
        "level":     level,
    }


# ---------------------------------------------------------------------------
# Wall traversal
# ---------------------------------------------------------------------------


def _get_category(obj) -> Optional[str]:
    """Get category from a Speckle object, trying multiple access patterns."""
    # 1. Top-level attribute (confirmed in viewer: RevitObject has .category)
    cat = getattr(obj, "category", None)
    if cat:
        return str(cat)
    # 2. Dict-style access (Base dynamic properties)
    try:
        cat = obj["category"]
        if cat:
            return str(cat)
    except (KeyError, TypeError, AttributeError):
        pass
    # 3. Inside properties dict (fallback)
    props = getattr(obj, "properties", None)
    if isinstance(props, dict):
        cat = props.get("category")
        if cat:
            return str(cat)
    return None


# Categories collected for conditioning. Revit models curtain walls as three
# categories distinct from "Walls" — the curtain wall host ("Curtain
# Systems"), the individual glazing/spandrel infill ("Curtain Panels"), and
# the framing members ("Curtain Wall Mullions"). All three were being
# silently skipped when the filter only matched "Walls" exactly, meaning
# every curtain wall element in a model was excluded from conditioning
# entirely. Matched case-insensitively/by substring on "curtain" rather than
# an exact string, since the exact category label wasn't verified against a
# live curtain-wall-bearing model the way "Walls" was (see docs/NOTES.md).
def _is_target_category(category: Optional[str]) -> bool:
    """True if `category` is a wall or curtain-wall-family Revit category."""
    if not category:
        return False
    if category == "Walls":
        return True
    return "curtain" in category.lower()


def _recursive_collect(obj, walls: list, visited: set) -> None:
    """Recursively walk the object graph, collecting wall elements."""
    obj_id = getattr(obj, "id", None) or id(obj)
    if obj_id in visited:
        return
    visited.add(obj_id)

    category = _get_category(obj)
    if _is_target_category(category):
        speckle_id = getattr(obj, "id", None) or ""
        if speckle_id:
            meta = get_wall_metadata(obj)
            walls.append(WallRecord(
                obj=obj,
                object_id=speckle_id,
                category=category or "",
                assembly_code=get_assembly_code(obj),
                **meta,
            ))

    # Recurse into all member properties
    for prop_name in obj.get_member_names():
        if prop_name in ("displayValue", "renderMaterial"):
            continue  # skip geometry — not BIM data
        try:
            value = getattr(obj, prop_name, None)
        except Exception:
            continue
        if value is None:
            continue
        if hasattr(value, "get_member_names"):
            _recursive_collect(value, walls, visited)
        elif isinstance(value, list):
            for item in value:
                if item is not None and hasattr(item, "get_member_names"):
                    _recursive_collect(item, walls, visited)


def collect_walls(root) -> list[WallRecord]:
    """Traverse the full object graph and return all wall + curtain-wall-family elements.

    Uses a manual recursive traversal as the primary strategy — GraphTraversal
    with empty rules can miss leaf objects nested inside Collections.
    """
    walls: list[WallRecord] = []
    visited: set = set()
    _recursive_collect(root, walls, visited)

    print(f"[ConditioningPOC] Visited {len(visited)} objects, found {len(walls)} walls.")
    return walls
