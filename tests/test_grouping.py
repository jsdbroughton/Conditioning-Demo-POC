"""Offline unit tests for wall-type sub-grouping.

Grouping exists because a Level 4 code is correct and immediately not
enough — every interior partition lands on C1010.10, and the next question
is which kind. See src/conditioning/grouping.py for why this is done by
similarity rather than by parsing type names, and why it is not a finer
Uniformat code.
"""

from __future__ import annotations

from conditioning.grouping import assign_type_groups
from conditioning.predict import predict_codes
from conditioning.walls import WallRecord


def _wall(
    object_id: str,
    type_name: str,
    function: str = "Interior",
    family: str = "Basic Wall",
    assembly_code: str | None = None,
) -> WallRecord:
    """Build a WallRecord with only the fields grouping reads."""
    return WallRecord(
        obj=object(),
        object_id=object_id,
        category="Walls",
        type_name=type_name,
        family=family,
        function=function,
        type_mark="",
        width_mm=200.0,
        level="LEVEL 01",
        assembly_code=assembly_code,
    )


def _grouped(walls):
    """Run the real prediction + grouping pipeline over `walls`."""
    return assign_type_groups(walls, predict_codes(walls))


class TestGroupsFormByResemblance:
    """Similar type names cluster; dissimilar ones don't."""

    def test_variants_of_one_type_share_a_group(self):
        """Variants of one type share a group."""
        walls = [
            _wall("a", 'Type H6 - Single Layer GWB - SMOKE - STC-35 - 6" Stud'),
            _wall("b", 'Type H6 - Single Layer GWB - SMOKE - STC-35 - 6" Stud L2'),
            _wall("c", 'Type H3 - Single Layer GWB - SMOKE - STC-35 - 3-5/8" Stud'),
        ]
        groups = _grouped(walls)
        assert len({groups[w.object_id].key for w in walls} ) == 1

    def test_unrelated_names_do_not_share_a_group(self):
        """Unrelated names do not share a group."""
        walls = [
            _wall("a", 'Type H6 - Single Layer GWB - SMOKE - STC-35 - 6" Stud'),
            _wall("b", "BRAKE METAL SLIDER ENCLOSURE WALL"),
        ]
        groups = _grouped(walls)
        assert groups["a"].key != groups["b"].key

    def test_unstructured_names_still_group(self):
        """Unstructured names still group.

        The case a type-name parser cannot serve at all: no fire rating, no
        STC, no stud size, nothing to extract — but plainly one family.
        """
        walls = [
            _wall("a", "CW_Unitized_IGU-8", function="Curtain"),
            _wall("b", "CW_Unitized_IGU-2", function="Curtain"),
            _wall("c", "CW_Unitized_IGU-4 L12", function="Curtain"),
        ]
        groups = _grouped(walls)
        assert len({groups[w.object_id].key for w in walls}) == 1
        assert "IGU" in groups["a"].label


class TestGroupsAreScopedToTheirCode:
    """A group never spans two Level 4 codes."""

    def test_same_name_under_different_codes_gets_different_groups(self):
        """Same name under different codes gets different groups."""
        interior = _wall("i", "Type A - Partition", function="Interior")
        exterior = _wall("e", "Type A - Partition", function="Exterior")
        groups = _grouped([interior, exterior])

        assert groups["i"].key.startswith("C1010.10 · inferred group ")
        assert groups["e"].key.startswith("B2010.10 · inferred group ")
        assert groups["i"].key != groups["e"].key


class TestKeysAndLabels:
    """Keys are stable and ordered; labels describe what members share."""

    def test_largest_group_under_a_code_is_lettered_a(self):
        """Largest group under a code is lettered A."""
        walls = (
            [_wall(f"big{i}", "Type H6 - Single Layer GWB - SMOKE") for i in range(5)]
            + [_wall("small", "BRAKE METAL SLIDER ENCLOSURE WALL")]
        )
        groups = _grouped(walls)
        assert groups["big0"].key.endswith("inferred group A")
        assert groups["big0"].size == 5
        assert groups["small"].size == 1

    def test_label_preserves_the_source_casing_and_order(self):
        """Label preserves the source casing and order."""
        walls = [
            _wall("a", "CW_Unitized_Spandrel", function="Curtain"),
            _wall("b", "CW_Unitized_Spandrel L5", function="Curtain"),
        ]
        label = _grouped(walls)["a"].label
        assert label == "CW Unitized Spandrel"

    def test_size_counts_elements_not_type_names(self):
        """Size counts elements, not type names."""
        walls = [_wall(f"w{i}", "Type H6 - Single Layer GWB - SMOKE") for i in range(7)]
        assert _grouped(walls)["w0"].size == 7

    def test_grouping_is_deterministic(self):
        """Grouping is deterministic across runs over the same input."""
        walls = [
            _wall("a", 'Type H6 - Single Layer GWB - SMOKE - STC-35 - 6" Stud'),
            _wall("b", "CW_Unitized_Spandrel", function="Curtain"),
            _wall("c", 'Type H3 - Single Layer GWB - NFR - STC-35 - 3-5/8" Stud'),
        ]
        first = {k: v.key for k, v in _grouped(walls).items()}
        second = {k: v.key for k, v in _grouped(walls).items()}
        assert first == second


class TestGroupingDoesNotDisturbClassification:
    """Grouping is a second axis, not a revision of the first."""

    def test_every_coded_wall_receives_a_group(self):
        """Every coded wall receives a group."""
        walls = [
            _wall("a", "Type H6 - GWB"),
            _wall("b", "CW_Unitized", function="Curtain"),
            _wall("c", "Brick Masonry Veneer", function="Exterior"),
            _wall("d", "Already Correct", assembly_code="B2010.40"),
        ]
        groups = _grouped(walls)
        assert set(groups) == {"a", "b", "c", "d"}

    def test_already_level4_walls_are_grouped_under_their_existing_code(self):
        """Already-Level4 walls are grouped under their existing code."""
        wall = _wall("a", "Curtain Panel Type 1", assembly_code="B2010.40")
        assert _grouped([wall])["a"].key.startswith("B2010.40 · inferred group ")
