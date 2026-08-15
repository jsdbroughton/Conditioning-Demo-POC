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
"""

from __future__ import annotations

import re
from dataclasses import dataclass

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


@dataclass(frozen=True)
class TypeAttributes:
    """What a type name asserts about a wall, where the naming allows it."""

    fire_rating: str | None = None   # "NFR" | "SMOKE" | "1HR" | "1HR SMOKE"
    stc: str | None = None           # "35" | "45" | "NA"
    stud: str | None = None          # '6"' | '3-5/8"' | '2 1/2"'

    def __bool__(self) -> bool:
        """True when the name yielded anything at all."""
        return any((self.fire_rating, self.stc, self.stud))

    @property
    def summary(self) -> str | None:
        """A single pivot-ready dimension, e.g. `SMOKE · STC-35 · 6" Stud`.

        This is the field the estimator asked to group by — the combination
        is the wall type, not any one attribute on its own. Partial
        combinations are rendered rather than suppressed: a name that gives
        up a rating but no stud size still narrows the field usefully.
        """
        parts = []
        if self.fire_rating:
            parts.append(self.fire_rating)
        if self.stc:
            parts.append(f"STC-{self.stc}")
        if self.stud:
            parts.append(f'{self.stud}" Stud')
        return " · ".join(parts) if parts else None


def extract_attributes(type_name: str) -> TypeAttributes:
    """Read the attributes a type name encodes, if it follows the convention.

    Returns an empty TypeAttributes rather than raising or guessing when the
    name doesn't match — `CW_Unitized_Spandrel` genuinely asserts none of
    these things, and inventing a value for it would be worse than the blank.
    """
    if not type_name:
        return TypeAttributes()

    fire = _FIRE.search(type_name)
    stc = _STC.search(type_name)
    stud = _STUD.search(type_name)

    return TypeAttributes(
        # Collapse internal whitespace so "1HR  SMOKE" and "1HR SMOKE" are
        # one value rather than two rows in a pivot table.
        fire_rating=" ".join(fire.group(1).upper().split()) if fire else None,
        stc=stc.group(1).upper() if stc else None,
        stud=stud.group(1).strip() if stud else None,
    )


def attributes_by_type(type_names: set[str]) -> dict[str, TypeAttributes]:
    """Extract once per distinct type name, not once per element.

    Same reasoning as the fingerprint deduplication in predict.py: a real
    model holds tens of thousands of elements across a few dozen names.
    """
    return {name: extract_attributes(name) for name in type_names}
