"""Sub-grouping wall types within a Uniformat code, by similarity.

The gap this closes, from the 2026-08-14 client call: a Level 4 code is the
right answer and immediately not enough. Every interior partition in a model
lands on `C1010.10`, which is correct — the estimator confirmed it on the
call — and then the next question is "yes, but which *kind*", because a 6"
smoke partition and a 3-5/8" furring wall do not cost the same per linear
foot. The ask was to take fifteen architects' wall types and collapse them
into roughly five of the contractor's own.

Three hierarchies got conflated in that conversation and only one of them is
this:

  * Uniformat Level 4 (`C1010.10`) — what predict.py produces. Correct, and
    not the thing that's missing.
  * Uniformat Level 5 (`C1010.10.0100`) — estimate line items. Not this
    either: one wall assembly spans several line items at once (membrane,
    flashing, sealant), so there is no single Level 5 code per element. See
    the hierarchy notes in codes.py.
  * The contractor's own wall-type taxonomy — orthogonal to Uniformat, not
    deeper into it. That is what this module approximates.

Because it is orthogonal, grouping does not change, refine or second-guess
any predicted code. It adds a second axis so a pivot table can put the
Uniformat code on one side and the wall type on the other.

Why clustering rather than parsing the type name
------------------------------------------------
Parsing is the obvious approach and it only works on disciplined models.
Measured across the two real models: one names its walls
`Type L3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud`, where
nine of the top ten types yield fire rating, acoustic rating, construction
and stud size to a regex. The other names them `CW_Unitized_Spandrel`,
`CW1D`, `20d panel` and `Empty`, where 182 of 185 types yield nothing at
all. A regex tuned to the first model reports no groups whatsoever on the
second.

Similarity doesn't care about convention. It only asks whether two names
resemble each other, so it groups `CW_Unitized_IGU-8` with
`CW_Unitized_IGU-2` for exactly the same reason, and with exactly the same
code, that it groups the fully-specified partition types. That is the whole
argument for doing this with the comparison engine instead of a parser.

What it deliberately cannot do
------------------------------
It cannot name a group in the contractor's vocabulary. It can say "these
eleven type names are one family and here is what they share"; it cannot
know that the family is called "6-inch smoke partition" internally. Naming
needs the client's key-code mapping. The value of grouping first is that
the mapping then has one row per *group* rather than one per architect type
name — which is the difference between a table someone will maintain and
one they won't.

2026-09-07 — a group's Type Mark(s)/Fire Rating(s) are reported, not adopted
-----------------------------------------------------------------------------
Follow-up ask: make a group more meaningful than a bare letter — in
particular, relate it back to Type Mark, the one thing the client's own
estimators already recognise a wall type by (see attributes.py). Checked
against this file's own already-measured real output before building
anything: the largest real cluster on record, `C1010.10 · inferred group A`
("Type Furring Single Sided GWB NFR STC NA Stud", 100 elements), spans SIX
distinct Type Marks (K1, K2, K3, L2, L3, L6) — they're all "Furring" walls
differing only in stud size, similar enough to cluster by name. That's the
norm for a big group, not an exception, because Type Mark contributes only
one token out of several to the similarity score (see _group_similarity) —
losing it rarely drops a pair below threshold on its own.

So a group's Type Mark cannot become its identity the way this request
first suggested; `key` and `label` are unchanged for exactly that reason
(and because Jessica's Power BI work already depends on `key`'s shape).
Instead `TypeGroup.description` and its wall_tags/fire_ratings/stc_values/
stud_sizes rollups reported what the group's members shared — one value when
they agreed, "varies (...)" listing all of them when they didn't.

2026-09-07 (later the same day) — Fire Rating and Acoustic STC are now a
hard split, not just a rollup
-----------------------------------------------------------------------------
The distinction drawn above — Type Mark is just an identifier, not a cost
driver — does not hold for Fire Rating or Acoustic STC. Per the Ken/Mike
call transcript, the estimators explicitly expect DIFFERENT costs to come
out of walls differing on fire rating and acoustics specifically. Once real-
model data started landing on the correct Level 4 code (see walls.py's
2026-09-07 path-resolution fix), groups like "C1010.10 · inferred group A"
turned out to span 1HR through 2HR SMOKE in one 3,780-element bucket —
precisely the "must split" pair attributes.py's own docstring already names
as a case plain name-similarity cannot tell apart (a `SMOKE`/`NFR`
difference is one token, the same magnitude as a cosmetic `Spandrel`/
`Spandrel L5` difference, so no similarity threshold can separate one from
the other). Reporting that spread via `description`/`fire_ratings` was
honest, but it doesn't fix the underlying problem: a group two estimators
would price differently is not one group.

Fixed by bucketing on `(fire_rating, stc)` BEFORE running
`_group_similarity` at all, inside `assign_type_groups()` — two type names
are only ever compared for similarity if they already agree on both. Name-
similarity clustering still runs within each such slice, so it keeps doing
the thing it is actually good at: merging cosmetic naming variants
(`Spandrel` vs `Spandrel L5`) that share an identical fire/acoustic profile.
Stud Size and Type Mark both stay reported rollups, not split keys — the
transcript calls out fire rating and acoustics specifically, not stud size,
so this does not assume it belongs in the same bucket without that same
confirmation. This raises the number of groups per code and lowers the size
of the largest one — `key`'s literal shape is unchanged, but its
cardinality is not, which is worth a heads-up for anyone whose Power BI
work already assumes today's group counts.

2026-09-07 (later still) — Height added as a third hard-split dimension, opinionated
---------------------------------------------------------------------------------------
Challenged directly: is height really only a quantity multiplier (more SF
costs more, no classification change needed), or a genuine cost
differentiator the way fire rating and STC are? It's the latter — interior
stud walls commonly need a heavier gauge or added bracing past a real
height threshold, independent of the takeoff quantity. The prior rejection
of height (see attributes.py's 2026-09-07 note) was really only an argument
against RAW height as a group identity — one Type Mark spans 38 distinct
heights on the Podium model, so using the exact figure would fragment a
type into dozens of pivot rows. Bucketed into bands, the same objection
doesn't apply.

No follow-up call was available to confirm Turner's own gauge/bracing
thresholds, so `attributes.height_band()`'s two constants
(`HEIGHT_BAND_SHORT_MAX_MM` / `HEIGHT_BAND_TALL_MIN_MM`) are a deliberately
opinionated stand-in — ordinary construction practice, not a number
measured against this client's own pricing — made to unblock delivery
rather than wait on confirmation. Flagged there, and flagged here: correct
those two constants the moment real thresholds are known.

The slice key that used to be `(fire_rating, stc)` is now
`(fire_rating, stc, height_band)`. Because height varies WITHIN a single
(type_name, family) bucket — unlike fire_rating/stc, which are genuinely
constant per type — the initial bucketing pass had to change too: a bucket
is now keyed on `(type_name, family, height_band)`, so two instances of the
same architect-named type at different heights are treated as separate
type-level units before clustering ever sees them, the same way two
differently-fire-rated instances already were. This raises group
cardinality again, for the same reason the fire/STC split did — worth the
same heads-up to Power BI consumers.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass

from conditioning.attributes import attributes_by_type, height_band
from conditioning.predict import Prediction, _tokens
from conditioning.walls import WallRecord

# Minimum weighted-Jaccard score for a wall type to join an existing group.
#
# Tuned against the live models rather than picked: at 0.20 groups start
# chaining together things that only share a filler word; at 0.45 and above
# two thirds of types sit alone in a group of one, which is a list, not a
# grouping. 0.30 puts ~70% of elements into groups holding more than one
# type while keeping the largest group recognisably one family. It is a
# starting point for a conversation with the estimator, not a tuned
# constant — the right value is whatever produces groups they recognise.
GROUP_SIMILARITY_THRESHOLD = 0.30

_WORD = re.compile(r"[A-Za-z0-9]+")


@dataclass(frozen=True)
class TypeGroup:
    """One cluster of similar wall types, at one of three granularities.

    2026-09-07 (later still) — three tiers, not one hard split
    ------------------------------------------------------------
    The 2026-09-07 fire/STC hard split (see module docstring) picked one
    granularity and forced everyone onto it — right for an estimator costing
    a takeoff, wrong for anyone who wants the coarser "these are basically
    the same wall" view a plain similarity cluster gives (e.g. a first
    pass mapping the model's chaos onto the client's own wall-type list).
    A single flat split can't be both. So `assign_type_groups()` now
    produces three tiers per code, each a real, independently-sized
    `TypeGroup`, one refining the last:

      * `tier="coarse"` — pure type-name similarity, ignoring fire rating,
        acoustic rating and height entirely. This is the pre-2026-09-07
        behaviour, restored as the top of the hierarchy rather than as the
        only view. It CAN span a fire-rating or acoustic boundary — that's
        the known, documented limitation (see "What it deliberately cannot
        do" above), and it's why finer tiers exist rather than why this
        tier is wrong to offer.
      * `tier="fire_acoustic"` — the coarse cluster's members re-partitioned
        by (Fire Rating, Acoustic STC). Only produced (i.e. only gets a key
        distinct from its coarse parent) where the coarse cluster actually
        spans more than one (fire, stc) pair — a cluster that was already
        uniform doesn't grow a meaningless sub-row.
      * `tier="full"` (the default, and what a wall is actually tagged
        with) — the fire/acoustic slice re-partitioned again by
        `attributes.height_band()`. Same non-inflation rule: only splits
        further where the slice actually spans more than one height band.

    `parent_key` names the tier immediately above (`None` for coarse), so
    the three tiers form a real hierarchy a reader — or Power BI — can walk
    in either direction: roll up from `full` to `fire_acoustic` to `coarse`
    by following `parent_key`, or drill down from a coarse key to every
    finer row that refines it. `assign_type_groups()` returns both a
    per-wall assignment (always the `full`-tier group, since that's the one
    that actually guarantees no two differently-priced walls share a group)
    and the complete list of every tier's `TypeGroup` rows, for reporting.
    """

    key: str      # "C1010.10 · inferred group A" — the letter is ours, see _INFERRED
    label: str    # derived from what the members share: "CW Unitized IGU"
    size: int     # number of elements, not number of type names
    tier: str = "full"          # "coarse" | "fire_acoustic" | "full"
    parent_key: str | None = None  # this row's immediate coarser ancestor's key
    # Everything below is a rollup OVER the group's members, computed after
    # clustering — never an input to which cluster a wall lands in (that's
    # _group_similarity, type-name tokens only). See the module's 2026-09-07
    # note for why Type Mark specifically cannot just become the group's
    # identity — real groups routinely span several of them.
    description: str = ""  # "5 elements — Type Mark H6, Fire Rating SMOKE, ..."
    # Distinct values across all members — e.g. {"H6"} for one shared mark,
    # {"K1","K2","K3"} for a mixed group. fire_ratings is param-or-name (see
    # attributes.py); wall_tags/stc_values/stud_sizes are their usual source.
    # On a `full`-tier group, fire_ratings/stc_values/height_bands are each
    # guaranteed to hold at most one value, by construction — the split that
    # produced this tier is exactly what forces that. wall_tags/stud_sizes
    # can still hold several; nothing splits on either.
    wall_tags: frozenset[str] = frozenset()
    fire_ratings: frozenset[str] = frozenset()
    stc_values: frozenset[str] = frozenset()
    stud_sizes: frozenset[str] = frozenset()
    height_bands: frozenset[str] = frozenset()
    # Populated only on the `full`-tier group returned per-wall (never on a
    # standalone row in the reporting list) — lets a single wall's
    # properties carry all three tiers' keys/labels without a join, so a
    # Power BI user can group by whichever granularity they want directly
    # off the wall's own row.
    coarse_key: str = ""
    coarse_label: str = ""
    fire_acoustic_key: str = ""
    fire_acoustic_label: str = ""


def _group_similarity(a: set[str], b: set[str]) -> float:
    """Jaccard overlap of two type names' token sets.

    Type name only — deliberately not predict.fingerprint_similarity(),
    and deliberately not blended with family either.

    Inside a single Level 4 bucket, function, category and family are
    near-constant: they are largely what put the walls in that bucket in the
    first place. A near-constant term contributes the same amount to every
    pair, which separates nothing and silently loosens the threshold — a
    first cut here weighted family at 0.15 and, because family was "Basic
    Wall" throughout, every score gained a flat 0.15 and the effective
    threshold fell from the tuned 0.30 to 0.18. The result was one group of
    251 elements whose members had no shared vocabulary at all.

    Width would be worse than useless: a 6" and an 8" stud partition are the
    same kind of wall to an estimator, and scoring them apart is the
    opposite of what grouping is for. The type name is where the architect
    actually encoded the type, so the type name is what gets compared.
    """
    union = len(a | b)
    return len(a & b) / union if union else 0.0


def _label_from(seed_name: str, shared: set[str], fallback: str) -> str:
    """Render the tokens a group has in common, in the seed name's own order.

    Reading them back off the seed keeps the original casing and word order,
    so `CW_Unitized_IGU-8` yields "CW Unitized IGU" rather than an
    alphabetised bag of lowercase tokens. A group whose members share
    nothing is a group of one, and is better described by its own name.
    """
    if not shared:
        return fallback
    words = [
        m.group() for m in _WORD.finditer(seed_name) if m.group().lower() in shared
    ]
    return " ".join(dict.fromkeys(words)) or fallback


def _rollup(walls: list[WallRecord], type_attrs: dict) -> dict[str, set[str]]:
    """Collect the distinct Tag/Fire Rating/STC/Stud/Height Band values a group carries.

    Reads Fire Rating/STC/Wall Tag/Stud from `type_attrs` (see
    attributes.attributes_by_type — constant per type name, computed once
    for the whole run) and Height Band per wall directly (genuinely
    per-instance, never cached by type name — see attributes.py). Blank
    values are skipped rather than added as an empty-string member, so an
    all-blank rollup renders as "nothing recognised" rather than a set of
    one empty string.
    """
    rollup = {
        "wall_tags": set(), "fire_ratings": set(), "stc_values": set(),
        "stud_sizes": set(), "height_bands": set(),
    }
    for wall in walls:
        attrs = type_attrs[wall.type_name]
        if attrs.wall_tag:
            rollup["wall_tags"].add(attrs.wall_tag)
        if attrs.fire_rating:
            rollup["fire_ratings"].add(attrs.fire_rating)
        if attrs.stc:
            rollup["stc_values"].add(attrs.stc)
        if attrs.stud:
            rollup["stud_sizes"].add(attrs.stud)
        band = height_band(wall.height_mm)
        if band:
            rollup["height_bands"].add(band)
    return rollup


def _describe_group(
    size: int,
    wall_tags: set[str],
    fire_ratings: set[str],
    stc_values: set[str],
    stud_sizes: set[str],
    height_bands: set[str],
) -> str:
    """Plain-English account of what a group's members actually have in common.

    One value per factor when the group agrees on it; "varies (...)" listing
    every distinct value seen when it doesn't — the honest answer for a group
    like the real 100-element Furring cluster that spans six Type Marks (see
    the module's 2026-09-07 note). Never invents a single representative
    value and hides the rest. On a `full`-tier group, Fire Rating, Acoustic
    STC and Height Band are each guaranteed to show exactly one value (that
    split is what defines the tier) — "varies" on any of those three can
    only appear on a coarser row.
    """
    noun = "element" if size == 1 else "elements"
    facts = []
    for label, values in (
        ("Type Mark", wall_tags),
        ("Fire Rating", fire_ratings),
        ("Acoustic STC", stc_values),
        ("Stud Size", stud_sizes),
        ("Height Band", height_bands),
    ):
        if len(values) == 1:
            facts.append(f"{label} {next(iter(values))}")
        elif len(values) > 1:
            facts.append(f"{label} varies ({', '.join(sorted(values))})")
    if not facts:
        facts.append(
            "no Type Mark, Fire Rating, STC, Stud Size or Height Band recognised"
        )
    return f"{size:,} {noun} — " + ", ".join(facts)


# Group keys read "C1010.10 · inferred group A", never "C1010.10-A".
#
# The hyphenated form was the first cut and it was a bad idea: it has the
# shape of a code. Pasted into a spreadsheet beside real Uniformat values it
# looks like it belongs to the client's taxonomy, and nothing about it warns
# the reader that Speckle invented the letter. These groups are observed
# from the model's own type names — they are not a client classification,
# have no authority, and will renumber if the model changes. The key says so
# in the key, because that is the only place guaranteed to travel with the
# value into a pivot table.
_INFERRED = "inferred group"


def _key_suffix(index: int) -> str:
    """A, B, ... Z, AA, AB — so a code with 30 groups still sorts sensibly."""
    letters = ""
    index += 1
    while index:
        index, rem = divmod(index - 1, 26)
        letters = chr(65 + rem) + letters
    return letters


def _final_code(wall: WallRecord, pred: Prediction | None) -> str | None:
    """The code a wall ends up carrying.

    Its existing code if already correct, otherwise the predicted one.
    """
    if wall.is_level4_coded:
        return wall.assembly_code
    return pred.predicted_code if pred else None


def _disambiguate(
    label: str, seed_name: str, shared: set[str], suffix: str, used: set[str]
) -> str:
    """Disambiguate a derived label against others already used at this tier.

    Labels are derived, so two groups under one code can land on the same
    text. Disambiguate with the first token that is distinctive to the seed,
    falling back to the tier suffix — a pivot table with two identically
    named rows is worse than a slightly clumsy label.
    """
    if label not in used:
        return label
    extra = next(
        (m.group() for m in _WORD.finditer(seed_name)
         if m.group().lower() not in shared),
        None,
    )
    return f"{label} ({extra})" if extra else f"{label} ({suffix})"


def _make_group(
    key: str, label: str, walls: list[WallRecord], type_attrs: dict,
    tier: str, parent_key: str | None,
) -> TypeGroup:
    """Build one TypeGroup row (any tier) from its final member list."""
    rollup = _rollup(walls, type_attrs)
    size = len(walls)
    return TypeGroup(
        key=key,
        label=label,
        size=size,
        tier=tier,
        parent_key=parent_key,
        description=_describe_group(
            size, rollup["wall_tags"], rollup["fire_ratings"],
            rollup["stc_values"], rollup["stud_sizes"], rollup["height_bands"],
        ),
        wall_tags=frozenset(rollup["wall_tags"]),
        fire_ratings=frozenset(rollup["fire_ratings"]),
        stc_values=frozenset(rollup["stc_values"]),
        stud_sizes=frozenset(rollup["stud_sizes"]),
        height_bands=frozenset(rollup["height_bands"]),
    )


def assign_type_groups(
    walls: Iterable[WallRecord],
    predictions: Iterable[Prediction],
    threshold: float = GROUP_SIMILARITY_THRESHOLD,
) -> tuple[dict[str, TypeGroup], list[TypeGroup]]:
    """Cluster wall types within each Level 4 code, at three granularities.

    Returns `(assignments, all_groups)`:

      * `assignments` maps each wall's object_id to its `full`-tier
        TypeGroup — the one that never lets two differently fire-rated,
        differently-acoustic-rated or differently-heighted walls share a
        group. This is what imprint_predictions() writes onto the wall
        (plus, from the same object, the coarser tiers' keys/labels — see
        TypeGroup's docstring).
      * `all_groups` is every TypeGroup row produced at every tier —
        coarse, fire_acoustic and full — for a reporting view that shows
        the roll-up structure rather than only the finest leaf. A coarse
        cluster that never actually got refined appears once, at coarse
        tier only; a fire_acoustic or full row is only emitted where that
        tier's split actually did something (see TypeGroup's docstring).

    Groups are formed independently within each Level 4 code — an exterior
    veneer must never cluster with an interior partition just because both
    are called "Type A". Within a code, clustering is greedy leader
    assignment on TYPE NAME ONLY (see _group_similarity) — this is the
    `coarse` tier, and is deliberately blind to fire rating, acoustic rating
    and height, the same algorithm this file ran before any of those
    existed as hard splits. Seeded biggest-first: the most common type
    becomes the first seed, and every less common type joins the first seed
    it resembles or starts its own group. Chosen over single-linkage
    because linkage chains — A resembles B, B resembles C, and C ends up
    grouped with an A it looks nothing like, which is how an entire model
    collapses into one group. Deterministic given a stable sort, which
    matters because these keys get written onto objects and compared
    between runs.

    Each coarse cluster's members are then re-partitioned by
    (Fire Rating, Acoustic STC) to produce the `fire_acoustic` tier, and
    each of those slices re-partitioned again by `attributes.height_band()`
    to produce `full` — never the other way around, and never by re-running
    similarity: a wall that passed the coarse name-similarity bar stays in
    that family at every finer tier, it just gets sliced within it. Absence
    of data (no Fire Rating, no STC, no recorded height) is not a
    contradiction, so walls that both leave an attribute unread still
    partition together, the same convention `attributes.py` already uses.
    """
    pred_map = {p.wall.object_id: p for p in predictions}
    walls = list(walls)
    type_attrs = attributes_by_type(walls)

    # Bucket by final code, and within a bucket collapse to distinct types —
    # the same deduplication predict.py relies on, for the same reason.
    buckets: dict[str, dict[tuple[str, str], list[WallRecord]]] = {}
    for wall in walls:
        code = _final_code(wall, pred_map.get(wall.object_id))
        if not code:
            continue
        buckets.setdefault(
            code,
            {}).setdefault((wall.type_name, wall.family),
            []).append(wall,
        )

    assignments: dict[str, TypeGroup] = {}
    all_groups: list[TypeGroup] = []

    for code in sorted(buckets):
        types = buckets[code]
        ordered = sorted(types.items(), key=lambda kv: (-len(kv[1]), kv[0]))

        # ---- Coarse tier: pure type-name similarity, exactly the
        # algorithm this file ran before any hard split existed. ----
        coarse_clusters: list[dict] = []
        for (type_name, _family), members in ordered:
            tokens = _tokens(type_name)
            for cluster in coarse_clusters:
                if _group_similarity(tokens, cluster["seed"]) >= threshold:
                    cluster["shared"] &= tokens
                    cluster["members"].extend(members)
                    break
            else:
                coarse_clusters.append({
                    "seed": tokens,
                    "seed_name": type_name,
                    "shared": set(tokens),
                    "members": list(members),
                })
        coarse_clusters.sort(key=lambda c: (-len(c["members"]), c["seed_name"]))

        used_coarse_labels: set[str] = set()
        for ci, coarse in enumerate(coarse_clusters):
            coarse_suffix = _key_suffix(ci)
            coarse_key = f"{code} · {_INFERRED} {coarse_suffix}"
            coarse_label = _disambiguate(
                _label_from(
                    coarse["seed_name"], coarse["shared"], coarse["seed_name"]
                ),
                coarse["seed_name"], coarse["shared"],
                coarse_suffix, used_coarse_labels,
            )
            used_coarse_labels.add(coarse_label)
            coarse_walls: list[WallRecord] = coarse["members"]

            coarse_group = _make_group(
                coarse_key, coarse_label, coarse_walls, type_attrs,
                tier="coarse", parent_key=None,
            )
            all_groups.append(coarse_group)

            # ---- fire_acoustic tier: this coarse cluster's own walls,
            # re-partitioned by (Fire Rating, Acoustic STC). Only grows a
            # key/row distinct from its coarse parent where the coarse
            # cluster actually spans more than one such pair — a cluster
            # that's already uniform doesn't gain a meaningless sub-row. ----
            fa_buckets: dict[tuple[str | None, str | None], list[WallRecord]] = {}
            for wall in coarse_walls:
                attrs = type_attrs[wall.type_name]
                fa_buckets.setdefault((attrs.fire_rating, attrs.stc), []).append(wall)
            fa_ordered = sorted(
                fa_buckets.items(),
                key=lambda kv: (-len(kv[1]), kv[0][0] or "", kv[0][1] or ""),
            )
            splits_on_fire_acoustic = len(fa_ordered) > 1

            for fi, (fa_slice, fa_walls) in enumerate(fa_ordered, start=1):
                if splits_on_fire_acoustic:
                    fa_key = f"{coarse_key}{fi}"
                    fa_label = f"{coarse_label} ({_slice_label(*fa_slice)})"
                    fa_group = _make_group(
                        fa_key, fa_label, fa_walls, type_attrs,
                        tier="fire_acoustic", parent_key=coarse_key,
                    )
                    all_groups.append(fa_group)
                else:
                    fa_key, fa_label = coarse_key, coarse_label

                # ---- full tier: this fire/acoustic slice, re-partitioned
                # by height band. Same non-inflation rule. ----
                height_buckets: dict[str | None, list[WallRecord]] = {}
                for wall in fa_walls:
                    band = height_band(wall.height_mm)
                    height_buckets.setdefault(band, []).append(wall)
                height_ordered = sorted(
                    height_buckets.items(), key=lambda kv: (-len(kv[1]), kv[0] or ""),
                )
                splits_on_height = len(height_ordered) > 1

                for hi, (band, h_walls) in enumerate(height_ordered):
                    if splits_on_height:
                        full_key = f"{fa_key}{_key_suffix(hi).lower()}"
                        full_label = f"{fa_label} ({band})"
                        full_parent = fa_key
                    else:
                        full_key, full_label, full_parent = fa_key, fa_label, fa_key

                    full_group = _make_group(
                        full_key, full_label, h_walls, type_attrs,
                        tier="full", parent_key=full_parent,
                    )
                    full_group = TypeGroup(
                        **{
                            **full_group.__dict__,
                            "coarse_key": coarse_key,
                            "coarse_label": coarse_label,
                            "fire_acoustic_key": fa_key,
                            "fire_acoustic_label": fa_label,
                        },
                    )
                    # Only add a distinct `full`-tier row when height
                    # actually split something new — if it didn't, the
                    # fire_acoustic row above (or the coarse row, if that
                    # didn't split either) already represents this exact
                    # member set, and a second row with the same key and
                    # membership would be a content-free duplicate, not a
                    # useful drill-down.
                    if splits_on_height:
                        all_groups.append(full_group)
                    for wall in h_walls:
                        assignments[wall.object_id] = full_group

    return assignments, all_groups


def _slice_label(fire_rating: str | None, stc: str | None) -> str:
    """Render a (Fire Rating, Acoustic STC) pair for a fire_acoustic-tier label."""
    parts = []
    if fire_rating:
        parts.append(fire_rating)
    if stc:
        parts.append(f"STC-{stc}")
    return " · ".join(parts) if parts else "unrated"
