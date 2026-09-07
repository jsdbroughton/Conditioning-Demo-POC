"""Offline unit tests for imprint_predictions.

The function that computes conditioning output for each wall.

Written under a single namespaced dict — keyed by `code_property_name`, a
user-facing Automate input as of 2026-08-14, defaulting to
DEFAULT_CONDITIONING_KEY — rather than several flat sibling keys, so
there's one predictable place to look in the viewer/report/PowerBI, and no
risk of colliding with a real Revit parameter name.

Direction as of 2026-08-12: every non-Level4 wall — blank or carrying a
legacy/non-ACME code — gets Status "predicted" with a real
Confidence/Tier/Method, auto-applied. "Original Code" is always present in
the dict (None if the wall had no code at all) so nothing is silently
dropped. An earlier version wrote a distinct "needs review" status that left
legacy-coded walls untouched instead — that's no longer the behaviour.

2026-09-07: imprint_predictions() writes to `wall.conditioning` now, not
`wall.obj.properties` — `wall.obj` is a read-only bundle ModelObject with no
properties dict to mutate (see speckle_io.py's and walls.py's module
docstrings). `wall.obj` is irrelevant to this function now, so these tests
no longer bother constructing one — a wall's `obj` field is left at its
dataclass default (None) throughout.
"""

from __future__ import annotations

from conditioning.codes import DEFAULT_CONDITIONING_KEY
from conditioning.predict import predict_codes
from conditioning.speckle_io import imprint_predictions
from conditioning.walls import WallRecord


def _wall(object_id: str, **overrides) -> WallRecord:
    defaults = dict(
        obj=None, category="Walls", type_name="", family="Basic Wall", function="",
        type_mark="", width_mm=200.0, level="LEVEL 01", assembly_code=None,
    )
    defaults.update(overrides)
    return WallRecord(object_id=object_id, **defaults)


class TestImprintExistingLevel4Wall:
    """A wall already in ACME Level 4 format is passed through unchanged."""

    def test_level4_wall_gets_existing_status(self):
        """Level4 wall gets existing status."""
        wall = _wall("l4-1", assembly_code="B2010.10")
        imprint_predictions([wall], predictions=[])

        result = wall.conditioning[DEFAULT_CONDITIONING_KEY]
        # Tier 0 ("no work to be done") added 2026-08-14 — every wall now
        # carries a Tier, not just predicted ones. See codes.TIER_LABELS.
        #
        # This is the only case where Requires Verification is False, and it
        # is the reason the flag is worth having: a reviewer filtering on it
        # gets exactly the elements Speckle decided, and nothing that the
        # model already asserted for itself.
        assert result == {
            "Status": "existing",
            "Level 4 Code": "B2010.10",
            "Level 4 Code Description": "Exterior Wall Veneer",
            "Level 4 Code Source": "authored — already a valid Level 4 code",
            "Requires Verification": False,
            "Tier": "Tier 0",
        }


class TestImprintPredictedWall:
    """A wall with no code at all gets a real prediction written.

    Original Code is None — there was nothing to preserve.
    """

    def test_uncoded_wall_gets_predicted_status(self):
        """Uncoded wall gets predicted status."""
        wall = _wall("blank-1", function="Exterior")
        predictions = predict_codes([wall], threshold=0.65)
        imprint_predictions([wall], predictions)

        result = wall.conditioning[DEFAULT_CONDITIONING_KEY]
        assert result["Status"] == "predicted"
        assert result["Level 4 Code"] == "B2010.10"
        assert result["Level 4 Code Description"] == "Exterior Wall Veneer"
        assert result["Method"] == "heuristic_function"
        assert result["Confidence"] == 0.75
        # A lone, uncorroborated Function-param match no longer clears
        # TIER_1_THRESHOLD (0.85) — this wall's blank type_name/family give
        # nothing else to corroborate it, so it lands Tier 2.
        assert result["Tier"] == "Tier 2"
        assert result["Original Code"] is None


class TestImprintRemapsLegacyCode:
    """A wall with an existing-but-non-Level4 code (e.g.

    legacy ASTM) gets remapped and auto-applied — the original code is preserved
    alongside the new one, never discarded. This replaces the earlier 'needs review,
    leave untouched' behaviour.
    """

    def test_astm_coded_wall_gets_predicted_status_with_original_preserved(self):
        """ASTM coded wall gets predicted status with original preserved."""
        wall = _wall("astm-1", function="Exterior", assembly_code="B2010160")
        predictions = predict_codes([wall], threshold=0.65)
        imprint_predictions([wall], predictions)

        result = wall.conditioning[DEFAULT_CONDITIONING_KEY]
        assert result["Status"] == "predicted"
        assert result["Level 4 Code"] == "B2010.10"
        assert result["Original Code"] == "B2010160"
        # Same lone-signal case as the uncoded test above — Tier 2, not 1.
        assert result["Tier"] == "Tier 2"
        # the wall's own assembly_code field is untouched by imprinting —
        # only the conditioning dict carries the new code
        assert wall.assembly_code == "B2010160"


class TestImprintCurtainWallElement:
    """Test imprint curtain wall element."""
    def test_curtain_panel_gets_predicted_b2010_40(self):
        """Curtain panel gets predicted b2010 40."""
        wall = _wall(
            "cp-1",
            category="Curtain Panels",
            type_name="Glazed Panel",
        )
        predictions = predict_codes([wall], threshold=0.65)
        imprint_predictions([wall], predictions)

        result = wall.conditioning[DEFAULT_CONDITIONING_KEY]
        assert result["Status"] == "predicted"
        assert result["Level 4 Code"] == "B2010.40"
        assert (
            result["Level 4 Code Description"] == "Fabricated Exterior Wall Assemblies"
        )
        assert result["Method"] == "heuristic_category"
        assert result["Tier"] == "Tier 1"


class TestConditioningKeyIsSingularNamespace:
    """Test conditioning key is singular namespace."""
    def test_only_one_top_level_key_written(self):
        """Only one top level key written."""
        wall = _wall("l4-1", assembly_code="B2010.10")
        imprint_predictions([wall], predictions=[])
        assert list(wall.conditioning.keys()) == [DEFAULT_CONDITIONING_KEY]
