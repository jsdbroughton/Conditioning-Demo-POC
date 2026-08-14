"""Shared pytest configuration.

Currently just the one knob: letting the live integration run override the
conditioned-code property name without editing test_function.py.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from dotenv import dotenv_values

from conditioning.codes import DEFAULT_CONDITIONING_KEY

_ENV_VAR = "CONDITIONING_CODE_PROPERTY_NAME"

# .env sits next to pyproject.toml, one level up from tests/.
_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


def _from_env_file() -> str | None:
    """Read the override out of .env.

    Necessary rather than incidental: the SDK fixtures already read .env for
    credentials, but they do it through pydantic-settings, which loads the
    file into its own settings model and does NOT export anything to
    os.environ. So a value sitting in .env is invisible to os.environ.get()
    — verified, not assumed. Reading the file directly is what makes .env
    work here regardless of how the suite was launched (bare pytest, uv,
    mise, CI), which matters because `mise run` will not forward a
    `--code-property-name` flag without an explicit `--` separator.

    dotenv_values() rather than load_dotenv() so this never mutates the
    process environment out from under the SDK.
    """
    if not _ENV_FILE.is_file():
        return None
    return dotenv_values(_ENV_FILE).get(_ENV_VAR) or None


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register --code-property-name for the live integration run."""
    parser.addoption(
        "--code-property-name",
        action="store",
        default=None,
        metavar="NAME",
        help=(
            "Property key the integration run writes conditioning output "
            "under, overriding FunctionInputs.code_property_name's default "
            f"({DEFAULT_CONDITIONING_KEY!r}). Also settable as {_ENV_VAR} "
            "in the environment or in .env."
        ),
    )


@pytest.fixture
def code_property_name(request: pytest.FixtureRequest) -> str:
    """The property key the live run should write under.

    Resolution order, most specific first:

    1. ``--code-property-name`` — an explicit choice for this one invocation.
    2. ``$CONDITIONING_CODE_PROPERTY_NAME`` in the real environment — how CI
       sets it without threading a pytest flag through a task runner.
    3. ``CONDITIONING_CODE_PROPERTY_NAME`` in ``.env`` — the per-developer
       default, alongside the project/automation IDs that already live
       there and get swapped between runs.
    4. ``codes.DEFAULT_CONDITIONING_KEY`` — exactly what the deployed
       function writes, so an un-configured run behaves like production.

    Worth having because this is the one input that changes something on
    every wall object of every run — pointing a test run at, say,
    "Conditioned UF Code (test)" keeps an exercise of the live path from
    overwriting the property a real conditioned model is already serving.
    """
    return (
        request.config.getoption("--code-property-name")
        or os.environ.get(_ENV_VAR)
        or _from_env_file()
        or DEFAULT_CONDITIONING_KEY
    )
