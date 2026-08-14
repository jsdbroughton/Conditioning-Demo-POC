"""Offline unit tests for the conditioning logic — no live Speckle call.

Direction as of 2026-08-12: every non-Level4 wall (blank OR carrying a
legacy/non-Turner code, e.g. ASTM Uniformat II like B2010160) gets a real,
method-based confidence score and a Tier 1/2/3 rating, and is auto-applied.
An earlier version of this function left ASTM-coded walls untouched and
flagged "needs review" instead of predicting — these tests assert the
current, intended behaviour instead.

Also covers curtain wall elements (Revit's "Curtain Systems" / "Curtain
Panels" / "Curtain Wall Mullions" categories, distinct from "Walls") getting
classified correctly via the category-based heuristic — these were
previously excluded from collection entirely, see test_walls_collection.py.

See docs/NOTES.md session history for the full write-up.
"""

from __future__ import annotations

from conditioning.codes import (
    CONFLICT_PENALTY,
    CORROBORATION_BONUS,
    CORROBORATION_CAP,
    CURTAIN_LEGACY_CROSSWALK_CONFIDENCE,
    METHOD_CONFIDENCE,
    confidence_to_tier,
    tier_label,
)
from conditioning.predict import predict_codes
from conditioning.walls import WallRecord


def _wall(
    object_id: str,
    type_name: str = "",
    category: str = "Walls",
    family: str = "Basic Wall",
    function: str = "",
    type_mark: str = "",
    width_mm: float = 200.0,
    level: str = "LEVEL 01",
    assembly_code: str | None = None,
) -> WallRecord:
    """Build a WallRecord with sensible defaults. `obj` is unused by the pure
    prediction logic under test, so a plain placeholder stands in for the
    real Speckle DataObject."""
    return WallRecord(
        obj=object(),
        object_id=object_id,
        category=category,
        type_name=type_name,
        family=family,
        function=function,
        type_mark=type_mark,
        width_mm=width_mm,
        level=level,
        assembly_code=assembly_code,
    )


class TestWallRecordFormatDetection:
    def test_level4_code_detected(self):
        assert _wall("a", assembly_code="B2010.10").is_level4_coded is True
        assert _wall("a", assembly_code="B2010.10").is_astm_coded is False

    def test_astm_code_detected(self):
        w = _wall("a", assembly_code="B2010160")
        assert w.is_astm_coded is True
        assert w.is_level4_coded is False
        assert w.is_coded is True

    def test_uncoded_wall(self):
        w = _wall("a", assembly_code=None)
        assert w.is_coded is False
        assert w.is_level4_coded is False
        assert w.is_astm_coded is False


class TestPredictCodesRemapsLegacyCodes:
    """Every non-Level4 wall — blank or ASTM-coded — gets a prediction.
    predict_codes() never mutates the WallRecord itself; the original code
    is preserved and applied at the imprint stage (see
    test_imprint_predictions.py), not discarded here or anywhere else."""

    def test_astm_coded_wall_gets_a_prediction(self):
        astm_wall = _wall(
            "astm-1", type_name="GFRC Panel", function="Exterior",
            assembly_code="B2010160",
        )
        uncoded_wall = _wall("uncoded-1", type_name="Unrelated Type", function="")

        predictions = predict_codes([astm_wall, uncoded_wall], threshold=0.65)

        predicted_ids = {p.wall.object_id for p in predictions}
        assert "astm-1" in predicted_ids
        # predict_codes must never mutate the WallRecord's own field
        assert astm_wall.assembly_code == "B2010160"

    def test_all_non_level4_walls_are_predicted(self):
        walls = [
            _wall("l4-1", assembly_code="B2010.10"),    # already good — not predicted
            _wall("astm-1", assembly_code="C1010145"),  # legacy code — remapped
            _wall("blank-1", assembly_code=None),         # prediction target
            _wall("blank-2", assembly_code=""),           # prediction target (empty string)
        ]
        predictions = predict_codes(walls, threshold=0.65)
        predicted_ids = {p.wall.object_id for p in predictions}
        assert predicted_ids == {"astm-1", "blank-1", "blank-2"}


class TestPredictCodesUsesAstmWallsAsReferences:
    """ASTM-coded walls contribute their type/family/function fingerprint to
    similarity matching for other walls — they're just not allowed to hand
    out their own raw (non-ACME-format) code as a "confident" match."""

    def test_uncoded_wall_matches_astm_reference_falls_back_to_heuristic(self):
        astm_wall = _wall(
            "astm-1", type_name="GFRC Panel", family="Basic Wall",
            function="Exterior", type_mark="CMV-1", width_mm=200.0,
            assembly_code="B2010160",
        )
        # Identical fingerprint fields → similarity score of 1.0 against astm_wall
        uncoded_wall = _wall(
            "uncoded-1", type_name="GFRC Panel", family="Basic Wall",
            function="Exterior", type_mark="CMV-1", width_mm=200.0,
        )

        predictions = predict_codes([astm_wall, uncoded_wall], threshold=0.65)
        uncoded_pred = next(p for p in predictions if p.wall.object_id == "uncoded-1")

        # Must NOT hand out the ASTM wall's raw non-ACME code as a
        # "similarity" match — falls back to the heuristic instead.
        assert uncoded_pred.method != "similarity"
        assert uncoded_pred.method == "heuristic_function"
        assert uncoded_pred.predicted_code == "B2010.10"
        # "GFRC Panel" also matches the "gfrc" keyword — an independent
        # signal agreeing with the Function param — so this lands above the
        # bare heuristic_function base confidence, not exactly on it.
        assert uncoded_pred.confidence == METHOD_CONFIDENCE["heuristic_function"] + CORROBORATION_BONUS
        # Traceability preserved even though the match wasn't used directly
        assert uncoded_pred.matched_from == "GFRC Panel"

    def test_wall_never_matches_itself_as_reference(self):
        # Alone in the list, this ASTM-coded wall is simultaneously in the
        # reference pool (is_coded) and the prediction targets (not
        # is_level4_coded) — it must not be compared against itself.
        astm_wall = _wall(
            "astm-1", type_name="GFRC Panel", function="Exterior",
            assembly_code="B2010160",
        )
        predictions = predict_codes([astm_wall], threshold=0.65)
        assert len(predictions) == 1
        assert predictions[0].method != "similarity"
        assert predictions[0].matched_from is None


class TestPredictCodesSimilarityAgainstLevel4Reference:
    def test_similarity_match_used_when_reference_is_level4(self):
        reference = _wall(
            "l4-1", type_name="Curtain Wall Type A", family="Curtain Wall",
            function="Exterior", type_mark="CW-1", width_mm=150.0,
            assembly_code="B2010.40",
        )
        uncoded_wall = _wall(
            "uncoded-1", type_name="Curtain Wall Type A", family="Curtain Wall",
            function="Exterior", type_mark="CW-1", width_mm=150.0,
        )

        predictions = predict_codes([reference, uncoded_wall], threshold=0.65)
        assert len(predictions) == 1
        pred = predictions[0]

        assert pred.method == "similarity"
        assert pred.predicted_code == "B2010.40"
        assert pred.confidence == 1.0
        assert pred.tier == 1
        assert pred.matched_from == "Curtain Wall Type A"

    def test_default_threshold_used_when_not_passed_explicitly(self):
        # confidence_threshold was removed as a user-facing Automate input
        # 2026-08-14 — production code (main.py) now calls predict_codes()
        # with no threshold argument at all, relying entirely on the
        # codes.SIMILARITY_MATCH_THRESHOLD default. This proves that default
        # actually produces the same behaviour as explicitly passing 0.65,
        # not just that the parameter still technically accepts a value.
        reference = _wall(
            "l4-2", type_name="Curtain Wall Type A", family="Curtain Wall",
            function="Exterior", type_mark="CW-1", width_mm=150.0,
            assembly_code="B2010.40",
        )
        uncoded_wall = _wall(
            "uncoded-2", type_name="Curtain Wall Type A", family="Curtain Wall",
            function="Exterior", type_mark="CW-1", width_mm=150.0,
        )

        predictions = predict_codes([reference, uncoded_wall])  # no threshold arg
        pred = predictions[0]

        assert pred.method == "similarity"
        assert pred.predicted_code == "B2010.40"


class TestCurtainWallCategoryHeuristic:
    """Curtain Systems / Curtain Panels / Curtain Wall Mullions are separate
    Revit categories from Walls. The category is checked first in
    _heuristic_predict — it's Revit's own authoritative assignment, stronger
    than any keyword or Function-param guess."""

    def test_curtain_system_classified_as_curtain_wall_assembly(self):
        # "Storefront" also matches the "storefront" keyword — an
        # independent signal agreeing with the category — so confidence
        # lands above the bare heuristic_category base, capped below 1.0.
        wall = _wall("cs-1", category="Curtain Systems", type_name="Storefront")
        predictions = predict_codes([wall], threshold=0.65)
        pred = predictions[0]
        assert pred.predicted_code == "B2010.40"
        assert pred.method == "heuristic_category"
        assert pred.confidence == min(
            CORROBORATION_CAP, METHOD_CONFIDENCE["heuristic_category"] + CORROBORATION_BONUS
        )
        assert pred.tier == 1

    def test_curtain_panel_classified_as_curtain_wall_assembly(self):
        wall = _wall("cp-1", category="Curtain Panels", type_name="Glazed Panel")
        predictions = predict_codes([wall], threshold=0.65)
        assert predictions[0].predicted_code == "B2010.40"
        assert predictions[0].method == "heuristic_category"

    def test_curtain_wall_mullions_classified_as_curtain_wall_assembly(self):
        wall = _wall("cm-1", category="Curtain Wall Mullions", type_name="Mullion")
        predictions = predict_codes([wall], threshold=0.65)
        assert predictions[0].predicted_code == "B2010.40"
        assert predictions[0].method == "heuristic_category"

    def test_category_signal_beats_function_param(self):
        # Function says "Interior" (would normally heuristic_function ->
        # C1010.10), but the category is a curtain category — category wins
        # on which code gets predicted. But the two signals *disagree*
        # (B2010.40 vs C1010.10) — a genuine data inconsistency on this
        # wall — so confidence is penalised below the bare category base
        # rather than staying at full trust.
        wall = _wall(
            "cp-2", category="Curtain Panels", type_name="Glazed Panel",
            function="Interior",
        )
        predictions = predict_codes([wall], threshold=0.65)
        pred = predictions[0]
        assert pred.predicted_code == "B2010.40"
        assert pred.method == "heuristic_category"
        assert pred.confidence == METHOD_CONFIDENCE["heuristic_category"] - CONFLICT_PENALTY

    def test_plain_wall_category_does_not_trigger_curtain_heuristic(self):
        wall = _wall("w-1", category="Walls", type_name="Basic Wall", function="Exterior")
        predictions = predict_codes([wall], threshold=0.65)
        assert predictions[0].method == "heuristic_function"
        assert predictions[0].predicted_code == "B2010.10"


class TestCurtainWallLegacyCodeCrosswalk:
    """A curtain-category wall's own pre-existing legacy code can disagree
    with what the category alone would suggest — e.g. a legacy B2020
    (Exterior Windows) code on a Revit 'Curtain Systems' element, which
    Revit's category taxonomy can't distinguish from true structural curtain
    wall (B2010). When that happens, trust the legacy code's section over
    the bare category guess, but only at Tier 2 (2026-08-13 direction)."""

    def test_legacy_code_disagreeing_section_crosswalks_to_window_wall(self):
        wall = _wall(
            "cs-1", category="Curtain Systems", type_name="Unremarkable Type",
            assembly_code="B2020200",
        )
        predictions = predict_codes([wall], threshold=0.65)
        pred = predictions[0]
        assert pred.predicted_code == "B2020.30"
        assert pred.method == "heuristic_category_crosswalk"
        assert pred.confidence == CURTAIN_LEGACY_CROSSWALK_CONFIDENCE
        assert pred.tier == 2

    def test_disagreeing_section_crosswalk_that_also_conflicts_with_function_drops_to_tier_3(self):
        # Real case, confirmed on a live run (2026-08-13): 24 elements had
        # category="Curtain Systems", legacy code B2020200 (crosswalks to
        # B2020.30), AND Function="Exterior" (which independently signals
        # B2010.10 — a different code again). Two disagreeing signals on a
        # wall whose primary code is already just a domain-read guess, not a
        # confirmed crosswalk — that combination deserves a closer look, not
        # a quick one.
        wall = _wall(
            "cs-4", category="Curtain Systems", type_name="Unremarkable Type",
            function="Exterior", assembly_code="B2020200",
        )
        predictions = predict_codes([wall], threshold=0.65)
        pred = predictions[0]
        assert pred.predicted_code == "B2020.30"
        assert pred.method == "heuristic_category_crosswalk"
        assert pred.confidence == CURTAIN_LEGACY_CROSSWALK_CONFIDENCE - CONFLICT_PENALTY
        assert pred.tier == 3

    def test_legacy_code_agreeing_section_stays_on_curtain_wall(self):
        wall = _wall(
            "cs-2", category="Curtain Systems", type_name="Unremarkable Type",
            assembly_code="B2010160",
        )
        predictions = predict_codes([wall], threshold=0.65)
        pred = predictions[0]
        assert pred.predicted_code == "B2010.40"
        assert pred.method == "heuristic_category"
        assert pred.confidence == METHOD_CONFIDENCE["heuristic_category"]
        assert pred.tier == 1

    def test_no_legacy_code_stays_on_curtain_wall(self):
        # No assembly_code at all — nothing to disagree with the category.
        wall = _wall("cs-3", category="Curtain Systems", type_name="Unremarkable Type")
        predictions = predict_codes([wall], threshold=0.65)
        pred = predictions[0]
        assert pred.predicted_code == "B2010.40"
        assert pred.method == "heuristic_category"


class TestPerObjectConfidenceAdjustment:
    """Confidence is a per-object value, not purely a lookup by method — two
    walls classified via the same method can score differently depending on
    whether other independent signals on that specific wall agree or
    disagree with the strongest one."""

    def test_single_signal_stays_at_method_base(self):
        # Only Function fires here — type_name/family are neutral text with
        # no HEURISTIC_MAP keyword in them, so there's no second, independent
        # signal to corroborate or conflict with the Function match. A lone
        # heuristic_function match (0.75) no longer clears TIER_1_THRESHOLD
        # (0.85) on its own — that's the point of raising it: one
        # uncorroborated parameter shouldn't earn "candidate for auto-accept".
        wall = _wall("r-1", type_name="Foo Type", family="Bar Family", function="Retaining")
        predictions = predict_codes([wall], threshold=0.65)
        pred = predictions[0]
        assert pred.method == "heuristic_function"
        assert pred.confidence == METHOD_CONFIDENCE["heuristic_function"]
        assert pred.tier == 2

    def test_agreeing_signals_boost_confidence_above_method_base(self):
        # Function says Exterior AND the type name says "masonry" — two
        # independent signals landing on the same code (B2010.10). The
        # corroborated score (0.85) is exactly what lifts this wall into
        # Tier 1, where the same match alone (0.75) would not have.
        wall = _wall("agree-1", type_name="Masonry Veneer", function="Exterior")
        predictions = predict_codes([wall], threshold=0.65)
        pred = predictions[0]
        assert pred.predicted_code == "B2010.10"
        assert pred.method == "heuristic_function"
        assert pred.confidence == min(
            CORROBORATION_CAP, METHOD_CONFIDENCE["heuristic_function"] + CORROBORATION_BONUS
        )
        assert pred.tier == 1

    def test_conflicting_signals_reduce_confidence_below_method_base(self):
        # Function says Exterior (-> B2010.10) but the type name says
        # "partition" (-> C1010.10) — a real contradiction on this wall.
        wall = _wall("conflict-1", type_name="Partition Type", function="Exterior")
        predictions = predict_codes([wall], threshold=0.65)
        pred = predictions[0]
        assert pred.predicted_code == "B2010.10"  # Function still wins the code itself
        assert pred.method == "heuristic_function"
        assert pred.confidence == METHOD_CONFIDENCE["heuristic_function"] - CONFLICT_PENALTY
        # A contradiction pulls this specific wall down a tier vs. the clean case
        assert pred.tier == 2

    def test_corroboration_bonus_is_capped_below_certainty(self):
        wall = _wall("cs-1", category="Curtain Systems", type_name="Storefront")
        predictions = predict_codes([wall], threshold=0.65)
        assert predictions[0].confidence <= CORROBORATION_CAP
        assert predictions[0].confidence < 1.0

    def test_bare_name_only_match_is_a_coin_toss_and_lands_tier_3(self):
        # Only a type-name keyword fires — no category, no Function param.
        # heuristic_name is only ever the primary/sole signal when nothing
        # else fired, so there's nothing left to corroborate or conflict it
        # away from its base (0.50) — a coin toss, not a "quick check" case.
        # Per 2026-08-13 direction this now lands Tier 3, not Tier 2.
        wall = _wall("name-only-1", type_name="Masonry Wall", function="")
        predictions = predict_codes([wall], threshold=0.65)
        pred = predictions[0]
        assert pred.method == "heuristic_name"
        assert pred.confidence == METHOD_CONFIDENCE["heuristic_name"]
        assert pred.tier == 3


class TestConfidenceReflectsMethodReliability:
    def test_default_fallback_has_zero_confidence(self):
        uncoded_wall = _wall(
            "uncoded-1", type_name="Unrecognisable Widget", family="",
            function="",
        )
        predictions = predict_codes([uncoded_wall], threshold=0.65)
        assert len(predictions) == 1
        pred = predictions[0]

        assert pred.method == "default"
        assert pred.confidence == 0.0
        assert pred.tier == 3

    def test_method_confidence_ordering(self):
        assert (
            METHOD_CONFIDENCE["heuristic_category"]
            > METHOD_CONFIDENCE["heuristic_function"]
            > METHOD_CONFIDENCE["heuristic_name"]
            > METHOD_CONFIDENCE["default"]
        )


class TestConfidenceToTier:
    def test_tier_1_boundary(self):
        assert confidence_to_tier(1.0) == 1
        assert confidence_to_tier(0.85) == 1

    def test_tier_2_band(self):
        assert confidence_to_tier(0.84) == 2
        assert confidence_to_tier(0.75) == 2  # a lone heuristic_function match no longer clears Tier 1
        assert confidence_to_tier(0.55) == 2

    def test_tier_3_band(self):
        # 0.50 is a bare heuristic_name match (a coin toss) — no longer
        # clears Tier 2, per 2026-08-13 direction.
        assert confidence_to_tier(0.54) == 3
        assert confidence_to_tier(0.50) == 3
        assert confidence_to_tier(0.49) == 3
        assert confidence_to_tier(0.0) == 3


class TestTierLabel:
    """tier_label() is the text form written onto Speckle objects — internal
    logic (counting, sorting, a future auto-accept gate) still works off the
    plain int from confidence_to_tier()."""

    def test_known_tiers_render_as_text(self):
        assert tier_label(1) == "Tier 1"
        assert tier_label(2) == "Tier 2"
        assert tier_label(3) == "Tier 3"
