"""Offline unit tests for attach_viewer_annotations()'s Tier 3 callout.

No live Speckle call — automate_context is a hand-rolled fake recording
attach_info_to_objects / attach_warning_to_objects calls, same pattern as
test_create_conditioned_version.py.

Feedback: knowing there are ANY genuinely Tier 3 predictions (low/no
confidence — the tier that actually means "a human needs to look at this
one", per codes.py) shouldn't require scrolling a big per-method table.
attach_viewer_annotations() now also fires a dedicated, warning-level
annotation for every Tier 3 prediction, grouped by predicted code and
independent of which method produced it.
"""

from __future__ import annotations

from conditioning.predict import predict_codes
from conditioning.speckle_io import attach_viewer_annotations
from conditioning.walls import WallRecord


class _FakeSpeckleObject:
    def __init__(self) -> None:
        self.properties: dict = {}


class _FakeAutomationContext:
    """Stands in for speckle_automate.AutomationContext.

    Implements only the methods attach_viewer_annotations() actually calls.
    """

    def __init__(self) -> None:
        self.info_calls: list[dict] = []
        self.warning_calls: list[dict] = []

    def attach_info_to_objects(
        self,
        category,
        affected_objects,
        message=None,
        **kwargs,
    ):
        self.info_calls.append(
            {"category": category, "objects": affected_objects, "message": message}
        )

    def attach_warning_to_objects(
        self,
        category,
        affected_objects,
        message=None,
        **kwargs,
    ):
        self.warning_calls.append(
            {"category": category, "objects": affected_objects, "message": message}
        )


def _wall(object_id: str, **overrides) -> WallRecord:
    defaults = dict(
        obj=_FakeSpeckleObject(), category="Walls", type_name="", family="Basic Wall",
        function="", type_mark="", width_mm=200.0, level="LEVEL 01", assembly_code=None,
    )
    defaults.update(overrides)
    return WallRecord(object_id=object_id, **defaults)


class TestTier3GetsAWarningLevelAnnotation:
    """Test tier3 gets a warning level annotation."""
    def test_genuine_tier_3_prediction_fires_a_warning(self):
        """Genuine tier 3 prediction fires a warning."""
        # No category, no Function match, no keyword match — falls all the
        # way through to the blind default (confidence 0.0, Tier 3).
        wall = _wall("t3-1", type_name="Unrecognisable Widget", family="", function="")
        predictions = predict_codes([wall], threshold=0.65)
        # sanity-check the fixture actually lands Tier 3
        assert predictions[0].tier == 3

        ctx = _FakeAutomationContext()
        attach_viewer_annotations(
            ctx,
            level4=[],
            non_level4_coded=[],
            predictions=predictions,
        )

        assert len(ctx.warning_calls) == 1
        call = ctx.warning_calls[0]
        assert call["category"] == "Uniformat — Needs Review (Tier 3)"
        assert call["objects"] == [wall.obj]
        assert "Tier 3" in call["message"]

    def test_no_tier_3_predictions_means_no_warning_call(self):
        """No tier 3 predictions means no warning call."""
        wall = _wall("cs-1", category="Curtain Systems", type_name="Storefront")
        predictions = predict_codes([wall], threshold=0.65)
        assert predictions[0].tier == 1  # sanity-check

        ctx = _FakeAutomationContext()
        attach_viewer_annotations(
            ctx,
            level4=[],
            non_level4_coded=[],
            predictions=predictions,
        )

        assert ctx.warning_calls == []
