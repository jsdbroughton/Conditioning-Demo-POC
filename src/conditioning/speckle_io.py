"""Everything that writes back to Speckle.

Imprinting results onto wall properties, viewer annotations, and creating the
'Conditioned' model version.

This is the one module in the package that talks to
speckle_automate.AutomationContext (for everything except the actual
receive/publish of a version's data — see below) — everything else is
plain, Speckle-free logic.

2026-09-07: ported onto specklepy 2026.9's bundle format — see main.py's
module docstring for the full picture of why AutomationContext's own
receive/send wrapping isn't used for the version data itself. Two
consequences land here:

  - imprint_predictions() can no longer mutate `wall.obj.properties` in
    place — `wall.obj` is now a specklepy.bundle.model.ModelObject, a
    read-only view over the downloaded parquet tables, not a Base with a
    mutable dict. It writes to the new WallRecord.conditioning field
    instead (see walls.py); create_conditioned_version() reads it back out
    when building the fresh output bundle.
  - create_conditioned_version() publishes with operations.send3 and a
    specklepy.bundle.builder.BundleBuilder instead of
    automate_context.create_new_version_in_project(). It builds NEW bundles
    from the conditioned WallRecord data (plus, as of 2026-09-07 later
    still, the rest of the received scene) rather than mutating and
    resending the received Model (unsupported for a bundle-only receive,
    and impossible anyway since Model is read-only) — see
    _build_walls_bundle()'s and _build_full_bundle()'s docstrings for what
    each bundle contains.

2026-09-07 (later still): create_conditioned_version() now publishes TWO
model versions per run — 'Conditioned/Walls/<source>' (conditioned walls only,
_build_walls_bundle()) and 'Conditioned/All/<source>' (every received object, walls
patched, _build_full_bundle()) — where it used to publish one, into
'Conditioned/<source>'. The walls-only bundle was the only output for a
while and that turned out to be a real gap, not an acceptable trade-off: a
reviewer opening it directly, rather than through the run report's merged
viewer, found every non-wall category simply absent. See
create_conditioned_version()'s own docstring for the direction and
ConditionedVersions for the return shape.
"""

from __future__ import annotations

import traceback
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass

from speckle_automate import AutomationContext
from specklepy.api import operations
from specklepy.bundle.builder import BundleBuilder, BundleGeometry
from specklepy.bundle.envelope_writer import Producer
from specklepy.bundle.model import GeometryRole
from specklepy.bundle.send import SendOptions

from conditioning.attributes import bucket_height_ft, extract_attributes, height_band
from conditioning.categories import CATEGORY_RULES, CategoryResult, is_non_physical
from conditioning.codes import (
    ACME_CODES,
    DEFAULT_CONDITIONING_KEY,
    METHOD_DESCRIPTIONS,
    tier_label,
)
from conditioning.grouping import TypeGroup
from conditioning.predict import Prediction
from conditioning.walls import WallRecord

# Provenance stamped into every bundle this function publishes (Producer.slug
# / .version — see specklepy.bundle.envelope_writer.Producer). Not the same
# thing as the Automate function's own semver in pyproject.toml; this is
# specifically the identity readers of the *output* Speckle version see
# recorded against it, so it's declared right where that bundle gets built.
_PRODUCER = Producer(slug="conditioning-demo-poc", version="1.0.0")

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

    2026-09-07: writes to `wall.conditioning` now, not `wall.obj.properties`
    — `wall.obj` is a read-only bundle ModelObject with no properties dict
    to mutate (see this module's and walls.py's module docstrings).
    `wall.conditioning` ends up holding exactly what `obj.properties` used
    to hold: `{code_property_name: {...}}`, one namespaced key — it's the
    storage location that changed, not the shape.
    create_conditioned_version() merges it into the fresh output bundle's
    properties for this wall.

    2026-09-07 (later the same day): "Level 4 Code Description" added
    alongside "Level 4 Code" on both branches below — the client's own
    plain-English description of that section from the source spreadsheet
    (codes.ACME_CODES, kept in lockstep with fixtures/ACME Studios -
    Uniformat Estimate Detail Structure.xlsx by
    tests/test_acme_codes_fixture.py), e.g. "Interior Fixed Partitions" for
    C1010.10. Lets a reviewer read what a code means directly off the wall
    in the viewer/Power BI without cross-referencing the spreadsheet by
    hand. `ACME_CODES.get(code, "")` rather than a KeyError — a wall could
    in principle already carry a Level4-shaped code that isn't one of
    ACME's own sections (is_level4_coded only checks the pattern, not
    membership), and an empty description is the honest answer for "not
    ours" rather than a spurious lookup failure.
    """
    pred_map = {p.wall.object_id: p for p in predictions}

    for wall in walls:
        pred = pred_map.get(wall.object_id)
        props: dict = {}

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
                "Level 4 Code Description": ACME_CODES.get(wall.assembly_code, ""),
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
                "Level 4 Code Description": ACME_CODES.get(pred.predicted_code, ""),
                "Level 4 Code Source": _code_source(wall, pred),
                "Requires Verification": True,
                "Confidence": pred.confidence,
                "Tier": tier_label(pred.tier),
                "Method": pred.method,
                "Original Code": wall.assembly_code if wall.is_coded else None,
            }
            _add_type_group(props, code_property_name, type_groups, wall)

        if code_property_name in props:
            wall.conditioning = props


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
            # 2026-09-07 (later still): grouping is now a three-tier
            # hierarchy, not one flat split (see grouping.py) — `group` here
            # is always the `full`-tier TypeGroup (fire/acoustic/height all
            # split). Every tier's key/label is written side by side, each
            # suffixed with its tier, so a wall can be grouped by whichever
            # granularity a reader wants directly off its own properties —
            # no join to a separate clusters table needed. The full tier
            # was briefly the unsuffixed "Inferred Type Group"; renamed
            # "(Fine Grained)" the same day on review of a real property
            # panel, where an unsuffixed key beside "(Coarse)" and
            # "(Fire/Acoustic)" read as the parent of the other two rather
            # than the finest of the three. Coarse/Fire-Acoustic keys equal
            # the fine-grained key wherever that tier's split never actually
            # found more than one value (see TypeGroup's docstring) — that's
            # correct, not a bug: it says plainly that finer splitting found
            # nothing more to say.
            entry = {
                "Inferred Type Group (Fine Grained)": group.key,
                "Inferred Group Label (Fine Grained)": group.label,
                "Inferred Group Size": group.size,
                "Inferred Type Group (Coarse)": group.coarse_key,
                "Inferred Group Label (Coarse)": group.coarse_label,
                "Inferred Type Group (Fire/Acoustic)": group.fire_acoustic_key,
                "Inferred Group Label (Fire/Acoustic)": group.fire_acoustic_label,
            }
            # Description and rollups (added 2026-09-07) report what the
            # group's members actually have in common — one value where they
            # agree, "varies (...)" listing every distinct value where they
            # don't (see grouping.py's 2026-09-07 note: a big real group
            # routinely spans several Type Marks, so picking just one here
            # would hide that rather than report it). Rollups are omitted
            # per-field when the group yielded nothing for that field, same
            # discipline as the "Observed *" keys below. On this `full`-tier
            # group, Fire Ratings/Acoustic STC/Height Bands are each
            # guaranteed to hold at most one value by construction — "varies"
            # on any of those three can only ever appear on a coarser row in
            # the report, never here.
            if group.description:
                entry["Inferred Group Description"] = group.description
            if group.wall_tags:
                entry["Inferred Group Wall Tags"] = ", ".join(sorted(group.wall_tags))
            if group.fire_ratings:
                entry["Inferred Group Fire Ratings"] = ", ".join(
                    sorted(group.fire_ratings)
                )
            if group.stc_values:
                entry["Inferred Group Acoustic STC"] = ", ".join(
                    sorted(group.stc_values)
                )
            if group.stud_sizes:
                entry["Inferred Group Stud Sizes"] = ", ".join(
                    sorted(group.stud_sizes)
                )
            if group.height_bands:
                entry["Inferred Group Height Bands"] = ", ".join(
                    sorted(group.height_bands)
                )
            props[code_property_name].update(entry)

    # Attributes read off the type name and/or the wall's own parameters
    # (Fire Rating, Type Mark) — see attributes.py's 2026-09-07 note for why
    # the parameter is preferred over the name-regex where both exist. A
    # separate axis from the group on purpose: the group is "what does this
    # resemble", these are "what does the wall actually assert". Keys are
    # omitted entirely when nothing is asserted — a blank that is visibly
    # blank beats a null that reads like a measured absence. See
    # attributes.py for why similarity cannot produce these.
    attrs = extract_attributes(
        wall.type_name,
        fire_rating_param=wall.fire_rating,
        wall_tag=wall.type_mark,
    )
    if attrs:
        observed = {"Observed Type Attributes": attrs.summary}
        if attrs.fire_rating:
            observed["Observed Fire Rating"] = attrs.fire_rating
            observed["Observed Fire Rating Source"] = attrs.fire_rating_source
        if attrs.stc:
            observed["Observed Acoustic STC"] = attrs.stc
        if attrs.stud:
            observed["Observed Stud Size"] = f'{attrs.stud}"'
        if attrs.wall_tag:
            observed["Observed Wall Tag"] = attrs.wall_tag
        props[code_property_name].update(observed)

    # Height is a genuine per-instance value, not a per-type one — never
    # routed through extract_attributes()/TypeAttributes (see attributes.py's
    # module docstring for why). Written independently of whether `attrs`
    # yielded anything, since a wall can have a height with no other
    # attribute asserted at all.
    height_label = bucket_height_ft(wall.height_mm)
    if height_label:
        props[code_property_name]["Observed Height"] = height_label
    band = height_band(wall.height_mm)
    if band:
        # The banded (short/standard/tall) reading of the same height —
        # see attributes.py's 2026-09-07 note for the bands and why they're
        # an owned, opinionated stand-in rather than a measured threshold.
        # Reported so a reader can see directly which side of a hard-split
        # boundary a wall's height actually landed on, without re-deriving
        # it from the raw "Observed Height" figure above.
        props[code_property_name]["Observed Height Band"] = band


def imprint_category_results(
    results: list[CategoryResult],
    code_property_name: str = DEFAULT_CONDITIONING_KEY,
) -> dict[str, dict]:
    """Conditioning dicts for non-wall objects, keyed by application_id.

    2026-09-07 (later still). Same shape and vocabulary as
    imprint_predictions() writes for a wall — Status / Level 4 Code /
    Description / Source / Requires Verification / Confidence / Tier / Method
    / Original Code — so a Power BI filter written against walls reads a
    door unchanged. Deliberately omits the wall-only keys (Observed *,
    Inferred *): there is no attribute vocabulary or sub-grouping for
    non-walls, and present-but-empty keys would imply there was.
    Returned as a dict rather than written onto a record because non-wall
    objects have no WallRecord — _build_full_bundle() merges these by id.
    """
    imprinted: dict[str, dict] = {}
    for result in results:
        if result.method == "component":
            # No Level 4 Code key at all — a count of coded elements must not
            # see this one. The parent's code rides along under its own name
            # so the relationship is visible without inflating anything.
            entry = {
                "Status": "component",
                "Level 4 Code Source": (
                    f"Not classified separately — {result.basis}; priced and "
                    f"counted with the parent, not on its own"
                ),
                "Requires Verification": False,
            }
            if result.code:
                entry["Parent Level 4 Code"] = result.code
                entry["Parent Level 4 Code Description"] = result.description
            imprinted[result.object_id] = {code_property_name: entry}
            continue
        if result.method == "existing":
            entry = {
                "Status": "existing",
                "Level 4 Code": result.code,
                "Level 4 Code Description": result.description,
                "Level 4 Code Source": result.basis,
                "Requires Verification": False,
                "Tier": tier_label(0),
            }
        else:
            prior = (
                f"replacing the existing code {result.original_code}"
                if result.original_code
                else "no code was present on the element"
            )
            entry = {
                "Status": "predicted",
                "Level 4 Code": result.code,
                "Level 4 Code Description": result.description,
                "Level 4 Code Source": (
                    f"Derived by Speckle from {result.basis} — {prior}"
                ),
                "Requires Verification": True,
                "Confidence": result.confidence,
                "Tier": tier_label(result.tier),
                "Method": result.method,
                "Original Code": result.original_code,
            }
        imprinted[result.object_id] = {code_property_name: entry}
    return imprinted


# ---------------------------------------------------------------------------
# Viewer annotations
# ---------------------------------------------------------------------------


class _ResultRef:
    """Duck-typed stand-in for the Base object attach_*_to_objects() expects.

    2026-09-07: `wall.obj` is now a specklepy.bundle.model.ModelObject (see
    walls.py's module docstring), which has no `.id` — a bundle object's
    only identity is `applicationId` (see main.py's module docstring).
    AutomationContext.attach_result_to_objects() (speckle_automate/
    automation_context.py) keys its result dict on `.id` and separately
    reads `.applicationId`: `ids[o.id] = getattr(o, "applicationId", None)`.
    Both are set to the wall's applicationId here — the same substitution
    specklepy's own Base-tree compatibility projection makes for a bundle
    receive (specklepy.bundle.base_projection._geometry_object:
    `obj.applicationId = obj.id = app_id`), for the same reason: there is no
    other identity to give it.
    """

    __slots__ = ("id", "applicationId")

    def __init__(self, application_id: str) -> None:
        self.id = application_id
        self.applicationId = application_id


def _result_ref(wall: WallRecord) -> _ResultRef:
    return _ResultRef(wall.object_id)


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
        level4_by_code[wall.assembly_code or ""].append(_result_ref(wall))
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
        non_l4_by_code[wall.assembly_code or ""].append(_result_ref(wall))
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
        pred_groups[key].append(_result_ref(pred.wall))

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
            tier3_by_code[pred.predicted_code].append(_result_ref(pred.wall))
    for code, objs in sorted(tier3_by_code.items()):
        automate_context.attach_warning_to_objects(
            category="Uniformat — Needs Review (Tier 3)",
            affected_objects=objs,
            message=f"Predicted {code} at Tier 3 (low/no confidence) — worth a "
                    f"human look "
                    f"({len(objs)} element{'s' if len(objs) != 1 else ''})",
        )


def attach_category_annotations(
    automate_context: AutomationContext,
    results: list[CategoryResult],
) -> None:
    """Viewer annotations for non-wall results, grouped by category and code.

    One info entry per (category, code) — a reviewer filtering the results
    panel sees "Doors → C1030.10 (412 elements)" rather than 412 rows — plus
    the same Tier 3 warning overlay walls get, for the same reason: low
    confidence is worth its own line, not a substring in a longer label.
    """
    by_key: dict[tuple[str, str, str], list] = defaultdict(list)
    for result in results:
        by_key[(result.category, result.code, result.method)].append(
            _ResultRef(result.object_id)
        )
    for (category, code, method), objs in sorted(by_key.items()):
        label = "existing" if method == "existing" else f"predicted via {method}"
        automate_context.attach_info_to_objects(
            category=f"Uniformat — {category}",
            affected_objects=objs,
            message=f"{code} — {ACME_CODES.get(code, '')} ({label}, "
                    f"{len(objs)} element{'s' if len(objs) != 1 else ''})",
        )

    tier3: dict[str, list] = defaultdict(list)
    for result in results:
        if result.tier == 3:
            tier3[result.code].append(_ResultRef(result.object_id))
    for code, objs in sorted(tier3.items()):
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
    """The leaf name of the model whose new version triggered this run.

    Speckle model names use '/' as a folder separator, so a source published
    to 'Source/Walls/Shell' would otherwise produce
    'Conditioned/Walls/Source/Walls/Shell' — the source tree's own folders
    dragged under ours. Only the last segment identifies the model; the
    folders it sat in are the source's organisation, not part of its name.
    'Source/Banana/Republic/Is/Hot' → 'Hot'.
    """
    source_model_id = automate_context.automation_run_data.triggers[0].payload.model_id
    return model_leaf_name(automate_context.get_model(source_model_id).name)


def model_leaf_name(model_name: str) -> str:
    """Last '/'-separated segment of a Speckle model name, e.g. 'A/B/C' → 'C'."""
    return model_name.rstrip("/").rsplit("/", 1)[-1] or model_name


_IDENTITY_TRANSFORM = (
    1.0, 0.0, 0.0, 0.0,
    0.0, 1.0, 0.0, 0.0,
    0.0, 0.0, 1.0, 0.0,
    0.0, 0.0, 0.0, 1.0,
)


def _copy_material(builder: BundleBuilder, material):
    """Intern a received ModelMaterial into `builder`, returning the handle."""
    return builder.get_or_add_material(
        f"material-{material.k}",
        material.name,
        material.argb or 0,
        opacity=material.opacity if material.opacity is not None else 1.0,
        metalness=material.metalness if material.metalness is not None else 0.0,
        roughness=material.roughness if material.roughness is not None else 1.0,
        emissive=material.emissive,
        ior=material.ior,
    )


def _copy_geometry_style(builder: BundleBuilder, received_model, geometry_k, target):
    """Carry a geometry's own material/color edge (if any) onto `target`."""
    rels = received_model.bundle.relations
    material = received_model.node(rels.material_by_geometry.get(geometry_k))
    if material is not None:
        target.material = _copy_material(builder, material)
    color = received_model.node(rels.color_by_geometry.get(geometry_k))
    if color is not None:
        target.color = builder.get_or_add_color(color.argb)


def _copy_definition(builder: BundleBuilder, received_model, definition):
    """Recreate a received ModelDefinition (geometry + nested placements) once.

    `get_or_add_definition` interns by key, so a definition placed by a
    thousand doors is written once and `populate` runs once — the same
    dedup the source bundle had.
    """
    rels = received_model.bundle.relations

    def populate(bundle_def) -> None:
        ords = rels.defines_ord_by_definition.get(definition.k)
        for i, geometry_k in enumerate(
            rels.defines_by_definition.get(definition.k, [])
        ):
            geometry = received_model.geometries.get(geometry_k)
            if geometry is None:
                continue
            handle = bundle_def.add_raw_geometry(
                geometry.content,
                geometry.type or "sgeo",
                geometry_key=f"geometry-{geometry_k}",
                member_ord=ords[i] if ords else i,
            )
            _copy_geometry_style(builder, received_model, geometry_k, handle)
        for nested_k in rels.defines_instance_by_definition.get(definition.k, []):
            nested = received_model.node(nested_k)
            nested_def = getattr(nested, "definition", None)
            if nested_def is None:
                continue
            bundle_def.place_nested(
                _copy_definition(builder, received_model, nested_def),
                nested.transform or _IDENTITY_TRANSFORM,
                units=nested.units,
                key=f"instance-{nested_k}",
            )

    return builder.get_or_add_definition(
        f"definition-{definition.k}", definition.name, populate
    )


def _add_raw_display(builder: BundleBuilder, bundle_obj, geometry) -> BundleGeometry:
    """Copy a world-space DISPLAY geometry's bytes verbatim onto `bundle_obj`.

    `BundleObject.add_geometry()` takes a decoded Base and SGEO-encodes it;
    `add_raw_geometry()` copies bytes but files them under the SOLID role.
    There's no public "raw bytes, display role" — so this goes one layer down
    to the same two pipeline calls `add_geometry()` makes, minus the
    decode→Mesh→encode round trip that was costing a full parse and
    re-serialisation of every mesh in the model for no change in output.
    Keeps the source ordinal, so draw order is preserved too. Asked directly
    on 2026-09-07 whether the republish could be quicker/lighter: the real
    answer is an SDK-level "patch a received bundle" API (see docs/NOTES.md);
    this is the part achievable inside this function today.
    """
    k = builder.pipeline.add_raw_geometry(
        f"geometry-{geometry.k}", geometry.content, geometry.type or "sgeo"
    )
    builder.pipeline.display(bundle_obj.k, k, geometry.ord)
    return BundleGeometry(builder, k, geometry.ord)


def _copy_object_geometry(builder: BundleBuilder, received_model, obj, bundle_obj):
    """Carry every renderable of `obj` into `bundle_obj`, placements included.

    2026-09-07 (later still): the first full-scene republish decoded
    `obj.geometries` and added every one as direct display geometry. That's
    right for a wall (its mesh is authored in world space) and silently wrong
    for anything instanced — doors, mechanical equipment, curtain panels,
    mullions, most furniture. `ModelObject.geometries` flattens a placement
    into ModelGeometry entries whose `.content` is the DEFINITION's geometry,
    in definition-local space, with the placement's matrix left on
    `.transform` for the caller to apply. `decode()` doesn't apply it, so
    every instance landed at the definition origin: on the live 'Shell'
    model the tower collapsed to a stack of slabs with the roof floating on
    its own, object count identical to the source (8,437). Fix: mirror the
    source structure instead of flattening it — world-space geometry
    (transform None) is copied as before by role (display → decode/encode,
    solid → raw bytes), and each top-level placement is re-created as a
    definition (`_copy_definition`, interned so shared definitions are
    written once) plus a `place()` with the original matrix. Nested
    placements recurse the same way, so a definition-in-a-definition
    survives too.

    Reads `received_model.index.instances_by_object` and
    `bundle.relations.*` — the same internals `ModelObject.geometries` itself
    is built on, pinned to this specklepy version. Nothing public exposes a
    definition's own geometry list, so there's no way to do this through the
    façade alone; if the SDK grows one, use it.
    """
    for geometry in obj.geometries:
        if geometry.transform is not None:
            continue  # instanced — rebuilt from the placement below
        if geometry.role is GeometryRole.SOLID:
            handle = bundle_obj.add_raw_geometry(
                geometry.content,
                geometry.type or "sgeo",
                geometry_key=f"geometry-{geometry.k}",
            )
        else:
            handle = _add_raw_display(builder, bundle_obj, geometry)
        _copy_geometry_style(builder, received_model, geometry.k, handle)

    for instance_k in received_model.index.instances_by_object.get(obj.k, []):
        instance = received_model.node(instance_k)
        definition = getattr(instance, "definition", None)
        if definition is None:
            continue
        bundle_obj.place(
            _copy_definition(builder, received_model, definition),
            instance.transform or _IDENTITY_TRANSFORM,
            units=instance.units,
            key=f"instance-{instance_k}",
        )


def _copy_object_style(builder: BundleBuilder, obj, bundle_obj) -> None:
    """Carry an object's level/material/color assignments onto `bundle_obj`."""
    source_level = obj.level
    if source_level is not None and source_level.name:
        bundle_obj.level = builder.get_or_add_level(
            f"level-{source_level.name}",
            source_level.name,
            source_level.elevation or 0.0,
        )
    material = obj.material
    if material is not None:
        bundle_obj.material = _copy_material(builder, material)
    color = obj.color
    if color is not None:
        bundle_obj.color = builder.get_or_add_color(color.argb)


def _build_walls_bundle(
    received_model,
    walls: list[WallRecord],
    output_model_name: str,
) -> BundleBuilder:
    """Build a fresh bundle for the 'Conditioned/Walls/<source model>' output.

    2026-09-07: replaces the old approach of mutating the received root's
    wall objects in place and resending that same tree — unsupported for a
    bundle-only receive (see main.py's module docstring) and impossible
    regardless, since `received_model` is a read-only view over the
    downloaded parquet files. This builds a NEW bundle instead, one object
    per conditioned wall, reusing each wall's ORIGINAL geometry
    (ModelGeometry.decode()) so the output still shows real wall solids, not
    placeholders.

    2026-09-07 (later still): this used to be the ONLY output model
    ('Conditioned/<source model>'), and that turned out to be a real
    problem, not a documented-and-fine limitation — a reviewer opening the
    output model directly (not the run report's merged viewer) found every
    non-wall category simply gone, compared side by side against the source
    model. Kept as a second, walls-only view because it's still useful on
    its own (smaller, faster to open, nothing to filter out when the only
    question is "what did conditioning do to the walls") — but
    `create_conditioned_version()` now ALSO publishes `_build_full_bundle()`
    below, a genuine like-for-like republish of the whole received scene, so
    nobody has to reach for this one to see the building in context.
    """
    builder = BundleBuilder(producer=_PRODUCER, units=received_model.units)
    root = builder.get_or_add_container_path([output_model_name])

    for wall in walls:
        wall_obj = wall.obj  # specklepy.bundle.model.ModelObject
        bundle_obj = builder.get_or_add_object(wall.object_id)

        # Original Revit parameters, reshaped back to a nested dict by
        # PropertyView.to_nested() (undoes the dotted-path flattening — see
        # walls.py's module docstring for the paths this reads elsewhere),
        # plus this wall's conditioning result merged in as one more
        # top-level, namespaced key — exactly the sibling relationship the
        # old code had between a wall's own Parameters and its conditioning
        # dict, just assembled here instead of via in-place mutation.
        properties = wall_obj.properties.to_nested()
        if wall.conditioning:
            properties.update(wall.conditioning)

        bundle_obj.set_properties(
            properties=properties,
            name=wall_obj.name,
            speckle_type=wall_obj.get_string("speckle_type"),
            source_type=wall_obj.get_string("type"),
            units=wall_obj.get_string("units") or builder.units,
        )

        _copy_object_geometry(builder, received_model, wall_obj, bundle_obj)

        # Flat one-collection-per-category tree — get_or_add_container
        # interns by key, so the same category maps to the same container.
        container_key = wall.category or "Walls"
        bundle_obj.collection = builder.get_or_add_container(
            container_key, container_key, root, subtype="Collection",
        )
        _copy_object_style(builder, wall_obj, bundle_obj)

    return builder


def _build_full_bundle(
    received_model,
    walls: list[WallRecord],
    output_model_name: str,
    code_property_name: str = DEFAULT_CONDITIONING_KEY,
    category_conditioning: dict[str, dict] | None = None,
) -> BundleBuilder:
    """Build a fresh bundle for the 'Conditioned/All/<source model>' output.

    Every received object, not just walls, with each conditioned wall's
    result patched onto its own properties.

    2026-09-07 (later still): added because `_build_walls_bundle()` above,
    for a long time the only output, silently dropped every non-wall
    category — doors, floors, rooms, MEP, stairs, everything. That was a
    real, deliberate scope decision when this was first ported to the
    bundle format (see the git history on this function's old name,
    `_build_conditioned_bundle`) — but "deliberate and documented" turned
    out not to be the same thing as "acceptable": a reviewer comparing the
    output model directly against the source, not through the run report's
    merged viewer, saw a building with almost everything missing and
    reasonably read it as data loss. Direction: no more limiting to walls.

    `received_model.objects` is EVERY object in the received bundle
    (confirmed against specklepy.bundle.model.Model's own docstring/source —
    it's keyed by application_id, the same identity `wall.object_id` already
    uses), so this walks that instead of the `walls` list — a wall is just
    an object whose application_id happens to have a conditioning result.
    Reuses the original scene's own collection hierarchy
    (`ModelObject.collection_path`, the same path segments the source
    model's own tree shows in the viewer) rather than the flat
    one-collection-per-category tree `_build_walls_bundle()` uses — the
    point of this bundle is to look like the source model, patched, not to
    reorganise it. Also carries over material and color assignments, which
    `_build_walls_bundle()` never did even for walls — free fidelity now
    that every object is being visited anyway.

    Deliberately NOT carried over: host/room/connection/assembly
    relationships (a door's host wall, a room's bounding elements, MEP
    connectivity). Reproducing those needs a second pass once every
    object's bundle key is known (an edge can't reference a not-yet-created
    node) and touches relations this function has no reason to inspect
    otherwise — real, scoped-out work, not an oversight, and worth flagging
    to whoever next needs those relationships to survive the round trip.
    Geometry, by contrast, IS copied structurally — display/solid role,
    definitions and placements, per-geometry material/color — see
    `_copy_object_geometry()` for why the first cut's flatten-and-decode
    approach put every instanced element at the origin.

    Every object that has no conditioning result gets `_not_conditioned()`
    under the same namespaced key, so nothing in this model is silently
    blank — see that function for the wording, and for whose gap it is.

    Memory note: this necessarily processes every object in the received
    model, not just the (usually much smaller) wall subset — on a model
    where the walls-only bundle was already the peak-memory stage (see
    instrumentation.py / docs/NOTES.md's 2026-08-14 OOM entry), this one
    will be larger still. Worth watching peak RSS on a real run before
    assuming this scales the same way.
    """
    builder = BundleBuilder(producer=_PRODUCER, units=received_model.units)
    builder.get_or_add_container_path([output_model_name])
    # Non-wall results first, walls second: a wall's own richer result always
    # wins if an id somehow appears in both (it shouldn't — classify_categories
    # excludes the wall set — but the precedence is stated, not accidental).
    conditioning_by_id: dict[str, dict] = dict(category_conditioning or {})
    conditioning_by_id.update(
        {w.object_id: w.conditioning for w in walls if w.conditioning}
    )

    for obj in received_model.objects:
        bundle_obj = builder.get_or_add_object(obj.application_id)

        properties = obj.properties.to_nested()
        cond = conditioning_by_id.get(obj.application_id)
        if cond:
            properties.update(cond)
        else:
            properties.update(
                _not_conditioned(obj.get_string("category"), code_property_name)
            )

        bundle_obj.set_properties(
            properties=properties,
            name=obj.name,
            speckle_type=obj.get_string("speckle_type"),
            source_type=obj.get_string("type"),
            units=obj.get_string("units") or builder.units,
        )

        _copy_object_geometry(builder, received_model, obj, bundle_obj)

        path = obj.collection_path
        if path:
            bundle_obj.collection = builder.get_or_add_container_path(
                [output_model_name, *path]
            )
        _copy_object_style(builder, obj, bundle_obj)

    return builder


def _not_conditioned(category: str | None, code_property_name: str) -> dict:
    """The conditioning dict for an object nothing could place.

    2026-09-07 (later still): once 'Conditioned/All/<source>' republished
    every object, a door or a floor opened in the output carried the same
    property panel as the source and nothing else — indistinguishable from a
    wall the function had failed on. Written under the SAME namespaced key
    as a real result so a Power BI filter on Status sees every object
    exactly once: `existing` / `predicted` / `not conditioned`.

    The reason has to say which of two very different things happened,
    because a reviewer reading it on a Door after the category engine
    shipped asked, reasonably, why doors weren't being conditioned at all:

      - the category has NO rule (Rooms, Generic Models, Specialty
        Equipment…) — this function knows nothing about it; or
      - the category HAS a rule but no signal fired — for a Door that means
        Function was blank, the type name matched nothing, no already-coded
        Door was close enough to vouch for it, and category alone can't
        choose interior (C1030) from exterior (B2050). Left blank on
        purpose: the whole engine is built on not trusting one field.

    A first version said the client had no codes for the category; wrong
    (see acme_reference.py) and corrected the same day.
    """
    label = f"category {category!r}" if category else "an object with no category"
    if is_non_physical(category):
        reason = (
            f"Not applicable — {label} is not physical construction (a room, "
            f"area, level, grid or reference), so no Uniformat cost code exists "
            f"for it"
        )
    elif category in CATEGORY_RULES:
        reason = (
            f"Not derived — rules exist for {label} but none of the evidence "
            f"they need was present (no Function parameter, no recognised type "
            f"name, no existing code, no already-coded element of the same "
            f"category close enough to match); category alone is not enough "
            f"to choose a section"
        )
    else:
        reason = (
            f"Not derived — this function has no derivation rule for {label}; "
            f"walls, curtain walls and the categories in categories.py are "
            f"the ones it currently codes"
        )
    return {
        code_property_name: {
            "Status": "not conditioned",
            "Level 4 Code Source": reason,
            "Requires Verification": False,
        }
    }


@dataclass(frozen=True)
class ConditionedVersions:
    """The two model versions one create_conditioned_version() call publishes.

    2026-09-07 (later still): a single call used to publish one version, into
    'Conditioned/<source>'. It now publishes two, into 'Conditioned/Walls/<source>' (the
    old walls-only bundle) and 'Conditioned/All/<source>' (a full republish of the whole
    received scene, walls patched) — see _build_walls_bundle() and
    _build_full_bundle(). Either half can be None on a partial failure
    (e.g. the walls bundle sent fine but the much larger full bundle hit a
    server-side size limit) — check each field independently rather than
    assuming both-or-neither.
    """

    walls_model_name: str
    walls_version_id: str | None
    all_model_name: str
    all_version_id: str | None


def _publish_bundle(
    automate_context: AutomationContext,
    output_model_name: str,
    model_description: str,
    builder: BundleBuilder,
    send_message: str,
) -> tuple[object, str] | None:
    """Create/reuse `output_model_name` and send3 `builder` into it.

    Shared by both bundles create_conditioned_version() publishes — the only
    difference between them is which builder function produced `builder` and
    what the model's own name/description say. Returns (model, version_id)
    on success, None on failure (logged, never raised — one bundle failing
    to publish shouldn't take the other down with it).
    """
    try:
        output_model = _get_or_create_model(
            automate_context,
            model_name=output_model_name,
            model_description=model_description,
        )
        result = operations.send3(
            automate_context.speckle_client.account,
            automate_context.automation_run_data.project_id,
            output_model.id,
            builder,
            SendOptions(message=send_message),
        )
        return output_model, result.version_id
    except Exception as exc:
        print(f"[ConditioningPOC] Publishing '{output_model_name}' failed: {exc}")
        return None


def create_conditioned_version(
    automate_context: AutomationContext,
    received_model,
    walls: list[WallRecord],
    predictions: list[Prediction],
    code_property_name: str = DEFAULT_CONDITIONING_KEY,
    type_groups: dict[str, TypeGroup] | None = None,
    category_results: list[CategoryResult] | None = None,
) -> ConditionedVersions:
    """Imprint predictions and publish the Conditioned/Walls and Conditioned/All models.

    Both are namespaced per source model — not a single shared model —
    because a workspace can have several source models feeding this function
    (e.g. one client's shell model alongside several other project models
    uploaded around the same time); writing them all into one output model
    would mix unrelated walls together and make each run's output ambiguous.
    Speckle model names use '/' as a folder separator, so 'Conditioned/Walls/<name>' and
    'Conditioned/All/<name>' each group their own output under one parent in the model
    tree while keeping each source distinct.

    2026-09-07 (later still): this used to publish ONE version, into
    'Conditioned/<source>', built by walking only the conditioned walls —
    every other category in the source model (doors, floors, rooms, MEP,
    stairs, ...) was simply never written into the output at all. Flagged in
    that function's own docstring as a deliberate, known scope limitation —
    but a reviewer comparing the output model directly against the source
    read it, reasonably, as data loss, not a documented trade-off. Direction:
    publish a genuine full-scene republish too, and stop treating walls-only
    as the default. `_build_walls_bundle()` (renamed from
    `_build_conditioned_bundle()`) is kept as a second, smaller, faster-to-
    open view — 'Conditioned/Walls/<source>' — for when the only question is
    what conditioning did to the walls; `_build_full_bundle()` is the new
    like-for-like copy of the whole received scene, patched —
    'Conditioned/All/<source>'.
    Both publish from the SAME imprint_predictions() call (below), so a
    wall's conditioning result is identical in both models, just surrounded
    by more or less of the building.

    Also adds both new artifact versions to the Automate run's context view
    (the "View Results" link), alongside the host model — see the comment at
    the set_context_view() call below.

    `code_property_name` is threaded through to imprint_predictions() — see
    main.FunctionInputs.code_property_name for why this is a per-run input
    rather than a hardcoded constant.

    2026-09-07: publishes via operations.send3 and a fresh BundleBuilder
    instead of automate_context.create_new_version_in_project() — see this
    module's and main.py's module docstrings for why. `_get_or_create_model()`
    / `_get_source_model_name()` are untouched: resolving or creating the
    output MODEL is a plain GraphQL call via automate_context.speckle_client
    either way — it's only publishing a VERSION into that model that moved
    off the old JSON-graph transport.

    Returns a ConditionedVersions — check each half independently, since one
    bundle can fail to publish without the other failing too.
    """
    imprint_predictions(
        walls,
        predictions,
        code_property_name=code_property_name,
        type_groups=type_groups,
    )

    category_conditioning = imprint_category_results(
        category_results or [], code_property_name=code_property_name
    )

    source_model_name = _get_source_model_name(automate_context)
    # 'Conditioned/' keeps every output of this function under one parent in
    # the project's model tree, with 'Walls/' and 'All/' as the two views
    # beneath it — Speckle treats '/' in a model name as a folder separator.
    walls_model_name = f"Conditioned/Walls/{source_model_name}"
    all_model_name = f"Conditioned/All/{source_model_name}"

    walls_published = _publish_bundle(
        automate_context,
        walls_model_name,
        model_description=(
            f"Walls and curtain-wall elements with predicted Uniformat "
            f"Assembly Codes for '{source_model_name}' — Conditioning Demo POC"
        ),
        builder=_build_walls_bundle(received_model, walls, walls_model_name),
        send_message=(
            "Uniformat Assembly Code predictions applied by Conditioning Demo POC"
        ),
    )
    all_published = _publish_bundle(
        automate_context,
        all_model_name,
        model_description=(
            f"Full republish of '{source_model_name}' with predicted Uniformat "
            f"Assembly Codes patched onto its walls — Conditioning Demo POC"
        ),
        builder=_build_full_bundle(
            received_model, walls, all_model_name, code_property_name,
            category_conditioning=category_conditioning,
        ),
        send_message=(
            "Full model republish with Uniformat Assembly Code predictions "
            "applied by Conditioning Demo POC"
        ),
    )

    # Add both artifact versions to the run's "View Results" viewer alongside
    # the host model (include_source_model_version=True, the SDK default)
    # rather than replacing it. The host model has to stay in view:
    # attach_viewer_annotations() (called earlier, against the unmutated wall
    # objects) records each result's Speckle object id, and that id is fixed
    # at receive time — it never gets reassigned to match the freshly-built
    # objects pushed to either artifact model. So the interactive per-object
    # highlight markers only resolve against a scene that still has the host
    # model loaded. Adding the artifact models as extra resources just means
    # reviewers can also inspect the actual conditioned output — either view
    # of it — in the same viewer, overlaid rather than swapped in.
    resource_ids = [
        f"{model.id}@{version_id}"
        for published in (walls_published, all_published)
        if published is not None
        for model, version_id in [published]
    ]
    if resource_ids:
        try:
            automate_context.set_context_view(
                resource_ids=resource_ids,
                include_source_model_version=True,
            )
        except Exception as exc:
            print(
                f"[ConditioningPOC] Could not add artifact models to "
                f"results view: {exc}"
            )

    return ConditionedVersions(
        walls_model_name=walls_model_name,
        walls_version_id=walls_published[1] if walls_published else None,
        all_model_name=all_model_name,
        all_version_id=all_published[1] if all_published else None,
    )
