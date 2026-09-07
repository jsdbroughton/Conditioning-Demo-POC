"""Level 4 codes for everything that is not a wall — same engine, new table.

2026-09-07 (later still). Direction: the 'Conditioned/All/<source>' model
should carry a code on every object it honestly can, not `not conditioned`
on everything that isn't a wall. The client's reference structure
(acme_reference.ACME_CODES, 526 Level 4 codes) has a section for every
category below; what was missing was a derivation rule.

The principle this has to honour — restated on the day, and it is the whole
point of the exercise: **no single field is trusted on its own.** Not
category, not Assembly Code, not family/type, not Type Mark. A first draft
of this module was a category → code lookup with Function and a keyword as
tie-breakers; that is exactly the single-signal shortcut the wall engine
exists to avoid, and it was thrown away. What's here instead is the wall
engine's own mechanism (predict.py, 2026-08-12) applied to a new table:

  1. Collect every INDEPENDENT signal that fires for the object —
       - Revit's category, via CATEGORY_RULES (heuristic_category, 0.85, or
         the rule's own lower `default_confidence` where the Level 4 choice
         within the section is a sound default rather than a determination);
       - the Function parameter, where the rule maps it (heuristic_function,
         0.75 — Interior/Exterior chooses the section for doors/windows);
       - a type-name/family keyword (heuristic_name, 0.50);
       - the SECTION of any Assembly Code already on the object, legacy or
         otherwise (legacy_code, CURTAIN_LEGACY_CROSSWALK_CONFIDENCE — the
         same trust the wall engine gives a legacy code's section);
       - the nearest already-Level-4-coded object in the SAME category, by
         type/family/function/Type-Mark token similarity (similarity — the
         reference-pool match that is the wall engine's first choice, with
         the same nearest-or-nothing rule and threshold).
  2. Similarity wins outright when it clears SIMILARITY_MATCH_THRESHOLD,
     as for walls. Otherwise the strongest heuristic signal decides the
     section; a weaker signal that agrees on section but names a more
     specific Level 4 refines the code (an "exterior" door that the name
     calls "overhead" is B2050.30, not B2050.10) and counts as
     corroboration; a signal naming a DIFFERENT section is a conflict.
  3. Confidence moves by codes.CORROBORATION_BONUS / CONFLICT_PENALTY /
     CORROBORATION_CAP — identical constants, so a door and a wall sit on
     one scale a reviewer already reads.
  4. No signal at all → None → `not conditioned`. There is no DEFAULT_CODE
     for non-walls: a visible blank beats a wrong-but-plausible code.
     Rooms, Areas, Levels, Grids, Generic Models, Specialty Equipment and
     unrecognised Mechanical Equipment land here by design.

Type Mark is deliberately a similarity-fingerprint field and NOT a code
signal: marks (D1, W3) are drawing references, not classification, and the
2026-09-07 wall work already showed one mark spanning several ratings.

CATEGORY_RULES itself is a TABLE OF JUDGEMENTS made without the estimator in
the room — same status as the height bands in attributes.py. Every result
carries `Requires Verification: True` and a plain-English source; the
estimator should read the table once and correct rows, and nothing else
needs to change to pick up a correction.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from conditioning.codes import (
    ACME_CODES,
    CONFLICT_PENALTY,
    CORROBORATION_BONUS,
    CORROBORATION_CAP,
    CURTAIN_LEGACY_CROSSWALK_CONFIDENCE,
    LEVEL4_PATTERN,
    METHOD_CONFIDENCE,
    SIMILARITY_MATCH_THRESHOLD,
    confidence_to_tier,
    legacy_code_section,
)
from conditioning.predict import _tokens
from conditioning.walls import _param

# Categories that are not physical construction and so can never carry a
# cost code — the honest output for these is "not applicable", not "not yet".
# Matched by lower-cased substring against the Revit category name.
NON_PHYSICAL_CATEGORY_MARKERS = (
    "room", "area", "space", "zone", "level", "grid", "separation",
    "reference", "view", "sheet", "scope box", "matchline",
)


def is_non_physical(category: str | None) -> bool:
    """True for Rooms, Areas, Levels, Grids, separation lines and the like."""
    lower = (category or "").lower()
    return any(marker in lower for marker in NON_PHYSICAL_CATEGORY_MARKERS)


# Confidence for a category default whose Level 4 choice is a sound reading
# within the right section rather than a determination — Tier 2 by design.
DEFAULT_RULE_CONFIDENCE = 0.70


@dataclass(frozen=True)
class CategoryRule:
    """How one Revit category contributes signals.

    `default` is the category signal's code; None means category alone says
    nothing codable (a Door needs Function, a keyword, a legacy code or a
    coded neighbour to be placed at all). `by_function` keys are lower-cased
    `Construction.Function` values. `by_keyword` is checked in order against
    the lower-cased type name + family; first hit is the name signal.
    """

    default: str | None
    default_confidence: float = METHOD_CONFIDENCE["heuristic_category"]
    by_function: dict[str, str] = field(default_factory=dict)
    by_keyword: tuple[tuple[str, str], ...] = ()
    note: str = ""


_DEF = DEFAULT_RULE_CONFIDENCE

# Revit category → rule. Ordered roughly by UniFormat division for reading.
CATEGORY_RULES: dict[str, CategoryRule] = {
    # ── A / B substructure & superstructure ─────────────────────────────────
    "Structural Foundations": CategoryRule(
        default="A1010.30", default_confidence=_DEF,
        by_keyword=(
            ("mat", "A1010.40"), ("raft", "A1010.40"),
            ("pile", "A1020.10"), ("caisson", "A1020.20"),
            ("strip", "A1010.10"), ("wall", "A1010.10"),
            ("pad", "A1010.30"), ("footing", "A1010.30"),
        ),
        note="Isolated (column) footing is the common default; the name "
             "picks mat/pile/strip where it says so.",
    ),
    "Floors": CategoryRule(
        default="B1010.20", default_confidence=_DEF,
        by_keyword=(("slab on grade", "A4010.10"), ("sog", "A4010.10"),
                    ("on grade", "A4010.10")),
        note="Suspended deck/slab/topping. A ground-bearing slab is A4010.10 "
             "and only the name can say so — Tier 2 for that reason.",
    ),
    "Structural Framing": CategoryRule(
        default="B1010.10", default_confidence=_DEF,
        by_keyword=(("roof", "B1020.10"),),
        note="Floor frame unless named roof; level alone can't tell.",
    ),
    "Structural Columns": CategoryRule(default="B1010.10"),
    "Columns": CategoryRule(
        default="C1010.90", default_confidence=_DEF,
        note="Architectural (non-structural) column — partition-related "
             "enclosure/furring, not superstructure.",
    ),
    "Roofs": CategoryRule(
        default="B1020.20", default_confidence=_DEF,
        note="Roof deck/slab/sheathing. The Revit roof also carries the "
             "membrane (B3010.x) — one element, two sections; deck chosen.",
    ),
    "Stairs": CategoryRule(default="B1080.10"),
    "Railings": CategoryRule(
        default="B1080.50", default_confidence=_DEF,
        by_keyword=(("guard", "B2080.50"), ("balcony", "B2080.50"),
                    ("handrail", "C1090.10"), ("wall rail", "C1090.10")),
        note="Stair railing unless named as a handrail/balcony guard.",
    ),
    "Ramps": CategoryRule(default="B1010.20", default_confidence=_DEF),
    # ── B2 exterior / C1 interior openings — Function decides the section ────
    "Doors": CategoryRule(
        default=None,
        by_function={"exterior": "B2050.10", "interior": "C1030.10"},
        by_keyword=(
            ("overhead", "B2050.30"), ("roll", "B2050.30"),
            ("coiling", "C1030.40"), ("sliding", "C1030.25"),
            ("folding", "C1030.30"), ("access panel", "C1030.80"),
            ("access door", "C1030.80"),
        ),
        note="Category alone cannot choose exterior (B2050) vs interior "
             "(C1030); entrance/swinging is the Level 4 default once it can.",
    ),
    "Windows": CategoryRule(
        default=None,
        by_function={"exterior": "B2020.20", "interior": "C1020.10"},
        by_keyword=(("operable", "B2020.10"), ("casement", "B2020.10"),
                    ("awning", "B2020.10"), ("hopper", "B2020.10"),
                    ("skylight", "B3060.10")),
        note="Exterior defaults to Fixed; a keyword marks it Operating.",
    ),
    # ── C1 interior construction / E2 furnishings / G2 site ──────────────────
    "Ceilings": CategoryRule(
        default="C1070.10", default_confidence=_DEF,
        by_keyword=(("act", "C1070.10"), ("acoustic", "C1070.10"),
                    ("tile", "C1070.10"), ("gwb", "C1070.20"),
                    ("gypsum", "C1070.20"), ("plaster", "C1070.20"),
                    ("wood", "C1070.50"), ("metal", "C1070.50")),
        note="Acoustical tile is the common default; GWB where named.",
    ),
    "Casework": CategoryRule(default="E2010.30"),
    "Furniture": CategoryRule(default="E2050.30"),
    "Furniture Systems": CategoryRule(default="E2050.30"),
    "Planting": CategoryRule(default="G2080.30"),
    # ── D2 plumbing / D4 fire ────────────────────────────────────────────────
    "Plumbing Fixtures": CategoryRule(default="D2010.60"),
    "Pipes": CategoryRule(
        default=None,
        by_keyword=(
            ("sanitary", "D2020.30"), ("waste", "D2020.30"), ("vent", "D2020.30"),
            ("storm", "D2030.20"), ("rain", "D2030.20"),
            ("sprinkler", "D4010.10"), ("fire", "D4010.10"),
            ("chilled", "D3050.10"), ("hydronic", "D3050.10"),
            ("heating water", "D3050.10"), ("hot water return", "D2010.40"),
            ("domestic", "D2010.40"), ("cold water", "D2010.40"),
            ("hot water", "D2010.40"), ("potable", "D2010.40"),
            ("gas", "D3010.10"), ("fuel", "D3010.10"),
        ),
        note="A pipe's section is its system — codable only when the type/"
             "system name says which.",
    ),
    "Pipe Fittings": CategoryRule(default="D2010.90", default_confidence=_DEF),
    "Pipe Accessories": CategoryRule(default="D2010.90", default_confidence=_DEF),
    "Sprinklers": CategoryRule(default="D4010.10"),
    # ── D3 HVAC ──────────────────────────────────────────────────────────────
    "Ducts": CategoryRule(default="D3050.50"),
    "Duct Fittings": CategoryRule(default="D3050.60"),
    "Duct Accessories": CategoryRule(default="D3050.60"),
    "Air Terminals": CategoryRule(default="D3050.60"),
    "Mechanical Equipment": CategoryRule(
        default=None,
        by_keyword=(
            ("boiler", "D3020.10"), ("furnace", "D3020.10"),
            ("chiller", "D3030.10"), ("cooling tower", "D3030.10"),
            ("air handl", "D3050.50"), ("ahu", "D3050.50"), ("rtu", "D3050.50"),
            ("fan", "D3060.30"), ("exhaust", "D3060.30"),
            ("vav", "D3050.60"), ("fcu", "D3020.70"), ("fan coil", "D3020.70"),
            ("unit heater", "D3020.70"), ("split", "D3030.70"),
            ("pump", "D3050.10"), ("water heater", "D2010.20"),
            ("generator", "D5010.10"), ("transformer", "D5020.30"),
            ("switchgear", "D5020.30"), ("panel", "D5020.30"),
        ),
        note="Too broad for one code — only the name, a legacy code or a "
             "coded neighbour can place it.",
    ),
    # ── D5 electrical / D6 comms / D7 safety / D1 conveying ──────────────────
    "Lighting Fixtures": CategoryRule(default="D5040.50"),
    "Lighting Devices": CategoryRule(default="D5040.10"),
    "Electrical Fixtures": CategoryRule(default="D5030.50", default_confidence=_DEF),
    "Electrical Equipment": CategoryRule(
        default="D5020.30", default_confidence=_DEF,
        by_keyword=(("generator", "D5010.10"), ("transfer switch", "D5010.70"),
                    ("ups", "D5010.60"), ("battery", "D5010.20")),
    ),
    "Cable Trays": CategoryRule(default="D5030.10"),
    "Conduits": CategoryRule(default="D5030.10"),
    "Data Devices": CategoryRule(default="D6005.30"),
    "Communication Devices": CategoryRule(default="D6005.30"),
    "Fire Alarm Devices": CategoryRule(default="D7050.10"),
    "Security Devices": CategoryRule(default="D7010.10", default_confidence=_DEF),
    "Nurse Call Devices": CategoryRule(default="D6060.30"),
    "Elevators": CategoryRule(default="D1010.10"),
}


@dataclass(frozen=True)
class ElementRecord:
    """The generic Revit fields the engine reads off any non-wall object.

    The same fields the wall engine fingerprints on (walls.WallRecord), minus
    width — read once per object so classification never touches the bundle
    twice.
    """

    obj: object
    object_id: str
    category: str
    type_name: str
    family: str
    function: str
    type_mark: str
    assembly_code: str | None

    @property
    def is_level4_coded(self) -> bool:
        """True if the object already carries a valid client Level 4 code."""
        code = self.assembly_code
        return bool(code and LEVEL4_PATTERN.match(code) and code in ACME_CODES)

    @property
    def tokens(self) -> set[str]:
        """Similarity fingerprint — the wall engine's text fields, minus width."""
        return _tokens(
            f"{self.type_name} {self.family} {self.function} {self.type_mark}"
        )


@dataclass(frozen=True)
class CategoryResult:
    """One non-wall object's derived (or pre-existing) Level 4 code."""

    object_id: str
    category: str
    code: str
    confidence: float
    tier: int
    method: str
    basis: str
    original_code: str | None = None
    matched_from: str | None = None

    @property
    def description(self) -> str:
        """The client's own description text for `code`."""
        return ACME_CODES.get(self.code, "")


def read_element(obj) -> ElementRecord | None:
    """Read the generic fields off a bundle object; None without id/category."""
    category = obj.get_string("category")
    if not category or not obj.application_id:
        return None
    raw_code = _param(obj, "Identity Data", "Assembly Code")
    return ElementRecord(
        obj=obj,
        object_id=obj.application_id,
        category=category,
        type_name=str(obj.get_string("type") or "").strip(),
        family=str(obj.get_string("family") or "").strip(),
        function=str(_param(obj, "Construction", "Function") or "").strip(),
        type_mark=str(_param(obj, "Identity Data", "Type Mark") or "").strip(),
        assembly_code=str(raw_code).strip().upper() or None if raw_code else None,
    )


# (code, method, base_confidence, plain-English evidence)
_Signal = tuple[str, str, float, str]


def _signals(element: ElementRecord, rule: CategoryRule) -> list[_Signal]:
    """Every independent heuristic signal for `element`, strongest first.

    Mirrors predict._heuristic_signals: each entry comes from a DIFFERENT
    Revit fact, so agreement between two of them is real corroboration and
    not the same datum restated.
    """
    signals: list[_Signal] = []
    if rule.default is not None:
        signals.append((
            rule.default, "heuristic_category", rule.default_confidence,
            f"Revit's own element category ({element.category})",
        ))
    function = element.function.lower()
    if function and function in rule.by_function:
        signals.append((
            rule.by_function[function], "heuristic_function",
            METHOD_CONFIDENCE["heuristic_function"],
            f"the Revit Function parameter ({element.function})",
        ))
    if element.assembly_code and not element.is_level4_coded:
        section = legacy_code_section(element.assembly_code)
        if section:
            # A legacy code only vouches for its SECTION (see the curtain-wall
            # crosswalk in predict.py) — represented as the section's most
            # generic Level 4 so it can agree/disagree on section below.
            signals.append((
                f"{section}.10", "legacy_code",
                CURTAIN_LEGACY_CROSSWALK_CONFIDENCE,
                f"the section of the existing code {element.assembly_code}",
            ))
    name = f"{element.type_name} {element.family}".lower()
    for keyword, code in rule.by_keyword:
        if keyword in name:
            signals.append((
                code, "heuristic_name", METHOD_CONFIDENCE["heuristic_name"],
                f"a keyword in the element type name ({keyword!r})",
            ))
            break
    signals.sort(key=lambda s: -s[2])
    return signals


def _nearest_coded(
    element: ElementRecord, references: list[ElementRecord], threshold: float
) -> tuple[ElementRecord, float] | None:
    """Nearest already-Level-4-coded object of the same category, or None.

    Jaccard over the wall engine's text fields; nearest-or-nothing exactly
    as predict._predict_one — a weaker match than the one rejected is a
    weaker claim, not a better one.
    """
    tokens = element.tokens
    if not tokens:
        return None
    best: tuple[ElementRecord, float] | None = None
    for ref in references:
        if ref.object_id == element.object_id:
            continue
        ref_tokens = ref.tokens
        union = len(tokens | ref_tokens)
        score = len(tokens & ref_tokens) / union if union else 0.0
        if best is None or score > best[1]:
            best = (ref, score)
    return best if best and best[1] >= threshold else None


def classify_element(
    element: ElementRecord,
    references: list[ElementRecord],
    threshold: float = SIMILARITY_MATCH_THRESHOLD,
) -> CategoryResult | None:
    """Derive one non-wall object's code; None when nothing can place it."""
    rule = CATEGORY_RULES.get(element.category)
    if rule is None:
        return None

    if element.is_level4_coded:
        return CategoryResult(
            object_id=element.object_id, category=element.category,
            code=element.assembly_code or "", confidence=1.0, tier=0,
            method="existing", basis="authored — already a valid Level 4 code",
        )

    nearest = _nearest_coded(element, references, threshold)
    if nearest is not None:
        ref, score = nearest
        confidence = round(score, 3)
        return CategoryResult(
            object_id=element.object_id, category=element.category,
            code=ref.assembly_code or "", confidence=confidence,
            tier=confidence_to_tier(confidence), method="similarity",
            basis=f"a close match to another {element.category} element "
                  f"already carrying a code ('{ref.type_name}')",
            original_code=element.assembly_code,
            matched_from=ref.type_name,
        )

    signals = _signals(element, rule)
    if not signals:
        return None

    code, method, confidence, basis = signals[0]
    agreeing: list[str] = []
    conflicting: list[str] = []
    for other_code, _method, _conf, other_basis in signals[1:]:
        if other_code[:5] == code[:5]:
            agreeing.append(other_basis)
            # Same section, more specific Level 4 than the deciding signal's
            # generic default → refine. Never crosses a section boundary.
            if other_code != code and _method != "legacy_code":
                code = other_code
        else:
            conflicting.append(other_basis)

    if agreeing:
        confidence = min(CORROBORATION_CAP, confidence + CORROBORATION_BONUS)
        basis += ", corroborated by " + " and ".join(agreeing)
    elif conflicting:
        confidence = max(0.0, confidence - CONFLICT_PENALTY)
        basis += ", contradicted by " + " and ".join(conflicting)
    confidence = round(confidence, 3)

    return CategoryResult(
        object_id=element.object_id, category=element.category, code=code,
        confidence=confidence, tier=confidence_to_tier(confidence),
        method=method, basis=basis, original_code=element.assembly_code,
    )


def classify_categories(
    model, exclude_ids: set[str], threshold: float = SIMILARITY_MATCH_THRESHOLD
) -> list[CategoryResult]:
    """Classify every non-wall object in `model` the rules can place.

    `exclude_ids` is the wall set (walls.collect_walls()) — those have their
    own, richer engine and must never be double-coded here. The reference
    pool for similarity is per category: only an already-coded Door can
    vouch for a Door.
    """
    elements: list[ElementRecord] = []
    for obj in model.objects:
        if obj.application_id in exclude_ids:
            continue
        element = read_element(obj)
        if element is not None and element.category in CATEGORY_RULES:
            elements.append(element)

    references: dict[str, list[ElementRecord]] = {}
    for element in elements:
        if element.is_level4_coded:
            references.setdefault(element.category, []).append(element)

    results: list[CategoryResult] = []
    for element in elements:
        result = classify_element(
            element, references.get(element.category, []), threshold
        )
        if result is not None:
            results.append(result)

    print(
        f"[ConditioningPOC] Category engine placed {len(results)} of "
        f"{len(elements)} non-wall objects in {len(CATEGORY_RULES)} known "
        f"categories ({len({r.category for r in results})} categories hit)."
    )
    return results
