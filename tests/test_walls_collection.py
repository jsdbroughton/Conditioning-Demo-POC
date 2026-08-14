"""Offline unit tests for collect_walls()'s category filter.

Revit models curtain walls as three categories distinct from "Walls": the
curtain wall host ("Curtain Systems"), the glazing/spandrel infill ("Curtain
Panels"), and the framing members ("Curtain Wall Mullions"). Before this fix,
collect_walls() only matched category == "Walls" exactly, so every curtain
wall element in a model was silently excluded from conditioning — not
misclassified, just never even collected. These tests build a minimal fake
Speckle object graph (no live Speckle call) to prove all four categories are
now picked up, and that unrelated categories (e.g. Doors) are still excluded.
"""

from __future__ import annotations

from conditioning.walls import _is_target_category, collect_walls


class _FakeSpeckleObject:
    """Minimal stand-in for a Speckle DataObject.

    Supports the traversal pattern collect_walls() relies on: .category, .id,
    .properties, and .get_member_names() / .elements for recursion.
    """

    def __init__(
        self,
        id: str,
        category: str | None = None,
        elements=None,
        properties=None,
    ):
        self.id = id
        self.category = category
        self.properties = properties or {}
        self.elements = elements or []

    def get_member_names(self):
        names = ["properties"]
        if self.elements:
            names.append("elements")
        return names


class TestIsTargetCategory:
    """Test is target category."""
    def test_walls_is_a_target(self):
        """Walls is a target."""
        assert _is_target_category("Walls") is True

    def test_curtain_categories_are_targets(self):
        """Curtain categories are targets."""
        assert _is_target_category("Curtain Systems") is True
        assert _is_target_category("Curtain Panels") is True
        assert _is_target_category("Curtain Wall Mullions") is True

    def test_curtain_match_is_case_insensitive(self):
        """Curtain match is case insensitive."""
        assert _is_target_category("CURTAIN SYSTEMS") is True
        assert _is_target_category("curtain panels") is True

    def test_unrelated_categories_are_not_targets(self):
        """Unrelated categories are not targets."""
        assert _is_target_category("Doors") is False
        assert _is_target_category("Windows") is False
        assert _is_target_category(None) is False
        assert _is_target_category("") is False


class TestCollectWallsIncludesCurtainWallFamily:
    """Test collect walls includes curtain wall family."""
    def test_all_curtain_categories_and_walls_collected_doors_excluded(self):
        """All curtain categories and walls collected doors excluded."""
        wall          = _FakeSpeckleObject("wall-1", category="Walls")
        curtain_sys   = _FakeSpeckleObject("cs-1", category="Curtain Systems")
        curtain_panel = _FakeSpeckleObject("cp-1", category="Curtain Panels")
        mullion       = _FakeSpeckleObject("cm-1", category="Curtain Wall Mullions")
        door          = _FakeSpeckleObject("door-1", category="Doors")

        root = _FakeSpeckleObject(
            "root",
            elements=[wall, curtain_sys, curtain_panel, mullion, door],
        )

        walls = collect_walls(root)
        ids = {w.object_id for w in walls}

        assert ids == {"wall-1", "cs-1", "cp-1", "cm-1"}
        assert "door-1" not in ids

    def test_category_is_recorded_on_the_wall_record(self):
        """Category is recorded on the wall record."""
        curtain_panel = _FakeSpeckleObject("cp-1", category="Curtain Panels")
        root = _FakeSpeckleObject("root", elements=[curtain_panel])

        walls = collect_walls(root)
        assert len(walls) == 1
        assert walls[0].category == "Curtain Panels"
