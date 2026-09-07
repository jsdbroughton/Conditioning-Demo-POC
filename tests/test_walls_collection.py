"""Offline unit tests for collect_walls()'s category filter.

Revit models curtain walls as three categories distinct from "Walls": the
curtain wall host ("Curtain Systems"), the glazing/spandrel infill ("Curtain
Panels"), and the framing members ("Curtain Wall Mullions"). Before this fix,
collect_walls() only matched category == "Walls" exactly, so every curtain
wall element in a model was silently excluded from conditioning — not
misclassified, just never even collected. These tests build a minimal fake
bundle Model (no live Speckle call) to prove all four categories are still
picked up after the 2026-09-07 port to the 2026.9 bundle format, and that
unrelated categories (e.g. Doors) are still excluded.

2026-09-07: rewritten for collect_walls(model) — model.objects is now a
flat list (no `.elements` tree to recurse; see walls.py's module docstring),
so there's no more "root with nested elements" fixture shape to build.
"""

from __future__ import annotations

from conditioning.walls import _is_target_category, collect_walls
from tests.fakes import FakeModel, FakeModelObject


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


def _obj(application_id: str, category: str | None) -> FakeModelObject:
    return FakeModelObject(
        application_id=application_id,
        properties={"category": category} if category else {},
    )


class TestCollectWallsIncludesCurtainWallFamily:
    """Test collect walls includes curtain wall family."""
    def test_all_curtain_categories_and_walls_collected_doors_excluded(self):
        """All curtain categories and walls collected doors excluded."""
        wall          = _obj("wall-1", "Walls")
        curtain_sys   = _obj("cs-1", "Curtain Systems")
        curtain_panel = _obj("cp-1", "Curtain Panels")
        mullion       = _obj("cm-1", "Curtain Wall Mullions")
        door          = _obj("door-1", "Doors")

        model = FakeModel([wall, curtain_sys, curtain_panel, mullion, door])

        walls = collect_walls(model)
        ids = {w.object_id for w in walls}

        assert ids == {"wall-1", "cs-1", "cp-1", "cm-1"}
        assert "door-1" not in ids

    def test_category_is_recorded_on_the_wall_record(self):
        """Category is recorded on the wall record."""
        model = FakeModel([_obj("cp-1", "Curtain Panels")])

        walls = collect_walls(model)
        assert len(walls) == 1
        assert walls[0].category == "Curtain Panels"
