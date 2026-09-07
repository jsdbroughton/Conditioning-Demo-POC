"""Extract WallRecord data from Speckle bundle objects, and classify walls.

Buckets a wall list into coded / level4 / non_level4_coded / uncoded.

"WallRecord" is the umbrella term for any Uniformat-conditionable envelope
element — that's Revit's "Walls" category, plus curtain wall's separate
"Curtain Systems", "Curtain Panels", and "Curtain Wall Mullions" categories.
ACME's own B2010 ("Exterior Walls") Uniformat section already treats
curtain walls as a wall sub-type (B2010.40), so grouping them under one
WallRecord model matches the target taxonomy, even though Revit models them
as distinct categories from plain "Walls" — see TARGET_CATEGORIES below.

2026-09-07: ported off the v3/JSON-object-graph reader onto specklepy
2026.9's columnar bundle format (`operations.receive3` → a
`specklepy.bundle.model.Model`, not a `Base` tree — see main.py and
https://docs.speckle.systems/next/developers/sdks/python/breaking-changes).
`wall_obj` below is a `specklepy.bundle.model.ModelObject`, not a Base/
DataObject: there is no `.elements` tree to recurse, and Revit parameters are
rows in a columnar property store read with `wall_obj.get_string(...)`/
`get_double(...)`.

CORRECTION (2026-09-07, later the same day): the first cut of this port
called `get_string()`/`get_double()` with a bare "<Group>.<Param>" path (e.g.
"Identity Data.Assembly Code", "Construction.Function") on the assumption —
stated in specklepy's own docs — that the SDK searches instance scope, then
type scope, then a root scalar, so a caller never has to say which scope a
parameter lives in. That is wrong for what this Revit connector actually
writes into the bundle. Confirmed by downloading the real
`specklepy==2026.9.0b3` wheel and reading `ModelObject._typed()`: it DOES
check the instance property table then the type property table, but both
lookups use the exact same literal path string — there's no group-name
normalisation between scopes. This connector's real stored paths are
"Parameters.Instance Parameters.<Group>.<Param>" for instance-scope
parameters and "Parameters.Type Parameters.<Group>.<Param>" for type-scope
ones — never the bare "<Group>.<Param>" — so every one of this module's
original path guesses missed on both scopes and silently returned None.

Confirmed live and empirically (2026-09-07) via a diagnostic script run
against the real "Walls/10386456_A_UKHC_Fitout_Tower.rvt" model
(app.speckle.systems/projects/3eaeb15ff9, model e89b8d5a97, version
bec8f561c0) that dumped every stored property path for several real walls
and printed get_string()/get_double() against candidate paths directly —
not inferred from the viewer UI alone. Root scalars (no "properties." prefix
at all, and no "Parameters." segment) are unaffected by any of this:
  - category, family, type, name, units, speckle_type → root scalars,
    wall_obj.get_string("category") etc. — always worked, still do.
  - level  → NOT a property at all; it's the ON_LEVEL relation
             (wall_obj.level.name).

Everything else needs the full scope-qualified path. `_param()`/
`_param_double()` below try instance scope first (a genuine Revit instance
override of an otherwise type-level parameter should win), then type scope,
mirroring real Revit instance-vs-type parameter semantics rather than
guessing which scope a given parameter lives in:
  - Assembly Code       → Parameters.Type Parameters.Identity Data.Assembly Code
                           (type-scoped on this connector — confirmed "C1010145"
                           on a real wall; the ORIGINAL bare-path guess silently
                           returned None for every wall in the model, meaning
                           classify_walls() treated every already-legacy-coded
                           wall as blank/uncoded and predict_codes()'s
                           similarity reference pool was always empty)
  - Type Mark           → Parameters.Type Parameters.Identity Data.Type Mark
  - Fire Rating         → Parameters.Type Parameters.Identity Data.Fire Rating
                           (confirmed "SMOKE" / "1HR/S" on real walls)
  - Function            → Parameters.Type Parameters.Construction.Function
                           (confirmed "Interior" on a real interior partition —
                           this is the field predict._heuristic_signals leans on
                           hardest; losing it silently is what pushed the bulk
                           of one real model's interior walls into the
                           `method="default"` blind-fallback bucket instead of
                           C1010.x)
  - Width               → Parameters.Type Parameters.Construction.Width (feet)
  - Unconnected Height  → Parameters.Instance Parameters.Constraints.Unconnected
                           Height (feet) — instance-scoped, not type-scoped,
                           on this connector

No separate "Wall Tag" parameter exists in any of the v3-era models checked
pre-port — what Kevin/Mike referred to on the call as "wall tag" is
Type Mark, already extracted above.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from conditioning.codes import (
    ASTM_CODE_PATTERN,
    LEVEL4_PATTERN,
    try_normalise_to_level4,
)

FEET_TO_MM = 304.8

# Revit parameters live under one of these two scope prefixes in the bundle's
# columnar property store — never as a bare "<Group>.<Param>" path (see
# module docstring's 2026-09-07 correction). Instance is checked first so a
# genuine per-instance override of an otherwise type-level parameter wins,
# matching real Revit instance-vs-type semantics.
_SCOPE_PREFIXES = ("Parameters.Instance Parameters.", "Parameters.Type Parameters.")


def _param(wall_obj, group: str, name: str) -> str | None:
    """Read a Revit parameter by group/name, trying instance scope then type scope."""
    for prefix in _SCOPE_PREFIXES:
        val = wall_obj.get_string(f"{prefix}{group}.{name}")
        if val is not None:
            return val
    return None


def _param_double(wall_obj, group: str, name: str) -> float | None:
    """Read a numeric Revit parameter by group/name, instance scope then type scope."""
    for prefix in _SCOPE_PREFIXES:
        val = wall_obj.get_double(f"{prefix}{group}.{name}")
        if val is not None:
            return val
    return None


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class WallRecord:
    """Extracted metadata for one Revit wall or curtain-wall-family element."""

    obj: object             # the specklepy.bundle.model.ModelObject (read-only)
    object_id: str          # wall_obj.application_id — the only stable identity
                             # a bundle object has (never a content-hash .id;
                             # see main.py's module docstring)
    # "Walls" | "Curtain Systems" | "Curtain Panels" | "Curtain Wall Mullions"
    category: str
    type_name: str          # "type" General property
    family: str             # "family" General property
    function: str           # Construction.Function
    type_mark: str          # Identity Data.Type Mark
    width_mm: float         # Construction.Width (feet) × 304.8
    level: str              # ON_LEVEL relation's level name ("" if unset)
    assembly_code: str | None  # Identity Data.Assembly Code; None if absent
    # Both added 2026-09-07, after the client call asking for wall
    # sub-grouping to weigh in fire rating and height alongside wall tag
    # (type_mark, above) and family type name (type_name, above). Defaulted
    # so existing WallRecord(...) call sites — test fixtures included — don't
    # need updating just to keep constructing one.
    fire_rating: str = ""   # Identity Data.Fire Rating
    height_mm: float = 0.0  # Constraints.Unconnected Height × 304.8
    # Set by speckle_io.imprint_predictions() — the conditioning payload for
    # this wall (Status/Level 4 Code/Tier/... keyed under the run's
    # code_property_name), or None until that pass runs. Added 2026-09-07
    # alongside the bundle port: a ModelObject is a read-only view over the
    # received parquet tables, so there is no live `obj.properties` dict left
    # to mutate in place the way the old Base-tree DataObject allowed — the
    # conditioning result has to be held somewhere else until
    # create_conditioned_version() writes it into the fresh output bundle.
    # See speckle_io.py's 2026-09-07 note for the full reasoning.
    conditioning: dict | None = None

    @property
    def is_coded(self) -> bool:
        """True if this wall already has an Assembly Code (any format)."""
        return bool(self.assembly_code and self.assembly_code.strip())

    @property
    def is_level4_coded(self) -> bool:
        """True if the Assembly Code is an ACME Level 4 sub-section code (e.g.

        B2010.10).
        """
        return bool(
            self.assembly_code and LEVEL4_PATTERN.match(self.assembly_code.strip())
        )

    @property
    def is_astm_coded(self) -> bool:
        """True if the Assembly Code is a legacy ASTM Uniformat II code (e.g. B2010160).

        These carry real classification signal (they're not blank) but aren't in
        ACME's dot-notation format, so they need a human crosswalk decision —
        they must never be silently overwritten by the prediction heuristic.
        """
        return bool(
            self.assembly_code and ASTM_CODE_PATTERN.match(self.assembly_code.strip())
        )


@dataclass
class WallClassification:
    """Walls bucketed by code status.

    The same split is needed by both the report and the orchestrator, so it's computed
    once and shared.
    """

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


def get_assembly_code(wall_obj) -> str | None:
    """Extract Assembly Code from the Identity Data parameter group, or None.

    Uppercased on the way in — LEVEL4_PATTERN/ASTM_CODE_PATTERN only match an
    uppercase leading letter, so a code authored lowercase (e.g. a fat-
    fingered 'b2010.10') would otherwise silently miss is_level4_coded and
    get treated as an unrecognised legacy code needing re-prediction, even
    though it's already correct. ACME/ASTM Uniformat codes have no
    legitimate lowercase form, so this is a safe, unconditional
    normalisation, not a guess.

    If the code looks like an ACME Level 4 code with the period accidentally
    stripped (e.g. 'B201010' → 'B2010.10'), normalise it on the way in so it
    is treated as already-coded Level 4 rather than needing upgrade.
    ASTM Uniformat II codes (3-digit suffix, e.g. 'B2010160') are NOT affected.
    """
    val = _param(wall_obj, "Identity Data", "Assembly Code")
    if not val:
        return None
    raw = str(val).strip().upper()
    if not raw:
        return None
    return try_normalise_to_level4(raw) or raw


def get_wall_metadata(wall_obj) -> dict:
    """Extract all fingerprinting fields from a wall's bundle object."""
    # Root-scope "General" properties — confirmed live, see module docstring.
    type_name = str(wall_obj.get_string("type")   or "").strip()
    family    = str(wall_obj.get_string("family") or "").strip()

    # ON_LEVEL relation, not a property — see module docstring. wall_obj.level
    # is a ModelLevel | None; absent for anything not level-hosted.
    level = wall_obj.level.name if wall_obj.level and wall_obj.level.name else ""

    function    = str(_param(wall_obj, "Construction", "Function")     or "").strip()
    type_mark   = str(_param(wall_obj, "Identity Data", "Type Mark")   or "").strip()
    fire_rating = str(_param(wall_obj, "Identity Data", "Fire Rating") or "").strip()

    width_ft = _param_double(wall_obj, "Construction", "Width")
    width_mm = (width_ft or 0.0) * FEET_TO_MM

    height_ft = _param_double(wall_obj, "Constraints", "Unconnected Height")
    height_mm = (height_ft or 0.0) * FEET_TO_MM

    return {
        "type_name":    type_name,
        "family":       family,
        "function":     function,
        "type_mark":    type_mark,
        "fire_rating":  fire_rating,
        "width_mm":     width_mm,
        "height_mm":    height_mm,
        "level":        level,
    }


# ---------------------------------------------------------------------------
# Wall collection
# ---------------------------------------------------------------------------


def _get_category(wall_obj) -> str | None:
    """Get category from a bundle object's root-scope "General" properties."""
    cat = wall_obj.get_string("category")
    return str(cat) if cat else None


# Categories collected for conditioning. Revit models curtain walls as three
# categories distinct from "Walls" — the curtain wall host ("Curtain
# Systems"), the individual glazing/spandrel infill ("Curtain Panels"), and
# the framing members ("Curtain Wall Mullions"). All three were being
# silently skipped when the filter only matched "Walls" exactly, meaning
# every curtain wall element in a model was excluded from conditioning
# entirely. Matched case-insensitively/by substring on "curtain" rather than
# an exact string, since the exact category label wasn't verified against a
# live curtain-wall-bearing model the way "Walls" was (see docs/NOTES.md).
def _is_target_category(category: str | None) -> bool:
    """True if `category` is a wall or curtain-wall-family Revit category."""
    if not category:
        return False
    if category == "Walls":
        return True
    return "curtain" in category.lower()


def collect_walls(model) -> list[WallRecord]:
    """Return wall and curtain-wall elements from a received bundle Model.

    `model.objects` is already a flat list of every object in the version —
    2026.9 has no nested `elements` tree to recurse (containment is a typed
    relation now, not something a reader has to reconstruct), and dropping
    curtain-panel-under-curtain-system SUBELEMENT nesting doesn't lose any
    panels: every object appears in this flat list regardless of what it's
    related to. See main.py's module docstring for where `model` comes from.
    """
    walls: list[WallRecord] = []
    for wall_obj in model.objects:
        category = _get_category(wall_obj)
        if not _is_target_category(category):
            continue
        application_id = wall_obj.application_id
        if not application_id:
            continue
        meta = get_wall_metadata(wall_obj)
        walls.append(WallRecord(
            obj=wall_obj,
            object_id=application_id,
            category=category or "",
            assembly_code=get_assembly_code(wall_obj),
            **meta,
        ))

    print(
        f"[ConditioningPOC] Visited {len(model.objects)} objects, "
        f"found {len(walls)} walls."
    )
    return walls
