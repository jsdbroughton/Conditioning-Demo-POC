"""Offline unit tests for get_wall_metadata()'s Fire Rating / Height extraction.

Added 2026-09-07 alongside the two new WallRecord fields. Verified against
the live UKHC Core/Podium/Tower models (see docs/NOTES.md) that Fire Rating
is a Type Parameter (same group as Type Mark, under Identity Data) and
Unconnected Height is an Instance Parameter (a different top-level group
entirely) — this file exists to pin that distinction in code, since getting
it wrong would silently read the wrong branch of the properties tree.

2026-09-07 (later the same day): rewritten again after discovering the SDK's
instance→type precedence search only helps when both scopes store a
parameter under the SAME literal path string — it does not strip or infer a
"Instance Parameters."/"Type Parameters." segment on the caller's behalf.
This connector's real paths are "Parameters.Instance Parameters.<Group>.
<Param>" and "Parameters.Type Parameters.<Group>.<Param>", confirmed live
against the Fitout Tower model (see walls.py's module docstring's 2026-09-07
correction) — Fire Rating and Type Mark are Type Parameters, Unconnected
Height is an Instance Parameter. get_wall_metadata() now calls walls._param()/
_param_double(), which try both scopes explicitly. What these tests still
pin: Fire Rating/Type Mark come from the TYPE scope's Identity Data group,
Unconnected Height from the INSTANCE scope's Constraints group — get either
the scope or the group wrong and you're silently reading nothing or the
wrong field.
"""

from __future__ import annotations

from conditioning.walls import get_wall_metadata
from tests.fakes import FakeLevel, FakeModelObject

_TYPE_ID = "Parameters.Type Parameters.Identity Data"
_INSTANCE_CONSTRAINTS = "Parameters.Instance Parameters.Constraints"


def _wall_obj(
    fire_rating_value=None,
    unconnected_height_value=None,
    type_mark_value=None,
    type_="",
    family="",
    level_name="",
) -> FakeModelObject:
    properties = {"type": type_, "family": family}
    if type_mark_value is not None:
        properties[f"{_TYPE_ID}.Type Mark"] = type_mark_value
    if fire_rating_value is not None:
        properties[f"{_TYPE_ID}.Fire Rating"] = fire_rating_value
    if unconnected_height_value is not None:
        properties[f"{_INSTANCE_CONSTRAINTS}.Unconnected Height"] = (
            unconnected_height_value
        )
    return FakeModelObject(
        properties=properties,
        level=FakeLevel(level_name) if level_name else None,
    )


class TestFireRatingExtraction:
    """Fire Rating is read from the Identity Data group, like Type Mark."""

    def test_populated_fire_rating_is_read(self):
        """Populated fire rating is read."""
        meta = get_wall_metadata(_wall_obj(fire_rating_value="1HR/S"))
        assert meta["fire_rating"] == "1HR/S"

    def test_blank_fire_rating_is_empty_string_not_none(self):
        """Blank fire rating is empty string not none.

        Matches the rest of get_wall_metadata()'s string fields (function,
        type_mark) — "" throughout, never None, so callers never have to
        branch on type before checking truthiness.
        """
        assert get_wall_metadata(_wall_obj())["fire_rating"] == ""
        blank = _wall_obj(fire_rating_value="")
        assert get_wall_metadata(blank)["fire_rating"] == ""

    def test_dash_value_is_read_verbatim_not_interpreted_here(self):
        """Dash value is read verbatim, not interpreted here.

        get_wall_metadata() is a pure extraction layer — deciding that "-"
        means "no rating" is attributes.py's job
        (_normalize_fire_rating_param), not this one's.
        """
        dashed = _wall_obj(fire_rating_value="-")
        assert get_wall_metadata(dashed)["fire_rating"] == "-"


class TestUnconnectedHeightExtraction:
    """Height is read from the Constraints group, unlike Fire Rating/Type Mark."""

    def test_height_is_converted_feet_to_mm(self):
        """Height is converted feet to mm."""
        meta = get_wall_metadata(_wall_obj(unconnected_height_value=10.0))
        assert meta["height_mm"] == 3048.0

    def test_missing_height_defaults_to_zero(self):
        """Missing height defaults to zero."""
        assert get_wall_metadata(_wall_obj())["height_mm"] == 0.0

    def test_non_numeric_height_defaults_to_zero_rather_than_raising(self):
        """Non numeric height defaults to zero rather than raising.

        get_double() on a real ModelObject already returns None for a
        non-numeric value at that path (it's a typed column lookup, not a
        string cast) — this pins that get_wall_metadata() still tolerates a
        None from get_double() rather than assuming a float.
        """
        obj = _wall_obj()
        obj.get_double = lambda path: None  # simulate a non-numeric/blank column
        assert get_wall_metadata(obj)["height_mm"] == 0.0


class TestLevelExtraction:
    """Level is the ON_LEVEL relation now, not a property — see module docstring."""

    def test_level_name_is_read_from_the_relation(self):
        """Level name is read from the relation."""
        meta = get_wall_metadata(_wall_obj(level_name="LEVEL 01"))
        assert meta["level"] == "LEVEL 01"

    def test_missing_level_defaults_to_empty_string(self):
        """Missing level defaults to empty string."""
        assert get_wall_metadata(_wall_obj())["level"] == ""
