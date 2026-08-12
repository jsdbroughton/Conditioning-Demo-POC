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

from conditioning.predict import predict_codes
from conditioning.report import build_report
from conditioning.speckle_io import (
    attach_viewer_annotations,
    create_conditioned_version,
)
from conditioning.walls import classify_walls, collect_walls


class FunctionInputs(AutomateBase):
    """Tunable parameters exposed in the Automate UI."""

    confidence_threshold: float = Field(
        default=0.65,
        title="Confidence Threshold",
        description=(
            "Minimum similarity score (0–1) to accept a model-based prediction. "
            "Below this threshold the heuristic fallback is used instead."
        ),
        ge=0.0,
        le=1.0,
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
        but the speckle-automate-github-action uses an AJV version that doesn't load that
        meta-schema, causing registration to fail with 'no schema with key or ref' error.
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
    # 1. Receive and traverse
    root  = automate_context.receive_version()
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
        f"({len(classification.level4)} Turner Level 4, "
        f"{len(classification.non_level4_coded)} other format), "
        f"{len(classification.uncoded)} uncoded."
    )

    # 2. Predict codes for uncoded walls
    predictions = predict_codes(walls, function_inputs.confidence_threshold)

    # 3. Per-object viewer annotations
    attach_viewer_annotations(
        automate_context,
        classification.level4,
        classification.non_level4_coded,
        predictions,
    )

    # 4. Conditioning report
    report_md   = build_report(walls, predictions, function_inputs.confidence_threshold)
    report_path = Path("conditioning_report.md")
    report_path.write_text(report_md, encoding="utf-8")
    try:
        automate_context.store_file_result(report_path)
    except Exception as exc:
        print(f"[ConditioningPOC] Could not store report: {exc}")

    # 5. Create augmented 'Conditioned/<source model name>' model version
    new_version_id = create_conditioned_version(
        automate_context, root, walls, predictions
    )

    # 6. Success summary
    sim_count  = sum(1 for p in predictions if p.method == "similarity")
    heur_count = len(predictions) - sim_count
    summary = (
        f"Processed {len(walls)} walls — "
        f"{len(classification.level4)} already Turner Level 4, "
        f"{len(classification.non_level4_coded)} non-Level4 codes flagged for "
        f"manual crosswalk review (NOT overwritten), "
        f"{len(classification.uncoded)} uncoded — "
        f"{len(predictions)} predicted "
        f"({sim_count} similarity, {heur_count} heuristic)."
    )
    if new_version_id:
        summary += f" Conditioned model version: {new_version_id}"

    automate_context.mark_run_success(summary)


if __name__ == "__main__":
    execute_automate_function(automate_function, FunctionInputs)
