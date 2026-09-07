"""Shared fake test doubles for specklepy.bundle.model objects.

Not pytest fixtures — just plain classes reused by several offline test
files that each need a minimal stand-in for a
specklepy.bundle.model.ModelObject (the read-only per-object accessor
2026.9's bundle receive path hands back — see conditioning/walls.py's
module docstring) without downloading a real bundle. Consolidated here
2026-09-07 during the port off the JSON-object-graph reader, replacing the
several near-identical `_FakeSpeckleObject`/`_FakeWallObj` classes that used
to live one per test file for the old Base-tree shape.
"""

from __future__ import annotations


class FakeLevel:
    """Minimal stand-in for specklepy.bundle.model.ModelLevel."""

    def __init__(self, name: str, elevation: float = 0.0) -> None:
        """Set the level's name and elevation, matching ModelLevel's shape."""
        self.name = name
        self.elevation = elevation


class FakeMaterial:
    """Minimal stand-in for specklepy.bundle.model.ModelMaterial.

    Only the fields speckle_io._build_full_bundle() reads when carrying a
    material over onto the output bundle (see its get_or_add_material() call)
    — added 2026-09-07 alongside collection_path/color for the full-scene
    republish path.
    """

    def __init__(
        self,
        k: str = "mat-1",
        name: str = "Fake Material",
        argb: int = 0xFFFFFFFF,
        opacity: float | None = 1.0,
        metalness: float | None = 0.0,
        roughness: float | None = 1.0,
        emissive: int | None = None,
        ior: float | None = None,
    ) -> None:
        """Set the fields _build_full_bundle() reads off a material."""
        self.k = k
        self.name = name
        self.argb = argb
        self.opacity = opacity
        self.metalness = metalness
        self.roughness = roughness
        self.emissive = emissive
        self.ior = ior


class FakeColor:
    """Minimal stand-in for specklepy.bundle.model.ModelColor — just `.argb`."""

    def __init__(self, argb: int = 0xFF000000) -> None:
        """Set the ARGB value _build_full_bundle() passes to get_or_add_color()."""
        self.argb = argb


class FakePropertyView:
    """Minimal stand-in for specklepy.bundle.property_table.PropertyView.

    Only `to_nested()` is exercised outside this module (by
    speckle_io._build_walls_bundle/_build_full_bundle) — implemented the same way the
    real one is (split each dotted path on ".", build the nested dict),
    since that reshape is exactly what a test verifying the merged output
    properties needs to trust.
    """

    def __init__(self, flat: dict) -> None:
        """Wrap a flat `{"dotted.path": value}` map."""
        self._flat = flat

    def to_nested(self) -> dict:
        """Reshape the flat dotted-path map into a nested dict."""
        root: dict = {}
        for key, value in self._flat.items():
            parts = key.split(".")
            cursor = root
            for part in parts[:-1]:
                cursor = cursor.setdefault(part, {})
            cursor[parts[-1]] = value
        return root


class FakeModelObject:
    """Minimal stand-in for specklepy.bundle.model.ModelObject.

    Supports exactly what this package reads off a wall's bundle object:
    conditioning.walls' get_string/get_double dotted-path lookups and
    `.level` relation, plus the `.application_id`/`.name`/`.geometries`/
    `.properties` bits conditioning.speckle_io.create_conditioned_version()
    also touches when building the output bundle.

    `properties` is a flat `{"<Group>.<Param>": value}` map covering both
    root-scope paths (category/type/family/units/speckle_type — no group
    prefix) and grouped ones (e.g. "Identity Data.Assembly Code") in the
    same namespace, matching how a real ModelObject resolves a path
    regardless of which scope (instance/type/root) it actually lives in —
    see walls.py's module docstring. Tests don't need to model that
    instance-vs-type precedence search, only its resolved result.

    2026-09-07 (later still): `collection_path`/`material`/`color` added —
    speckle_io._build_full_bundle() (the new 'All/<source>' full-scene
    republish) reads all three off every received object, not just walls.
    Default to `None`/empty so existing wall-only fakes built before this
    date keep working unchanged.
    """

    def __init__(
        self,
        application_id: str = "fake-1",
        properties: dict | None = None,
        level: FakeLevel | None = None,
        name: str | None = None,
        geometries: list | None = None,
        collection_path: list[str] | None = None,
        material: FakeMaterial | None = None,
        color: FakeColor | None = None,
    ) -> None:
        """Set the fields conditioning.walls/speckle_io read off a wall object."""
        self.application_id = application_id
        self._properties = dict(properties or {})
        self.level = level
        self.name = name
        self.geometries = geometries or []
        self.collection_path = collection_path or []
        self.material = material
        self.color = color
        self.k: int | None = None  # assigned by FakeModel, matching ModelObject.k

    def get_string(self, path: str) -> str | None:
        """Look up `path` in the flat properties map, as a string."""
        val = self._properties.get(path)
        return None if val is None else str(val)

    def get_double(self, path: str) -> float | None:
        """Look up `path` in the flat properties map, as a float."""
        val = self._properties.get(path)
        if val is None:
            return None
        return float(val)

    @property
    def properties(self) -> FakePropertyView:
        """A FakePropertyView over this object's flat properties map."""
        return FakePropertyView(self._properties)


class FakeGeometry:
    """Minimal stand-in for specklepy.bundle.model.ModelGeometry.

    `transform is None` means world-space (copied directly); a 16-float
    transform means the geometry came from a placement and
    speckle_io._copy_object_geometry() must skip it in favour of rebuilding
    the placement. Bytes are copied verbatim in every path now, so there is
    no `decode()` — tests only need to see the bytes arrive.
    """

    def __init__(
        self,
        k: int,
        role: str = "display",
        transform: list[float] | None = None,
        content: bytes = b"SGEO",
        type: str | None = "mesh",
        ord: int = 0,
    ) -> None:
        """Set the fields _copy_object_geometry() reads off a geometry."""
        from specklepy.bundle.model import GeometryRole

        self.k = k
        self.role = GeometryRole(role)
        self.transform = transform
        self.content = content
        self.type = type
        self.ord = ord


class FakeDefinition:
    """Minimal stand-in for ModelDefinition — `.k`/`.name` only.

    Its geometry lives in FakeModel's relations, as in the real bundle.
    """

    def __init__(self, k: int, name: str = "Fake Definition") -> None:
        """Set the definition's node key and name."""
        self.k = k
        self.name = name


class FakeInstance:
    """Minimal stand-in for ModelInstance — `.transform`/`.units`/`.definition`."""

    def __init__(
        self,
        k: int,
        definition: FakeDefinition,
        transform: list[float] | None = None,
        units: str | None = "ft",
    ) -> None:
        """Set the placement's key, matrix, units and target definition."""
        self.k = k
        self.definition = definition
        self.transform = transform
        self.units = units


class _FakeRelations:
    """The `bundle.relations` maps _copy_object_geometry()/_copy_definition() read."""

    def __init__(self) -> None:
        self.defines_by_definition: dict[int, list[int]] = {}
        self.defines_ord_by_definition: dict[int, list[int]] = {}
        self.defines_instance_by_definition: dict[int, list[int]] = {}
        self.material_by_geometry: dict[int, int] = {}
        self.color_by_geometry: dict[int, int] = {}


class FakeModel:
    """Minimal stand-in for specklepy.bundle.model.Model.

    `.objects`/`.units` are what the wall-only paths read. The rest —
    `.index.instances_by_object`, `.bundle.relations`, `.geometries`,
    `.node()` — is the instancing surface speckle_io._copy_object_geometry()
    walks (2026-09-07, later still) to rebuild definitions and placements.
    All empty by default; a test that wants an instanced object registers
    its definition/instance nodes via `add_definition()` / `add_instance()`.
    """

    def __init__(self, objects: list[FakeModelObject], units: str = "ft") -> None:
        """Wrap a flat list of FakeModelObject, matching Model.objects' shape."""
        from types import SimpleNamespace

        self.objects = objects
        self.units = units
        self.index = SimpleNamespace(instances_by_object={})
        self.bundle = SimpleNamespace(relations=_FakeRelations())
        self.geometries: dict[int, FakeGeometry] = {}
        self._nodes: dict[int, object] = {}
        # Give every object a stable `.k` so instances_by_object can key on it.
        for i, obj in enumerate(objects):
            if getattr(obj, "k", None) is None:
                obj.k = i

    def node(self, k):
        """Look up a registered definition/instance/material/color node by key."""
        return None if k is None else self._nodes.get(k)

    def add_definition(
        self, definition: FakeDefinition, geometries: list[FakeGeometry]
    ) -> FakeDefinition:
        """Register a definition and the geometries it DEFINES, in order."""
        self._nodes[definition.k] = definition
        rels = self.bundle.relations
        rels.defines_by_definition[definition.k] = [g.k for g in geometries]
        rels.defines_ord_by_definition[definition.k] = list(range(len(geometries)))
        for g in geometries:
            self.geometries[g.k] = g
        return definition

    def add_instance(self, obj: FakeModelObject, instance: FakeInstance) -> None:
        """Register `instance` as a top-level placement displayed by `obj`."""
        self._nodes[instance.k] = instance
        self.index.instances_by_object.setdefault(obj.k, []).append(instance.k)
