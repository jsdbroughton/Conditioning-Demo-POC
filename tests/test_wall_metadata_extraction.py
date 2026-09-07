"""Offline unit tests for get_wall_metadata()'s Fire Rating / Height extraction.

Added 2026-09-07 alongside the two new WallRecord fields. Verified against
the live UKHC Core/Podium/Tower models (see docs/NOTES.md) that Fire Rating
is a Type Parameter (same group as Type Mark, under Identity Data) and
Unconnected Height is an Instance Parameter (a different top-level group
entirely) — this file exists to pin that distinction in code, since getting
it wrong would silently read the wrong branch of the properties tree.
"""

from __future__ import annotations

from conditioning.walls import get_wall_metadata


class _FakeWallObj:
    """Minimal stand-in for a Speckle DataObject with both parameter groups.

    Identity Data (Fire Rating, Type Mark) lives under Type Parameters;
    Unconnected Height lives under the sibling Instance Parameters group —
    matching the live model structure, not the Type-Parameters-only shape
    test_get_assembly_code.py's fake object uses.
    """

    def __init__(
        self,
        fire_rating_value=None,
        unconnected_height_value=None,
        type_mark_value=None,
        type_="",
        family="",
        level="",
    ):
        self.type = type_
        self.family = family
        self.level = level
        self.properties = {
            "Parameters": {
                "Type Parameters": {
                    "Identity Data": {
                        "Type Mark": {"value": type_mark_value},
                        "Fire Rating": {"value": fire_rating_value},
                    },
                    "Construction": {},
                },
                "Instance Parameters": {
                    "Constraints": {
                        "Unconnected Height": {"value": unconnected_height_value},
                    },
                },
            }
        }


class TestFireRatingExtraction:
    """Fire Rating is read from Type Parameters > Identity Data, like Type Mark."""

    def test_populated_fire_rating_is_read(self):
        """Populated fire rating is read."""
        meta = get_wall_metadata(_FakeWallObj(fire_rating_value="1HR/S"))
        assert meta["fire_rating"] == "1HR/S"

    def test_blank_fire_rating_is_empty_string_not_none(self):
        """Blank fire rating is empty string not none.

        Matches the rest of get_wall_metadata()'s string fields (function,
        type_mark) — "" throughout, never None, so callers never have to
        branch on type before checking truthiness.
        """
        assert get_wall_metadata(_FakeWallObj())["fire_rating"] == ""
        blank = _FakeWallObj(fire_rating_value="")
        assert get_wall_metadata(blank)["fire_rating"] == ""

    def test_dash_value_is_read_verbatim_not_interpreted_here(self):
        """Dash value is read verbatim, not interpreted here.

        get_wall_metadata() is a pure extraction layer — deciding that "-"
        means "no rating" is attributes.py's job
        (_normalize_fire_rating_param), not this one's.
        """
        dashed = _FakeWallObj(fire_rating_value="-")
        assert get_wall_metadata(dashed)["fire_rating"] == "-"


class TestUnconnectedHeightExtraction:
    """Height is read from Instance Parameters > Constraints, unlike other fields."""

    def test_height_is_converted_feet_to_mm(self):
        """Height is converted feet to mm."""
        meta = get_wall_metadata(_FakeWallObj(unconnected_height_value=10.0))
        assert meta["height_mm"] == 3048.0

    def test_missing_height_defaults_to_zero(self):
        """Missing height defaults to zero."""
        assert get_wall_metadata(_FakeWallObj())["height_mm"] == 0.0

    def test_non_numeric_height_defaults_to_zero_rather_than_raising(self):
        """Non numeric height defaults to zero rather than raising."""
        meta = get_wall_metadata(_FakeWallObj(unconnected_height_value="N/A"))
        assert meta["height_mm"] == 0.0

    def test_height_does_not_read_from_type_parameters(self):
        """Height does not read from type parameters.

        A Width-shaped Instance Parameters block with nothing under
        Constraints must not accidentally fall back to a Type Parameters
        value — the two groups are genuinely different Revit parameter
        classes and this pins that they're never conflated.
        """
        obj = _FakeWallObj(unconnected_height_value=None)
        obj.properties["Parameters"]["Type Parameters"]["Constraints"] = {
            "Unconnected Height": {"value": 99.0}
        }
        assert get_wall_metadata(obj)["height_mm"] == 0.0
