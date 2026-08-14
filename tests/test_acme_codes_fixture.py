"""Fixture-driven guardrail: the hardcoded ACME_CODES dict in codes.py must
match the client's own source spreadsheet exactly.

This is deliberately NOT a switch to loading codes dynamically from the
spreadsheet at runtime — direction as of 2026-08-12 is to keep the hardcoded
solution for now. This test exists so that dict can't silently drift from the
source of truth (typo'd code, wrong description, missing section) without a
test failure calling it out.

Requires the `openpyxl` dev dependency (see pyproject.toml) and the fixture
file at fixtures/ACME Studios - Uniformat Estimate Detail Structure.xlsx.

Renamed 2026-08-14 from its previous client-named filename as part of the
anonymization pass — see docs/NOTES.md.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from conditioning.codes import ACME_CODES

openpyxl = pytest.importorskip("openpyxl")

FIXTURE_PATH = (
    Path(__file__).resolve().parent.parent
    / "fixtures"
    / "ACME Studios - Uniformat Estimate Detail Structure.xlsx"
)

# ACME_CODES only hardcodes level 3 (e.g. B2010) and level 4 (e.g. B2010.10)
# codes — the spreadsheet goes deeper (level 5, e.g. B2010.10.0100) but those
# quantity line items aren't Revit Assembly Code targets.
_LEVEL34_PATTERN = re.compile(r"^[A-Z]\d{4}(\.\d{1,2})?$")


def _load_fixture_codes() -> dict[str, str]:
    """Return {code: description} for every level 3/4 UF code in the fixture."""
    if not FIXTURE_PATH.exists():
        pytest.skip(f"fixture not found at {FIXTURE_PATH}")

    wb = openpyxl.load_workbook(FIXTURE_PATH, data_only=True)
    ws = wb["Sheet1"]
    codes: dict[str, str] = {}
    for row in ws.iter_rows(min_row=1, max_row=ws.max_row, values_only=True):
        if len(row) < 4:
            continue
        code, description = row[2], row[3]
        if isinstance(code, str) and _LEVEL34_PATTERN.match(code.strip()):
            codes[code.strip()] = str(description or "").strip()
    return codes


class TestHardcodedAcmeCodesMatchFixture:
    def test_every_hardcoded_code_exists_in_source_spreadsheet(self):
        fixture_codes = _load_fixture_codes()
        missing = [code for code in ACME_CODES if code not in fixture_codes]
        assert not missing, (
            f"ACME_CODES has codes not found in the source spreadsheet: {missing}"
        )

    def test_every_hardcoded_description_matches_source_spreadsheet(self):
        fixture_codes = _load_fixture_codes()
        mismatches = {
            code: {"hardcoded": desc, "source": fixture_codes[code]}
            for code, desc in ACME_CODES.items()
            if code in fixture_codes and desc.strip() != fixture_codes[code]
        }
        assert not mismatches, f"Description drift from source spreadsheet: {mismatches}"

    def test_curtain_walls_confirmed_as_b2010_40_not_b2050(self):
        """Regression guard for the specific gotcha flagged in docs/NOTES.md —
        curtain walls are B2010.40 in this system, not B2050. The line
        item itself ("Curtain wall assemblies") lives one level deeper than
        ACME_CODES tracks, so confirm B2010.40 is the section it sits under."""
        fixture_codes = _load_fixture_codes()
        assert fixture_codes["B2010.40"] == "Fabricated Exterior Wall Assemblies"
        assert "B2050" not in ACME_CODES
