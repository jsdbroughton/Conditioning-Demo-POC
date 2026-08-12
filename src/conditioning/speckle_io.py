"""Everything that writes back to Speckle: imprinting results onto wall
properties, viewer annotations, and creating the 'Conditioned' model version.

This is the one module in the package that talks to
speckle_automate.AutomationContext — everything else is plain, Speckle-free
logic.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Optional

from speckle_automate import AutomationContext

from conditioning.codes import CONDITIONING_KEY, tier_label
from conditioning.predict import Prediction
from conditioning.walls import WallRecord

# ---------------------------------------------------------------------------
# Imprinting predictions onto wall objects
# ---------------------------------------------------------------------------


def imprint_predictions(walls: list[WallRecord], predictions: list[Prediction]) -> None:
    """Mutate wall objects in-place to embed conditioning output.

    All output is written under a single namespaced `Turner UF Code`
    dict (CONDITIONING_KEY) rather than several flat sibling keys — one
    predictable place to look in the viewer/report/PowerBI, and no risk of
    colliding with a real Revit parameter name.

    Direction as of 2026-08-12: every non-Level4 wall (blank or an existing
    non-Turner-format code) gets predict.predict_codes()'s fuzzy match/
    heuristic applied and written here — auto-applied regardless of
    confidence/tier for this POC. Tier is recorded so a future pass can gate
    on it; nothing is held back or skipped in the meantime.
    """
    pred_map = {p.wall.object_id: p for p in predictions}

    for wall in walls:
        obj  = wall.obj
        pred = pred_map.get(wall.object_id)

        # Write into obj.properties (the existing dict) so values appear under
        # the "properties" section in the Speckle viewer, not at the top level.
        props = getattr(obj, "properties", None)
        if not isinstance(props, dict):
            # Shouldn't happen for a real Revit wall, but guard gracefully
            props = {}
            setattr(obj, "properties", props)

        if wall.is_level4_coded:
            # Already correct — passed through unchanged
            props[CONDITIONING_KEY] = {
                "Status": "existing",
                "Level 4 Code": wall.assembly_code,
            }
        elif pred:
            # Predicted — reachable for every non-Level4 wall (blank or an
            # existing non-Turner-format code; see predict.predict_codes).
            # "Original Code" is None for walls that had no code at all, and
            # the prior code for walls being remapped from a legacy format —
            # always present so the shape is consistent for downstream
            # consumers, never silently dropped.
            props[CONDITIONING_KEY] = {
                "Status": "predicted",
                "Level 4 Code": pred.predicted_code,
                "Confidence": pred.confidence,
                "Tier": tier_label(pred.tier),
                "Method": pred.method,
                "Original Code": wall.assembly_code if wall.is_coded else None,
            }


# ---------------------------------------------------------------------------
# Viewer annotations
# ---------------------------------------------------------------------------


def attach_viewer_annotations(
    automate_context: AutomationContext,
    level4: list[WallRecord],
    non_level4_coded: list[WallRecord],
    predictions: list[Prediction],
) -> None:
    """Attach per-object viewer annotations, grouped so each unique
    code/message is one result entry with all matching objects attached,
    rather than one entry per wall."""
    # Turner Level 4 coded walls — gold standard, highlight separately
    level4_by_code: dict[str, list] = defaultdict(list)
    for wall in level4:
        level4_by_code[wall.assembly_code or ""].append(wall.obj)
    for code, objs in sorted(level4_by_code.items()):
        automate_context.attach_info_to_objects(
            category="Uniformat — Turner Level 4 Code",
            affected_objects=objs,
            message=f"Level 4 code: {code} ({len(objs)} element{'s' if len(objs) != 1 else ''})",
        )

    # Non-Level4 coded walls — has a legacy-format code (e.g. ASTM B2010160).
    # These are auto-remapped, not just flagged — see the prediction groups
    # below for the new code/confidence/tier each one gets.
    non_l4_by_code: dict[str, list] = defaultdict(list)
    for wall in non_level4_coded:
        non_l4_by_code[wall.assembly_code or ""].append(wall.obj)
    for code, objs in sorted(non_l4_by_code.items()):
        automate_context.attach_info_to_objects(
            category="Uniformat — Legacy Code (remapped)",
            affected_objects=objs,
            message=f"Original code {code!r} is not Turner Level 4 format — "
                    f"remapped, see Predicted annotations "
                    f"({len(objs)} element{'s' if len(objs) != 1 else ''})",
        )

    # Predictions: group by (category, predicted_code). Category-matched
    # predictions (e.g. curtain wall elements matched by Revit's own
    # category, not a guess) get their own bucket, called out separately
    # from plain keyword/function heuristics.
    pred_groups: dict[tuple[str, str], list] = defaultdict(list)
    pred_group_labels: dict[tuple[str, str], str] = {}
    for pred in predictions:
        if pred.method == "similarity":
            cat = "Uniformat — Predicted (similarity)"
            label = f"{pred.predicted_code} — Tier {pred.tier}"
        elif pred.method == "heuristic_category":
            cat = "Uniformat — Predicted (curtain wall category match)"
            label = f"{pred.predicted_code} — Tier {pred.tier}"
        elif pred.method.startswith("heuristic"):
            cat = "Uniformat — Predicted (heuristic)"
            label = f"{pred.predicted_code} — {pred.description} — Tier {pred.tier}"
        else:
            cat = "Uniformat — Predicted (default fallback)"
            label = f"{pred.predicted_code} — Tier {pred.tier} (low confidence — review manually)"
        key = (cat, pred.predicted_code)
        pred_group_labels.setdefault(key, label)
        pred_groups[key].append(pred.wall.obj)

    for (cat, _code), objs in sorted(pred_groups.items()):
        label = pred_group_labels[(cat, _code)]
        automate_context.attach_info_to_objects(
            category=cat,
            affected_objects=objs,
            message=f"Predicted: {label} ({len(objs)} element{'s' if len(objs) != 1 else ''})",
        )


# ---------------------------------------------------------------------------
# Augmented model version
# ---------------------------------------------------------------------------


def _get_or_create_model(automate_context: AutomationContext, model_name: str, model_description: str):
    """
    Return a model object with an .id attribute, creating it if it doesn't exist.

    create_new_model_in_project raises BRANCH_CREATE_ERROR when the model already
    exists (subsequent runs). In that case we use client.model.get_models with a
    name search filter — the specklepy 3.x SDK API, which replaced client.branch.
    """
    try:
        return automate_context.create_new_model_in_project(
            model_name=model_name,
            model_description=model_description,
        )
    except Exception as exc:
        if "already exists" not in str(exc).lower() and "BRANCH_CREATE_ERROR" not in str(exc):
            raise

    # Model exists from a previous run — look it up by name via the SDK
    from specklepy.core.api.inputs.project_inputs import ProjectModelsFilter

    client     = automate_context.speckle_client
    project_id = automate_context.automation_run_data.project_id

    collection = client.model.get_models(
        project_id,
        models_filter=ProjectModelsFilter(search=model_name),
    )
    match = next(
        (m for m in (collection.items or []) if m.name == model_name),
        None,
    )
    if not match:
        raise RuntimeError(f"Model '{model_name}' not found in project {project_id} after creation failed")
    return match


def _get_source_model_name(automate_context: AutomationContext) -> str:
    """Look up the display name of the model whose new version triggered this run."""
    source_model_id = automate_context.automation_run_data.triggers[0].payload.model_id
    return automate_context.get_model(source_model_id).name


def create_conditioned_version(
    automate_context: AutomationContext,
    root,
    walls: list[WallRecord],
    predictions: list[Prediction],
) -> Optional[str]:
    """
    Imprint predictions onto wall objects and push a new version into a
    'Conditioned/<source model name>' model, creating it on first run for
    that source and reusing it thereafter.

    Namespaced per source model — not a single shared 'Conditioned' model —
    because a workspace can have several source models feeding this function
    (e.g. Henry Ford Wall Takeoff's SHELL model alongside the UKHC Fitout
    Tower/Podium/EXT_Core models Kevin Wanner uploaded 2026-07-21); writing
    them all into one output model would mix unrelated walls together and
    make each run's output ambiguous. Speckle model names use '/' as a
    folder separator, so 'Conditioned/<name>' groups all conditioned output
    under one parent in the model tree while keeping each source distinct.

    Returns the new version ID, or None on failure.
    """
    imprint_predictions(walls, predictions)

    try:
        source_model_name = _get_source_model_name(automate_context)
        output_model_name = f"Conditioned/{source_model_name}"

        model = _get_or_create_model(
            automate_context,
            model_name=output_model_name,
            model_description=(
                f"Walls with predicted Uniformat Assembly Codes for "
                f"'{source_model_name}' — Conditioning Demo POC"
            ),
        )
        new_version = automate_context.create_new_version_in_project(
            root_object=root,
            model_id=model.id,
            version_message="Uniformat Assembly Code predictions applied by Conditioning Demo POC",
        )
        return new_version.id

    except Exception as exc:
        print(f"[ConditioningPOC] Augmented version creation failed: {exc}")
        return None
