"""The prediction engine: fingerprint similarity + heuristic fallback.

Produces Prediction objects for every wall that doesn't already carry a
Turner Level 4 code — that covers both walls with no code at all AND walls
with an existing non-Level4 code (e.g. legacy ASTM Uniformat II). Both get a
real, method-based confidence score and Tier 1/2/3 rating; nothing is
silently defaulted to 0 confidence and nothing gets skipped. See
predict_codes() docstring for the full reasoning.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from conditioning.codes import (
    CONFLICT_PENALTY,
    CORROBORATION_BONUS,
    CORROBORATION_CAP,
    CURTAIN_LEGACY_CROSSWALK_CONFIDENCE,
    DEFAULT_CODE,
    FUNCTION_TO_CODE,
    HEURISTIC_MAP,
    METHOD_CONFIDENCE,
    confidence_to_tier,
    legacy_code_section,
)
from conditioning.walls import WallRecord


@dataclass
class Prediction:
    """A predicted Turner Level 4 code for one non-Level4 wall."""

    wall: WallRecord
    predicted_code: str
    description: str
    confidence: float
    tier: int                      # 1 (high) / 2 (medium) / 3 (low) — see codes.confidence_to_tier
    method: str                    # "similarity" | "heuristic_category" | "heuristic_category_crosswalk" | "heuristic_function" | "heuristic_name" | "default"
    matched_from: Optional[str]    # type_name of the best-scoring reference wall


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


def _heuristic_signals(wall: WallRecord) -> list[tuple[str, str, str, float]]:
    """Collect every independent heuristic signal that fires for this wall.

    Ordered strongest-first: Revit's own category assignment (authoritative,
    not a guess), then the Function parameter, then a type-name/family
    keyword match. Each entry is (code, description, method, base_confidence)
    — the first entry decides the prediction itself (see _heuristic_predict);
    any others are used only to corroborate or conflict with it.
    """
    signals: list[tuple[str, str, str, float]] = []

    if "curtain" in wall.category.lower():
        # Revit's category alone can't distinguish true structural curtain
        # wall (B2010.40) from a storefront/window-wall system filed under a
        # different Uniformat section entirely (B2020 "Exterior Windows") —
        # both get modelled under the same generic "Curtain Systems"/
        # "Curtain Panels"/"Curtain Wall Mullions" categories. If this wall
        # already carries a legacy code whose section disagrees with B2010,
        # trust that over the bare category guess (see codes.legacy_code_section
        # and CURTAIN_LEGACY_CROSSWALK_CONFIDENCE) — but only at Tier 2, since
        # this is a plausible domain read, not a confirmed crosswalk.
        legacy_section = legacy_code_section(wall.assembly_code) if wall.is_coded else None
        if legacy_section and legacy_section != "B2010":
            signals.append((
                "B2020.30",
                "Exterior Window Wall",
                "heuristic_category_crosswalk",
                CURTAIN_LEGACY_CROSSWALK_CONFIDENCE,
            ))
        else:
            signals.append((
                "B2010.40",
                "Fabricated Exterior Wall Assemblies (Curtain Wall)",
                "heuristic_category",
                METHOD_CONFIDENCE["heuristic_category"],
            ))

    func_lower = wall.function.lower().strip()
    for keyword, (code, desc) in FUNCTION_TO_CODE.items():
        if keyword in func_lower:
            signals.append((code, desc, "heuristic_function", METHOD_CONFIDENCE["heuristic_function"]))
            break

    # type_name + family only — deliberately excludes wall.function. Every
    # FUNCTION_TO_CODE keyword (exterior/interior/retaining/foundation/
    # curtain) also appears verbatim in HEURISTIC_MAP mapped to the same
    # code, so if function's own text were included here, a Function-param
    # match would almost always "corroborate" itself via this second loop —
    # not a genuinely independent signal, just the same data point restated.
    # Keeping this to type_name/family means a keyword hit here reflects
    # what whoever modeled the wall actually named it, an independent check
    # against what Revit's Function parameter says.
    combined = f"{wall.type_name} {wall.family}".lower()
    for keyword, code, desc in HEURISTIC_MAP:
        if keyword in combined:
            signals.append((code, desc, "heuristic_name", METHOD_CONFIDENCE["heuristic_name"]))
            break

    return signals


def _heuristic_predict(wall: WallRecord) -> tuple[str, str, str, float]:
    """Return (code, description, method, confidence) for one wall.

    The strongest signal (category > Function param > keyword match — see
    _heuristic_signals) decides the predicted code and method. Confidence
    starts at that signal's base trust level (codes.METHOD_CONFIDENCE) and is
    then adjusted per-object: nudged up toward CORROBORATION_CAP if a weaker,
    independent signal on the same wall agrees with it, nudged down by
    CONFLICT_PENALTY if one contradicts it instead. Two walls classified by
    the same method can end up with different confidence — that's the point;
    it's no longer purely a lookup by method.
    """
    signals = _heuristic_signals(wall)
    if not signals:
        return DEFAULT_CODE[0], DEFAULT_CODE[1], "default", METHOD_CONFIDENCE["default"]

    code, desc, method, confidence = signals[0]
    others = signals[1:]

    if any(s[0] == code for s in others):
        confidence = min(CORROBORATION_CAP, confidence + CORROBORATION_BONUS)
    elif any(s[0] != code for s in others):
        confidence = max(0.0, confidence - CONFLICT_PENALTY)

    return code, desc, method, round(confidence, 3)


def predict_codes(walls: list[WallRecord], threshold: float) -> list[Prediction]:
    """Predict Turner Level 4 codes for every wall that isn't already Level4-coded.

    Prediction targets: any wall where `is_level4_coded` is False — that's
    both truly blank walls AND walls with an existing non-Level4 code (e.g.
    legacy ASTM Uniformat II like B2010160). Direction as of 2026-08-12: the
    fuzzy match/heuristic runs and is applied for ALL of these, with a real
    confidence score and Tier rating recorded — not silently skipped. An
    earlier version of this function left ASTM-coded walls untouched and
    flagged them "needs review" instead of predicting; that undersells what
    the heuristic can already do (it works off the wall's own
    type_name/family/function, which is just as informative whether or not
    the wall happens to have an old-format code) and isn't the intended POC
    outcome. The original code is preserved by the caller (see
    speckle_io.imprint_predictions) for traceability — nothing is discarded,
    it's recorded alongside the new prediction.

    Reference pool (for similarity matching): any wall that already carries
    a code, in ANY format. A wall is never compared against itself. If the
    best-scoring reference is itself not Level4-coded, its raw code is NOT
    handed out as a "confident" match (that would just propagate one
    non-Turner code onto another wall) — falls back to the heuristic instead,
    keeping the match for traceability via `matched_from`.

    Auto-apply, no gating: everything above gets an entry in the returned
    list and is imprinted regardless of confidence/tier. Tier is recorded so
    a future pass can gate on it (e.g. auto-accept Tier 1, human review
    Tier 3) — that gate is the direction of travel, not implemented here.
    """
    reference  = [w for w in walls if w.is_coded]
    needs_pred = [w for w in walls if not w.is_level4_coded]
    predictions: list[Prediction] = []

    for wall in needs_pred:
        best_score = 0.0
        best_ref: Optional[WallRecord] = None

        for ref in reference:
            if ref.object_id == wall.object_id:
                continue  # never match a wall against itself
            score = fingerprint_similarity(wall, ref)
            if score > best_score:
                best_score = score
                best_ref   = ref

        if best_ref and best_score >= threshold:
            # Similarity match: if the reference wall is itself not
            # Level4-coded, we can't hand its raw code to another wall as a
            # "confident" Level 4 prediction — fall back to the heuristic
            # instead, but keep the match for traceability.
            if best_ref.is_level4_coded:
                confidence = round(best_score, 3)
                predictions.append(Prediction(
                    wall=wall,
                    predicted_code=best_ref.assembly_code,  # type: ignore[arg-type]
                    description=f"Matched to '{best_ref.type_name}'",
                    confidence=confidence,
                    tier=confidence_to_tier(confidence),
                    method="similarity",
                    matched_from=best_ref.type_name,
                ))
                continue

        code, desc, method, confidence = _heuristic_predict(wall)
        predictions.append(Prediction(
            wall=wall,
            predicted_code=code,
            description=desc,
            confidence=confidence,
            tier=confidence_to_tier(confidence),
            method=method,
            matched_from=best_ref.type_name if best_ref else None,
        ))

    return predictions
