"""Everything that writes back to Speckle.

Imprinting results onto wall properties, viewer annotations, and creating the
'Conditioned' model version.

This is the one module in the package that talks to
speckle_automate.AutomationContext — everything else is plain, Speckle-free
logic.
"""

from __future__ import annotations

from collections import defaultdict

from speckle_automate import AutomationContext

from conditioning.attributes import extract_attributes
from conditioning.codes import (
    DEFAULT_CONDITIONING_KEY,
    METHOD_DESCRIPTIONS,
    tier_label,
)
from conditioning.grouping import TypeGroup
from conditioning.predict import Prediction
from conditioning.walls import WallRecord

# ---------------------------------------------------------------------------
# Imprinting predictions onto wall objects
# ---------------------------------------------------------------------------


def imprint_predictions(
    walls: list[WallRecord],
    predictions: list[Prediction],
    code_property_name: str = DEFAULT_CONDITIONING_KEY,
    type_groups: dict[str, TypeGroup] | None = None,
) -> None:
    """Mutate wall objects in-place to embed conditioning output.

    All output is written under a single namespaced dict — keyed by
    `code_property_name` (a user-facing Automate input as of 2026-08-14, see
    main.FunctionInputs.code_property_name; defaults to
    codes.DEFAULT_CONDITIONING_KEY) — rather than several flat sibling keys.
    One predictable place to look in the viewer/report/PowerBI, and no risk
    of colliding with a real Revit parameter name.

    Direction as of 2026-08-12: every non-Level4 wall (blank or an existing
    non-conforming code) gets predict.predict_codes()'s fuzzy match/
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
            # Already correct — passed through unchanged. Tier 0 ("no work
            # to be done") added 2026-08-14 so every wall carries a Tier
            # value, not just predicted ones — before this, "already
            # correct" walls sat outside the Tier 1/2/3 system entirely,
            # which made "how many walls need attention at each level"
            # unanswerable from this property alone. See codes.TIER_LABELS.
            props[code_property_name] = {
                "Status": "existing",
                "Level 4 Code": wall.assembly_code,
                "Level 4 Code Source": "authored — already a valid Level 4 code",
                "Requires Verification": False,
                "Tier": tier_label(0),
            }
            _add_type_group(props, code_property_name, type_groups, wall)
        elif pred:
            # Predicted — reachable for every non-Level4 wall (blank or an
            # existing non-conforming code; see predict.predict_codes).
            # "Original Code" is None for walls that had no code at all, and
            # the prior code for walls being remapped from a legacy format —
            # always present so the shape is consistent for downstream
            # consumers, never silently dropped.
            # "Requires Verification" is the tag asked for on the 2026-08-14
            # call — "if it makes a judgment, it would be nice if that was
            # tagged to say, hey, please tag the verifier". It is deliberately
            # NOT the same question as Tier. Tier asks how sure we are the
            # code is right; this asks whether the building told us or
            # Speckle worked it out. Note "worked out", not "predicted" and
            # not "inferred by a model" — nothing here is trained or
            # AI-backed, and conflating it with the separate AI capability
            # would drag an unrelated security review onto this function.
            # A high-confidence guess still needs a human to accept it, and
            # before this existed a Tier 1 reading actively concealed that —
            # 91% of one real model sat at Tier 1, including an element whose
            # type name was literally "Empty".
            #
            # It is True on every predicted element, which today means every
            # element in every model conditioned so far. That is not a
            # degenerate flag, it is the honest headline: none of these codes
            # came from the model, all of them are ours. Tier remains the
            # triage axis for *which* to look at first.
            # "predicted" is deliberate and stays, despite the wording
            # discipline everywhere else in this dict. Prediction is not an
            # AI-exclusive word — a rule that maps evidence to a likely value
            # is making a prediction, and that is mechanically what happens
            # here. It is the honest verb, so it is the one used.
            #
            # What had to change was never this word, it was the absence of
            # anything saying *how*. "Level 4 Code Source" and "Requires
            # Verification" below now answer that in plain terms, so a reader
            # meeting "predicted" has no room to fill the gap with an
            # assumption about models or AI. Renaming it would also break any
            # downstream filter already written against the value, for no gain.
            props[code_property_name] = {
                "Status": "predicted",
                "Level 4 Code": pred.predicted_code,
                "Level 4 Code Source": _code_source(wall, pred),
                "Requires Verification": True,
                "Confidence": pred.confidence,
                "Tier": tier_label(pred.tier),
                "Method": pred.method,
                "Original Code": wall.assembly_code if wall.is_coded else None,
            }
            _add_type_group(props, code_property_name, type_groups, wall)


def _code_source(wall: WallRecord, pred: Prediction) -> str:
    """Say, in an estimator's words, where a derived code came from.

    Two facts a reviewer needs and cannot otherwise get: that Speckle worked
    this out rather than reading it, and what evidence it worked it out
    from. `Method` already carries the second in our vocabulary
    (`heuristic_category`); this says it in theirs.

    Wording avoids "model", "predicted by", "AI" and "machine learning"
    throughout — see codes.METHOD_DESCRIPTIONS for why that precision is
    load-bearing rather than fussy. "Derived" is the honest verb: these are
    rules over Revit parameters plus a string comparison.
    """
    basis = METHOD_DESCRIPTIONS.get(pred.method, pred.method)
    prior = (
        f"replacing the existing code {wall.assembly_code}"
        if wall.is_coded
        else "no code was present on the element"
    )
    return f"Derived by Speckle from {basis} — {prior}"


def _add_type_group(
    props: dict,
    code_property_name: str,
    type_groups: dict[str, TypeGroup] | None,
    wall: WallRecord,
) -> None:
    """Add the wall-type sub-grouping to the conditioning dict, if computed.

    Deliberately written into the SAME namespaced dict as the code itself
    rather than as sibling properties. The conditioning output is one thing
    to look for in the viewer, one thing to select in Power BI, and one
    thing that can't collide with a real Revit parameter — splitting the
    group across separate top-level keys would give up all three for no
    gain. See grouping.py for what the group means and why it is not a
    finer Uniformat code.

    Absent when no grouping was computed, rather than present-and-null: the
    keys only appear on runs that actually produced groups.
    """
    if type_groups:
        group = type_groups.get(wall.object_id)
        if group is not None:
            props[code_property_name].update({
                "Inferred Type Group": group.key,
                "Inferred Group Label": group.label,
                "Inferred Group Size": group.size,
            })

    # Attributes read straight off the type name, where its naming allows.
    # A separate axis from the group on purpose: the group is "what does this
    # resemble", these are "what does the name actually assert". Keys are
    # omitted entirely when the name yields nothing — a blank that is visibly
    # blank beats a null that reads like a measured absence. See
    # attributes.py for why similarity cannot produce these.
    attrs = extract_attributes(wall.type_name)
    if attrs:
        observed = {"Observed Type Attributes": attrs.summary}
        if attrs.fire_rating:
            observed["Observed Fire Rating"] = attrs.fire_rating
        if attrs.stc:
            observed["Observed Acoustic STC"] = attrs.stc
        if attrs.stud:
            observed["Observed Stud Size"] = f'{attrs.stud}"'
        props[code_property_name].update(observed)


# ---------------------------------------------------------------------------
# Viewer annotations
# ---------------------------------------------------------------------------


def attach_viewer_annotations(
    automate_context: AutomationContext,
    level4: list[WallRecord],
    non_level4_coded: list[WallRecord],
    predictions: list[Prediction],
) -> None:
    """Attach per-object viewer annotations, grouped by unique code/message.

    Each unique code/message becomes one result entry with all matching objects
    attached, rather than one entry per wall.
    """
    # ACME Level 4 coded walls — gold standard, highlight separately
    level4_by_code: dict[str, list] = defaultdict(list)
    for wall in level4:
        level4_by_code[wall.assembly_code or ""].append(wall.obj)
    for code, objs in sorted(level4_by_code.items()):
        automate_context.attach_info_to_objects(
            category="Uniformat — ACME Level 4 Code",
            affected_objects=objs,
            message=f"Level 4 code: {code} — Tier 0, no work needed "
                    f"({len(objs)} element{'s' if len(objs) != 1 else ''})",
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
            message=f"Original code {code!r} is not ACME Level 4 format — "
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
        elif pred.method == "heuristic_category_crosswalk":
            cat = "Uniformat — Predicted (window wall crosswalk — verify)"
            label = (
                f"{pred.predicted_code} — Tier {pred.tier} (legacy code says a "
                f"different section — verify)"
            )
        elif pred.method.startswith("heuristic"):
            cat = "Uniformat — Predicted (heuristic)"
            label = f"{pred.predicted_code} — {pred.description} — Tier {pred.tier}"
        else:
            cat = "Uniformat — Predicted (default fallback)"
            label = (
                f"{pred.predicted_code} — Tier {pred.tier} (low confidence — review "
                f"manually)"
            )
        key = (cat, pred.predicted_code)
        pred_group_labels.setdefault(key, label)
        pred_groups[key].append(pred.wall.obj)

    for (cat, _code), objs in sorted(pred_groups.items()):
        label = pred_group_labels[(cat, _code)]
        automate_context.attach_info_to_objects(
            category=cat,
            affected_objects=objs,
            message=(
                f"Predicted: {label} ({len(objs)} "
                f"element{'s' if len(objs) != 1 else ''})"
            ),
        )

    # Tier 3 predictions get a second, warning-level annotation on top of
    # whichever method bucket they landed in above — regardless of method,
    # low/no confidence is worth surfacing as its own thing in the run
    # report, not just a "Tier 3" substring inside a longer info label that's
    # easy to scroll past. attach_warning_to_objects (vs. attach_info) is a
    # real severity distinction here, not cosmetic: Tier 3 means "a human
    # actually needs to look at this one" per the tier definitions in
    # codes.py.
    tier3_by_code: dict[str, list] = defaultdict(list)
    for pred in predictions:
        if pred.tier == 3:
            tier3_by_code[pred.predicted_code].append(pred.wall.obj)
    for code, objs in sorted(tier3_by_code.items()):
        automate_context.attach_warning_to_objects(
            category="Uniformat — Needs Review (Tier 3)",
            affected_objects=objs,
            message=f"Predicted {code} at Tier 3 (low/no confidence) — worth a "
                    f"human look "
                    f"({len(objs)} element{'s' if len(objs) != 1 else ''})",
        )


# ---------------------------------------------------------------------------
# Augmented model version
# ---------------------------------------------------------------------------


def _get_or_create_model(
    automate_context: AutomationContext,
    model_name: str,
    model_description: str,
):
    """Return a model object with an .id attribute, creating it if it doesn't exist.

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
        if "already exists" not in str(
            exc).lower() and "BRANCH_CREATE_ERROR" not in str(exc
        ):
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
        raise RuntimeError(
            f"Model '{model_name}' not found in project {project_id} "
            f"after creation failed"
        )
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
    code_property_name: str = DEFAULT_CONDITIONING_KEY,
    type_groups: dict[str, TypeGroup] | None = None,
) -> str | None:
    """Imprint predictions and push a new version into a 'Conditioned' model.

    Writes to 'Conditioned/<source model name>', creating it on first run for that
    source and reusing it thereafter.

    Namespaced per source model — not a single shared 'Conditioned' model —
    because a workspace can have several source models feeding this function
    (e.g. one client's shell model alongside several other project models
    uploaded around the same time); writing them all into one output model
    would mix unrelated walls together and make each run's output ambiguous.
    Speckle model names use '/' as a folder separator, so 'Conditioned/<name>'
    groups all conditioned output under one parent in the model tree while
    keeping each source distinct.

    Also adds this new artifact version to the Automate run's context view
    (the "View Results" link), alongside the host model — see the comment
    at the set_context_view() call below.

    `code_property_name` is threaded through to imprint_predictions() — see
    main.FunctionInputs.code_property_name for why this is a per-run input
    rather than a hardcoded constant.

    Returns the new version ID, or None on failure.
    """
    imprint_predictions(
        walls,
        predictions,
        code_property_name=code_property_name,
        type_groups=type_groups,
    )

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
            version_message=(
                "Uniformat Assembly Code predictions applied by Conditioning Demo POC"
            ),
        )

        # Add the conditioned output to the run's "View Results" viewer
        # alongside the host model (include_source_model_version=True, the
        # SDK default) rather than replacing it. The host model has to stay
        # in view: attach_viewer_annotations() (called earlier, against the
        # unmutated wall objects) records each result's Speckle object id,
        # and that id is fixed at receive time — it never gets reassigned to
        # match the mutated/re-hashed objects pushed to the artifact model
        # (confirmed against specklepy's serializer, see NOTES.md). So the
        # interactive per-object highlight markers only resolve against a
        # scene that still has the host model loaded. Adding the artifact
        # model as an extra resource just means reviewers can also inspect
        # the actual conditioned-code output in the same viewer, overlaid
        # rather than swapped in.
        try:
            automate_context.set_context_view(
                resource_ids=[f"{model.id}@{new_version.id}"],
                include_source_model_version=True,
            )
        except Exception as exc:
            print(
                f"[ConditioningPOC] Could not add artifact model to results view: {exc}"
            )

        return new_version.id

    except Exception as exc:
        print(f"[ConditioningPOC] Augmented version creation failed: {exc}")
        return None
