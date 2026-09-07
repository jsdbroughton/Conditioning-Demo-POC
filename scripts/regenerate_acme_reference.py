"""Regenerate src/conditioning/acme_reference.py from the fixture spreadsheet.

Run from the repo root: PYTHONPATH=src:. python3 scripts/regenerate_acme_reference.py
The header text lives in the existing module and is preserved verbatim.
"""

from __future__ import annotations

from pathlib import Path

from tests.test_acme_codes_fixture import _load_fixture_codes

TARGET = Path(__file__).resolve().parent.parent / "src/conditioning/acme_reference.py"


def main() -> None:
    """Rewrite the ACME_CODES dict body, keeping everything above it."""
    text = TARGET.read_text()
    head = text[: text.index("ACME_CODES: dict[str, str] = {")]
    body = ["ACME_CODES: dict[str, str] = {"]
    for code, description in sorted(_load_fixture_codes().items()):
        body.append(f"    {code!r}: {description!r},")
    body.append("}\n")
    TARGET.write_text(head + "\n".join(body))
    print(f"wrote {len(body) - 2} codes to {TARGET}")


if __name__ == "__main__":
    main()
