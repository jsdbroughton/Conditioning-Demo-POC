"""Markdown conditioning report builder."""

from __future__ import annotations

from collections import Counter, defaultdict

from conditioning.codes import ACME_CODES, SIMILARITY_MATCH_THRESHOLD
from conditioning.predict import Prediction
from conditioning.walls import WallRecord, classify_walls


def build_report(
    walls: list[WallRecord],
    predictions: list[Prediction],
    threshold: float,
) -> str:
    """Build a markdown conditioning report."""
    classification = classify_walls(walls)
    level4          = classification.level4
    non_level4_coded = classification.non_level4_coded
    uncoded         = classification.uncoded
    pred_by_wall_id = {p.wall.object_id: p for p in predictions}

    sim_preds  = [p for p in predictions if p.method == "similarity"]
    cat_preds  = [p for p in predictions if p.method == "heuristic_category"]
    heur_preds = [p for p in predictions if p.method not in ("similarity", "heuristic_category")]
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
        f"| Tier 3 (low/no confidence — no signal at all, or one too weak/contradictory to trust) | {tier_counts.get(3, 0)} |",
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
        "| Type Name | Category | Original Code | New Code | Confidence | Tier |",
        "|-----------|----------|----------------|----------|------------|------|",
    ]

    if non_level4_coded:
        for w in sorted(non_level4_coded, key=lambda w: w.assembly_code or ""):
            p = pred_by_wall_id.get(w.object_id)
            new_code = f"`{p.predicted_code}`" if p else "—"
            conf_str = f"{p.confidence:.0%}" if p and p.confidence > 0 else "—"
            tier_str = f"Tier {p.tier}" if p else "—"
            lines.append(
                f"| {w.type_name or '—'} | {w.category or '—'} | `{w.assembly_code}` "
                f"| {new_code} | {conf_str} | {tier_str} |"
            )
    else:
        lines.append("| — | — | — | — | — | — |")

    lines += [
        "",
        "---",
        "",
        "## Predictions (all non-Level4 elements — blank + remapped)",
        "",
        "| # | Type Name | Category | Level | Width (mm) | Original Code | Predicted Code | Confidence | Tier | Method | Matched From |",
        "|---|-----------|----------|-------|------------|----------------|-----------------|------------|------|--------|--------------|",
    ]

    for i, p in enumerate(sorted(predictions, key=lambda x: -x.confidence), 1):
        w         = p.wall
        conf_str  = f"{p.confidence:.0%}" if p.confidence > 0 else "—"
        matched   = p.matched_from or "—"
        orig_code = f"`{w.assembly_code}`" if w.is_coded else "—"
        lines.append(
            f"| {i} | {w.type_name or '—'} | {w.category or '—'} | {w.level or '—'} | {round(w.width_mm)} "
            f"| {orig_code} | `{p.predicted_code}` | {conf_str} | Tier {p.tier} | {p.method} | {matched} |"
        )

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
            f"{len(tier3_preds)} prediction(s) landed at Tier 3 — not enough confidence "
            "to trust. Two different reasons land an element here: either nothing about "
            "it resembled anything else in the model at all (`default` method, `no clue "
            "what this element is`), or something DID match but it's a lone, uncorroborated "
            "signal (a coin-toss keyword match) or one that actively contradicts another "
            "signal on the same wall — see Method below for which. These are still "
            "auto-applied for this POC (see the direction-of-travel note above), but "
            "they're the ones actually worth a human looking at, not just a quick check.",
            "",
            "| Type Name | Category | Original Code | Predicted Code | Confidence | Method |",
            "|-----------|----------|----------------|-----------------|------------|--------|",
        ]
        for p in sorted(tier3_preds, key=lambda x: x.confidence):
            w         = p.wall
            orig_code = f"`{w.assembly_code}`" if w.is_coded else "—"
            lines.append(
                f"| {w.type_name or '—'} | {w.category or '—'} | {orig_code} "
                f"| `{p.predicted_code}` | {p.confidence:.0%} | {p.method} |"
            )
    else:
        lines.append("None — every prediction cleared at least Tier 2.")

    lines += [
        "",
        "---",
        "",
        "## Elements Not Conditioned (already ACME Level 4)",
        "",
        "These elements already carry an ACME Level 4 code and were passed through unchanged.",
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
        for (type_name, category, code), count in sorted(level4_counts.items(), key=lambda x: x[0][2] or ""):
            tm, fn, ww = level4_meta.get((type_name, category, code), ("", "", 0))
            lines.append(f"| {type_name} | {category or '—'} | {tm} | {fn} | {ww} | `{code}` | {count} |")
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
