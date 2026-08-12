"""Conditioning Demo POC — Uniformat Assembly Code prediction for Revit walls.

Identifies wall elements missing Uniformat Assembly Codes, predicts codes via
similarity matching against already-coded walls and a heuristic fallback, then:

  1. Attaches per-object predictions to the Speckle viewer
  2. Writes a markdown conditioning report as a run artifact
  3. Creates a new version in a "Conditioned" model with predicted codes imprinted

Data structure verified against Henry Ford Hospital shell model (project 0b23109140):
  - wall.category         → top-level str == "Walls"
  - wall.type             → top-level str, Revit type name
  - wall.family           → top-level str, Revit family name
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

import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from pydantic import Field
from speckle_automate import AutomateBase, AutomationContext, execute_automate_function


# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------


class FunctionInputs(AutomateBase):
    """Tunable parameters exposed in the Automate UI."""

    confidence_threshold: float = Field(
        default=0.65,
        title="Confidence Threshold",
        description=(
            "Minimum similarity score (0–1) to accept a model-based prediction. "
            "Below this threshold the heuristic fallback is used instead."
        ),
        ge=0.0,
        le=1.0,
    )

    @classmethod
    def model_json_schema(cls, **kwargs) -> dict:
        """Strip the JSON Schema dialect declaration for GitHub Action compatibility.

        AutomateGenerateJsonSchema adds '$schema: https://json-schema.org/draft/2020-12/schema'
        but the speckle-automate-github-action uses an AJV version that doesn't load that
        meta-schema, causing registration to fail with 'no schema with key or ref' error.
        Removing the field lets AJV use its default validation mode.
        """
        schema = super().model_json_schema(**kwargs)
        schema.pop("$schema", None)
        return schema


# ---------------------------------------------------------------------------
# Turner Uniformat code reference
#
# Source: Turner - Uniformat Estimate Detail Structure.xlsx
# Sections: A2010 (Subgrade Walls), B2010 (Exterior Walls), C1010 (Interior Partitions)
#
# IMPORTANT: In Turner's system curtain walls are B2010.40 ("Fabricated Exterior Wall
# Assemblies"), NOT B2050 ("Exterior Doors and Grilles"). This is a common mistake.
# ---------------------------------------------------------------------------

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
FEET_TO_MM = 304.8

# Matches Turner Level 4 sub-section codes: one capital letter, 4 digits, dot, 1-2 digits
# e.g. B2010.10, C1010.40, A2010.10
_LEVEL4_PATTERN = re.compile(r"^[A-Z]\d{4}\.\d{1,2}$")

# Matches codes that look like a Level 4 code with the period accidentally stripped:
# one capital letter, 4 digits, then exactly 2 digits (e.g. B201010, C101010).
# These are candidates for normalisation to B2010.10 form.
# NOTE: ASTM Uniformat II codes use a 3-digit suffix (e.g. B2010160) so they will
# NOT match this pattern — they are a different numbering scheme, not stripped Level 4.
_COLLAPSED_LEVEL4_PATTERN = re.compile(r"^([A-Z]\d{4})(\d{2})$")


def _try_normalise_to_level4(code: str) -> Optional[str]:
    """
    If `code` looks like a Level 4 code with the period stripped (e.g. 'B201010'),
    return the normalised form ('B2010.10'). Otherwise return None.
    """
    m = _COLLAPSED_LEVEL4_PATTERN.match(code.strip())
    if m:
        normalised = f"{m.group(1)}.{m.group(2)}"
        # Only accept if the normalised code is a known Turner Level 4 code
        if normalised in TURNER_CODES:
            return normalised
    return None


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class WallRecord:
    """Extracted metadata for one Revit wall element."""

    obj: object             # the DataObject (Base subclass)
    object_id: str          # wall.id
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
        return bool(self.assembly_code and _LEVEL4_PATTERN.match(self.assembly_code.strip()))


@dataclass
class Prediction:
    """A predicted Uniformat code for one uncoded wall."""

    wall: WallRecord
    predicted_code: str
    description: str
    confidence: float
    method: str                    # "similarity" | "heuristic_function" | "heuristic_name" | "default"
    matched_from: Optional[str]    # type_name of the best-scoring reference wall


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
    return _try_normalise_to_level4(raw) or raw


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


def _recursive_collect(obj, walls: list, visited: set) -> None:
    """Recursively walk the object graph, collecting wall elements."""
    obj_id = getattr(obj, "id", None) or id(obj)
    if obj_id in visited:
        return
    visited.add(obj_id)

    category = _get_category(obj)
    if category == "Walls":
        speckle_id = getattr(obj, "id", None) or ""
        if speckle_id:
            meta = get_wall_metadata(obj)
            walls.append(WallRecord(
                obj=obj,
                object_id=speckle_id,
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
    """Traverse the full object graph and return all Revit wall elements.

    Uses a manual recursive traversal as the primary strategy — GraphTraversal
    with empty rules can miss leaf objects nested inside Collections.
    """
    walls: list[WallRecord] = []
    visited: set = set()
    _recursive_collect(root, walls, visited)

    print(f"[ConditioningPOC] Visited {len(visited)} objects, found {len(walls)} walls.")
    return walls


# ---------------------------------------------------------------------------
# Fingerprinting & similarity
# ---------------------------------------------------------------------------


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


# Field weights — Function is the strongest Revit signal for wall classification
_WEIGHTS = {
    "type_name": 0.40,
    "family":    0.15,
    "function":  0.25,
    "type_mark": 0.10,
    "width_mm":  0.10,
}


def fingerprint_similarity(a: WallRecord, b: WallRecord) -> float:
    """Weighted Jaccard similarity over text fields + proportional width match."""
    score = 0.0
    for field, weight in _WEIGHTS.items():
        if field == "width_mm":
            w1, w2 = a.width_mm, b.width_mm
            if w1 > 0 and w2 > 0:
                score += weight * (min(w1, w2) / max(w1, w2))
        else:
            t1 = _tokens(getattr(a, field, "") or "")
            t2 = _tokens(getattr(b, field, "") or "")
            union = t1 | t2
            if union:
                score += weight * (len(t1 & t2) / len(union))
    return score


# ---------------------------------------------------------------------------
# Prediction engine
# ---------------------------------------------------------------------------


def _heuristic_predict(wall: WallRecord) -> tuple[str, str, str]:
    """Return (code, description, method) using Revit Function then keyword search."""
    func_lower = wall.function.lower().strip()
    for keyword, (code, desc) in FUNCTION_TO_CODE.items():
        if keyword in func_lower:
            return code, desc, "heuristic_function"

    combined = f"{wall.type_name} {wall.family} {wall.function}".lower()
    for keyword, code, desc in HEURISTIC_MAP:
        if keyword in combined:
            return code, desc, "heuristic_name"

    return DEFAULT_CODE[0], DEFAULT_CODE[1], "default"


def predict_codes(walls: list[WallRecord], threshold: float) -> list[Prediction]:
    """Predict Turner Level 4 codes for walls that don't have one yet.

    Reference pool: walls that already carry a Turner Level 4 code — these are
    the gold-standard examples for similarity matching.

    Prediction targets: walls with NO code AND walls whose existing code is NOT
    Turner Level 4 format (e.g. ASTM codes like B2010160 that need upgrading).
    """
    # Only Level4-coded walls are valid similarity references
    reference  = [w for w in walls if w.is_level4_coded]
    # Everything else needs a prediction (no code OR wrong format)
    needs_pred = [w for w in walls if not w.is_level4_coded]
    predictions: list[Prediction] = []

    for wall in needs_pred:
        best_score = 0.0
        best_ref: Optional[WallRecord] = None

        for ref in reference:
            score = fingerprint_similarity(wall, ref)
            if score > best_score:
                best_score = score
                best_ref   = ref

        if best_ref and best_score >= threshold:
            predictions.append(Prediction(
                wall=wall,
                predicted_code=best_ref.assembly_code,  # type: ignore[arg-type]
                description=f"Matched to '{best_ref.type_name}'",
                confidence=round(best_score, 3),
                method="similarity",
                matched_from=best_ref.type_name,
            ))
        else:
            code, desc, method = _heuristic_predict(wall)
            predictions.append(Prediction(
                wall=wall,
                predicted_code=code,
                description=desc,
                confidence=round(best_score, 3) if best_ref else 0.0,
                method=method,
                matched_from=best_ref.type_name if best_ref else None,
            ))

    return predictions


# ---------------------------------------------------------------------------
# Markdown report
# ---------------------------------------------------------------------------


def build_report(
    walls: list[WallRecord],
    predictions: list[Prediction],
    threshold: float,
) -> str:
    """Build a markdown conditioning report."""
    coded           = [w for w in walls if w.is_coded]
    level4          = [w for w in walls if w.is_level4_coded]
    non_level4_coded = [w for w in walls if w.is_coded and not w.is_level4_coded]
    uncoded         = [w for w in walls if not w.is_coded]
    sim_preds       = [p for p in predictions if p.method == "similarity"]
    heur_preds      = [p for p in predictions if p.method != "similarity"]

    lines = [
        "# Conditioning Demo POC — Uniformat Prediction Report",
        "",
        "## Summary",
        "",
        "| Metric | Count |",
        "|--------|-------|",
        f"| Total walls analysed | {len(walls)} |",
        "",
        "**Validation**",
        "",
        "| Metric | Count |",
        "|--------|-------|",
        f"| Has Turner Level 4 code (e.g. B2010.10) | {len(level4)} |",
        f"| Has code but NOT Turner Level 4 format (needs review) | {len(non_level4_coded)} |",
        f"| No code at all (uncoded) | {len(uncoded)} |",
        "",
        "**Conditioning**",
        "",
        "| Metric | Count |",
        "|--------|-------|",
        f"| Predicted via similarity match | {len(sim_preds)} |",
        f"| Predicted via heuristic / default | {len(heur_preds)} |",
        f"| Confidence threshold | {threshold} |",
        "",
        "---",
        "",
        "## Non-Level4 Codes (upgraded by conditioning)",
        "",
        "These walls had existing codes in a non-Turner-Level4 format. "
        "A predicted Level 4 code has been applied; the original code is "
        "preserved in the `Original Assembly Code (upgraded)` property for review.",
        "",
        "| Type Name | Type Mark | Function | Width (mm) | Original Code |",
        "|-----------|-----------|----------|------------|---------------|",
    ]

    nl4_counts: Counter = Counter()
    nl4_meta: dict = {}
    for w in non_level4_coded:
        key = (w.type_name, w.assembly_code)
        nl4_counts[key] += 1
        nl4_meta[key] = (w.type_mark, w.function, round(w.width_mm))

    if nl4_counts:
        for (type_name, code), count in sorted(nl4_counts.items(), key=lambda x: x[0][1] or ""):
            tm, fn, ww = nl4_meta.get((type_name, code), ("", "", 0))
            lines.append(f"| {type_name} | {tm} | {fn} | {ww} | `{code}` ×{count} |")
    else:
        lines.append("| — | — | — | — | _none_ |")

    lines += [
        "",
        "---",
        "",
        "## Predictions",
        "",
        "| # | Type Name | Level | Width (mm) | Predicted Code | Confidence | Method | Matched From |",
        "|---|-----------|-------|------------|----------------|------------|--------|--------------|",
    ]

    for i, p in enumerate(sorted(predictions, key=lambda x: -x.confidence), 1):
        w        = p.wall
        conf_str = f"{p.confidence:.0%}" if p.confidence > 0 else "—"
        matched  = p.matched_from or "—"
        lines.append(
            f"| {i} | {w.type_name or '—'} | {w.level or '—'} | {round(w.width_mm)} "
            f"| `{p.predicted_code}` | {conf_str} | {p.method} | {matched} |"
        )

    lines += [
        "",
        "---",
        "",
        "## Elements Not Conditioned (already Turner Level 4)",
        "",
        "These walls already carry a Turner Level 4 code and were passed through unchanged.",
        "",
        "| Type Name | Type Mark | Function | Width (mm) | Code | Count |",
        "|-----------|-----------|----------|------------|------|-------|",
    ]

    level4_counts: Counter = Counter()
    level4_meta: dict = {}
    for w in level4:
        key = (w.type_name, w.assembly_code)
        level4_counts[key] += 1
        level4_meta[key] = (w.type_mark, w.function, round(w.width_mm))

    if level4_counts:
        for (type_name, code), count in sorted(level4_counts.items(), key=lambda x: x[0][1] or ""):
            tm, fn, ww = level4_meta.get((type_name, code), ("", "", 0))
            lines.append(f"| {type_name} | {tm} | {fn} | {ww} | `{code}` | {count} |")
    else:
        lines.append("| — | — | — | — | _none_ | 0 |")

    lines += [
        "",
        "---",
        "",
        "## Final Code Distribution (all elements)",
        "",
        "| Code | Description | Count |",
        "|------|-------------|-------|",
    ]

    dist: dict[str, int] = defaultdict(int)
    for w in level4:
        if w.assembly_code:
            dist[w.assembly_code] += 1
    for p in predictions:
        dist[p.predicted_code] += 1

    for code in sorted(dist):
        lines.append(f"| `{code}` | {TURNER_CODES.get(code, code)} | {dist[code]} |")

    lines += ["", "---", "_Generated by Conditioning Demo POC · Speckle Automate_"]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Augmented model version
# ---------------------------------------------------------------------------


def _imprint_predictions(walls: list[WallRecord], predictions: list[Prediction]) -> None:
    """Mutate wall objects in-place to embed codes inside the properties dict."""
    pred_map = {p.wall.object_id: p for p in predictions}

    for wall in walls:
        obj  = wall.obj
        pred = pred_map.get(wall.object_id)

        # Write into obj.properties (the existing dict) so values appear under
        # the "properties" section in the Speckle viewer, not at the top level.
        props = getattr(obj, "properties", None)
        if not isinstance(props, dict):
            # Shouldn't happen for a real Revit wall, but guard gracefully
            props = {}
            obj["properties"] = props

        if wall.is_level4_coded:
            # Already correct — surface it under the standard property name
            props["Turner Level 4 Code"] = wall.assembly_code
        elif pred:
            # Predicted (covers both truly uncoded and non-Level4 coded walls)
            props["Conditioned Turner Level 4 Code"]            = pred.predicted_code
            props["Conditioned Turner Level 4 Code Confidence"] = pred.confidence
            props["Conditioned Turner Level 4 Code Method"]     = pred.method
            if wall.is_coded:
                # Preserve the original code so reviewers can compare
                props["Original Assembly Code (upgraded)"] = wall.assembly_code


def _get_or_create_model(automate_context: AutomationContext, model_name: str, model_description: str):
    """
    Return a model object with an .id attribute, creating it if it doesn't exist.

    create_new_model_in_project raises BRANCH_CREATE_ERROR when the model already
    exists (subsequent runs). In that case we use client.model.get_models with a
    name search filter — the specklepy 3.x SDK API, which replaced client.branch.
    """
    try:
        return automate_context.create_new_model_in_project(
            model_name=model_name,
            model_description=model_description,
        )
    except Exception as exc:
        if "already exists" not in str(exc).lower() and "BRANCH_CREATE_ERROR" not in str(exc):
            raise

    # Model exists from a previous run — look it up by name via the SDK
    from specklepy.core.api.inputs.project_inputs import ProjectModelsFilter

    client     = automate_context.speckle_client
    project_id = automate_context.automation_run_data.project_id

    collection = client.model.get_models(
        project_id,
        models_filter=ProjectModelsFilter(search=model_name),
    )
    match = next(
        (m for m in (collection.items or []) if m.name == model_name),
        None,
    )
    if not match:
        raise RuntimeError(f"Model '{model_name}' not found in project {project_id} after creation failed")
    return match


def create_conditioned_version(
    automate_context: AutomationContext,
    root,
    walls: list[WallRecord],
    predictions: list[Prediction],
) -> Optional[str]:
    """
    Imprint predictions onto wall objects and push a new version into the
    'Conditioned' model (creating it on first run, reusing it thereafter).

    Returns the new version ID, or None on failure.
    """
    _imprint_predictions(walls, predictions)

    try:
        model = _get_or_create_model(
            automate_context,
            model_name="Conditioned",
            model_description="Walls with predicted Uniformat Assembly Codes — Conditioning Demo POC",
        )
        new_version = automate_context.create_new_version_in_project(
            root_object=root,
            model_id=model.id,
            version_message="Uniformat Assembly Code predictions applied by Conditioning Demo POC",
        )
        return new_version.id

    except Exception as exc:
        print(f"[ConditioningPOC] Augmented version creation failed: {exc}")
        return None


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def automate_function(
    automate_context: AutomationContext,
    function_inputs: FunctionInputs,
) -> None:
    """Run Uniformat conditioning on all wall elements in the triggered version."""
    # 1. Receive and traverse
    root  = automate_context.receive_version()
    walls = collect_walls(root)

    if not walls:
        automate_context.mark_run_success(
            "No wall elements found in this version — nothing to condition."
        )
        return

    coded           = [w for w in walls if w.is_coded]
    level4          = [w for w in walls if w.is_level4_coded]
    non_level4_coded = [w for w in walls if w.is_coded and not w.is_level4_coded]
    uncoded         = [w for w in walls if not w.is_coded]

    print(
        f"[ConditioningPOC] "
        f"{len(coded)} with any code "
        f"({len(level4)} Turner Level 4, {len(non_level4_coded)} other format), "
        f"{len(uncoded)} uncoded."
    )

    # 2. Predict codes for uncoded walls
    predictions = predict_codes(walls, function_inputs.confidence_threshold)

    # 3. Per-object viewer annotations — grouped so each unique code/message is
    #    one result entry with all matching objects attached, rather than one
    #    entry per wall.

    # Turner Level 4 coded walls — gold standard, highlight separately
    level4_by_code: dict[str, list] = defaultdict(list)
    for wall in level4:
        level4_by_code[wall.assembly_code or ""].append(wall.obj)
    for code, objs in sorted(level4_by_code.items()):
        automate_context.attach_info_to_objects(
            category="Uniformat — Turner Level 4 Code",
            affected_objects=objs,
            message=f"Level 4 code: {code} ({len(objs)} element{'s' if len(objs) != 1 else ''})",
        )

    # Non-Level4 coded walls — has a code but not Turner Level 4 format
    non_l4_by_code: dict[str, list] = defaultdict(list)
    for wall in non_level4_coded:
        non_l4_by_code[wall.assembly_code or ""].append(wall.obj)
    for code, objs in sorted(non_l4_by_code.items()):
        automate_context.attach_info_to_objects(
            category="Uniformat — Non-Level4 Code (needs review)",
            affected_objects=objs,
            message=f"Code {code!r} is not Turner Level 4 format — review required "
                    f"({len(objs)} element{'s' if len(objs) != 1 else ''})",
        )

    # Predictions: group by (category, predicted_code)
    pred_groups: dict[tuple[str, str], list] = defaultdict(list)
    pred_group_labels: dict[tuple[str, str], str] = {}
    for pred in predictions:
        if pred.method == "similarity":
            cat = "Uniformat — Predicted (similarity)"
            key = (cat, pred.predicted_code)
            pred_group_labels.setdefault(key, pred.predicted_code)
        elif pred.method.startswith("heuristic"):
            cat = "Uniformat — Predicted (heuristic)"
            key = (cat, pred.predicted_code)
            pred_group_labels.setdefault(key, f"{pred.predicted_code} — {pred.description}")
        else:
            cat = "Uniformat — Predicted (default fallback)"
            key = (cat, pred.predicted_code)
            pred_group_labels.setdefault(key, f"{pred.predicted_code} (low confidence — review manually)")
        pred_groups[key].append(pred.wall.obj)

    for (cat, _code), objs in sorted(pred_groups.items()):
        label = pred_group_labels[(cat, _code)]
        automate_context.attach_info_to_objects(
            category=cat,
            affected_objects=objs,
            message=f"Predicted: {label} ({len(objs)} element{'s' if len(objs) != 1 else ''})",
        )

    # 4. Conditioning report
    report_md   = build_report(walls, predictions, function_inputs.confidence_threshold)
    report_path = Path("conditioning_report.md")
    report_path.write_text(report_md, encoding="utf-8")
    try:
        automate_context.store_file_result(report_path)
    except Exception as exc:
        print(f"[ConditioningPOC] Could not store report: {exc}")

    # 5. Create augmented 'Conditioned' model version
    new_version_id = create_conditioned_version(
        automate_context, root, walls, predictions
    )

    # 6. Success summary
    sim_count  = sum(1 for p in predictions if p.method == "similarity")
    heur_count = len(predictions) - sim_count
    needs_pred_count = len(uncoded) + len(non_level4_coded)
    summary = (
        f"Processed {len(walls)} walls — "
        f"{len(level4)} already Turner Level 4, "
        f"{len(non_level4_coded)} non-Level4 codes upgraded, "
        f"{len(uncoded)} uncoded — "
        f"{needs_pred_count} predicted "
        f"({sim_count} similarity, {heur_count} heuristic)."
    )
    if new_version_id:
        summary += f" Conditioned model version: {new_version_id}"

    automate_context.mark_run_success(summary)


if __name__ == "__main__":
    execute_automate_function(automate_function, FunctionInputs)
