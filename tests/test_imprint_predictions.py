"""Offline unit tests for imprint_predictions — the function that writes
conditioning output onto wall objects.

As of 2026-08-12 this is written under a single namespaced
`Conditioning Results` dict (CONDITIONING_KEY) rather than several flat
sibling keys, so there's one predictable place to look in the viewer/report/
PowerBI, and no risk of colliding with a real Revit parameter name.
"""

from __future__ import annotations

from conditioning.codes import CONDITIONING_KEY
from conditioning.predict import predict_codes
from conditioning.speckle_io import imprint_predictions
from conditioning.walls import WallRecord


class _FakeSpeckleObject:
    """Minimal stand-in for a Speckle DataObject — just needs a .properties dict."""

    def __init__(self) -> None:
        self.properties: dict = {}


def _wall_with_obj(object_id: str, **overrides) -> WallRecord:
    defaults = dict(
        type_name="", family="Basic Wall", function="", type_mark="",
        width_mm=200.0, level="LEVEL 01", assembly_code=None,
    )
    defaults.update(overrides)
    return WallRecord(obj=_FakeSpeckleObject(), object_id=object_id, **defaults)


class TestImprintExistingLevel4Wall:
    """A wall already in Turner Level 4 format is passed through unchanged."""

    def test_level4_wall_gets_existing_status(self):
        wall = _wall_with_obj("l4-1", assembly_code="B2010.10")
        imprint_predictions([wall], predictions=[])

        result = wall.obj.properties[CONDITIONING_KEY]
        assert result == {"Status": "existing", "Level 4 Code": "B2010.10"}


class TestImprintPredictedWall:
    """A wall with no code at all gets a real prediction written."""

    def test_uncoded_wall_gets_predicted_status(self):
        wall = _wall_with_obj("blank-1", function="Exterior")
        predictions = predict_codes([wall], threshold=0.65)
        imprint_predictions([wall], predictions)

        result = wall.obj.properties[CONDITIONING_KEY]
        assert result["Status"] == "predicted"
        assert result["Level 4 Code"] == "B2010.10"
        assert result["Method"] == "heuristic_function"
        assert result["Confidence"] == 0.75


class TestImprintNeedsReviewWall:
    """A wall with an existing-but-non-Level4 code (e.g. legacy ASTM) is
    flagged for manual review and NEVER overwritten — this is the regression
    test for the bug caught live on the 2026-07-17 Turner call."""

    def test_astm_coded_wall_gets_needs_review_status_and_is_not_overwritten(self):
        wall = _wall_with_obj("astm-1", assembly_code="B2010160")
        predictions = predict_codes([wall], threshold=0.65)  # no uncoded walls -> []
        imprint_predictions([wall], predictions)

        result = wall.obj.properties[CONDITIONING_KEY]
        assert result["Status"] == "needs review"
        assert result["Original Code"] == "B2010160"
        assert "not Turner Level 4" in result["Reason"]
        # the wall's own assembly_code must be untouched by imprinting
        assert wall.assembly_code == "B2010160"


class TestConditioningKeyIsSingularNamespace:
    def test_only_one_top_level_key_written(self):
        wall = _wall_with_obj("l4-1", assembly_code="B2010.10")
        imprint_predictions([wall], predictions=[])
        assert list(wall.obj.properties.keys()) == [CONDITIONING_KEY]
