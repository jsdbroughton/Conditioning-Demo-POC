"""Offline unit tests for the conditioning logic — no live Speckle call.

These exercise the exact regression caught live on the 2026-07-17 Turner call:
the prediction engine was overwriting walls that already had a legacy ASTM
Uniformat II code (e.g. B2010160) with a generic default (B2010.10), and
reporting a confidence of 0.0 for every single prediction because the
similarity-reference pool only ever contained dot-notation Level 4 walls,
which this model has none of.

See docs/NOTES.md session history for the fix write-up.
"""

from __future__ import annotations

from conditioning.codes import METHOD_CONFIDENCE
from conditioning.predict import predict_codes
from conditioning.walls import WallRecord


def _wall(
    object_id: str,
    type_name: str = "",
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


class TestPredictCodesDoesNotOverwriteExistingCodes:
    """The core regression test: an ASTM-coded wall must survive predict_codes
    completely untouched — it must never appear as a Prediction target."""

    def test_astm_coded_wall_is_never_predicted(self):
        astm_wall = _wall(
            "astm-1", type_name="GFRC Panel", function="Exterior",
            assembly_code="B2010160",
        )
        uncoded_wall = _wall(
            "uncoded-1", type_name="Unrelated Type", function="",
        )

        predictions = predict_codes([astm_wall, uncoded_wall], threshold=0.65)

        predicted_ids = {p.wall.object_id for p in predictions}
        assert "astm-1" not in predicted_ids
        # original code must be untouched on the WallRecord itself
        assert astm_wall.assembly_code == "B2010160"

    def test_only_truly_uncoded_walls_are_predicted(self):
        walls = [
            _wall("l4-1", assembly_code="B2010.10"),           # already good
            _wall("astm-1", assembly_code="C1010145"),         # needs review, not prediction
            _wall("blank-1", assembly_code=None),               # prediction target
            _wall("blank-2", assembly_code=""),                 # prediction target (empty string)
        ]
        predictions = predict_codes(walls, threshold=0.65)
        predicted_ids = {p.wall.object_id for p in predictions}
        assert predicted_ids == {"blank-1", "blank-2"}


class TestPredictCodesUsesAstmWallsAsReferences:
    """ASTM-coded walls should still contribute their type/family/function
    fingerprint to similarity matching for genuinely uncoded walls — they're
    just not allowed to hand out their own raw (non-Turner-format) code."""

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
        assert len(predictions) == 1
        pred = predictions[0]

        # Must NOT hand out the ASTM wall's raw non-Turner code as a
        # "similarity" match — falls back to the heuristic instead.
        assert pred.method != "similarity"
        assert pred.method == "heuristic_function"
        assert pred.predicted_code == "B2010.10"
        assert pred.confidence == METHOD_CONFIDENCE["heuristic_function"]
        # Traceability preserved even though the match wasn't used directly
        assert pred.matched_from == "GFRC Panel"


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
        assert pred.matched_from == "Curtain Wall Type A"


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

    def test_heuristic_function_beats_heuristic_name_confidence(self):
        assert (
            METHOD_CONFIDENCE["heuristic_function"]
            > METHOD_CONFIDENCE["heuristic_name"]
            > METHOD_CONFIDENCE["default"]
        )
