"""Offline unit tests for type-name attribute extraction.

These cover the estimator's ask from the 2026-08-14 call — fire rating,
acoustic rating and stud size — which similarity clustering provably cannot
deliver (see attributes.py and grouping.py). Because this is the one place
the codebase assumes a naming convention, the tests that matter most are the
ones asserting it stays silent when the convention doesn't hold.
"""

from __future__ import annotations

from conditioning.attributes import TypeAttributes, extract_attributes


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
