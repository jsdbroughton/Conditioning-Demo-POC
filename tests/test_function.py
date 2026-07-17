"""Integration tests for the Conditioning Demo POC automate function."""

from speckle_automate import (
    AutomationContext,
    AutomationRunData,
    AutomationStatus,
    run_function,
)
from speckle_automate.fixtures import *  # noqa: F403

from main import FunctionInputs, automate_function


def test_function_run(
    test_automation_run_data: AutomationRunData, test_automation_token: str
):
    """Run an integration test against the configured test model."""
    automation_context = AutomationContext.initialize(
        test_automation_run_data, test_automation_token
    )
    automate_sdk = run_function(
        automation_context,
        automate_function,
        FunctionInputs(
            confidence_threshold=0.65,
        ),
    )

    assert automate_sdk.run_status == AutomationStatus.SUCCEEDED
