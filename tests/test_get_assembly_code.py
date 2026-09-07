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

2026-09-07: rewritten for the port to specklepy 2026.9's bundle format —
get_assembly_code() reads via conditioning.walls._param(), which tries
"Parameters.Instance Parameters.Identity Data.Assembly Code" then
"Parameters.Type Parameters.Identity Data.Assembly Code" (this connector
stores Assembly Code at type scope — confirmed live against a real wall, see
conditioning/walls.py's module docstring's 2026-09-07 correction). Not a
nested properties.Parameters["Type Parameters"] dict walk, and not the bare
"Identity Data.Assembly Code" path this test originally used before that
correction — a bare path silently misses on both scopes and get_assembly_code
would wrongly return None for every wall.
"""

from __future__ import annotations

from conditioning.walls import get_assembly_code
from tests.fakes import FakeModelObject

_ASSEMBLY_CODE_PATH = "Parameters.Type Parameters.Identity Data.Assembly Code"


def _wall_obj(assembly_code_value) -> FakeModelObject:
    properties = {}
    if assembly_code_value is not None:
        properties[_ASSEMBLY_CODE_PATH] = assembly_code_value
    return FakeModelObject(properties=properties)


class TestGetAssemblyCodeUppercasesOnIngestion:
    """Test get assembly code uppercases on ingestion."""
    def test_lowercase_level4_code_is_uppercased(self):
        """Lowercase level4 code is uppercased."""
        assert get_assembly_code(_wall_obj("b2010.10")) == "B2010.10"

    def test_mixed_case_astm_code_is_uppercased(self):
        """Mixed case ASTM code is uppercased."""
        assert get_assembly_code(_wall_obj("b2010160")) == "B2010160"

    def test_lowercase_collapsed_code_still_normalises_to_level4(self):
        """Lowercase collapsed code still normalises to level4."""
        # 'b201010' -> uppercased to 'B201010' -> recognised as a Level 4
        # code with the period stripped -> normalised to 'B2010.10'.
        assert get_assembly_code(_wall_obj("b201010")) == "B2010.10"

    def test_whitespace_still_stripped(self):
        """Whitespace still stripped."""
        assert get_assembly_code(_wall_obj("  B2010.10  ")) == "B2010.10"

    def test_blank_value_returns_none(self):
        """Blank value returns none."""
        assert get_assembly_code(_wall_obj("")) is None
        assert get_assembly_code(_wall_obj(None)) is None
