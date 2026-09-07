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
stud_sizes rollups report what the group's members actually share — one
value when they agree, "varies (...)" listing all of them when they don't.
This is reporting on the group's membership, never an input to it:
`_group_similarity` still compares type-name tokens only, unchanged.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass

from conditioning.attributes import extract_attributes
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
    """One cluster of similar wall types within a single Level 4 code."""

    key: str      # "C1010.10 · inferred group A" — the letter is ours, see _INFERRED
    label: str    # derived from what the members share: "CW Unitized IGU"
    size: int     # number of elements, not number of type names
    # Everything below is a rollup OVER the group's members, computed after
    # clustering — never an input to which cluster a wall lands in (that's
    # _group_similarity, type-name tokens only). See the module's 2026-09-07
    # note for why Type Mark specifically cannot just become the group's
    # identity — real groups routinely span several of them.
    description: str = ""  # "5 elements — Type Mark H6, Fire Rating SMOKE, ..."
    # Distinct values across all members — e.g. {"H6"} for one shared mark,
    # {"K1","K2","K3"} for a mixed group. fire_ratings is param-or-name (see
    # attributes.py); wall_tags/stc_values/stud_sizes are their usual source.
    wall_tags: frozenset[str] = frozenset()
    fire_ratings: frozenset[str] = frozenset()
    stc_values: frozenset[str] = frozenset()
    stud_sizes: frozenset[str] = frozenset()


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


def _merge_bucket_attrs(cluster: dict, attrs) -> None:
    """Fold one (type_name, family) bucket's attributes into a cluster's rollup.

    Called once per distinct bucket as it joins a cluster (new or existing) —
    never per element. Blank values are skipped rather than added as an
    empty-string member of the set, matching _describe_group's "nothing to
    report" case.
    """
    if attrs.wall_tag:
        cluster["wall_tags"].add(attrs.wall_tag)
    if attrs.fire_rating:
        cluster["fire_ratings"].add(attrs.fire_rating)
    if attrs.stc:
        cluster["stc_values"].add(attrs.stc)
    if attrs.stud:
        cluster["stud_sizes"].add(attrs.stud)


def _describe_group(
    size: int,
    wall_tags: set[str],
    fire_ratings: set[str],
    stc_values: set[str],
    stud_sizes: set[str],
) -> str:
    """Plain-English account of what a group's members actually have in common.

    One value per factor when the group agrees on it; "varies (...)" listing
    every distinct value seen when it doesn't — the honest answer for a group
    like the real 100-element Furring cluster that spans six Type Marks (see
    the module's 2026-09-07 note). Never invents a single representative
    value and hides the rest.
    """
    noun = "element" if size == 1 else "elements"
    facts = []
    for label, values in (
        ("Type Mark", wall_tags),
        ("Fire Rating", fire_ratings),
        ("Acoustic STC", stc_values),
        ("Stud Size", stud_sizes),
    ):
        if len(values) == 1:
            facts.append(f"{label} {next(iter(values))}")
        elif len(values) > 1:
            facts.append(f"{label} varies ({', '.join(sorted(values))})")
    if not facts:
        facts.append("no Type Mark, Fire Rating, STC or Stud Size recognised")
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


def assign_type_groups(
    walls: Iterable[WallRecord],
    predictions: Iterable[Prediction],
    threshold: float = GROUP_SIMILARITY_THRESHOLD,
) -> dict[str, TypeGroup]:
    """Map each wall's object_id to the wall-type group it belongs to.

    Groups are formed independently within each Level 4 code — an exterior
    veneer must never cluster with an interior partition just because both
    are called "Type A" — and are keyed and lettered by descending element
    count, so `<code>-A` is always the largest family under that code.

    Clustering is greedy leader assignment, seeded biggest-first: the most
    common type in a bucket becomes the first seed, and every less common
    type joins the first seed it resembles or starts its own group. Chosen
    over single-linkage because linkage chains — A resembles B, B resembles
    C, and C ends up grouped with an A it looks nothing like, which is how
    an entire model collapses into one group. Deterministic given a stable
    sort, which matters because these keys get written onto objects and
    compared between runs.
    """
    pred_map = {p.wall.object_id: p for p in predictions}
    walls = list(walls)

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

    for code in sorted(buckets):
        types = buckets[code]
        ordered = sorted(types.items(), key=lambda kv: (-len(kv[1]), kv[0]))

        clusters: list[dict] = []
        for (type_name, _family), members in ordered:
            tokens = _tokens(type_name)
            # Type Mark and Fire Rating are Type Parameters (see walls.py) —
            # constant across every member of one (type_name, family) bucket,
            # so any one member is a safe representative. Computed once per
            # distinct bucket, not per element, for the same reason
            # predict.py dedupes by fingerprint: a real model has far fewer
            # distinct types than elements.
            rep = members[0]
            attrs = extract_attributes(
                type_name, fire_rating_param=rep.fire_rating, wall_tag=rep.type_mark
            )

            for cluster in clusters:
                if _group_similarity(tokens, cluster["seed"]) >= threshold:
                    cluster["shared"] &= tokens
                    cluster["members"].extend(members)
                    _merge_bucket_attrs(cluster, attrs)
                    break
            else:
                cluster = {
                    "seed": tokens,
                    "seed_name": type_name,
                    "shared": set(tokens),
                    "members": list(members),
                    "wall_tags": set(),
                    "fire_ratings": set(),
                    "stc_values": set(),
                    "stud_sizes": set(),
                }
                _merge_bucket_attrs(cluster, attrs)
                clusters.append(cluster)

        clusters.sort(key=lambda c: (-len(c["members"]), c["seed_name"]))

        # Labels are derived, so two groups under one code can land on the
        # same text. Disambiguate with the first token that is distinctive to
        # the seed, falling back to the key — a pivot table with two
        # identically-named rows is worse than a slightly clumsy label.
        used: set[str] = set()
        for i, cluster in enumerate(clusters):
            key = f"{code} · {_INFERRED} {_key_suffix(i)}"
            label = _label_from(
                cluster["seed_name"],
                cluster["shared"],
                cluster["seed_name"],
            )
            if label in used:
                extra = next(
                    (m.group() for m in _WORD.finditer(cluster["seed_name"])
                     if m.group().lower() not in cluster["shared"]),
                    None,
                )
                label = f"{label} ({extra})" if extra else f"{label} ({_key_suffix(i)})"
            used.add(label)

            size = len(cluster["members"])
            group = TypeGroup(
                key=key,
                label=label,
                size=size,
                description=_describe_group(
                    size,
                    cluster["wall_tags"],
                    cluster["fire_ratings"],
                    cluster["stc_values"],
                    cluster["stud_sizes"],
                ),
                wall_tags=frozenset(cluster["wall_tags"]),
                fire_ratings=frozenset(cluster["fire_ratings"]),
                stc_values=frozenset(cluster["stc_values"]),
                stud_sizes=frozenset(cluster["stud_sizes"]),
            )
            for wall in cluster["members"]:
                assignments[wall.object_id] = group

    return assignments
