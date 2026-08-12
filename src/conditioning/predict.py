"""The prediction engine: fingerprint similarity + heuristic fallback.

Produces Prediction objects for walls with no Assembly Code at all. Walls
that already have a code — in any format — are never prediction targets;
see predict_codes() docstring for why.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from conditioning.codes import DEFAULT_CODE, FUNCTION_TO_CODE, HEURISTIC_MAP, METHOD_CONFIDENCE
from conditioning.walls import WallRecord


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
    """Predict Turner Level 4 codes for walls that have NO code at all.

    Reference pool: any wall that already carries a code, in ANY format —
    Turner Level 4 dot-notation (gold standard) or legacy ASTM Uniformat II
    (e.g. B2010160). Both are real classification signal on the same
    type_name/family/function fingerprint; excluding ASTM walls from the
    reference pool (the previous behaviour) starves similarity matching of
    data on models like Henry Ford Wall Takeoff where NO wall has a
    dot-notation code yet, which is why every prediction there fell through
    to the heuristic with a hardcoded confidence of 0.

    Prediction targets: ONLY walls with no code at all. Walls that already
    have a code — even a non-Level4 one — are never touched here; overwriting
    a specific ASTM sub-code (e.g. the '160' in B2010160) with a generic
    heuristic guess destroys real information and is exactly the regression
    caught live on the 2026-07-17 Turner call. Existing-but-wrong-format
    codes are surfaced separately for manual crosswalk review — see
    WallClassification.non_level4_coded in conditioning.walls.
    """
    reference  = [w for w in walls if w.is_coded]
    needs_pred = [w for w in walls if not w.is_coded]
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
            # Similarity match: if the reference wall is itself ASTM-coded
            # (not yet in Turner Level 4 format), we can't hand its raw code
            # to another wall as a "confident" Level 4 prediction — fall back
            # to the heuristic instead, but keep the match for traceability.
            if best_ref.is_level4_coded:
                predictions.append(Prediction(
                    wall=wall,
                    predicted_code=best_ref.assembly_code,  # type: ignore[arg-type]
                    description=f"Matched to '{best_ref.type_name}'",
                    confidence=round(best_score, 3),
                    method="similarity",
                    matched_from=best_ref.type_name,
                ))
                continue

        code, desc, method = _heuristic_predict(wall)
        predictions.append(Prediction(
            wall=wall,
            predicted_code=code,
            description=desc,
            confidence=METHOD_CONFIDENCE.get(method, 0.0),
            method=method,
            matched_from=best_ref.type_name if best_ref else None,
        ))

    return predictions
