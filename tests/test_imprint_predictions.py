"""Offline unit tests for imprint_predictions — the function that writes
conditioning output onto wall objects.

Written under a single namespaced `Turner UF Code` dict
(CONDITIONING_KEY) rather than several flat sibling keys, so there's one
predictable place to look in the viewer/report/PowerBI, and no risk of
colliding with a real Revit parameter name.

Direction as of 2026-08-12: every non-Level4 wall — blank or carrying a
legacy/non-Turner code — gets Status "predicted" with a real
Confidence/Tier/Method, auto-applied. "Original Code" is always present in
the dict (None if the wall had no code at all) so nothing is silently
dropped. An earlier version wrote a distinct "needs review" status that left
legacy-coded walls untouched instead — that's no longer the behaviour.
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
        category="Walls", type_name="", family="Basic Wall", function="",
        type_mark="", width_mm=200.0, level="LEVEL 01", assembly_code=None,
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
    """A wall with no code at all gets a real prediction written, with no
    Original Code (nothing to preserve)."""

    def test_uncoded_wall_gets_predicted_status(self):
        wall = _wall_with_obj("blank-1", function="Exterior")
        predictions = predict_codes([wall], threshold=0.65)
        imprint_predictions([wall], predictions)

        result = wall.obj.properties[CONDITIONING_KEY]
        assert result["Status"] == "predicted"
        assert result["Level 4 Code"] == "B2010.10"
        assert result["Method"] == "heuristic_function"
        assert result["Confidence"] == 0.75
        assert result["Tier"] == "Tier 1"
        assert result["Original Code"] is None


class TestImprintRemapsLegacyCode:
    """A wall with an existing-but-non-Level4 code (e.g. legacy ASTM) gets
    remapped and auto-applied — the original code is preserved alongside the
    new one, never discarded. This replaces the earlier 'needs review,
    leave untouched' behaviour."""

    def test_astm_coded_wall_gets_predicted_status_with_original_preserved(self):
        wall = _wall_with_obj("astm-1", function="Exterior", assembly_code="B2010160")
        predictions = predict_codes([wall], threshold=0.65)
        imprint_predictions([wall], predictions)

        result = wall.obj.properties[CONDITIONING_KEY]
        assert result["Status"] == "predicted"
        assert result["Level 4 Code"] == "B2010.10"
        assert result["Original Code"] == "B2010160"
        assert result["Tier"] == "Tier 1"
        # the wall's own assembly_code field is untouched by imprinting —
        # only the written properties dict carries the new code
        assert wall.assembly_code == "B2010160"


class TestImprintCurtainWallElement:
    def test_curtain_panel_gets_predicted_b2010_40(self):
        wall = _wall_with_obj("cp-1", category="Curtain Panels", type_name="Glazed Panel")
        predictions = predict_codes([wall], threshold=0.65)
        imprint_predictions([wall], predictions)

        result = wall.obj.properties[CONDITIONING_KEY]
        assert result["Status"] == "predicted"
        assert result["Level 4 Code"] == "B2010.40"
        assert result["Method"] == "heuristic_category"
        assert result["Tier"] == "Tier 1"


class TestConditioningKeyIsSingularNamespace:
    def test_only_one_top_level_key_written(self):
        wall = _wall_with_obj("l4-1", assembly_code="B2010.10")
        imprint_predictions([wall], predictions=[])
        assert list(wall.obj.properties.keys()) == [CONDITIONING_KEY]
