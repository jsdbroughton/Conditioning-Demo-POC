"""Conditioning Demo POC — Uniformat Assembly Code prediction for Revit walls.

This file is the orchestrator only — the Speckle Automate runtime invokes it
directly (see Dockerfile / README "Running the Docker Container Image"), so
it stays here as a thin script at the repo root. All business logic lives in
the `conditioning` package under src/ — see src/conditioning/__init__.py for
the module map.

Identifies wall elements missing Uniformat Assembly Codes, predicts codes via
similarity matching against already-coded walls and a heuristic fallback, then:

  1. Attaches per-object predictions to the Speckle viewer
  2. Writes a markdown conditioning report as a run artifact
  3. Creates a new version in a "Conditioned/<source model name>" model with
     predicted codes imprinted — namespaced per source model so runs from
     different models don't collide into one shared output
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from pydantic import Field
from pydantic.json_schema import GenerateJsonSchema, JsonSchemaMode
from speckle_automate import AutomateBase, AutomationContext, execute_automate_function

from conditioning.codes import DEFAULT_CONDITIONING_KEY
from conditioning.grouping import assign_type_groups
from conditioning.instrumentation import stage
from conditioning.predict import predict_codes
from conditioning.report import build_report
from conditioning.speckle_io import (
    attach_viewer_annotations,
    create_conditioned_version,
)
from conditioning.walls import classify_walls, collect_walls


class FunctionInputs(AutomateBase):
    """One user-tunable parameter: the conditioned-code property name.

    A `confidence_threshold` field ("Confidence Threshold" in the Automate
    UI) was removed 2026-08-14 — it described itself as gating "a
    model-based prediction," which overstated what it did (there's no
    trained model, just a same-run similarity heuristic — see
    codes.SIMILARITY_MATCH_THRESHOLD), and had no observable effect on any
    real run to date: see that constant's comment for why. An input that
    never visibly changes a run's output is worse than no input at all.

    `code_property_name` replaces it as the one genuinely meaningful input:
    it's the literal property key written onto every wall object, so it
    changes something visible on every single run — the opposite problem to
    the field it replaces. Defaulting it here (rather than hardcoding a
    fixed key in codes.py) also means this function's source never has to
    hardcode any one organisation's naming convention.
    """

    code_property_name: str = Field(
        default=DEFAULT_CONDITIONING_KEY,
        title="Conditioned Code Property Name",
        description=(
            "Name of the property written onto every wall object's "
            "properties, holding the conditioning result (Status, Level 4 "
            "Code, Confidence, Tier, Method, Original Code). Set this to "
            "match your organisation's own naming convention."
        ),
    )

    @classmethod
    def model_json_schema(
        cls,
        by_alias: bool = True,
        ref_template: str = "#/$defs/{model}",
        schema_generator: type[GenerateJsonSchema] = GenerateJsonSchema,
        mode: JsonSchemaMode = "validation",
        *,
        union_format: Literal["any_of", "primitive_type_array"] = "any_of",
    ) -> dict[str, Any]:
        """Strip the JSON Schema dialect declaration for GitHub Action compatibility.

        AutomateGenerateJsonSchema adds '$schema: https://json-schema.org/draft/2020-12/schema'
        but the speckle-automate-github-action uses an AJV version that doesn't load
        that
        meta-schema, causing registration to fail with 'no schema with key or ref'
        error.
        Removing the field lets AJV use its default validation mode.
        """
        schema = super().model_json_schema(
            by_alias=by_alias,
            ref_template=ref_template,
            schema_generator=schema_generator,
            mode=mode,
            union_format=union_format,
        )
        schema.pop("$schema", None)
        return schema


def automate_function(
    automate_context: AutomationContext,
    function_inputs: FunctionInputs,
) -> None:
    """Run Uniformat conditioning on all wall elements in the triggered version."""
    # Each stage is wrapped in `stage()` so the run log carries elapsed time
    # and peak RSS per phase. A deployed run that dies otherwise gives you a
    # pod exit code and nothing to attribute it to — see
    # conditioning/instrumentation.py.

    # 1. Receive and traverse
    with stage("receive_version"):
        root = automate_context.receive_version()

    with stage("collect_walls"):
        walls = collect_walls(root)

    if not walls:
        automate_context.mark_run_success(
            "No wall elements found in this version — nothing to condition."
        )
        return

    classification = classify_walls(walls)
    print(
        f"[ConditioningPOC] "
        f"{len(classification.coded)} with any code "
        f"({len(classification.level4)} Level 4, "
        f"{len(classification.non_level4_coded)} other format), "
        f"{len(classification.uncoded)} uncoded."
    )

    # 2. Predict codes for uncoded walls (threshold defaults to
    # codes.SIMILARITY_MATCH_THRESHOLD — no longer a user input, see
    # FunctionInputs docstring above)
    with stage("predict_codes"):
        predictions = predict_codes(walls)

    # 2b. Sub-group wall types within each predicted code. A Level 4 code on
    # its own answers "what kind of element" and immediately raises "yes, but
    # which one" — a 6" smoke partition and a furring wall are both
    # C1010.10 and cost nothing like each other. See conditioning/grouping.py.
    with stage("assign_type_groups"):
        type_groups = assign_type_groups(walls, predictions)
        print(
            f"[ConditioningPOC] {len(set(g.key for g in type_groups.values()))} "
            f"wall-type groups across {len(walls)} elements."
        )

    # 3. Per-object viewer annotations
    with stage("attach_viewer_annotations"):
        attach_viewer_annotations(
            automate_context,
            classification.level4,
            classification.non_level4_coded,
            predictions,
        )

    # 4. Conditioning report. Deliberately not bound to a local: the report
    # is the largest single string this function builds, and holding it
    # alive through create_conditioned_version() below — the peak-memory
    # stage, where the whole received graph is re-serialized — stacks the
    # two high-water marks on top of each other for no reason.
    with stage("build_and_store_report"):
        report_path = Path("conditioning_report.md")
        report_path.write_text(
            build_report(walls, predictions, type_groups=type_groups),
            encoding="utf-8",
        )
        try:
            automate_context.store_file_result(report_path)
        except Exception as exc:
            print(f"[ConditioningPOC] Could not store report: {exc}")

    # 5. Create augmented 'Conditioned/<source model name>' model version
    with stage("create_conditioned_version"):
        new_version_id = create_conditioned_version(
            automate_context, root, walls, predictions,
            code_property_name=function_inputs.code_property_name,
            type_groups=type_groups,
        )

    # 6. Success summary — leads with the outcome (what changed and how
    # trustworthy it is), not a raw tally, since this is the headline a
    # reviewer sees on the run report before opening anything.
    sim_count   = sum(1 for p in predictions if p.method == "similarity")
    cat_count   = sum(1 for p in predictions if p.method == "heuristic_category")
    tier1_count = sum(1 for p in predictions if p.tier == 1)
    tier2_count = sum(1 for p in predictions if p.tier == 2)
    tier3_count = sum(1 for p in predictions if p.tier == 3)

    # Tier 3 gets called out on its own, not folded into "Tier 2/3" — Tier 2
    # means "quick check", Tier 3 means "a human actually needs to look at
    # this one" (see codes.py's tier definitions), and that distinction
    # shouldn't get lost in the headline just because both are non-Tier-1.
    if not predictions:
        confidence_note = "nothing needed conditioning"
    elif tier3_count:
        confidence_note = (
            f"{tier1_count} at Tier 1, {tier2_count} at Tier 2, "
            f"{tier3_count} at Tier 3 — those genuinely need a closer look, "
            f"not just a quick check"
        )
    elif tier2_count:
        confidence_note = (
            f"{tier1_count} at Tier 1, {tier2_count} flagged Tier 2 "
            f"for a quick review"
        )
    else:
        confidence_note = "every prediction landed at Tier 1 — no manual triage needed"

    summary = (
        f"Auto-conditioned all {len(walls)} wall elements to Uniformat Level 4 "
        f"in one pass — {len(classification.level4)} already correct (Tier 0), "
        f"{len(classification.non_level4_coded)} legacy codes remapped, "
        f"{len(classification.uncoded)} classified from a blank Assembly Code. "
        f"{confidence_note}."
    )
    if sim_count:
        summary += (
            f" {sim_count} matched directly against an already-coded reference wall."
        )
    if cat_count:
        summary += f" {cat_count} classified via Revit's own curtain wall category."
    if new_version_id:
        summary += f" Conditioned model: {new_version_id}"

    automate_context.mark_run_success(summary)


if __name__ == "__main__":
    execute_automate_function(automate_function, FunctionInputs)
