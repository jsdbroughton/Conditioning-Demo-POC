"""Offline unit tests for get_assembly_code()'s case normalisation.

Prompted by a false alarm worth guarding against for real: a report showing
"0 already ACME Level 4" for the target SHELL model turned out to be
correct (verified directly against the raw Assembly Code values in Speckle —
see docs/NOTES.md) — but while checking it, found that LEVEL4_PATTERN and
ASTM_CODE_PATTERN only match an uppercase leading letter. A code authored
lowercase (a plausible Revit data-entry slip, e.g. 'b2010.10') would
previously fail is_level4_coded and get treated as an unrecognised legacy
code needing re-prediction, even though it's already correct. get_assembly_code()
now uppercases on the way in — ACME/ASTM Uniformat codes have no
legitimate lowercase form, so this is safe and unconditional, not a guess.
"""

from __future__ import annotations

from conditioning.walls import get_assembly_code


class _FakeWallObj:
    """Minimal stand-in matching the properties.Parameters.Type Parameters.
    Identity Data.Assembly Code.value path get_assembly_code() reads."""

    def __init__(self, assembly_code_value):
        self.properties = {
            "Parameters": {
                "Type Parameters": {
                    "Identity Data": {
                        "Assembly Code": {"value": assembly_code_value},
                    }
                }
            }
        }


class TestGetAssemblyCodeUppercasesOnIngestion:
    def test_lowercase_level4_code_is_uppercased(self):
        assert get_assembly_code(_FakeWallObj("b2010.10")) == "B2010.10"

    def test_mixed_case_astm_code_is_uppercased(self):
        assert get_assembly_code(_FakeWallObj("b2010160")) == "B2010160"

    def test_lowercase_collapsed_code_still_normalises_to_level4(self):
        # 'b201010' -> uppercased to 'B201010' -> recognised as a Level 4
        # code with the period stripped -> normalised to 'B2010.10'.
        assert get_assembly_code(_FakeWallObj("b201010")) == "B2010.10"

    def test_whitespace_still_stripped(self):
        assert get_assembly_code(_FakeWallObj("  B2010.10  ")) == "B2010.10"

    def test_blank_value_returns_none(self):
        assert get_assembly_code(_FakeWallObj("")) is None
        assert get_assembly_code(_FakeWallObj(None)) is None
