"""Uniformat code reference data and code-format detection.

For a construction firm's own estimate-detail structure (anonymized here as "ACME
Studios" — see docs/NOTES.md for the 2026-08-14 anonymization pass).

Source: fixtures/ACME Studios - Uniformat Estimate Detail Structure.xlsx
Sections: A2010 (Subgrade Walls), B2010 (Exterior Walls), B2020 (Exterior
Windows — only enough of this section is included to resolve the curtain
wall / window wall crosswalk below, not the full B2020 family), C1010
(Interior Partitions)

This organisation's own code hierarchy, confirmed directly against the
fixture spreadsheet (2026-08-12, while investigating why a legacy code
wasn't matching a Level 4 sub-code):
  Level 1  "A"              — major group (e.g. Substructure)
  Level 2  "A10"             — group element
  Level 3  "A1010" / "B2010" — individual element (a bare 4-digit section —
                                this is what ACME_CODES' top-level keys are)
  Level 4  "A1010.10"        — sub-element (dot + 1-2 digits) — the level a
                                Revit Assembly Code is typically set to, and
                                the prediction target for this POC
  Level 5  "A1010.10.0100"   — individual estimate/quantity-takeoff line item
                                (dot + 2 digits + dot + 4 digits, with its own
                                QUANTITY/UNIT columns in the source spreadsheet).
                                NOT a per-element classification tag — a single
                                wall assembly typically spans several Level 5
                                line items at once (material + flashing +
                                sealant...), so there's no single "correct"
                                Level 5 code to predict per wall the way there
                                is at Level 4. Not modelled here.

IMPORTANT: In this system curtain walls are B2010.40 ("Fabricated Exterior Wall
Assemblies"), NOT B2050 ("Exterior Doors and Grilles"). This is a common mistake.

The hardcoded ACME_CODES dict below is validated against the source
spreadsheet in tests/test_acme_codes_fixture.py (fixtures/ACME Studios -
Uniformat Estimate Detail Structure.xlsx) — that test is the guardrail
against drift, not a switch to loading codes dynamically. Direction as of
2026-08-12 is to keep this hardcoded for now.
"""

from __future__ import annotations

import re

ACME_CODES: dict[str, str] = {
    # ── A2010 Subgrade / Basement Walls ─────────────────────────────────────
    "A2010":    "Walls for Subgrade Enclosures",
    "A2010.10": "Subgrade Enclosure Wall Construction",
    "A2010.20": "Subgrade Enclosure Wall Interior Skin",
    "A2010.90": "Subgrade Enclosure Wall Supplementary Components",
    # ── B2010 Exterior Walls ─────────────────────────────────────────────────
    "B2010":    "Exterior Walls",
    # masonry, precast, metal panels, GFRC, stone
    "B2010.10": "Exterior Wall Veneer",
    "B2010.20": "Exterior Wall Back-up Construction",  # CMU/metal stud backup
    "B2010.30": "Exterior Wall Interior Skin",
    "B2010.40": "Fabricated Exterior Wall Assemblies",  # ← curtain walls go here
    "B2010.50": "Parapet Back-up Construction",
    "B2010.60": "Equipment Screens",
    "B2010.80": "Exterior Wall Supplementary Components",
    "B2010.90": "Exterior Wall Opening Supplementary Components",
    # ── B2020 Exterior Windows (partial — only the crosswalk target) ─────────
    # storefronts, aluminum window wall — see legacy_code_section() crosswalk below
    "B2020.30": "Exterior Window Wall",
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
ACME_WALL_TARGETS: dict[str, str] = {
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

# Revit Function parameter value → code (most reliable signal)
FUNCTION_TO_CODE: dict[str, tuple[str, str]] = {
    "exterior":   ("B2010.10", "Exterior Wall Veneer"),
    "interior":   ("C1010.10", "Interior Fixed Partitions"),
    "retaining":  ("A2010.10", "Subgrade Enclosure Wall Construction"),
    "foundation": ("A2010.10", "Subgrade Enclosure Wall Construction"),
    "curtain":    ("B2010.40", "Fabricated Exterior Wall Assemblies (Curtain Wall)"),
}

# (keyword_in_combined_text, code, description) — ordered by specificity
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
# compare against (see predict.predict_codes). Ordering matches reliability:
# Revit's own element category (e.g. "Curtain Systems") is the single most
# authoritative signal available — it's not a guess, Revit assigned it — then
# the Function parameter, then keyword matching, then blind default.
METHOD_CONFIDENCE = {
    "heuristic_category": 0.85,
    "heuristic_function": 0.75,
    "heuristic_name": 0.50,
    "default": 0.0,
}

# Four-band human-in-the-loop rating (2026-08-14 direction — Tier 0 added
# alongside the original three, described live on the 2026-07-17 client
# call):
#   Tier 0 — no work to be done. The wall already carries a genuine ACME
#            Level 4 code; nothing was predicted, there's no confidence
#            score to band. Not produced by confidence_to_tier() below —
#            assigned directly wherever a wall's is_level4_coded is True
#            (see speckle_io.imprint_predictions).
#   Tier 1 — high confidence, candidate for auto-accept.
#   Tier 2 — medium confidence, propagate but flag for a quick human check.
#   Tier 3 — the bottom: not enough confidence to trust. Two distinct
#            sub-cases land here, not just one — (a) genuinely no signal at
#            all (`default` method, confidence 0.0 — no clue what this
#            element is, nothing about it resembles anything else in the
#            model), and (b) some signal DID fire but it's too weak to
#            trust on its own (a lone, uncorroborated heuristic_name coin
#            toss at 0.50) or it actively contradicts another signal on the
#            same wall (e.g. the curtain/window-wall crosswalk conflicting
#            with Function, also landing at 0.50). Both are "needs a human
#            to look at it," but for different reasons — (a) is missing
#            data, (b) is untrustworthy or contradictory data.
# As of 2026-08-12 direction: everything is auto-applied regardless of tier
# for this POC — the tier is recorded, not yet enforced as a gate. That gate
# is the direction of travel, not implemented here.
#
# TIER_1_THRESHOLD = 0.85, matching heuristic_category's base confidence —
# NOT heuristic_function's (0.75). Originally set to 0.75, which meant a
# single, uncorroborated Function-parameter match alone was enough to earn
# "Tier 1 — candidate for auto-accept". That's too permissive: one parameter,
# unconfirmed by anything else, isn't the same kind of confidence as Revit's
# own authoritative category assignment. At 0.85, Tier 1 now means either
# an authoritative signal (heuristic_category) on its own, or a heuristic
# match independently corroborated by a second signal on the same wall
# (see CORROBORATION_BONUS below) — a bare heuristic_function match (0.75)
# now lands in Tier 2 unless something else on the wall agrees with it.
TIER_1_THRESHOLD = 0.85
#
# TIER_2_THRESHOLD = 0.55, NOT 0.50. Originally set to 0.50 — exactly
# heuristic_name's base confidence — which meant a bare keyword-only match
# ("no category, no Function param, just a word in the type name") landed
# Tier 2, "propagate but flag for a quick check". Feedback (2026-08-13): 50%
# is a coin toss, not a "medium confidence, quick check" reading — it
# belongs in Tier 3, "needs a human to look at it", alongside the other
# Tier 3 case (the `default` method: no category, no Function match, no
# keyword match at all — literally nothing shared with anything else).
# At 0.55, a bare heuristic_name match (always exactly 0.50 — see
# predict._heuristic_predict: it can only ever be the sole/primary signal
# when nothing else fired, so there's nothing left to corroborate or
# conflict it away from its base) now correctly lands Tier 3. This also
# demotes the one case CURTAIN_LEGACY_CROSSWALK_CONFIDENCE can be pushed
# down to by CONFLICT_PENALTY (0.65 - 0.15 = 0.50) — exactly right, since a
# hardcoded crosswalk guess that ALSO contradicts the wall's own Function
# parameter is precisely the kind of case that deserves a closer look, not
# a quick one.
TIER_2_THRESHOLD = 0.55

# Per-object confidence adjustment for heuristic predictions. METHOD_CONFIDENCE
# above is the base trust in a *signal type* (Revit's own category assignment
# is more reliable than a keyword match) — on its own that makes every wall
# classified by the same method land on an identical score, which isn't a
# real per-object confidence, just a per-method one. These adjust that base
# up or down per wall depending on whether OTHER independent signals on the
# same wall agree or disagree with the strongest one (see
# predict._heuristic_predict): a wall where category, Function, and a type-
# name keyword all point to the same code is more trustworthy than one
# where only a single weak signal fired; a wall where signals actively
# contradict each other (e.g. category says curtain wall but Function says
# "Interior") is a genuine data inconsistency worth flagging with lower
# confidence, not averaging away.
CORROBORATION_BONUS = 0.10
# stays below 1.0 — still a heuristic, never a genuine reference-wall match
CORROBORATION_CAP = 0.95
CONFLICT_PENALTY = 0.15

# Confidence for the curtain-wall-vs-window-wall crosswalk (see
# predict._heuristic_signals and legacy_code_section() below). Revit's
# generic "Curtain Systems"/"Curtain Panels"/"Curtain Wall Mullions"
# categories don't distinguish true structural curtain wall (ACME's
# B2010.40) from storefront/window-wall systems (ACME's B2020.30) — but a
# wall's own pre-existing legacy code sometimes does, when its section
# prefix disagrees with B2010. B2020.30 is a plausible domain read (the
# fixture explicitly lists storefronts/window wall aluminum there), not
# a confirmed ASTM-to-ACME crosswalk — there's no source data mapping the
# ASTM 3-digit suffix to a specific ACME sub-code. Deliberately capped
# below TIER_1_THRESHOLD so this always lands Tier 2 ("suggest but verify"),
# never auto-confident, per 2026-08-13 direction.
CURTAIN_LEGACY_CROSSWALK_CONFIDENCE = 0.65

# Minimum fingerprint-similarity score (predict.fingerprint_similarity) to
# reuse another already-coded wall's exact code as a confident "similarity"
# match, rather than falling through to the heuristic. Was exposed as a
# user-facing Automate input ("Confidence Threshold") through 2026-08-14 —
# removed per direction that a single knob describing itself as gating "a
# model-based prediction" was misleading (there's no trained model, just
# this same-run nearest-neighbour heuristic) and, worse, had no observable
# effect on any real run: a similarity match only counts as confident when
# the winning reference wall is ITSELF genuinely Level4-coded, and every
# model conditioned so far (the target shell model + the 3 other client
# project models) has zero such walls — so this line has never once been the deciding
# factor on
# live data. Kept as a real, named constant rather than an inline literal:
# the code path is real and would start mattering the moment a model shows
# up with pre-existing Level4-coded walls to learn from.
SIMILARITY_MATCH_THRESHOLD = 0.65


def confidence_to_tier(confidence: float) -> int:
    """Band a confidence score into a Tier 1/2/3 rating.

    Never returns 0 — Tier 0 ("no work to be done") isn't a confidence band,
    it's assigned directly for already-Level4-coded walls, which never go
    through prediction/confidence scoring at all. See TIER_LABELS.
    """
    if confidence >= TIER_1_THRESHOLD:
        return 1
    if confidence >= TIER_2_THRESHOLD:
        return 2
    return 3


# Text labels for the tier band, used wherever Tier is written out as a
# property value (e.g. onto Speckle objects) rather than used internally for
# counting/sorting. A raw int (0/1/2/3) reads ambiguously once it's sitting
# in a properties panel or an exported table next to other numeric
# parameters — "Tier 1" is self-explanatory even out of context. A wall's
# tier stays an int internally (see predict.Prediction.tier / the level4
# case in speckle_io.py) since internal logic (counting, thresholds, a
# future auto-accept gate) wants to compare/sort on it.
TIER_LABELS: dict[int, str] = {0: "Tier 0", 1: "Tier 1", 2: "Tier 2", 3: "Tier 3"}


def tier_label(tier: int) -> str:
    """Render a numeric tier (1/2/3) as its display text ('Tier 1')."""
    return TIER_LABELS.get(tier, f"Tier {tier}")


# All conditioning output is written under this single namespaced key inside
# wall.properties, rather than as several flat sibling keys — keeps the
# viewer/report/PowerBI surface predictable (one place to look) and avoids
# ever colliding with a real Revit parameter name.
#
# DEFAULT_CONDITIONING_KEY, not a fixed constant — 2026-08-14 direction: the
# property name is a user-facing Automate input (FunctionInputs.
# code_property_name in main.py) so each deployment can use its own naming
# convention (e.g. a real ACME Studios deployment might set this to
# "ACME UF Code") without hardcoding any specific client's name into this
# function's source.
# This module-level value is only the fallback used when no override is
# passed — see speckle_io.imprint_predictions / create_conditioned_version.
# Unlike the similarity threshold removed the same day (see
# SIMILARITY_MATCH_THRESHOLD below), this one earns its place as a real
# input: it changes something genuinely visible on every single run (the
# literal property key on every wall object), not something that's never
# once affected an output.
DEFAULT_CONDITIONING_KEY = "Conditioned UF Code"

# Matches Level 4 sub-section codes: one capital letter, 4 digits, dot, 1-2 digits
# e.g. B2010.10, C1010.40, A2010.10
LEVEL4_PATTERN = re.compile(r"^[A-Z]\d{4}\.\d{1,2}$")

# Matches codes that look like a Level 4 code with the period accidentally stripped:
# one capital letter, 4 digits, then exactly 2 digits (e.g. B201010, C101010).
# These are candidates for normalisation to B2010.10 form.
# NOTE: ASTM Uniformat II codes use a 3-digit suffix (e.g. B2010160) so they will
# NOT match this pattern — they are a different numbering scheme, not stripped Level 4.
COLLAPSED_LEVEL4_PATTERN = re.compile(r"^([A-Z]\d{4})(\d{2})$")

# Matches legacy ASTM Uniformat II codes: one capital letter, 4 digits, then a
# 3-digit sub-code (e.g. B2010160, C1010145). These get re-predicted to an
# ACME Level 4 code like any other non-Level4 wall (see predict.predict_codes)
# — the original code is preserved alongside the new one for traceability,
# never silently discarded.
ASTM_CODE_PATTERN = re.compile(r"^[A-Z]\d{4}\d{3}$")


def try_normalise_to_level4(code: str) -> str | None:
    """If `code` looks like a Level 4 code with the period stripped.

    e.g. 'B201010', return the normalised form ('B2010.10'). Otherwise return
    None.
    """
    m = COLLAPSED_LEVEL4_PATTERN.match(code.strip())
    if m:
        normalised = f"{m.group(1)}.{m.group(2)}"
        # Only accept if the normalised code is a known ACME Level 4 code
        if normalised in ACME_CODES:
            return normalised
    return None


def legacy_code_section(code: str | None) -> str | None:
    """Return the Uniformat *section* prefix of a legacy code.

    The first 5 characters, e.g. 'B2020' from 'B2020200', or bare 'B2010'
    as-is.

    Used to sanity-check heuristics that assume a specific section (e.g. the
    curtain wall category heuristic assumes B2010 "Exterior Walls") against
    what a wall's own pre-existing legacy code actually says — Revit's
    category alone can't tell true curtain wall apart from a storefront/
    window-wall system filed under a different section (B2020 "Exterior
    Windows"), but a human who originally coded the wall may already have.
    """
    if not code or len(code) < 5:
        return None
    return code[:5]
