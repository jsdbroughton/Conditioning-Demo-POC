"""Integration test for the Conditioning Demo POC automate function.

Unlike every other file under tests/, this one is NOT offline — the
speckle_automate.fixtures pull real credentials from .env and this test
performs an actual live run against the real project/model configured
there, including writing a new "Conditioned/<model>" version. Marked
`integration` and excluded from the default `pytest`/`pytest tests/`
invocation (see [tool.pytest.ini_options] in pyproject.toml) so running the
suite doesn't silently mutate a live Speckle project every time. Run it
deliberately with `pytest tests/ -m integration` when you actually want to
exercise the real path end-to-end.
"""

import pytest
from speckle_automate import (
    AutomationContext,
    AutomationRunData,
    AutomationStatus,
    run_function,
)
from speckle_automate.fixtures import *  # noqa: F403

from main import FunctionInputs, automate_function


@pytest.mark.integration
def test_function_run(
    test_automation_run_data: AutomationRunData,
    test_automation_token: str,
    code_property_name: str,
):
    """Run a live integration test against the configured real Speckle model.

    `code_property_name` comes from --code-property-name / the
    CONDITIONING_CODE_PROPERTY_NAME env var, defaulting to the same key the
    deployed function uses (see tests/conftest.py). Point it somewhere
    disposable when exercising this against a project whose conditioned
    output someone is actually reading:

        pytest tests/ -m integration --code-property-name "Conditioned UF Code (test)"
    """
    automation_context = AutomationContext.initialize(
        test_automation_run_data, test_automation_token
    )
    automate_sdk = run_function(
        automation_context,
        automate_function,
        FunctionInputs(code_property_name=code_property_name),
    )

    assert automate_sdk.run_status == AutomationStatus.SUCCEEDED
