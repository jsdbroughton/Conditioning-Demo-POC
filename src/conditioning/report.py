"""Markdown conditioning report builder."""

from __future__ import annotations

from collections import Counter, defaultdict

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


def build_report(
    walls: list[WallRecord],
    predictions: list[Prediction],
    threshold: float = SIMILARITY_MATCH_THRESHOLD,
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

    lines += ["", "---", "_Generated by Conditioning Demo POC · Speckle Automate_"]
    return "\n".join(lines)
