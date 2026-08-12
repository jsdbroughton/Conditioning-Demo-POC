"""Markdown conditioning report builder."""

from __future__ import annotations

from collections import Counter, defaultdict

from conditioning.codes import TURNER_CODES
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
    sim_preds       = [p for p in predictions if p.method == "similarity"]
    heur_preds      = [p for p in predictions if p.method != "similarity"]

    lines = [
        "# Conditioning Demo POC — Uniformat Prediction Report",
        "",
        "## Summary",
        "",
        "| Metric | Count |",
        "|--------|-------|",
        f"| Total walls analysed | {len(walls)} |",
        "",
        "**Validation**",
        "",
        "| Metric | Count |",
        "|--------|-------|",
        f"| Has Turner Level 4 code (e.g. B2010.10) | {len(level4)} |",
        f"| Has code but NOT Turner Level 4 format (needs review) | {len(non_level4_coded)} |",
        f"| No code at all (uncoded) | {len(uncoded)} |",
        "",
        "**Conditioning**",
        "",
        "| Metric | Count |",
        "|--------|-------|",
        f"| Predicted via similarity match | {len(sim_preds)} |",
        f"| Predicted via heuristic / default | {len(heur_preds)} |",
        f"| Confidence threshold | {threshold} |",
        "",
        "---",
        "",
        "## Non-Level4 Codes (needs manual crosswalk review — NOT auto-changed)",
        "",
        "These walls already have an Assembly Code, but not in Turner's Level 4 "
        "dot-notation format (e.g. legacy ASTM Uniformat II codes like "
        "`B2010160`). Conditioning does **not** overwrite these — a prior "
        "version of this function did, discarding the specific sub-code in "
        "favour of a generic default, which is the exact regression caught "
        "live on the 2026-07-17 Turner call. They're flagged via "
        "`Turner Level 4 Code Review Needed` for a human to map, and their "
        "type/family/function are used as similarity references for "
        "genuinely uncoded walls below.",
        "",
        "| Type Name | Type Mark | Function | Width (mm) | Original Code |",
        "|-----------|-----------|----------|------------|---------------|",
    ]

    nl4_counts: Counter = Counter()
    nl4_meta: dict = {}
    for w in non_level4_coded:
        key = (w.type_name, w.assembly_code)
        nl4_counts[key] += 1
        nl4_meta[key] = (w.type_mark, w.function, round(w.width_mm))

    if nl4_counts:
        for (type_name, code), count in sorted(nl4_counts.items(), key=lambda x: x[0][1] or ""):
            tm, fn, ww = nl4_meta.get((type_name, code), ("", "", 0))
            lines.append(f"| {type_name} | {tm} | {fn} | {ww} | `{code}` ×{count} |")
    else:
        lines.append("| — | — | — | — | _none_ |")

    lines += [
        "",
        "---",
        "",
        "## Predictions (walls with NO existing code)",
        "",
        "| # | Type Name | Level | Width (mm) | Predicted Code | Confidence | Method | Matched From |",
        "|---|-----------|-------|------------|----------------|------------|--------|--------------|",
    ]

    for i, p in enumerate(sorted(predictions, key=lambda x: -x.confidence), 1):
        w        = p.wall
        conf_str = f"{p.confidence:.0%}" if p.confidence > 0 else "—"
        matched  = p.matched_from or "—"
        lines.append(
            f"| {i} | {w.type_name or '—'} | {w.level or '—'} | {round(w.width_mm)} "
            f"| `{p.predicted_code}` | {conf_str} | {p.method} | {matched} |"
        )

    lines += [
        "",
        "---",
        "",
        "## Elements Not Conditioned (already Turner Level 4)",
        "",
        "These walls already carry a Turner Level 4 code and were passed through unchanged.",
        "",
        "| Type Name | Type Mark | Function | Width (mm) | Code | Count |",
        "|-----------|-----------|----------|------------|------|-------|",
    ]

    level4_counts: Counter = Counter()
    level4_meta: dict = {}
    for w in level4:
        key = (w.type_name, w.assembly_code)
        level4_counts[key] += 1
        level4_meta[key] = (w.type_mark, w.function, round(w.width_mm))

    if level4_counts:
        for (type_name, code), count in sorted(level4_counts.items(), key=lambda x: x[0][1] or ""):
            tm, fn, ww = level4_meta.get((type_name, code), ("", "", 0))
            lines.append(f"| {type_name} | {tm} | {fn} | {ww} | `{code}` | {count} |")
    else:
        lines.append("| — | — | — | — | _none_ | 0 |")

    lines += [
        "",
        "---",
        "",
        "## Final Code Distribution (all elements)",
        "",
        "Turner Level 4 codes (existing + predicted) vs. legacy codes still "
        "awaiting manual crosswalk review — kept separate so a passing run "
        "can't be misread as \"fully conditioned\".",
        "",
        "| Code | Description | Count | Status |",
        "|------|-------------|-------|--------|",
    ]

    dist: dict[str, int] = defaultdict(int)
    for w in level4:
        if w.assembly_code:
            dist[w.assembly_code] += 1
    for p in predictions:
        dist[p.predicted_code] += 1

    for code in sorted(dist):
        lines.append(f"| `{code}` | {TURNER_CODES.get(code, code)} | {dist[code]} | Level 4 |")

    legacy_dist: Counter = Counter(w.assembly_code for w in non_level4_coded if w.assembly_code)
    for code, count in sorted(legacy_dist.items()):
        lines.append(f"| `{code}` | _legacy / non-Turner format_ | {count} | Needs review |")

    lines += ["", "---", "_Generated by Conditioning Demo POC · Speckle Automate_"]
    return "\n".join(lines)
