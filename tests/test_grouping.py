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
    type_mark: str = "",
    fire_rating: str = "",
    height_mm: float = 0.0,
) -> WallRecord:
    """Build a WallRecord with only the fields grouping reads."""
    return WallRecord(
        obj=object(),
        object_id=object_id,
        category="Walls",
        type_name=type_name,
        family=family,
        function=function,
        type_mark=type_mark,
        width_mm=200.0,
        level="LEVEL 01",
        assembly_code=assembly_code,
        fire_rating=fire_rating,
        height_mm=height_mm,
    )


def _grouped(walls):
    """Run the real prediction + grouping pipeline over `walls`.

    2026-09-07 (later still): assign_type_groups() returns
    (assignments, all_groups) now that grouping is a three-tier hierarchy
    (see grouping.py) — assignments (per-wall, always the `full` tier) is
    what every existing test here was already written against, so this
    helper keeps returning that and drops all_groups. Tests specifically
    exercising the tier hierarchy (coarse/fire_acoustic rows, parent_key)
    call assign_type_groups() directly instead — see
    TestGroupingHasThreeTiers below.
    """
    return assign_type_groups(walls, predict_codes(walls))[0]


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


class TestGroupDescriptionAndRollups:
    """Description/rollups report what a group's members share, never decide it.

    Added 2026-09-07, following a client ask to relate a group back to Type
    Mark. Checked against this module's own already-measured real output
    first: the largest real cluster on record spans six distinct Type
    Marks, so a group's rollup has to handle "several, not one" as the norm,
    not an edge case — see grouping.py's 2026-09-07 note.
    """

    def test_single_shared_wall_tag_is_reported_as_one_value(self):
        """Single shared wall tag is reported as one value."""
        walls = [
            _wall(
                "a",
                'Type H6 - Single Layer GWB - SMOKE - STC-35 - 6" Stud',
                type_mark="H6",
                fire_rating="SMOKE",
            ),
            _wall(
                "b",
                'Type H6 - Single Layer GWB - SMOKE - STC-35 - 6" Stud L2',
                type_mark="H6",
                fire_rating="SMOKE",
            ),
        ]
        group = _grouped(walls)["a"]
        assert group.wall_tags == frozenset({"H6"})
        assert group.fire_ratings == frozenset({"SMOKE"})
        assert group.stc_values == frozenset({"35"})
        assert group.stud_sizes == frozenset({"6"})
        assert "Type Mark H6" in group.description
        assert "Fire Rating SMOKE" in group.description

    def test_a_group_spanning_several_wall_tags_reports_all_of_them(self):
        """A group spanning several wall tags reports all of them.

        Mirrors the real Furring cluster (K1/K2/K3/L2/L3/L6, one Level 4
        code, one similarity group) — different Type Marks whose names are
        otherwise near-identical still cluster together, and the rollup must
        say so rather than silently picking one.
        """
        walls = [
            _wall(
                "a",
                'Type L3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud',
                type_mark="L3",
            ),
            _wall(
                "b",
                'Type L6 - Furring - Single Sided GWB - NFR - STC-NA - 6" Stud',
                type_mark="L6",
            ),
        ]
        group = _grouped(walls)["a"]
        assert group.wall_tags == frozenset({"L3", "L6"})
        assert "Type Mark varies (L3, L6)" in group.description

    def test_fire_rating_now_splits_the_group_even_when_the_name_is_near_identical(
        self,
    ):
        """Fire Rating is a hard split, not just a rollup (2026-09-07).

        This used to be the exact case grouping.py's "what this cannot do"
        note warned about — SMOKE vs NFR is a one-token difference a
        similarity cluster cannot reliably split on by name alone — and the
        rollup used to just report the resulting span. Per the Ken/Mike
        transcript the estimators price these two differently, so
        assign_type_groups() now partitions by (Fire Rating, Acoustic STC)
        BEFORE running name similarity: these two near-identical names must
        land in different groups, each internally consistent.
        """
        walls = [
            _wall(
                "a",
                'Type H6 - Single Layer GWB - NFR - STC-35 - 6" Stud',
                type_mark="H6",
                fire_rating="",  # blank parameter — falls back to name -> NFR
            ),
            _wall(
                "b",
                'Type H6 - Single Layer GWB - SMOKE - STC-35 - 6" Stud',
                type_mark="H6",
                fire_rating="SMOKE",
            ),
        ]
        groups = _grouped(walls)
        assert groups["a"].key != groups["b"].key
        assert groups["a"].fire_ratings == frozenset({"NFR"})
        assert groups["b"].fire_ratings == frozenset({"SMOKE"})

    def test_acoustic_stc_also_splits_the_group(self):
        """Acoustic STC is a hard split too, independently of Fire Rating."""
        walls = [
            _wall(
                "a",
                'Type H6 - Single Layer GWB - NFR - STC-35 - 6" Stud',
                type_mark="H6",
            ),
            _wall(
                "b",
                'Type H6 - Single Layer GWB - NFR - STC-45 - 6" Stud',
                type_mark="H6",
            ),
        ]
        groups = _grouped(walls)
        assert groups["a"].key != groups["b"].key
        assert groups["a"].stc_values == frozenset({"35"})
        assert groups["b"].stc_values == frozenset({"45"})

    def test_group_with_nothing_recognised_says_so_plainly(self):
        """Group with nothing recognised says so plainly."""
        walls = [
            _wall("a", "CW_Unitized_IGU-8", function="Curtain"),
            _wall("b", "CW_Unitized_IGU-2", function="Curtain"),
        ]
        group = _grouped(walls)["a"]
        assert group.wall_tags == frozenset()
        assert group.fire_ratings == frozenset()
        assert (
            "no Type Mark, Fire Rating, STC, Stud Size or Height Band recognised"
            in group.description
        )

    def test_description_leads_with_the_element_count(self):
        """Description leads with the element count."""
        walls = [_wall(f"w{i}", "Type H6 - Single Layer GWB - SMOKE") for i in range(3)]
        assert _grouped(walls)["w0"].description.startswith("3 elements")

    def test_singular_element_count_uses_singular_noun(self):
        """Singular element count uses singular noun."""
        wall = _wall("a", "CW_Unitized_Spandrel", function="Curtain")
        assert _grouped([wall])["a"].description.startswith("1 element —")

    def test_wall_tag_rollup_does_not_affect_which_group_a_wall_joins(self):
        """Type Mark stays a reported rollup, not a split key (2026-09-07).

        Unlike Fire Rating/Acoustic STC (see TestGroupDescriptionAndRollups'
        fire-rating/STC split tests above), Type Mark is just an identifier
        — the transcript's cost-differentiation ask names fire rating and
        acoustics specifically, not tag. Two differently-tagged walls that
        agree on fire rating/STC and are otherwise near-identical still
        land in one group (the real Furring K1-L6 cluster this mirrors —
        see test_a_group_spanning_several_wall_tags_reports_all_of_them).
        """
        walls = [
            _wall(
                "a",
                'Type L3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud',
                type_mark="L3",
            ),
            _wall(
                "b",
                'Type L6 - Furring - Single Sided GWB - NFR - STC-NA - 6" Stud',
                type_mark="L6",
            ),
        ]
        groups = _grouped(walls)
        assert groups["a"].key == groups["b"].key
        assert groups["a"].wall_tags == frozenset({"L3", "L6"})

    def test_similarity_scoring_itself_stays_type_name_token_only(self):
        """_group_similarity never sees a wall_tag/fire_rating argument.

        The (Fire Rating, Acoustic STC) split happens as a separate
        partition BEFORE similarity clustering runs (see
        assign_type_groups) — not by teaching the scorer itself about
        attributes, which would make it a different, harder-to-reason-about
        function. This pins that boundary.
        """
        import inspect

        from conditioning.grouping import _group_similarity

        params = list(inspect.signature(_group_similarity).parameters)
        assert params == ["a", "b"], (
            "similarity scoring must stay type-name-token-only — the Fire "
            "Rating/Acoustic STC split belongs in assign_type_groups' "
            "pre-partitioning step, not folded into the scorer itself"
        )


class TestGroupingHasThreeTiers:
    """assign_type_groups() returns a coarse/fire_acoustic/full hierarchy.

    2026-09-07 (later still): a flat (fire_rating, stc) hard split forced
    every consumer onto one granularity. This asks the direct question —
    "the inferred groups can be more or less coarse" — by exposing all
    three tiers rather than picking one. See grouping.py's module docstring
    and TypeGroup's own docstring for the shape.
    """

    def test_uniform_coarse_cluster_produces_no_finer_rows(self):
        """A coarse cluster already uniform on fire/stc/height gains no sub-rows.

        Same two walls as test_wall_tag_rollup_does_not_affect_which_group_a
        _wall_joins above (agree on Fire Rating and STC, no height
        recorded) — nothing here should manufacture a fire_acoustic or full
        row that just duplicates the coarse one.
        """
        walls = [
            _wall(
                "a",
                'Type L3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud',
                type_mark="L3",
            ),
            _wall(
                "b",
                'Type L6 - Furring - Single Sided GWB - NFR - STC-NA - 6" Stud',
                type_mark="L6",
            ),
        ]
        assignments, all_groups = assign_type_groups(walls, predict_codes(walls))
        tiers = {g.tier for g in all_groups}
        assert tiers == {"coarse"}
        coarse = next(g for g in all_groups if g.tier == "coarse")
        # The per-wall assignment is still nominally "full" tier, but its
        # key is identical to the coarse row's — no split happened, so
        # there's nothing distinct to point to.
        assert assignments["a"].key == coarse.key == assignments["b"].key
        assert assignments["a"].coarse_key == coarse.key
        assert assignments["a"].fire_acoustic_key == coarse.key

    def test_fire_acoustic_split_produces_a_fire_acoustic_row_and_a_coarse_parent(self):
        """A coarse cluster spanning two fire ratings gains fire_acoustic rows.

        Mirrors test_fire_rating_now_splits_the_group_even_when_the_name_is
        _near_identical above, but checks the tier structure rather than
        just the per-wall key.
        """
        walls = [
            _wall(
                "a",
                'Type H6 - Single Layer GWB - NFR - STC-35 - 6" Stud',
                type_mark="H6",
                fire_rating="",
            ),
            _wall(
                "b",
                'Type H6 - Single Layer GWB - SMOKE - STC-35 - 6" Stud',
                type_mark="H6",
                fire_rating="SMOKE",
            ),
        ]
        assignments, all_groups = assign_type_groups(walls, predict_codes(walls))
        coarse = [g for g in all_groups if g.tier == "coarse"]
        fire_acoustic = [g for g in all_groups if g.tier == "fire_acoustic"]
        assert len(coarse) == 1
        assert len(fire_acoustic) == 2
        assert {g.parent_key for g in fire_acoustic} == {coarse[0].key}
        # No height was recorded on either wall, so the full tier adds
        # nothing beyond the fire_acoustic split — no `full`-tier row.
        assert not [g for g in all_groups if g.tier == "full"]
        assert assignments["a"].key == assignments["a"].fire_acoustic_key
        assert assignments["a"].coarse_key == coarse[0].key

    def test_height_band_splits_further_within_a_fire_acoustic_slice(self):
        """Walls sharing fire/stc but at very different heights split at full tier."""
        walls = [
            _wall(
                "a",
                'Type H6 - Single Layer GWB - NFR - STC-35 - 6" Stud',
                type_mark="H6",
                height_mm=1000.0,  # well under the 4' short-band threshold
            ),
            _wall(
                "b",
                'Type H6 - Single Layer GWB - NFR - STC-35 - 6" Stud',
                type_mark="H6",
                height_mm=7000.0,  # over the 6m tall-band threshold
            ),
        ]
        assignments, all_groups = assign_type_groups(walls, predict_codes(walls))
        assert assignments["a"].key != assignments["b"].key
        assert assignments["a"].height_bands == frozenset({"short (<4')"})
        assert assignments["b"].height_bands == frozenset({"tall (>6m)"})
        full_rows = [g for g in all_groups if g.tier == "full"]
        assert len(full_rows) == 2
        # No fire/acoustic split happened (both NFR/STC-35), so the full
        # rows' parent is the coarse cluster directly, not a fire_acoustic
        # row that was never created.
        coarse_key = next(g.key for g in all_groups if g.tier == "coarse")
        assert {g.parent_key for g in full_rows} == {coarse_key}
        assert not [g for g in all_groups if g.tier == "fire_acoustic"]

    def test_standard_height_band_does_not_split_ordinary_floor_to_floor_walls(self):
        """Two walls at ordinary, different-but-both-'standard' heights stay one group.

        The bands are coarse on purpose — the point is to catch a real
        assembly-cost threshold (short kneewalls, tall double-height
        walls), not to fragment every few inches of floor-to-floor
        variation the way raw height would (see attributes.py).
        """
        walls = [
            _wall(
                "a",
                'Type H6 - Single Layer GWB - NFR - STC-35 - 6" Stud',
                type_mark="H6",
                height_mm=3000.0,
            ),
            _wall(
                "b",
                'Type H6 - Single Layer GWB - NFR - STC-35 - 6" Stud',
                type_mark="H6",
                height_mm=4200.0,
            ),
        ]
        assignments, all_groups = assign_type_groups(walls, predict_codes(walls))
        assert assignments["a"].key == assignments["b"].key
        assert assignments["a"].height_bands == frozenset({"standard"})
        assert not [g for g in all_groups if g.tier in ("fire_acoustic", "full")]
