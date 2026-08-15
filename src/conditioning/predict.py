"""The prediction engine: fingerprint similarity + heuristic fallback.

Produces Prediction objects for every wall that doesn't already carry an
ACME Level 4 code — that covers both walls with no code at all AND walls
with an existing non-Level4 code (e.g. legacy ASTM Uniformat II). Both get a
real, method-based confidence score and Tier 1/2/3 rating; nothing is
silently defaulted to 0 confidence and nothing gets skipped. See
predict_codes() docstring for the full reasoning.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import NamedTuple

from conditioning.codes import (
    CONFLICT_PENALTY,
    CORROBORATION_BONUS,
    CORROBORATION_CAP,
    CURTAIN_LEGACY_CROSSWALK_CONFIDENCE,
    DEFAULT_CODE,
    FUNCTION_TO_CODE,
    HEURISTIC_MAP,
    METHOD_CONFIDENCE,
    SIMILARITY_MATCH_THRESHOLD,
    confidence_to_tier,
    legacy_code_section,
)
from conditioning.walls import WallRecord


@dataclass
class Prediction:
    """A predicted ACME Level 4 code for one non-Level4 wall."""

    wall: WallRecord
    predicted_code: str
    description: str
    confidence: float
    # 1 (high) / 2 (medium) / 3 (low) — see codes.confidence_to_tier
    tier: int
    # "similarity" | "heuristic_category" | "heuristic_category_crosswalk" |
    # "heuristic_function" | "heuristic_name" | "default"
    method: str
    matched_from: str | None    # type_name of the best-scoring reference wall


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

# The text fields compared as token sets, and their weights, flattened into a
# positional tuple. _Fingerprint.tokens is built in this same order so the
# scoring loop indexes straight into it — no per-comparison dict lookup or
# getattr.
_TEXT_FIELDS = ("type_name", "family", "function", "type_mark")
_TEXT_WEIGHTS = tuple((i, _WEIGHTS[f]) for i, f in enumerate(_TEXT_FIELDS))
_WIDTH_WEIGHT = _WEIGHTS["width_mm"]


def fingerprint_key(wall: WallRecord) -> tuple:
    """Every field prediction actually reads off a wall, as a hashable tuple.

    Two walls with an equal key are indistinguishable to BOTH
    fingerprint_similarity() (type_name/family/function/type_mark/width_mm)
    and _heuristic_signals() (category/function/type_name/family/
    assembly_code), so they must produce an identical prediction. That's what
    lets predict_codes() compute once per distinct fingerprint and fan the
    result out, instead of repeating identical work once per element — the
    difference between 60 predictions and 31,483 on a real model.

    Anything added to the prediction inputs must be added here too, or walls
    that now differ would silently share a cached result.
    """
    return (
        wall.type_name,
        wall.family,
        wall.function,
        wall.type_mark,
        wall.width_mm,
        wall.category,
        wall.assembly_code,
    )


class _Fingerprint:
    """A wall's similarity inputs, tokenised once.

    The tokenisation used to happen inside the similarity inner loop — eight
    `re.findall` calls per pair — so a run scoring n×m pairs paid for the
    same handful of distinct type names millions of times over. Hoisting it
    here makes tokenisation O(distinct walls) instead of O(comparisons).
    """

    __slots__ = ("tokens", "width_mm")

    def __init__(self, wall: WallRecord) -> None:
        self.tokens = tuple(
            _tokens(getattr(wall, f, "") or "") for f in _TEXT_FIELDS
        )
        self.width_mm = wall.width_mm


def _similarity(a: _Fingerprint, b: _Fingerprint) -> float:
    """Weighted Jaccard over the token sets + proportional width match."""
    score = 0.0
    a_tokens, b_tokens = a.tokens, b.tokens
    for i, weight in _TEXT_WEIGHTS:
        t1, t2 = a_tokens[i], b_tokens[i]
        union = len(t1 | t2)
        if union:
            score += weight * (len(t1 & t2) / union)
    w1, w2 = a.width_mm, b.width_mm
    if w1 > 0 and w2 > 0:
        score += _WIDTH_WEIGHT * (min(w1, w2) / max(w1, w2))
    return score


def fingerprint_similarity(a: WallRecord, b: WallRecord) -> float:
    """Weighted Jaccard similarity over text fields + proportional width match.

    Kept as the module's public, WallRecord-level entry point. The hot path
    in predict_codes() works on pre-tokenised _Fingerprint objects instead —
    this wrapper tokenises both walls on every call, which is exactly the
    cost that made the old O(n×m) loop unusable.
    """
    return _similarity(_Fingerprint(a), _Fingerprint(b))


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

    category_is_curtain = "curtain" in wall.category.lower()

    if category_is_curtain:
        # Revit's category alone can't distinguish true structural curtain
        # wall (B2010.40) from a storefront/window-wall system filed under a
        # different Uniformat section entirely (B2020 "Exterior Windows") —
        # both get modelled under the same generic "Curtain Systems"/
        # "Curtain Panels"/"Curtain Wall Mullions" categories. If this wall
        # already carries a legacy code whose section disagrees with B2010,
        # trust that over the bare category guess (see codes.legacy_code_section
        # and CURTAIN_LEGACY_CROSSWALK_CONFIDENCE) — but only at Tier 2, since
        # this is a plausible domain read, not a confirmed crosswalk.
        legacy_section = (
            legacy_code_section(wall.assembly_code) if wall.is_coded else None
        )
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
            # A Function of "Curtain" on an element Revit already filed under
            # a curtain category is the same fact restated, not a second
            # opinion — Revit sets that Function *because* of the category.
            # Counting it separately let CORROBORATION_BONUS lift every
            # curtain element from 0.85 to 0.95, i.e. to the top of the
            # confidence scale, on one piece of evidence. A wall type
            # literally named "Empty" was scoring 0.95 and Tier 1 that way.
            #
            # This is the same self-corroboration trap already documented
            # below for the type-name keyword loop (2026-08-12), which was
            # fixed there and missed here. A Function that DISAGREES with the
            # category still fires — that is a real conflict and should cost
            # confidence, which is exactly what happens.
            if category_is_curtain and keyword == "curtain":
                break
            signals.append(
                (code, desc, "heuristic_function",
                 METHOD_CONFIDENCE["heuristic_function"])
            )
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
            signals.append(
                (code, desc, "heuristic_name", METHOD_CONFIDENCE["heuristic_name"])
            )
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


class _Outcome(NamedTuple):
    """A prediction with the wall stripped off.

    This is the part that depends only on the fingerprint, and is therefore
    safe to cache and reuse across every wall sharing it. Field names match
    Prediction's so it can be splatted straight into one.
    """

    predicted_code: str
    description: str
    confidence: float
    tier: int
    method: str
    matched_from: str | None


class _RefClass(NamedTuple):
    """One distinct reference fingerprint.

    Stands in for every coded wall that shares it. `first_idx`/`second_idx`
    are those walls' positions in the original list — needed only to
    reproduce the original tie-breaking exactly (see _predict_one).
    """

    key: tuple
    fingerprint: _Fingerprint
    wall: WallRecord
    count: int
    first_idx: int
    second_idx: int


def _predict_one(
    wall: WallRecord,
    key: tuple,
    is_first_of_class: bool,
    references: list[_RefClass],
    threshold: float,
) -> _Outcome:
    """Predict for a single distinct fingerprint (see predict_codes).

    Ties on score are common and decide real outcomes — walls of one type
    differ only in their code, and any wall with width 0 has every score
    capped at 0.90. The original implementation resolved them by scanning
    the wall list in order and keeping the first maximum, i.e. "the
    earliest-emitted coded wall that is joint-nearest, excluding myself".
    That rule is arbitrary (it depends on Revit's emission order) but it is
    the existing behaviour, and changing it is not a performance decision —
    breaking ties toward Level4 references instead looks obviously better
    and moves 1,291 of 2,000 predictions on a mixed-code model. So it is
    reproduced here exactly, by ranking on (score, -effective_index) rather
    than relying on iteration order.
    """
    best_score = 0.0
    best_rank: tuple[float, int] = (0.0, 0)
    best_ref: WallRecord | None = None

    if references:
        fp = _Fingerprint(wall)
        for ref in references:
            # Never match a wall against itself. Under fingerprint dedup the
            # reference is a *representative* of its class, so identity
            # can't be checked by object_id: if two or more coded walls
            # share this fingerprint then some wall other than the target
            # has it, and matching it is legitimate (the original scored
            # against that sibling). Only a class of exactly one member is
            # necessarily the target itself.
            eff_idx = ref.first_idx
            if ref.key == key:
                if ref.count == 1:
                    continue
                # The target is excluded from its own class, so the earliest
                # *other* member stands in — which shifts this class later
                # in the tie-break order, but only for that one wall.
                if is_first_of_class:
                    eff_idx = ref.second_idx

            score = _similarity(fp, ref.fingerprint)
            rank = (score, -eff_idx)
            if rank > best_rank:
                best_rank  = rank
                best_score = score
                best_ref   = ref.wall

    if best_ref is not None and best_score >= threshold:
        # Nearest-neighbour-or-nothing: if the closest coded wall isn't
        # itself Level4, its raw code can't be handed out as a confident
        # Level 4 prediction, and we do NOT reach past it to a further-away
        # Level4 wall either — a weaker similarity than the one just
        # rejected is a weaker claim, not a better one. Falls through to the
        # heuristic instead, keeping the match for traceability.
        #
        # This is load-bearing and easy to "optimise" away by mistake:
        # restricting the reference pool to Level4 walls up front looks
        # equivalent (and is much faster) but changes real output — it
        # unblocks matches this branch deliberately refuses. Measured on the
        # live model's type distribution with 15% of walls promoted to
        # Level4: 1,317 of 2,000 predictions changed. Kept as-is; the speed
        # comes from deduplication instead, which changes nothing.
        if best_ref.is_level4_coded:
            confidence = round(best_score, 3)
            return _Outcome(
                predicted_code=best_ref.assembly_code,  # type: ignore[arg-type]
                description=f"Matched to '{best_ref.type_name}'",
                confidence=confidence,
                tier=confidence_to_tier(confidence),
                method="similarity",
                matched_from=best_ref.type_name,
            )

    code, desc, method, confidence = _heuristic_predict(wall)
    return _Outcome(
        predicted_code=code,
        description=desc,
        confidence=confidence,
        tier=confidence_to_tier(confidence),
        method=method,
        matched_from=best_ref.type_name if best_ref else None,
    )


def predict_codes(
    walls: list[WallRecord], threshold: float = SIMILARITY_MATCH_THRESHOLD
) -> list[Prediction]:
    """Predict ACME Level 4 codes for every wall that isn't already Level4-coded.

    `threshold` defaults to codes.SIMILARITY_MATCH_THRESHOLD and is no longer
    a user-facing Automate input (removed 2026-08-14 — see the constant's
    comment in codes.py for why). Kept as a parameter, not inlined, purely
    for testability — callers in production should not pass this explicitly.

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
    non-ACME code onto another wall) — falls back to the heuristic instead,
    keeping the match for traceability via `matched_from`.

    Performance (2026-08-14): this used to score every (target, reference)
    pair individually — 31,483 × 30,513 = 960 million comparisons on the
    live model, each re-tokenising both walls from scratch, for ~67 minutes
    of single-core work. It now computes once per distinct *fingerprint*
    (see fingerprint_key) and fans the result out. Real models have far
    fewer wall types than wall instances — 60 distinct fingerprints across
    those 31,483 elements — and walls sharing a fingerprint provably share a
    prediction, since the fingerprint is every input both the similarity
    scorer and the heuristic read. References are deduplicated the same way.
    960M comparisons becomes ~3,600; the stage went from 66.6 minutes to
    0.03 seconds.

    This is a pure speed change — every predicted code, confidence, tier,
    method and matched_from is bit-identical to the old implementation,
    verified by differential-testing both against the live model's type
    distribution. Restricting the reference pool to Level4 walls would be
    faster still and looks equivalent, but is NOT (see the nearest-
    neighbour-or-nothing note in _predict_one).

    Auto-apply, no gating: everything above gets an entry in the returned
    list and is imprinted regardless of confidence/tier. Tier is recorded so
    a future pass can gate on it (e.g. auto-accept Tier 1, human review
    Tier 3) — that gate is the direction of travel, not implemented here.
    """
    needs_pred = [w for w in walls if not w.is_level4_coded]
    if not needs_pred:
        return []

    # Deduplicate the reference pool by fingerprint — identical fingerprints
    # score identically against every target, so keeping more than one is
    # pure repeated work. Tokenise each survivor once, here, rather than on
    # every comparison. The positions are carried through only to reproduce
    # the original tie-breaking (see _predict_one).
    counts: dict[tuple, int] = {}
    firsts: dict[tuple, WallRecord] = {}
    first_idx: dict[tuple, int] = {}
    second_idx: dict[tuple, int] = {}
    for i, ref in enumerate(walls):
        if not ref.is_coded:
            continue
        ref_key = fingerprint_key(ref)
        counts[ref_key] = counts.get(ref_key, 0) + 1
        if ref_key not in firsts:
            firsts[ref_key]     = ref
            first_idx[ref_key]  = i
        elif ref_key not in second_idx:
            second_idx[ref_key] = i

    references = [
        _RefClass(
            key=k,
            fingerprint=_Fingerprint(r),
            wall=r,
            count=counts[k],
            first_idx=first_idx[k],
            second_idx=second_idx.get(k, first_idx[k]),
        )
        for k, r in firsts.items()
    ]

    # Cached on (fingerprint, am-I-the-first-of-my-class) — the second half
    # matters because that one wall alone is excluded from its own class and
    # so tie-breaks differently from its siblings. At most two entries per
    # fingerprint either way.
    cache: dict[tuple, _Outcome] = {}
    predictions: list[Prediction] = []

    for wall in needs_pred:
        key = fingerprint_key(wall)
        is_first = firsts.get(key) is wall
        cache_key = (key, is_first)
        outcome = cache.get(cache_key)
        if outcome is None:
            outcome = _predict_one(wall, key, is_first, references, threshold)
            cache[cache_key] = outcome
        predictions.append(Prediction(wall=wall, **outcome._asdict()))

    return predictions
