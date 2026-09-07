"""Offline unit tests for type-name / wall-parameter attribute extraction.

These cover the estimator's ask from the 2026-08-14 call — fire rating,
acoustic rating and stud size — which similarity clustering provably cannot
deliver (see attributes.py and grouping.py). Because this is the one place
the codebase assumes a naming convention, the tests that matter most are the
ones asserting it stays silent when the convention doesn't hold.

Extended 2026-09-07 for the follow-up call's ask (wall tag, fire rating from
the real parameter, height) — see attributes.py's module docstring for what
was verified against live models before any of this was written.
"""

from __future__ import annotations

from conditioning.attributes import (
    TypeAttributes,
    attributes_by_type,
    bucket_height_ft,
    extract_attributes,
)
from conditioning.walls import WallRecord


def _wall(type_name: str, fire_rating: str = "", type_mark: str = "") -> WallRecord:
    """Build a bare WallRecord — only the fields attributes_by_type reads."""
    return WallRecord(
        obj=object(),
        object_id=type_name,
        category="Walls",
        type_name=type_name,
        family="Basic Wall",
        function="Interior",
        type_mark=type_mark,
        width_mm=200.0,
        level="LEVEL 01",
        assembly_code=None,
        fire_rating=fire_rating,
    )


class TestStructuredNames:
    """Names following the convention give up all three attributes."""

    def test_smoke_partition(self):
        """Smoke partition."""
        a = extract_attributes('Type H6 - Single Layer GWB - SMOKE - STC-35 - 6" Stud')
        assert (a.fire_rating, a.stc, a.stud) == ("SMOKE", "35", "6")
        assert a.summary == 'SMOKE · STC-35 · 6" Stud'

    def test_non_fire_rated_with_fractional_stud(self):
        """Non fire rated with fractional stud."""
        a = extract_attributes(
            'Type L3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud'
        )
        assert (a.fire_rating, a.stc, a.stud) == ("NFR", "NA", "3-5/8")

    def test_spaced_fractional_stud(self):
        """Spaced fractional stud."""
        a = extract_attributes('Type 02 -  NO GWB - NFR - STC-NA - 2 1/2" Stud')
        assert a.stud == "2 1/2"

    def test_hour_rating(self):
        """Hour rating."""
        assert extract_attributes(
            'Type A6 - Single Layer GWB - 1HR - STC-35 - 6" Stud'
        ).fire_rating == "1HR"

    def test_combined_hour_and_smoke_is_not_truncated(self):
        """Combined hour and smoke is not truncated.

        A 1-hour smoke partition is its own thing to an estimator, not a
        1-hour wall with a note, so the combined form must survive intact.
        """
        assert extract_attributes(
            'Type S6 - Single Layer GWB - 1HR SMOKE - STC-45 - 6" Stud'
        ).fire_rating == "1HR SMOKE"

    def test_stc_na_is_a_value_not_a_blank(self):
        """STC-NA is a value, not a blank.

        "No acoustic rating applies" is an assertion; absent means the name
        never said. They must not collapse into each other.
        """
        assert extract_attributes('Type L2 - NFR - STC-NA - 4" Stud').stc == "NA"


class TestUnstructuredNamesYieldNothing:
    """The convention doesn't hold everywhere, and silence is the correct output."""

    def test_curtain_wall_names_yield_nothing(self):
        """Curtain wall names yield nothing."""
        for name in ("CW_Unitized_Spandrel", "CW1D", "20d panel", "Empty"):
            attrs = extract_attributes(name)
            assert not attrs
            assert attrs.summary is None

    def test_descriptive_name_without_the_convention_yields_nothing(self):
        """Descriptive name without the convention yields nothing.

        Shaped like a real exterior type name — a project prefix, an
        abbreviation, a material and a location note — but carrying none of
        the rating/STC/stud vocabulary.
        """
        assert (
            not extract_attributes("_XYZ - BMV - Brick Masonry Veneer. 2nd fl channel")
        )

    def test_empty_name_is_safe(self):
        """Empty name is safe."""
        assert extract_attributes("") == TypeAttributes()

    def test_a_bare_dimension_is_not_mistaken_for_a_stud_size(self):
        """A bare dimension is not mistaken for a stud size.

        'Sill Cap Extrusion - 8"D' carries a dimension but says nothing about
        studs; reading 8" as a stud size would be an invention.
        """
        assert extract_attributes('Interior - Sill Cap Extrusion - 8"D').stud is None


class TestPartialExtraction:
    """A name that yields some attributes still narrows the field usefully."""

    def test_rating_only_still_summarises(self):
        """Rating only still summarises."""
        a = extract_attributes("Shaft Wall - 2HR")
        assert a.fire_rating == "2HR"
        assert a.stc is None and a.stud is None
        assert a.summary == "2HR"

    def test_truthiness_tracks_whether_anything_was_found(self):
        """Truthiness tracks whether anything was found."""
        assert extract_attributes("Shaft Wall - 2HR")
        assert not extract_attributes("Shaft Wall")


class TestFireRatingParameterIsPreferredOverName:
    """The real Fire Rating parameter, where present, beats the name-regex.

    Verified against the live UKHC models before this was written — see the
    module docstring's 2026-09-07 note.
    """

    def test_parameter_wins_when_both_are_present(self):
        """Parameter wins when both are present."""
        a = extract_attributes(
            'Type H6 - Single Layer GWB - NFR - STC-35 - 6" Stud',
            fire_rating_param="SMOKE",
        )
        # The name says NFR, the parameter says SMOKE — parameter wins, and
        # says so, because it's the more authoritative of the two sources.
        assert a.fire_rating == "SMOKE"
        assert a.fire_rating_source == "parameter"

    def test_slash_smoke_notation_is_normalised_to_the_name_convention(self):
        """Slash smoke notation is normalised to the name convention.

        The parameter renders a combined rating as "1HR/S"; the name
        convention (and the regex) renders "1HR SMOKE". Both must produce
        the same value so the two sources never disagree in the summary.
        """
        a = extract_attributes("Type A6 - Something", fire_rating_param="1HR/S")
        assert a.fire_rating == "1HR SMOKE"
        assert a.fire_rating_source == "parameter"

    def test_bare_smoke_parameter_passes_through(self):
        """Bare smoke parameter passes through."""
        a = extract_attributes("Type H6 - Something", fire_rating_param="SMOKE")
        assert a.fire_rating == "SMOKE"

    def test_dash_parameter_falls_back_to_name(self):
        """Dash parameter falls back to name.

        A bare "-" in the Fire Rating parameter means "nothing to report",
        seen on the live Podium model — not a literal rating of "-". Falls
        through to whatever the name itself says.
        """
        a = extract_attributes(
            'Type A6 - Single Layer GWB - 1HR - STC-35 - 6" Stud',
            fire_rating_param="-",
        )
        assert a.fire_rating == "1HR"
        assert a.fire_rating_source == "name"

    def test_blank_parameter_falls_back_to_name(self):
        """Blank parameter falls back to name."""
        a = extract_attributes(
            'Type L3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud',
            fire_rating_param="",
        )
        assert a.fire_rating == "NFR"
        assert a.fire_rating_source == "name"

    def test_neither_source_yields_a_rating(self):
        """Neither source yields a rating."""
        a = extract_attributes("CW_Unitized_Spandrel", fire_rating_param="")
        assert a.fire_rating is None
        assert a.fire_rating_source is None


class TestWallTag:
    """Wall tag is Type Mark, passed straight through — no parsing involved."""

    def test_wall_tag_is_recorded(self):
        """Wall tag is recorded."""
        a = extract_attributes("Type H6 - Something", wall_tag="H6")
        assert a.wall_tag == "H6"

    def test_wall_tag_leads_the_summary(self):
        """Wall tag leads the summary."""
        a = extract_attributes(
            'Type H6 - Single Layer GWB - SMOKE - STC-35 - 6" Stud',
            wall_tag="H6",
        )
        assert a.summary == 'H6 · SMOKE · STC-35 · 6" Stud'

    def test_blank_wall_tag_is_none_not_empty_string(self):
        """Blank wall tag is none not empty string."""
        assert extract_attributes("Type H6", wall_tag="").wall_tag is None
        assert extract_attributes("Type H6", wall_tag="   ").wall_tag is None

    def test_wall_tag_alone_makes_attributes_truthy(self):
        """Wall tag alone makes attributes truthy.

        A wall can have a real Type Mark with a type name that yields
        nothing else at all (no rating/STC/stud vocabulary) — the tag is
        still worth surfacing on its own.
        """
        assert extract_attributes("CW_Unitized_Spandrel", wall_tag="CW1")


class TestAttributesByTypeCachesPerTypeName:
    """attributes_by_type extracts once per distinct type name, from WallRecords."""

    def test_fire_rating_and_wall_tag_carried_through_from_the_wall(self):
        """Fire rating and wall tag carried through from the wall."""
        walls = [_wall("Type H6 - Something", fire_rating="SMOKE", type_mark="H6")]
        result = attributes_by_type(walls)
        assert result["Type H6 - Something"].fire_rating == "SMOKE"
        assert result["Type H6 - Something"].wall_tag == "H6"

    def test_one_entry_per_distinct_type_name_not_per_element(self):
        """One entry per distinct type name, not per element."""
        walls = [
            _wall("Type H6 - Something", fire_rating="SMOKE", type_mark="H6"),
            _wall("Type H6 - Something", fire_rating="SMOKE", type_mark="H6"),
            _wall("Type A6 - Other", fire_rating="1HR", type_mark="A6"),
        ]
        result = attributes_by_type(walls)
        assert set(result) == {"Type H6 - Something", "Type A6 - Other"}


class TestBucketHeightFt:
    """Height bucketing — separate from TypeAttributes because it's per-instance.

    See attributes.py's module docstring for why this is never folded into
    the cached, per-type-name TypeAttributes/attributes_by_type path.
    """

    def test_rounds_to_the_nearest_foot_by_default(self):
        """Rounds to the nearest foot by default."""
        # 14.62 ft, a real value measured on the Podium model.
        assert bucket_height_ft(14.62 * 304.8) == "15'"
        assert bucket_height_ft(14.4 * 304.8) == "14'"

    def test_whole_foot_value_renders_without_a_decimal(self):
        """Whole foot value renders without a decimal."""
        assert bucket_height_ft(10 * 304.8) == "10'"

    def test_zero_or_missing_height_is_none(self):
        """Zero or missing height is none."""
        assert bucket_height_ft(0.0) is None
        assert bucket_height_ft(0) is None

    def test_negative_height_is_none(self):
        """Negative height is none.

        Never expected from real Revit data, but a guard against a garbled
        upstream value silently producing a nonsense negative bucket label.
        """
        assert bucket_height_ft(-100.0) is None

    def test_a_custom_bucket_width_is_honoured(self):
        """A custom bucket width is honoured."""
        # Half-foot buckets: 14.62 ft rounds to 14.5'.
        assert bucket_height_ft(14.62 * 304.8, bucket_ft=0.5) == "14.5'"
