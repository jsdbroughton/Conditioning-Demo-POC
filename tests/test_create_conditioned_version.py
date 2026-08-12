"""Offline unit test for create_conditioned_version()'s results-view wiring.

No live Speckle call — automate_context is a hand-rolled fake exposing just
the methods create_conditioned_version() touches, so this stays inside the
same "no network" boundary as the rest of the offline suite even though
speckle_io.py is otherwise the one module that talks to a real
AutomationContext.

Covers the fix where the run's "View Results" viewer only ever loaded the
host model that triggered the run, with no way to also inspect the actual
conditioned output (the Turner UF Code properties only exist on the new
version pushed to the artifact model). create_conditioned_version() now
calls automate_context.set_context_view() to add the artifact model/version
to that viewer, alongside the host model rather than replacing it —
include_source_model_version=True (the SDK default) keeps the host model in
view because the interactive per-object result markers (attach_info_to_objects,
called earlier against unmutated wall objects) are keyed to the host
model's object ids, which never get reassigned to match the artifact
model's re-hashed objects. Dropping the host model from the view would
break those markers.
"""

from __future__ import annotations

from types import SimpleNamespace

from conditioning.speckle_io import create_conditioned_version


class _FakeModel:
    def __init__(self, id: str) -> None:
        self.id = id


class _FakeVersion:
    def __init__(self, id: str) -> None:
        self.id = id


class _FakeAutomationContext:
    """Stands in for speckle_automate.AutomationContext — only the methods
    create_conditioned_version() actually calls."""

    def __init__(self) -> None:
        self.automation_run_data = SimpleNamespace(
            triggers=[SimpleNamespace(payload=SimpleNamespace(model_id="source-model-1"))]
        )
        self.created_model = _FakeModel("artifact-model-1")
        self.created_version = _FakeVersion("artifact-version-1")
        self.context_view_calls: list[dict] = []

    def get_model(self, model_id: str):
        assert model_id == "source-model-1"
        return SimpleNamespace(name="SHELL.rvt")

    def create_new_model_in_project(self, model_name: str, model_description: str | None = None):
        return self.created_model

    def create_new_version_in_project(self, root_object, model_id: str, version_message: str = ""):
        assert model_id == self.created_model.id
        return self.created_version

    def set_context_view(self, resource_ids=None, include_source_model_version: bool = True):
        self.context_view_calls.append(
            {"resource_ids": resource_ids, "include_source_model_version": include_source_model_version}
        )


class TestCreateConditionedVersionSetsContextView:
    def test_context_view_adds_artifact_model_alongside_host(self):
        ctx = _FakeAutomationContext()

        new_version_id = create_conditioned_version(ctx, root=object(), walls=[], predictions=[])

        assert new_version_id == "artifact-version-1"
        assert ctx.context_view_calls == [
            {
                "resource_ids": ["artifact-model-1@artifact-version-1"],
                "include_source_model_version": True,
            }
        ]
