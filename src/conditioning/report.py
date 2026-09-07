"""Markdown conditioning report builder."""

from __future__ import annotations

from collections import Counter, defaultdict

from conditioning.attributes import bucket_height_ft, extract_attributes
from conditioning.codes import ACME_CODES, SIMILARITY_MATCH_THRESHOLD
from conditioning.predict import Prediction
from conditioning.walls import WallRecord, classify_walls


def _tally(items, key_fn) -> list[tuple[tuple, int]]:
    """Group `items` by `key_fn`, returning (key, count) ordered by count desc.

    Every table in this report describes a handful of wall *types* repeated
    across thousands of wall *instances* — a real model run produced 31,483
    elements spanning 60 distinct type names. Emitting one markdown row per
    element made a 62,027-row, 10 MB artifact that nobody read (and that
    nothing consumed: per-element data already lives on the objects in the
    Conditioned model, queryable via SQL/PowerBI, which is strictly better
    than a text table of the same thing). Tallying instead keeps every
    distinct outcome visible with a Count column, in ~100 rows.

    Keys must be all-string tuples — the sort falls back to comparing them
    when counts tie, and a None would raise.
    """
    counts: Counter = Counter(key_fn(i) for i in items)
    return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))


def _conf_str(confidence: float) -> str:
    return f"{confidence:.0%}" if confidence > 0 else "—"


def _observed_attributes_section(walls: list[WallRecord]) -> list[str]:
    """Report wall tag / fire rating / STC / stud size / height, and coverage.

    Coverage is the point of this section as much as the values are. Wall
    tag and fire rating can come from either a real Revit parameter or a
    name-convention regex (see attributes.py's 2026-09-07 note); STC and
    stud size are still name-only. Height comes from a real parameter and is
    reported separately — see attributes.bucket_height_ft — because it is a
    per-instance value, not a per-type one, and cannot share the same
    coverage/summary machinery as the others without silently averaging over
    real floor-to-floor variation.
    """
    counts: Counter = Counter()
    covered = 0
    fire_rating_by_source: Counter = Counter()
    height_covered = 0
    for wall in walls:
        attrs = extract_attributes(
            wall.type_name,
            fire_rating_param=wall.fire_rating,
            wall_tag=wall.type_mark,
        )
        if attrs:
            covered += 1
            counts[attrs.summary] += 1
        if attrs.fire_rating_source:
            fire_rating_by_source[attrs.fire_rating_source] += 1
        if bucket_height_ft(wall.height_mm):
            height_covered += 1

    lines = [
        "",
        "---",
        "",
        "## Observed type attributes",
        "",
    ]
    if not walls:
        return lines + ["No elements analysed."]

    pct = covered / len(walls)
    height_pct = height_covered / len(walls)
    lines += [
        f"Wall tag (Type Mark), fire rating, acoustic rating and stud size — "
        f"**{covered:,} of {len(walls):,} elements ({pct:.0%})** yield at "
        f"least one of them.",
        "",
        "Wall tag is always read from the Type Mark parameter. Fire rating "
        "prefers the real Fire Rating parameter where the wall carries one "
        f"({fire_rating_by_source.get('parameter', 0):,} elements) and falls "
        "back to reading it off the type name otherwise "
        f"({fire_rating_by_source.get('name', 0):,} elements) — the naming "
        "convention is no longer the only source, but it's still the only "
        "way to get acoustic rating (STC) and stud size, and the only "
        "fallback for fire rating on a wall whose parameter is blank. Where "
        "neither the parameter nor the name gives anything at all — "
        "`CW_Unitized_Spandrel`, `Empty` — the elements are simply absent "
        "from the table below; a low figure describes the naming/parameters, "
        "not the model's quality.",
        "",
        f"Height (Unconnected Height, a real parameter, rounded to the "
        f"nearest foot) is recorded separately: "
        f"**{height_covered:,} of {len(walls):,} elements ({height_pct:.0%})**. "
        "It is never folded into the summary column below, because it's a "
        "per-instance value — one wall type can span dozens of real heights "
        "— and merging it into a per-type summary would silently pick one "
        "and hide the rest.",
        "",
    ]
    if not counts:
        return lines + [
            "No elements in this model yielded a wall tag, fire rating, STC "
            "or stud size from either their parameters or their type names.",
        ]

    lines += [
        "| Wall Tag · Fire rating · STC · Stud | Elements |",
        "|--------------------------------------|----------|",
    ]
    for summary, count in counts.most_common():
        lines.append(f"| {summary} | {count} |")
    return lines


_TIER_LABELS = {
    "coarse": "Coarse (name only)",
    "fire_acoustic": "+ Fire/Acoustic",
    "full": "+ Height (full)",
}


def _category_section(results: list) -> list[str]:
    """Non-wall objects coded by the category engine, one row per (category, code).

    2026-09-07 (later still) — see categories.py. Kept separate from the wall
    tables above on purpose: these come from a different, smaller evidence
    base (no attribute vocabulary, no sub-grouping), and the table of rules
    behind them is a set of judgements the estimator has not yet reviewed.
    Says so up front rather than in a footnote.
    """
    rows: dict[tuple[str, str], list] = defaultdict(list)
    for result in results:
        rows[(result.category, result.code)].append(result)
    tiers: Counter = Counter(r.tier for r in results)
    methods: Counter = Counter(r.method for r in results)
    heuristic_count = sum(
        n for method, n in methods.items() if method.startswith("heuristic")
    )

    lines = [
        "",
        "## Non-wall elements — category engine",
        "",
        f"{len(results)} non-wall elements were given a Level 4 code by the "
        "category engine (`categories.py`). **The category → code table "
        "behind these is a set of judgements made without the estimator; "
        "every row below should be read as a proposal to correct, not a "
        "determination.** Elements in categories with no rule, or where no "
        "signal fired, are `not conditioned` in the `Conditioned/All` model "
        "rather than guessed.",
        "",
        "| Metric | Count |",
        "|--------|-------|",
        f"| Already coded (Tier 0) | {methods.get('existing', 0)} |",
        f"| Matched to a coded neighbour of the same category | "
        f"{methods.get('similarity', 0)} |",
        f"| Derived from category / Function / name | {heuristic_count} |",
        f"| Tier 1 / Tier 2 / Tier 3 | {tiers.get(1, 0)} / {tiers.get(2, 0)} "
        f"/ {tiers.get(3, 0)} |",
        "",
        "| Category | Level 4 Code | Description | Elements | Tiers | Methods |",
        "|----------|--------------|-------------|----------|-------|---------|",
    ]
    for (category, code), group in sorted(rows.items()):
        tier_str = ", ".join(
            f"T{t}: {n}" for t, n in sorted(Counter(r.tier for r in group).items())
        )
        method_str = ", ".join(sorted({r.method for r in group}))
        lines.append(
            f"| {category} | `{code}` | {ACME_CODES.get(code, '')} | "
            f"{len(group)} | {tier_str} | {method_str} |"
        )
    return lines


def _type_group_section(type_groups: list) -> list[str]:
    """Render the wall-type sub-groups found within each Level 4 code.

    This is the section an estimator actually reads: the Level 4 code says
    what kind of element it is, and this says which kind of that kind. The
    labels are derived from what the type names in each group share, so they
    are the model's own vocabulary rather than anything imposed — which is
    exactly what makes them a starting point for mapping onto the client's
    own wall types rather than a substitute for it.

    2026-09-07 (later still): `type_groups` is now the flat list every tier
    produces (see grouping.assign_type_groups), not a per-wall dict — a
    group can be more or less coarse, and the table now shows that as
    multiple rows per family (one per tier that actually split something)
    rather than picking one granularity and hiding the rest. A `Parent`
    column lets a reader trace a fine row back up to the coarser one it
    refines; a row with no parent is a coarse, top-of-hierarchy group.
    """
    lines = [
        "",
        "---",
        "",
        "## Wall type groups",
        "",
        "**These groups are not a classification and carry no authority.** "
        "They are observed by Speckle from the model's own element type "
        "names, they do not come from any estimating standard, and the "
        "letters/numbers are ours — assigned by size, renumbering whenever "
        "the model changes. Nothing here should be treated as a code.",
        "",
        "Element types are clustered by name similarity within each Level 4 "
        "code, so a code covering thousands of walls can be broken down by "
        "what those walls appear to be. Each label reports the words a "
        "group's members have in common.",
        "",
        "**Three tiers, not one.** A coarse group (name similarity only) can "
        "span a fire rating, acoustic rating or height difference that "
        "matters for cost — `Spandrel` and `Spandrel L5` differ by one word "
        "and are the same wall; `SMOKE` and `NFR` differ by one word and are "
        "different ones, and no similarity threshold separates those two "
        "cases. So each coarse group is refined into a Fire/Acoustic tier "
        "(splitting on Fire Rating + Acoustic STC), refined again into a "
        "full tier (splitting further on Height Band). A row only appears at "
        "a finer tier where that split actually found more than one value — "
        "a coarse group that's already uniform on fire/acoustic/height stops "
        "there and gains no redundant sub-rows. Pick whichever tier suits "
        "the question: coarse for \"which architect types resemble each "
        "other at all\", full for \"which of these would ever be priced "
        "differently\".",
        "",
        "**Description** answers the same span question in words, per row — "
        "one value where every member agrees, `varies (...)` listing all of "
        "them where they don't. On a `full`-tier row, Fire Rating, Acoustic "
        "STC and Height Band are always single values by construction; "
        "Type Mark and Stud Size can still vary — nothing splits on either.",
        "",
        "| Tier | Group | Parent | Label | Elements | Description |",
        "|------|-------|--------|-------|----------|-------------|",
    ]
    tier_order = {"coarse": 0, "fire_acoustic": 1, "full": 2}
    for group in sorted(
        type_groups,
        key=lambda g: (g.key.split(" · ")[0], -g.size, tier_order[g.tier], g.key),
    ):
        tier_label = _TIER_LABELS.get(group.tier, group.tier)
        parent = f"`{group.parent_key}`" if group.parent_key else "—"
        lines.append(
            f"| {tier_label} | `{group.key}` | {parent} | {group.label} | "
            f"{group.size} | {group.description or '—'} |"
        )
    return lines


def build_report(
    walls: list[WallRecord],
    predictions: list[Prediction],
    threshold: float = SIMILARITY_MATCH_THRESHOLD,
    type_groups: list | None = None,
    category_results: list | None = None,
) -> str:
    """Build a markdown conditioning report."""
    classification = classify_walls(walls)
    level4          = classification.level4
    non_level4_coded = classification.non_level4_coded
    uncoded         = classification.uncoded
    pred_by_wall_id = {p.wall.object_id: p for p in predictions}

    sim_preds  = [p for p in predictions if p.method == "similarity"]
    cat_preds  = [p for p in predictions if p.method == "heuristic_category"]
    heur_preds = [
        p for p in predictions if p.method not in ("similarity", "heuristic_category")
    ]
    tier_counts: Counter = Counter(p.tier for p in predictions)

    category_counts: Counter = Counter(w.category for w in walls)

    lines = [
        "# Conditioning Demo POC — Uniformat Prediction Report",
        "",
        "## Summary",
        "",
        "| Metric | Count |",
        "|--------|-------|",
        f"| Total elements analysed | {len(walls)} |",
        "",
        "**By category** (Walls + curtain wall family — mullions/panels/systems "
        "are separate Revit categories from Walls, and are included here)",
        "",
        "| Category | Count |",
        "|----------|-------|",
    ]
    for cat, count in sorted(category_counts.items()):
        lines.append(f"| {cat or '—'} | {count} |")

    lines += [
        "",
        "**Validation**",
        "",
        "| Metric | Count |",
        "|--------|-------|",
        f"| Has ACME Level 4 code (e.g. B2010.10) | {len(level4)} |",
        f"| Has a legacy/non-ACME code (remapped below) | {len(non_level4_coded)} |",
        f"| No code at all (predicted below) | {len(uncoded)} |",
        "",
        "**Conditioning — everything below is auto-applied for this POC** "
        "(no gating on confidence/tier yet — that's the direction of travel, "
        "not implemented here; Tier is recorded so a future pass can gate on it)",
        "",
        "| Metric | Count |",
        "|--------|-------|",
        f"| Predicted via similarity match | {len(sim_preds)} |",
        f"| Predicted via curtain wall category match | {len(cat_preds)} |",
        f"| Predicted via other heuristic / default | {len(heur_preds)} |",
        f"| Tier 0 (already correct — no work needed) | {len(level4)} |",
        f"| Tier 1 (high confidence) | {tier_counts.get(1, 0)} |",
        f"| Tier 2 (medium confidence) | {tier_counts.get(2, 0)} |",
        "| Tier 3 (low/no confidence — no signal at all, or one too "
        f"weak/contradictory to trust) | {tier_counts.get(3, 0)} |",
        f"| Similarity match threshold (fixed, not user-configurable) | {threshold} |",
        "",
        "---",
        "",
        "## Legacy Codes Remapped",
        "",
        "These elements already had an Assembly Code, but not in ACME's "
        "Level 4 dot-notation format (e.g. legacy ASTM Uniformat II codes "
        "like `B2010160`). They're run through the same fuzzy-match/heuristic "
        "as uncoded elements and remapped — the original code is kept "
        "alongside the new one for traceability, never silently discarded. "
        "An earlier version of this function left these untouched and "
        "flagged them for manual review instead; that undersold what the "
        "heuristic can already do and wasn't the intended POC outcome.",
        "",
        "| Type Name | Category | Original Code | New Code | Confidence "
        "| Tier | Count |",
        "|-----------|----------|----------------|----------|------------"
        "|------|-------|",
    ]

    if non_level4_coded:
        def _remap_key(w: WallRecord) -> tuple:
            p = pred_by_wall_id.get(w.object_id)
            return (
                w.type_name or "—",
                w.category or "—",
                f"`{w.assembly_code}`",
                f"`{p.predicted_code}`" if p else "—",
                _conf_str(p.confidence) if p else "—",
                f"Tier {p.tier}" if p else "—",
            )

        for key, count in _tally(non_level4_coded, _remap_key):
            lines.append("| " + " | ".join(key) + f" | {count} |")
    else:
        lines.append("| — | — | — | — | — | — | 0 |")

    lines += [
        "",
        "---",
        "",
        "## Predictions (all non-Level4 elements — blank + remapped)",
        "",
        "Grouped by outcome — every element sharing a type name, original "
        "code and prediction is one row with a Count. Per-element detail "
        "isn't reproduced here: it's written onto each object in the "
        "Conditioned model, where it can be queried directly rather than "
        "read out of a table.",
        "",
        "| Type Name | Category | Original Code | Predicted Code "
        "| Confidence | Tier | Method | Matched From | Count |",
        "|-----------|----------|----------------|-----------------"
        "|------------|------|--------|--------------|-------|",
    ]

    def _pred_key(p: Prediction) -> tuple:
        w = p.wall
        return (
            w.type_name or "—",
            w.category or "—",
            f"`{w.assembly_code}`" if w.is_coded else "—",
            f"`{p.predicted_code}`",
            _conf_str(p.confidence),
            f"Tier {p.tier}",
            p.method,
            p.matched_from or "—",
        )

    if predictions:
        for key, count in _tally(predictions, _pred_key):
            lines.append("| " + " | ".join(key) + f" | {count} |")
    else:
        lines.append("| — | — | — | — | — | — | — | — | 0 |")

    tier3_preds = [p for p in predictions if p.tier == 3]
    lines += [
        "",
        "---",
        "",
        "## Needs a Closer Look (Tier 3)",
        "",
    ]
    if tier3_preds:
        lines += [
            f"{len(tier3_preds)} prediction(s) landed at Tier 3 — not enough "
            "confidence to trust. Two different reasons land an element here: "
            "either nothing about it resembled anything else in the model at "
            "all (`default` method, `no clue "
            "what this element is`), or something DID match but it's a lone, "
            "uncorroborated "
            "signal (a coin-toss keyword match) or one that actively contradicts "
            "another "
            "signal on the same wall — see Method below for which. These are still "
            "auto-applied for this POC (see the direction-of-travel note above), but "
            "they're the ones actually worth a human looking at, not just a quick "
            "check.",
            "",
            "| Type Name | Category | Original Code | Predicted Code | Confidence | "
            "Method | Count |",
            "|-----------|----------|----------------|-----------------|------------|--------|-------|",
        ]

        def _tier3_key(p: Prediction) -> tuple:
            w = p.wall
            return (
                w.type_name or "—",
                w.category or "—",
                f"`{w.assembly_code}`" if w.is_coded else "—",
                f"`{p.predicted_code}`",
                f"{p.confidence:.0%}",
                p.method,
            )

        for key, count in _tally(tier3_preds, _tier3_key):
            lines.append("| " + " | ".join(key) + f" | {count} |")
    else:
        lines.append("None — every prediction cleared at least Tier 2.")

    lines += [
        "",
        "---",
        "",
        "## Elements Not Conditioned (already ACME Level 4)",
        "",
        "These elements already carry an ACME Level 4 code and were passed through "
        "unchanged.",
        "",
        "| Type Name | Category | Type Mark | Function | Width (mm) | Code | Count |",
        "|-----------|----------|-----------|----------|------------|------|-------|",
    ]

    level4_counts: Counter = Counter()
    level4_meta: dict = {}
    for w in level4:
        key = (w.type_name, w.category, w.assembly_code)
        level4_counts[key] += 1
        level4_meta[key] = (w.type_mark, w.function, round(w.width_mm))

    if level4_counts:
        for (type_name, category, code), count in sorted(
            level4_counts.items(), key=lambda x: x[0][2] or ""
        ):
            tm, fn, ww = level4_meta.get((type_name, category, code), ("", "", 0))
            lines.append(
                f"| {type_name} | {category or '—'} | {tm} | {fn} | {ww} "
                f"| `{code}` | {count} |"
            )
    else:
        lines.append("| — | — | — | — | — | _none_ | 0 |")

    lines += [
        "",
        "---",
        "",
        "## Final Code Distribution (all elements)",
        "",
        "Every element ends up with an ACME Level 4 code — existing ones "
        "passed through, everything else predicted (blank or remapped from "
        "legacy format) and auto-applied.",
        "",
        "| Code | Description | Count |",
        "|------|-------------|-------|",
    ]

    dist: dict[str, int] = defaultdict(int)
    for w in level4:
        if w.assembly_code:
            dist[w.assembly_code] += 1
    for p in predictions:
        dist[p.predicted_code] += 1

    for code in sorted(dist):
        lines.append(f"| `{code}` | {ACME_CODES.get(code, code)} | {dist[code]} |")

    lines += _observed_attributes_section(walls)

    if type_groups:
        lines += _type_group_section(type_groups)

    if category_results:
        lines += _category_section(category_results)

    lines += ["", "---", "_Generated by Conditioning Demo POC · Speckle Automate_"]
    return "\n".join(lines)
