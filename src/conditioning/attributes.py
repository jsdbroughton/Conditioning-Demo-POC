"""Reading fire rating, acoustic rating and stud size out of a type name.

This is the estimator's actual ask from the 2026-08-14 call, stated almost
verbatim: "we can see if it's an STC rating, we can see if it's a smoke or
firewall, we can see if it's single-layered GWB, and we can see the stud
size."

It exists because similarity clustering provably cannot do it. That was
tried first and measured (see grouping.py, and the NOTES entry for the
same date): plain Jaccard put 23,644 elements into one group mixing NFR
with SMOKE, and no weighting scheme fixes it. Under plain, IDF and
balance-weighted scoring alike, a must-split pair (`SMOKE` vs `NFR`) scores
*higher* than a must-merge pair (`Spandrel` vs `Spandrel L5`), so no
threshold satisfies both. Both are one-token differences in otherwise
identical names; one means "different wall", the other means "same wall,
level 5". Token overlap compares words, not meaning.

So this module does the thing similarity can't: it knows that NFR, SMOKE
and 1HR are a category of information, and that a trailing "L5" is not.

What that knowledge costs
-------------------------
It is a convention assumption, and it is the only one in this codebase. It
happens to hold across an entire real interiors model, where every partition
is named `Type <id> - <construction> - <rating> - STC-<n> - <n>" Stud`. It
holds nowhere in the curtain-wall model, whose types are `CW_Unitized_
Spandrel`, `CW1D`, `20d panel` and `Empty`.

That is the honest behaviour and the reason this is a separate axis rather
than folded into the group: where the convention holds you get precise,
estimator-legible attributes; where it doesn't you get nothing at all, and
nothing is visibly nothing. A run reports its own coverage so the reader can
see which case they are in, rather than discovering it from a pivot table
that is quietly half-empty.

Every value is prefixed "Observed" wherever it is written out, for the same
reason the cluster keys are: these are read off the architect's naming, not
supplied by the estimator, and must never be mistaken for an agreed
classification.

2026-09-07 — Fire Rating and Wall Tag read from real parameters, not names
--------------------------------------------------------------------------
The follow-up client call asked for wall sub-grouping to also weigh in wall
tag and height, on top of fire rating. Checked directly against the live
UKHC Core/Podium/Tower models (queried via the EAV property dataset) before
writing any of this, rather than assumed:

  * "Wall tag" is Type Mark. No separate parameter exists in any of the
    three models. It's read on WallRecord already (`type_mark`); this module
    just accepts it as an optional input now.
  * Fire Rating exists as a real Type Parameter
    (`Identity Data.Fire Rating`) — see walls.py's docstring for the path
    and measured coverage (23%-93%, varies by source file). Where it's
    populated it is authoritative and preferred over the name-regex below.
    Where it's blank the wall is presumed non-rated by the same convention
    the regex already assumes, so the name-regex fallback still runs and
    still catches an explicit "NFR" in the type name.
  * The parameter's own vocabulary isn't the name convention's vocabulary:
    it renders a combined rating as `1HR/S`, `2HR/S` where the type name
    convention (and the regex below) renders `1HR SMOKE`, `2HR SMOKE`. Both
    mean the same thing to an estimator, so `_normalize_fire_rating_param`
    converts the parameter's slash form to the name convention's form —
    the two sources must never render as different values for the same
    fact in the "Observed" summary.
  * Confirmed on real data that Type Mark alone is not a safe stand-in for
    Fire Rating: on the Podium model, Type Mark `A6` covers both `1HR` and
    `1HR/S`, and `T6`/`S6` each cover three different ratings. So Fire
    Rating has to keep coming from its own source, never inferred from tag.
  * Height (Unconnected Height) is real, well-covered (~100% in two of the
    three models checked), and NOT handled here — it's a genuine
    per-instance value (see walls.py's docstring: one Type Mark alone spans
    38 distinct heights), so it cannot be folded into TypeAttributes without
    breaking attributes_by_type's per-type-name cache (two elements sharing
    a type name would silently share one cached height). It's bucketed
    by the separate, uncached `bucket_height_ft()` below and reported
    alongside `TypeAttributes`, never inside it.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass

from conditioning.walls import WallRecord

# Fire/smoke rating. Combined forms first so "1HR SMOKE" isn't truncated to
# "1HR" by an earlier alternative — a 1-hour smoke partition is its own
# thing to an estimator, not a 1-hour wall with a note.
_FIRE = re.compile(r"\b(\d+\s*HR(?:\s+SMOKE)?|SMOKE|NFR)\b", re.IGNORECASE)

# Acoustic rating. "STC-NA" is a real, meaningful value — it asserts that no
# rating applies — so it is captured rather than treated as missing.
_STC = re.compile(r"\bSTC[-\s]?(\d+|NA)\b", re.IGNORECASE)

# Stud size, allowing the fractional inch forms that appear in real models:
# 6" Stud, 3-5/8" Stud, 2 1/2" Stud.
_STUD = re.compile(r'(\d+(?:[\s\-]\d+/\d+)?)\s*"?\s*Stud\b', re.IGNORECASE)

# Values the real Fire Rating parameter uses to mean "nothing to report" —
# seen on the live UKHC models as a bare dash rather than an absent value.
# Treated the same as blank/absent, not as a rating of "-".
_BLANK_FIRE_RATING_VALUES = {"-", "—", "N/A"}


def _normalize_fire_rating_param(raw: str | None) -> str | None:
    """Normalise a real Fire Rating parameter value to the name-regex's vocabulary.

    The parameter and the type-name convention encode the same fact two
    different ways: the parameter renders a combined rating as `1HR/S`,
    `2HR/S`, while the type-name convention (and _FIRE above) renders
    `1HR SMOKE`, `2HR SMOKE` — confirmed against the live Podium model,
    where both forms exist for the same wall families. Left un-normalised,
    the same fact would render as two different values depending purely on
    which source happened to supply it, in the same "Observed" summary.

    Returns None for a blank/dash value (see _BLANK_FIRE_RATING_VALUES) —
    that means "presumed non-rated", not "value is a dash".
    """
    if not raw:
        return None
    value = raw.strip()
    if not value or value.upper() in _BLANK_FIRE_RATING_VALUES:
        return None
    value = value.upper()
    if value.endswith("/S"):
        value = f"{value[:-2]} SMOKE"
    return " ".join(value.split())


@dataclass(frozen=True)
class TypeAttributes:
    """What a wall type asserts, from its name and/or its own parameters.

    Everything here is safe to cache once per distinct type name (see
    attributes_by_type) — fire_rating, stc, stud and wall_tag are all either
    read from the type name itself or from a Type Parameter, so every
    element sharing a type name shares these values. Height is deliberately
    NOT a field here — see the module docstring's 2026-09-07 note and
    bucket_height_ft() below.
    """

    fire_rating: str | None = None   # "NFR" | "SMOKE" | "1HR" | "1HR SMOKE"
    # "parameter" if fire_rating came from the real Fire Rating Type
    # Parameter, "name" if it came from the _FIRE regex on the type name
    # instead, None if fire_rating itself is None. Kept separate from
    # fire_rating rather than folded into its text — this codebase already
    # learned once (see NOTES.md, 2026-08-14, the "Observed"/"Inferred"
    # rename) that a reader needs to be able to tell "the building told us"
    # from "we worked it out" without cross-referencing another field.
    fire_rating_source: str | None = None
    stc: str | None = None           # "35" | "45" | "NA"
    stud: str | None = None          # '6"' | '3-5/8"' | '2 1/2"'
    wall_tag: str | None = None      # Type Mark, e.g. "H6" — see walls.py

    def __bool__(self) -> bool:
        """True when the name or its parameters yielded anything at all."""
        return any((self.fire_rating, self.stc, self.stud, self.wall_tag))

    @property
    def summary(self) -> str | None:
        """A single pivot-ready dimension, e.g. `H6 · SMOKE · STC-35 · 6" Stud`.

        This is the field the estimator asked to group by — the combination
        is the wall type, not any one attribute on its own. Partial
        combinations are rendered rather than suppressed: a name that gives
        up a rating but no stud size still narrows the field usefully.
        wall_tag leads when present, since it's the short id an estimator
        would actually recognise a wall type by (see walls.py) — the same
        role the "Type H6" prefix plays in the full type name.
        """
        parts = []
        if self.wall_tag:
            parts.append(self.wall_tag)
        if self.fire_rating:
            parts.append(self.fire_rating)
        if self.stc:
            parts.append(f"STC-{self.stc}")
        if self.stud:
            parts.append(f'{self.stud}" Stud')
        return " · ".join(parts) if parts else None


def extract_attributes(
    type_name: str,
    fire_rating_param: str | None = None,
    wall_tag: str | None = None,
) -> TypeAttributes:
    """Read the attributes a wall type asserts, from its name and/or parameters.

    `fire_rating_param` and `wall_tag` are optional and default to None so
    every existing name-only call site keeps working unchanged — this is a
    strict addition, not a replacement, of the original name-only signature.

    Fire rating prefers the real parameter (normalised — see
    _normalize_fire_rating_param) when it's present and non-blank; only
    falls back to the type-name regex when the parameter is absent, which is
    exactly the walls in these models that never carried one in the first
    place (see walls.py's docstring). Returns an empty TypeAttributes rather
    than raising or guessing when neither yields anything — `CW_Unitized_
    Spandrel` genuinely asserts none of these things, and inventing a value
    for it would be worse than the blank.
    """
    param_fire_rating = _normalize_fire_rating_param(fire_rating_param)
    if param_fire_rating:
        fire_rating = param_fire_rating
        fire_rating_source = "parameter"
    else:
        fire = _FIRE.search(type_name) if type_name else None
        # Collapse internal whitespace so "1HR  SMOKE" and "1HR SMOKE" are
        # one value rather than two rows in a pivot table.
        fire_rating = " ".join(fire.group(1).upper().split()) if fire else None
        fire_rating_source = "name" if fire_rating else None

    stc = _STC.search(type_name) if type_name else None
    stud = _STUD.search(type_name) if type_name else None

    return TypeAttributes(
        fire_rating=fire_rating,
        fire_rating_source=fire_rating_source,
        stc=stc.group(1).upper() if stc else None,
        stud=stud.group(1).strip() if stud else None,
        wall_tag=wall_tag.strip() if wall_tag and wall_tag.strip() else None,
    )


def attributes_by_type(walls: Iterable[WallRecord]) -> dict[str, TypeAttributes]:
    """Extract once per distinct type name, not once per element.

    Same reasoning as the fingerprint deduplication in predict.py: a real
    model holds tens of thousands of elements across a few dozen names.
    Takes WallRecords rather than bare type-name strings (changed
    2026-09-07) because fire_rating and wall_tag now have to come from
    somewhere — the first wall seen for a given type name supplies them,
    which is safe precisely because both are Type Parameters and therefore
    constant across every instance of that type (see TypeAttributes). Height
    is NOT threaded through here for the opposite reason — it isn't
    constant per type, so it has no business in a per-type-name cache at
    all; call bucket_height_ft() per wall instead.
    """
    by_name: dict[str, WallRecord] = {}
    for wall in walls:
        by_name.setdefault(wall.type_name, wall)
    return {
        name: extract_attributes(
            name, fire_rating_param=wall.fire_rating, wall_tag=wall.type_mark
        )
        for name, wall in by_name.items()
    }


# ---------------------------------------------------------------------------
# Height — deliberately separate from TypeAttributes; see module docstring.
# ---------------------------------------------------------------------------

# Round Unconnected Height to the nearest foot for reporting. A starting
# point for the estimator conversation, not a tuned constant — the same
# status as grouping.GROUP_SIMILARITY_THRESHOLD. Measured on the live
# Podium model: one Type Mark ("H6") alone spans 38 distinct heights from
# 1.0 ft to 23.1 ft, all floor-to-floor variation rather than anything about
# the wall assembly, so reporting it raw would turn one wall type into
# three dozen pivot rows — exactly the fragmentation grouping.py exists to
# avoid for type names. Nearest-foot is a reasonable first cut for "does
# this cost the same"; the right bucket width is whatever the estimator
# actually needs to see the field distinguished at.
HEIGHT_BUCKET_FT = 1.0

_MM_PER_FT = 304.8


def bucket_height_ft(
    height_mm: float, bucket_ft: float = HEIGHT_BUCKET_FT
) -> str | None:
    """Round a wall's Unconnected Height to the nearest bucket, as a label.

    Returns None for a wall with no height recorded (0 or missing) — a
    genuine absence, not "0 feet tall". Takes height_mm directly rather than
    a WallRecord so it has no dependency on attributes_by_type's cache — see
    the module docstring for why height must never be cached by type name.
    """
    if not height_mm or height_mm <= 0:
        return None
    height_ft = height_mm / _MM_PER_FT
    bucketed = round(height_ft / bucket_ft) * bucket_ft
    # Whole-foot buckets render without a decimal point ("14'" not "14.0'").
    if bucketed == int(bucketed):
        return f"{int(bucketed)}'"
    return f"{bucketed:g}'"
