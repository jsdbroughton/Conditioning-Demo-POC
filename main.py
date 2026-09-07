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

2026-09-07: ported onto specklepy 2026.9's parquet bundle format, in place of
the pre-2026.9 JSON object graph — see
https://docs.speckle.systems/next/developers/sdks/python/breaking-changes
and https://docs.speckle.systems/next/developers/object-model/overview.
`AutomationContext.receive_version()`/`.create_new_version_in_project()`
still only speak the old `operations.receive`/`send` JSON-graph transport
even on specklepy 2026.9.0b3 (checked directly against that release's
`speckle_automate/automation_context.py`) — bumping the dependency alone
changes nothing, and the old receive path's Base-tree compatibility
projection silently drops the top-level `category`/`type`/`family` fields
and the level string this function's wall-identification logic depends on
(confirmed by reading `specklepy/bundle/base_projection.py`; not carried
over by design — see the Warning on the breaking-changes page that this
projection "is not a lossless round trip"). So this function bypasses
`AutomationContext` for both the receive and the publish and talks to the
new `operations.receive3`/`send3` bundle API directly:

  - Receive: `operations.receive3(...)` returns a disposable
    `specklepy.bundle.model.Model` — a flat `model.objects` list plus typed
    relations, not a `Base` tree (there is no more `.elements` to recurse).
    See conditioning/walls.py's module docstring for exactly how wall
    identification reads that shape.
  - Publish: mutating the received Model and resending it is explicitly
    unsupported ("Receiving a bundle-only version as a Base tree and
    sending it again with operations.send is not a supported copy
    workflow" — same breaking-changes page), and there's nothing to mutate
    in-place anyway since Model is a read-only view over the downloaded
    parquet files. create_conditioned_version() in speckle_io.py instead
    builds a fresh `specklepy.bundle.builder.BundleBuilder` from the
    conditioned WallRecord data and publishes it with `operations.send3`.

`automate_context` (AutomationContext) is kept and still used for everything
that isn't receiving/sending a version's data: looking up/creating the
"Conditioned/<model>" model, attaching viewer result annotations, storing
the report artifact, and marking run success — none of those touch the
object-graph-vs-bundle question.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any, Literal

from pydantic import Field
from pydantic.json_schema import GenerateJsonSchema, JsonSchemaMode
from speckle_automate import AutomateBase, AutomationContext, execute_automate_function
from specklepy.api import operations

from conditioning.categories import classify_categories
from conditioning.codes import DEFAULT_CONDITIONING_KEY
from conditioning.grouping import assign_type_groups
from conditioning.instrumentation import stage
from conditioning.predict import predict_codes
from conditioning.report import build_report
from conditioning.speckle_io import (
    attach_category_annotations,
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

    # 1. Receive via operations.receive3, not automate_context.receive_version()
    # — see this module's docstring for why. `model` owns the downloaded
    # bundle files (parquet + SGEO blobs) until closed, and geometry is
    # parsed from those files lazily on first access (Model.geometries /
    # ModelGeometry.decode()) — so everything that might touch a wall's
    # geometry, including the fresh bundle create_conditioned_version()
    # builds from the *original* wall geometry, has to happen inside this
    # `with` block. Closing early and touching geometry afterwards raises.
    trigger = automate_context.automation_run_data.triggers[0].payload
    with stage("receive_version"), operations.receive3(
        automate_context.speckle_client.account,
        automate_context.automation_run_data.project_id,
        trigger.model_id,
        trigger.version_id,
    ) as model:
        with stage("collect_walls"):
            walls = collect_walls(model)

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

        # 2a. Everything that isn't a wall (2026-09-07 later still). The
        # 'Conditioned/All/<source>' model republishes every object, so every
        # object the category engine can honestly place gets a code too —
        # same corroborate/conflict mechanism as the wall engine, applied to
        # a per-category rule table (see categories.py; the table is a set
        # of judgements the estimator hasn't reviewed, and every result says
        # so via Requires Verification). Anything it can't place stays
        # `not conditioned`, visibly, rather than guessed.
        with stage("classify_categories"):
            category_results = classify_categories(
                model, exclude_ids={w.object_id for w in walls}
            )

        # 2b. Sub-group wall types within each predicted code. A Level 4 code
        # on its own answers "what kind of element" and immediately raises
        # "yes, but which one" — a 6" smoke partition and a furring wall are
        # both C1010.10 and cost nothing like each other. See
        # conditioning/grouping.py.
        with stage("assign_type_groups"):
            # assign_type_groups() now returns a tier hierarchy, not one flat
            # split — type_groups (per-wall, always the `full` tier) is what
            # gets imprinted; all_type_groups is every tier's row (coarse,
            # fire_acoustic, full), for the report to show the roll-up
            # structure rather than only the finest leaf. See grouping.py.
            type_groups, all_type_groups = assign_type_groups(walls, predictions)
            tier_counts = Counter(g.tier for g in all_type_groups)
            print(
                f"[ConditioningPOC] {tier_counts['coarse']} coarse wall-type "
                f"groups, refined into {tier_counts['fire_acoustic']} "
                f"fire/acoustic groups and {tier_counts['full']} fully-split "
                f"groups, across {len(walls)} elements."
            )

        # 3. Per-object viewer annotations
        with stage("attach_viewer_annotations"):
            attach_viewer_annotations(
                automate_context,
                classification.level4,
                classification.non_level4_coded,
                predictions,
            )
            attach_category_annotations(automate_context, category_results)

        # 4. Conditioning report. Deliberately not bound to a local: the
        # report is the largest single string this function builds, and
        # holding it alive through create_conditioned_version() below — the
        # peak-memory stage, where every wall's geometry gets re-encoded into
        # the new bundle — stacks the two high-water marks on top of each
        # other for no reason.
        with stage("build_and_store_report"):
            report_path = Path("conditioning_report.md")
            report_path.write_text(
                build_report(
                    walls, predictions, type_groups=all_type_groups,
                    category_results=category_results,
                ),
                encoding="utf-8",
            )
            try:
                automate_context.store_file_result(report_path)
            except Exception as exc:
                print(f"[ConditioningPOC] Could not store report: {exc}")

        # 5. Create augmented 'Conditioned/Walls/<source model name>' and
        # 'Conditioned/All/<source model name>' model versions — the former is
        # conditioned walls only, the latter a full republish of the whole
        # received scene with the same conditioning patched onto its walls
        # (added 2026-09-07 later still, after walls-only turned out to read
        # as data loss to a reviewer comparing models directly — see
        # speckle_io.py's module docstring). Both publish via
        # operations.send3/BundleBuilder from the conditioned WallRecord
        # data — not by mutating and resending `model`, which isn't a
        # supported workflow for a bundle-only receive (see this module's
        # docstring) and wouldn't be possible anyway since `model` is a
        # read-only view. See speckle_io.py.
        with stage("create_conditioned_version"):
            conditioned_versions = create_conditioned_version(
                automate_context, model, walls, predictions,
                code_property_name=function_inputs.code_property_name,
                type_groups=type_groups,
                category_results=category_results,
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
    if category_results:
        cat_tier3 = sum(1 for r in category_results if r.tier == 3)
        summary += (
            f" Beyond walls, {len(category_results)} other elements were coded "
            f"by category rules (unreviewed by the estimator — "
            f"{cat_tier3} at Tier 3)."
        )
    if conditioned_versions.all_version_id:
        summary += f" Full model: {conditioned_versions.all_version_id}"
    elif conditioned_versions.walls_version_id:
        # The full republish can fail independently of the walls-only one
        # (it's the larger of the two bundles — see speckle_io.py's
        # ConditionedVersions docstring) — fall back to naming whichever
        # model actually published rather than going silent.
        summary += f" Walls model: {conditioned_versions.walls_version_id}"

    automate_context.mark_run_success(summary)


if __name__ == "__main__":
    execute_automate_function(automate_function, FunctionInputs)
