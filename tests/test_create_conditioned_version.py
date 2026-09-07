"""Offline unit test for create_conditioned_version()'s results-view wiring.

No live Speckle call — automate_context is a hand-rolled fake exposing just
the methods create_conditioned_version() touches, so this stays inside the
same "no network" boundary as the rest of the offline suite even though
speckle_io.py is otherwise the one module that talks to a real
AutomationContext.

Covers the fix where the run's "View Results" viewer only ever loaded the
host model that triggered the run, with no way to also inspect the actual
conditioned output (the conditioned-code properties only exist on the new
version pushed to the artifact model). create_conditioned_version() now
calls automate_context.set_context_view() to add the artifact model/version
to that viewer, alongside the host model rather than replacing it —
include_source_model_version=True (the SDK default) keeps the host model in
view because the interactive per-object result markers (attach_info_to_objects,
called earlier against the wall objects) are keyed by applicationId, which
never gets reassigned to match the freshly-built objects pushed to the
artifact model.

2026-09-07: create_conditioned_version() now publishes via
specklepy.api.operations.send3 and a specklepy.bundle.builder.BundleBuilder
(see speckle_io.py's module docstring) instead of
automate_context.create_new_version_in_project(). Both are monkeypatched
here to plain recording fakes — this test is about create_conditioned_version's
OWN orchestration (resolve/create the output model, build a bundle from the
conditioned walls, publish it, wire up the results view), not about
re-exercising specklepy's real bundle-writing internals (parquet encoding,
SGEO), which belong to that SDK's own test suite, not this one. A real,
unfaked bundle round-trip only happens in the live `pytest -m integration`
run (test_function.py) against the real support-workspace project.

2026-09-07 (later still): create_conditioned_version() now publishes TWO
model versions per call — 'Walls/<source>' (_build_walls_bundle(), renamed
from _build_conditioned_bundle()) and 'All/<source>' (_build_full_bundle(),
a full-scene republish of every received object) — and returns a
ConditionedVersions instead of a bare version-id string. Both bundles are
built from the SAME received_model/walls, so every test below now exercises
_build_full_bundle() too, not just the walls-only path; the fakes carry
enough shape (FakeModel.objects, ModelObject.collection_path/material/color)
for that path to run without erroring, even where a given test doesn't
assert anything about the 'All/<source>' output specifically.
"""

from __future__ import annotations

from types import SimpleNamespace

import conditioning.speckle_io as speckle_io
from conditioning.speckle_io import create_conditioned_version, model_leaf_name
from conditioning.walls import WallRecord
from tests.fakes import (
    FakeColor,
    FakeDefinition,
    FakeGeometry,
    FakeInstance,
    FakeLevel,
    FakeMaterial,
    FakeModel,
    FakeModelObject,
)


class _FakeModel:
    def __init__(self, id: str) -> None:
        self.id = id


class _FakeGeometryHandle:
    """Stands in for specklepy.bundle.builder.BundleGeometry (material/color)."""

    def __init__(self, payload, raw: bool = False) -> None:
        self.payload = payload
        self.raw = raw
        self.material = None
        self.color = None


class _FakeBundleDefinition:
    """Stands in for BundleDefinition — records geometry and nested placements."""

    def __init__(self, key: str, name: str | None) -> None:
        self.key = key
        self.name = name
        self.raw_geometries: list[tuple[bytes, str, int]] = []
        self.nested: list[tuple[_FakeBundleDefinition, list[float]]] = []

    def add_raw_geometry(self, content, type, geometry_key=None, member_ord=None):
        self.raw_geometries.append((content, type, member_ord))
        return _FakeGeometryHandle(content, raw=True)

    def place_nested(self, definition, transform, units=None, key=None):
        self.nested.append((definition, list(transform)))
        return SimpleNamespace(definition=definition)


class _FakePipeline:
    """The two pipeline calls speckle_io._add_raw_display() makes, recorded."""

    def __init__(self) -> None:
        self.raw: dict[str, tuple[bytes, str]] = {}
        self.display_edges: list[tuple[int, int, int]] = []
        self._next_k = 0

    def add_raw_geometry(self, key, content, type_label):
        self.raw[key] = (content, type_label)
        self._next_k += 1
        return self._next_k

    def display(self, object_k, geometry_k, ord):
        self.display_edges.append((object_k, geometry_k, ord))


class _FakeBundleObject:
    def __init__(self, application_id: str, k: int = 0) -> None:
        self.application_id = application_id
        self.k = k
        self.properties: dict | None = None
        self.name = None
        self.speckle_type = None
        self.source_type = None
        self.units = None
        self.geometries: list[_FakeGeometryHandle] = []
        self.placements: list[tuple[_FakeBundleDefinition, list[float]]] = []
        self.collection = None
        self.level = None
        self.material = None
        self.color = None

    def set_properties(self, properties=None, name=None, speckle_type=None,
                        source_type=None, units=None, **kwargs):
        self.properties = properties
        self.name = name
        self.speckle_type = speckle_type
        self.source_type = source_type
        self.units = units
        return self

    def add_geometry(self, geometry, geometry_key=None):
        handle = _FakeGeometryHandle(geometry)
        self.geometries.append(handle)
        return handle

    def add_raw_geometry(self, content, type, geometry_key=None):
        handle = _FakeGeometryHandle(content, raw=True)
        self.geometries.append(handle)
        return handle

    def place(self, definition, transform, units=None, key=None):
        self.placements.append((definition, list(transform)))
        return SimpleNamespace(definition=definition)


class _FakeBundleBuilder:
    """Stands in for specklepy.bundle.builder.BundleBuilder.

    Implements only the methods _build_walls_bundle()/_build_full_bundle()
    actually call — see those functions in speckle_io.py. get_or_add_material/
    get_or_add_color added 2026-09-07 alongside _build_full_bundle(), which
    carries material/color over for every received object, not just walls.
    """

    def __init__(self, producer, units) -> None:
        self.producer = producer
        self.units = units
        self.objects: dict[str, _FakeBundleObject] = {}
        self.containers: dict[str, object] = {}
        self.levels: dict[str, object] = {}
        self.materials: dict[str, object] = {}
        self.colors: dict[int, object] = {}
        self.definitions: dict[str, _FakeBundleDefinition] = {}
        self.pipeline = _FakePipeline()

    def get_or_add_definition(self, key, name, populate=None):
        existing = self.definitions.get(key)
        if existing is not None:
            return existing
        definition = self.definitions[key] = _FakeBundleDefinition(key, name)
        if populate is not None:
            populate(definition)
        return definition

    def get_or_add_container_path(self, path):
        key = "/".join(path)
        return self.containers.setdefault(key, SimpleNamespace(key=key))

    def get_or_add_container(self, key, name, parent, subtype="Collection",
                              gh_topology=None):
        return self.containers.setdefault(
            key, SimpleNamespace(key=key, name=name, parent=parent, subtype=subtype)
        )

    def get_or_add_object(self, application_id: str) -> _FakeBundleObject:
        return self.objects.setdefault(
            application_id, _FakeBundleObject(application_id, k=len(self.objects))
        )

    def get_or_add_level(self, key, name, elevation):
        return self.levels.setdefault(
            key, SimpleNamespace(key=key, name=name, elevation=elevation)
        )

    def get_or_add_material(self, key, name, argb, opacity=1.0, metalness=0.0,
                             roughness=1.0, emissive=None, ior=None):
        return self.materials.setdefault(
            key,
            SimpleNamespace(
                key=key, name=name, argb=argb, opacity=opacity,
                metalness=metalness, roughness=roughness, emissive=emissive,
                ior=ior,
            ),
        )

    def get_or_add_color(self, argb):
        return self.colors.setdefault(argb, SimpleNamespace(argb=argb))


class _FakeSendResult:
    def __init__(self, version_id: str) -> None:
        self.version_id = version_id


class _FakeAutomationContext:
    """Stands in for speckle_automate.AutomationContext.

    Implements only the methods create_conditioned_version() actually calls.
    `create_new_model_in_project` now tracks one created model per model name
    (2026-09-07, since a single call creates both 'Walls/<source>' and
    'All/<source>') rather than always returning the same fake model.
    """

    def __init__(self) -> None:
        self.automation_run_data = SimpleNamespace(
            project_id="project-1",
            triggers=[SimpleNamespace(payload=SimpleNamespace(model_id="source-model-1"))],
        )
        self.speckle_client = SimpleNamespace(account=SimpleNamespace(userInfo=None))
        self.created_models: dict[str, _FakeModel] = {}
        self.context_view_calls: list[dict] = []

    def get_model(self, model_id: str):
        assert model_id == "source-model-1"
        return SimpleNamespace(name="SHELL.rvt")

    def create_new_model_in_project(
        self,
        model_name: str,
        model_description: str | None = None,
    ):
        model = self.created_models.setdefault(
            model_name, _FakeModel(f"artifact-model-{len(self.created_models) + 1}")
        )
        return model

    def set_context_view(
        self,
        resource_ids=None,
        include_source_model_version: bool = True,
    ):
        self.context_view_calls.append(
            {
                "resource_ids": resource_ids,
                "include_source_model_version": include_source_model_version,
            }
        )


def _wall(object_id: str, **overrides) -> WallRecord:
    defaults = dict(
        obj=FakeModelObject(application_id=object_id, level=FakeLevel("LEVEL 01")),
        category="Walls", type_name="", family="Basic Wall", function="",
        type_mark="", width_mm=200.0, level="LEVEL 01", assembly_code="B2010.10",
    )
    defaults.update(overrides)
    return WallRecord(object_id=object_id, **defaults)


class TestCreateConditionedVersionSetsContextView:
    """Test create conditioned version sets context view."""
    def test_context_view_adds_both_artifact_models_alongside_host(self, monkeypatch):
        """Context view adds both artifact models alongside host."""
        ctx = _FakeAutomationContext()
        received_model = FakeModel(objects=[], units="ft")

        version_ids = iter(["walls-version-1", "all-version-1"])

        def fake_send3(account, project_id, model_id, builder, options=None):
            return _FakeSendResult(next(version_ids))

        monkeypatch.setattr(speckle_io, "BundleBuilder", _FakeBundleBuilder)
        monkeypatch.setattr(speckle_io.operations, "send3", fake_send3)

        versions = create_conditioned_version(
            ctx,
            received_model,
            walls=[],
            predictions=[],
        )

        assert versions.walls_model_name == "Conditioned/Walls/SHELL.rvt"
        assert versions.all_model_name == "Conditioned/All/SHELL.rvt"
        assert versions.walls_version_id == "walls-version-1"
        assert versions.all_version_id == "all-version-1"

        walls_model_id = ctx.created_models["Conditioned/Walls/SHELL.rvt"].id
        all_model_id = ctx.created_models["Conditioned/All/SHELL.rvt"].id
        assert ctx.context_view_calls == [
            {
                "resource_ids": [
                    f"{walls_model_id}@walls-version-1",
                    f"{all_model_id}@all-version-1",
                ],
                "include_source_model_version": True,
            }
        ]

    def test_wall_properties_and_conditioning_are_merged_into_both_bundles(
        self, monkeypatch,
    ):
        """Original properties and the conditioning result land on both outputs."""
        ctx = _FakeAutomationContext()
        wall_obj = FakeModelObject(
            application_id="wall-1",
            properties={"Identity Data.Type Mark": "L6"},
            level=FakeLevel("LEVEL 01", elevation=10.0),
            name="A basic wall",
            collection_path=["LEVEL 01", "Walls"],
            material=FakeMaterial(k="mat-1", name="Concrete", argb=0xFFAAAAAA),
            color=FakeColor(argb=0xFFBBBBBB),
        )
        wall = _wall("wall-1", obj=wall_obj)
        received_model = FakeModel(objects=[wall_obj], units="ft")

        monkeypatch.setattr(speckle_io, "BundleBuilder", _FakeBundleBuilder)

        captured_builders: list = []

        def fake_send3(account, project_id, model_id, builder, options=None):
            captured_builders.append(builder)
            return _FakeSendResult(f"version-{len(captured_builders)}")

        monkeypatch.setattr(speckle_io.operations, "send3", fake_send3)

        create_conditioned_version(ctx, received_model, walls=[wall], predictions=[])

        from conditioning.codes import DEFAULT_CONDITIONING_KEY

        walls_builder, all_builder = captured_builders
        for builder in (walls_builder, all_builder):
            bundle_obj = builder.objects["wall-1"]
            # The wall's own parameters (reshaped by to_nested()) ...
            assert bundle_obj.properties["Identity Data"]["Type Mark"] == "L6"
            # ... alongside the conditioning payload, as a sibling namespaced
            # key — imprint_predictions() is called by
            # create_conditioned_version() itself, so a Level 4-coded wall
            # gets a real "existing" result.
            assert (
                bundle_obj.properties[DEFAULT_CONDITIONING_KEY]["Status"]
                == "existing"
            )
            assert bundle_obj.name == "A basic wall"
            assert bundle_obj.level.name == "LEVEL 01"

        # Both bundles share _copy_object_style(), so material/color carry
        # over identically — the walls bundle never used to have this.
        for builder in (walls_builder, all_builder):
            assert builder.objects["wall-1"].material.argb == 0xFFAAAAAA
            assert builder.objects["wall-1"].color.argb == 0xFFBBBBBB

    def test_a_failed_bundle_publish_does_not_take_the_other_down(self, monkeypatch):
        """One bundle failing to send still lets the other publish and return."""
        ctx = _FakeAutomationContext()
        received_model = FakeModel(objects=[], units="ft")

        monkeypatch.setattr(speckle_io, "BundleBuilder", _FakeBundleBuilder)

        def fake_send3(account, project_id, model_id, builder, options=None):
            # _publish_bundle() creates/looks up the output model before
            # calling send3, so by the time this runs for the walls bundle,
            # ctx.created_models already has its id — no need to pre-seed it.
            if model_id == ctx.created_models["Conditioned/Walls/SHELL.rvt"].id:
                raise RuntimeError("boom")
            return _FakeSendResult("all-version-1")

        monkeypatch.setattr(speckle_io.operations, "send3", fake_send3)

        versions = create_conditioned_version(
            ctx, received_model, walls=[], predictions=[],
        )

        assert versions.walls_version_id is None
        assert versions.all_version_id == "all-version-1"
        # set_context_view only gets the half that actually published.
        assert ctx.context_view_calls[0]["resource_ids"] == [
            f"{ctx.created_models['Conditioned/All/SHELL.rvt'].id}@all-version-1"
        ]


def _publish_all_bundle(monkeypatch, received_model, walls):
    """Run create_conditioned_version() and return the 'All/<source>' builder."""
    ctx = _FakeAutomationContext()
    monkeypatch.setattr(speckle_io, "BundleBuilder", _FakeBundleBuilder)
    captured: list = []

    def fake_send3(account, project_id, model_id, builder, options=None):
        captured.append(builder)
        return _FakeSendResult(f"version-{len(captured)}")

    monkeypatch.setattr(speckle_io.operations, "send3", fake_send3)
    create_conditioned_version(ctx, received_model, walls=walls, predictions=[])
    return captured[1]


class TestFullBundleGeometryIsStructural:
    """Instanced geometry is rebuilt as definition + placement, not flattened.

    The bug this pins: the first full republish decoded every ModelGeometry
    and added it as direct display geometry, dropping the placement matrix
    — so on the live model every door, panel and piece of equipment landed
    at the definition origin and the tower collapsed into a stack of slabs.
    """

    def test_world_space_geometry_is_copied_directly_by_role(self, monkeypatch):
        """Untransformed display geometry decodes; solid geometry copies raw."""
        obj = FakeModelObject(
            application_id="wall-1",
            properties={"category": "Walls"},
            geometries=[
                FakeGeometry(k=10, role="display", content=b"MESH-BYTES", type="mesh"),
                FakeGeometry(k=11, role="solid", content=b"BREP-BYTES", type="brep"),
            ],
        )
        builder = _publish_all_bundle(monkeypatch, FakeModel([obj]), walls=[])

        wall = builder.objects["wall-1"]
        # Display geometry: raw bytes straight onto the pipeline, DISPLAY edge,
        # source ordinal kept — never decoded.
        assert builder.pipeline.raw["geometry-10"] == (b"MESH-BYTES", "mesh")
        assert builder.pipeline.display_edges == [(wall.k, 1, 0)]
        # Solid geometry: raw bytes via the object's own SOLID path.
        assert [(h.payload, h.raw) for h in wall.geometries] == [(b"BREP-BYTES", True)]
        assert wall.placements == []

    def test_instanced_geometry_becomes_definition_plus_placement(self, monkeypatch):
        """A placed object gets place(definition, matrix), not origin geometry."""
        matrix = [1, 0, 0, 5, 0, 1, 0, 6, 0, 0, 1, 7, 0, 0, 0, 1]
        door = FakeModelObject(
            application_id="door-1",
            properties={"category": "Doors"},
            # What ModelObject.geometries hands back for a placement: the
            # DEFINITION's geometry, with the matrix left on .transform.
            geometries=[FakeGeometry(k=20, transform=matrix, content=b"DOOR-MESH")],
        )
        model = FakeModel([door])
        definition = model.add_definition(
            FakeDefinition(k=100, name="Single Flush"),
            [FakeGeometry(k=20, content=b"DOOR-MESH", type="mesh")],
        )
        model.add_instance(door, FakeInstance(k=200, definition=definition,
                                              transform=matrix))

        builder = _publish_all_bundle(monkeypatch, model, walls=[])

        bundle_door = builder.objects["door-1"]
        # Nothing landed as direct geometry — that's exactly the bug.
        assert bundle_door.geometries == []
        (placed_def, placed_matrix), = bundle_door.placements
        assert placed_matrix == matrix
        assert placed_def.name == "Single Flush"
        assert placed_def.raw_geometries == [(b"DOOR-MESH", "mesh", 0)]

    def test_shared_definition_is_written_once(self, monkeypatch):
        """Two placements of one definition intern to a single definition."""
        identity = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]
        doors = [
            FakeModelObject(
                application_id=f"door-{i}", properties={"category": "Doors"}
            )
            for i in range(2)
        ]
        model = FakeModel(doors)
        definition = model.add_definition(
            FakeDefinition(k=100), [FakeGeometry(k=20, content=b"M", type="mesh")]
        )
        for i, door in enumerate(doors):
            model.add_instance(door, FakeInstance(k=200 + i, definition=definition,
                                                  transform=identity))

        builder = _publish_all_bundle(monkeypatch, model, walls=[])

        assert len(builder.definitions) == 1
        assert builder.objects["door-0"].placements[0][0] is (
            builder.objects["door-1"].placements[0][0]
        )


class TestFullBundleStampsEveryObject:
    """Non-wall objects carry an explicit 'not conditioned' result, not nothing."""

    def test_non_wall_gets_not_conditioned_under_the_same_key(self, monkeypatch):
        """A door in 'All/<source>' says plainly that it was out of scope, and why."""
        from conditioning.codes import DEFAULT_CONDITIONING_KEY

        door = FakeModelObject(
            application_id="door-1",
            properties={"category": "Doors", "Identity Data.Mark": "D1"},
        )
        builder = _publish_all_bundle(monkeypatch, FakeModel([door]), walls=[])

        props = builder.objects["door-1"].properties
        assert props["Identity Data"]["Mark"] == "D1"  # source properties intact
        cond = props[DEFAULT_CONDITIONING_KEY]
        assert cond["Status"] == "not conditioned"
        assert cond["Requires Verification"] is False
        # Doors HAS a rule — so the reason must say the evidence was missing,
        # not that the category is unknown.
        assert "'Doors'" in cond["Level 4 Code Source"]
        assert "rules exist" in cond["Level 4 Code Source"]
        assert "category alone is not enough" in cond["Level 4 Code Source"]

    def test_category_without_a_rule_says_so(self, monkeypatch):
        """A Room says the function has no rule for it — a different gap."""
        from conditioning.codes import DEFAULT_CONDITIONING_KEY

        room = FakeModelObject(application_id="r1", properties={"category": "Rooms"})
        builder = _publish_all_bundle(monkeypatch, FakeModel([room]), walls=[])
        cond = builder.objects["r1"].properties[DEFAULT_CONDITIONING_KEY]
        assert cond["Status"] == "not conditioned"
        assert "Not applicable" in cond["Level 4 Code Source"]
        assert "not physical construction" in cond["Level 4 Code Source"]

    def test_category_with_no_rule_and_physical_says_no_rule(self, monkeypatch):
        """A Generic Model is physical but unknown — a different message again."""
        from conditioning.codes import DEFAULT_CONDITIONING_KEY

        gm = FakeModelObject(
            application_id="g1", properties={"category": "Generic Models"}
        )
        builder = _publish_all_bundle(monkeypatch, FakeModel([gm]), walls=[])
        cond = builder.objects["g1"].properties[DEFAULT_CONDITIONING_KEY]
        assert "no derivation rule for category 'Generic Models'" in (
            cond["Level 4 Code Source"]
        )

    def test_category_results_land_on_non_wall_objects_in_the_all_bundle(
        self, monkeypatch,
    ):
        """A door the category engine placed carries a real result, not a blank."""
        from conditioning.categories import CategoryResult
        from conditioning.codes import DEFAULT_CONDITIONING_KEY

        door = FakeModelObject(
            application_id="door-1", properties={"category": "Doors"}
        )
        ctx = _FakeAutomationContext()
        monkeypatch.setattr(speckle_io, "BundleBuilder", _FakeBundleBuilder)
        captured: list = []

        def fake_send3(account, project_id, model_id, builder, options=None):
            captured.append(builder)
            return _FakeSendResult(f"version-{len(captured)}")

        monkeypatch.setattr(speckle_io.operations, "send3", fake_send3)
        result = CategoryResult(
            object_id="door-1", category="Doors", code="C1030.10", confidence=0.85,
            tier=1, method="heuristic_function",
            basis="the Revit Function parameter (Interior)", original_code=None,
        )
        create_conditioned_version(
            ctx, FakeModel([door]), walls=[], predictions=[],
            category_results=[result],
        )

        cond = captured[1].objects["door-1"].properties[DEFAULT_CONDITIONING_KEY]
        assert cond["Status"] == "predicted"
        assert cond["Level 4 Code"] == "C1030.10"
        assert cond["Level 4 Code Description"] == "Interior Swinging Doors"
        assert cond["Requires Verification"] is True
        assert cond["Tier"] == "Tier 1"
        assert cond["Method"] == "heuristic_function"
        assert "Derived by Speckle from the Revit Function parameter" in (
            cond["Level 4 Code Source"]
        )
        # Wall-only keys are absent, not present-and-empty.
        assert not any(k.startswith(("Observed", "Inferred")) for k in cond)


class TestOutputModelNaming:
    """Only the source model's leaf name goes under Conditioned/."""

    def test_leaf_name_drops_the_source_folders(self):
        """'Source/Walls/Shell' → 'Shell'; deep paths keep only the last segment."""
        assert model_leaf_name("Source/Walls/Shell") == "Shell"
        assert model_leaf_name("Source/Banana/Republic/Is/Hot") == "Hot"
        assert model_leaf_name("Shell") == "Shell"
        assert model_leaf_name("Shell/") == "Shell"

    def test_output_models_use_the_leaf_name(self, monkeypatch):
        """A source in a folder does not drag that folder under Conditioned/."""
        ctx = _FakeAutomationContext()
        ctx.get_model = lambda model_id: SimpleNamespace(name="Source/Walls/Shell")
        monkeypatch.setattr(speckle_io, "BundleBuilder", _FakeBundleBuilder)
        monkeypatch.setattr(
            speckle_io.operations, "send3",
            lambda *a, **k: _FakeSendResult("v"),
        )
        versions = create_conditioned_version(
            ctx, FakeModel([]), walls=[], predictions=[]
        )
        assert versions.walls_model_name == "Conditioned/Walls/Shell"
        assert versions.all_model_name == "Conditioned/All/Shell"
