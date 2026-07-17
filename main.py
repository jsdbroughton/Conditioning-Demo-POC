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
from specklepy.objects.graph_traversal.traversal import GraphTraversal


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
        """True if this wall already has an Assembly Code."""
        return bool(self.assembly_code and self.assembly_code.strip())


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
    """Extract Assembly Code from Identity Data > Type Parameters, or None."""
    identity = _type_params(wall_obj).get("Identity Data", {})
    val = _pval(identity, "Assembly Code")
    return str(val).strip() if val and str(val).strip() else None


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


def collect_walls(root) -> list[WallRecord]:
    """Traverse the full object graph and return all Revit wall elements."""
    traversal = GraphTraversal([])
    walls: list[WallRecord] = []

    for context in traversal.traverse(root):
        obj = context.current
        # category is a top-level attribute in the v3 Revit connector
        if getattr(obj, "category", None) != "Walls":
            continue
        obj_id = getattr(obj, "id", None) or ""
        if not obj_id:
            continue
        meta = get_wall_metadata(obj)
        walls.append(WallRecord(
            obj=obj,
            object_id=obj_id,
            assembly_code=get_assembly_code(obj),
            **meta,
        ))

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
    """For each uncoded wall: similarity match → heuristic fallback → default."""
    coded   = [w for w in walls if w.is_coded]
    uncoded = [w for w in walls if not w.is_coded]
    predictions: list[Prediction] = []

    for wall in uncoded:
        best_score = 0.0
        best_ref: Optional[WallRecord] = None

        for ref in coded:
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
    coded      = [w for w in walls if w.is_coded]
    uncoded    = [w for w in walls if not w.is_coded]
    sim_preds  = [p for p in predictions if p.method == "similarity"]
    heur_preds = [p for p in predictions if p.method != "similarity"]

    lines = [
        "# Conditioning Demo POC — Uniformat Prediction Report",
        "",
        "## Summary",
        "",
        "| Metric | Count |",
        "|--------|-------|",
        f"| Total walls analysed | {len(walls)} |",
        f"| Already coded (reference set) | {len(coded)} |",
        f"| Uncoded (predictions generated) | {len(uncoded)} |",
        f"| Predicted via similarity match | {len(sim_preds)} |",
        f"| Predicted via heuristic / default | {len(heur_preds)} |",
        f"| Confidence threshold | {threshold} |",
        "",
        "---",
        "",
        "## Reference Codes (already coded walls)",
        "",
        "| Type Name | Type Mark | Function | Width (mm) | Code |",
        "|-----------|-----------|----------|------------|------|",
    ]

    code_counts: Counter = Counter()
    code_meta: dict = {}
    for w in coded:
        key = (w.type_name, w.assembly_code)
        code_counts[key] += 1
        code_meta[key] = (w.type_mark, w.function, round(w.width_mm))

    for (type_name, code), count in sorted(code_counts.items(), key=lambda x: x[1][1] or ""):
        tm, fn, ww = code_meta.get((type_name, code), ("", "", 0))
        lines.append(f"| {type_name} | {tm} | {fn} | {ww} | `{code}` ×{count} |")

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
        "## Code Distribution (coded + predicted)",
        "",
        "| Code | Description | Count |",
        "|------|-------------|-------|",
    ]

    dist: dict[str, int] = defaultdict(int)
    for w in coded:
        if w.assembly_code:
            dist[w.assembly_code] += 1
    for p in predictions:
        dist[p.predicted_code] += 1

    for code in sorted(dist):
        lines.append(f"| `{code}` | {UNIFORMAT_LABELS.get(code, code)} | {dist[code]} |")

    lines += ["", "---", "_Generated by Conditioning Demo POC · Speckle Automate_"]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Augmented model version
# ---------------------------------------------------------------------------


def _imprint_predictions(walls: list[WallRecord], predictions: list[Prediction]) -> None:
    """Mutate uncoded wall objects in-place to embed predicted Assembly Codes."""
    pred_map = {p.wall.object_id: p for p in predictions}

    for wall in walls:
        pred = pred_map.get(wall.object_id)
        if not pred:
            continue

        obj = wall.obj

        # Top-level annotation — always readable downstream
        obj["conditioningPrediction"] = {
            "predictedAssemblyCode": pred.predicted_code,
            "confidence":            pred.confidence,
            "method":                pred.method,
            "matchedFrom":           pred.matched_from or "",
            "description":           pred.description,
        }

        # Best-effort: mirror into Identity Data alongside existing params
        try:
            props = getattr(obj, "properties", None)
            if isinstance(props, dict):
                params   = props.setdefault("Parameters", {})
                tp       = params.setdefault("Type Parameters", {})
                identity = tp.setdefault("Identity Data", {})
                identity["Assembly Code (Predicted)"] = {
                    "value": pred.predicted_code,
                    "name":  "Assembly Code (Predicted)",
                    "internalDefinitionName": "ASSEMBLY_CODE_PREDICTED",
                }
        except Exception:
            pass  # top-level annotation above is the canonical output


def create_conditioned_version(
    automate_context: AutomationContext,
    root,
    walls: list[WallRecord],
    predictions: list[Prediction],
) -> Optional[str]:
    """
    Imprint predictions onto wall objects and create a new version in a
    'Conditioned' model in the same project.

    Uses automate_context.create_new_model_in_project +
         automate_context.create_new_version_in_project
    as provided by the speckle_automate SDK.

    Returns the new version ID, or None on failure.
    """
    _imprint_predictions(walls, predictions)

    try:
        # Create (or reuse) the target model
        conditioned_model = automate_context.create_new_model_in_project(
            model_name="Conditioned",
            model_description="Walls with predicted Uniformat Assembly Codes — Conditioning Demo POC",
        )

        new_version = automate_context.create_new_version_in_project(
            root_object=root,
            model_id=conditioned_model.id,
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

    coded   = [w for w in walls if w.is_coded]
    uncoded = [w for w in walls if not w.is_coded]

    # 2. Predict codes for uncoded walls
    predictions = predict_codes(walls, function_inputs.confidence_threshold)

    # 3. Per-object viewer annotations
    for wall in coded:
        automate_context.attach_info_to_objects(
            category="Uniformat — Existing Code",
            affected_objects=[wall.obj],
            message=f"Assembly Code: {wall.assembly_code}",
        )

    for pred in predictions:
        if pred.method == "similarity":
            cat = "Uniformat — Predicted (similarity)"
            msg = (
                f"Predicted: {pred.predicted_code} "
                f"({pred.confidence:.0%} confidence) "
                f"← matched to '{pred.matched_from}'"
            )
        elif pred.method.startswith("heuristic"):
            cat = "Uniformat — Predicted (heuristic)"
            msg = f"Predicted: {pred.predicted_code} — {pred.description}"
        else:
            cat = "Uniformat — Predicted (default fallback)"
            msg = f"Predicted: {pred.predicted_code} (low confidence — review manually)"

        automate_context.attach_info_to_objects(
            category=cat,
            affected_objects=[pred.wall.obj],
            message=msg,
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
    summary = (
        f"Processed {len(walls)} walls — "
        f"{len(coded)} already coded, "
        f"{len(uncoded)} predicted "
        f"({sim_count} similarity, {heur_count} heuristic)."
    )
    if new_version_id:
        summary += f" Conditioned model version: {new_version_id}"

    automate_context.mark_run_success(summary)


if __name__ == "__main__":
    execute_automate_function(automate_function, FunctionInputs)
