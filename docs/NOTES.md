# Conditioning Demo POC — Development Log

## Purpose

Speckle Automate function that predicts Uniformat Assembly Codes for uncoded Revit wall elements, using Turner's estimate detail structure as the reference code set.

**Target model:** `https://app.speckle.systems/projects/0b23109140/models/9edde2c89f`
Project ID: `0b23109140` · Model ID: `9edde2c89f`
Model name: `Henry Ford Hospital - SHELL.rvt`

---

## Confirmed v3 Speckle Object Data Structure

Verified by directly querying the target model via GraphQL in browser session (July 2026).

### Wall object top-level attributes

```python
wall.category   # str — "Walls" (not in properties, top-level)
wall.type       # str — Revit type name, e.g. "_HFH - GFRC"
wall.family     # str — Revit family, e.g. "Basic Wall"
wall.level      # str — plain string, e.g. "LEVEL 01" (NOT a proxy object)
wall.id         # str — Speckle object ID (use for attach_info_to_objects)
```

### Parameter access paths

All parameters live under `wall.properties["Parameters"]`, **not** at `wall.parameters` (which is empty in v3):

```python
tp = wall.properties["Parameters"]["Type Parameters"]

# Assembly Code
tp["Identity Data"]["Assembly Code"]["value"]          # e.g. "B2010160"
tp["Identity Data"]["Assembly Description"]["value"]   # e.g. "Ext. Wall - Stone Veneer w/ Stud"
tp["Identity Data"]["Type Mark"]["value"]              # e.g. "CMV-1"

# Construction
tp["Construction"]["Function"]["value"]                # e.g. "Exterior" | "Interior" | "Retaining"
tp["Construction"]["Width"]["value"]                   # float, in FEET (not metres, not mm)

# Width conversion
width_mm = tp["Construction"]["Width"]["value"] * 304.8
```

### Category detection (correct v3 pattern)

```python
# CORRECT — category is top-level
if getattr(obj, "category", None) == "Walls":
    ...

# WRONG — category is NOT in obj.properties in this connector version
if obj.properties.get("category") == "Walls":   # ← fails
    ...
```

### Object graph structure

The model is organised: Root → Level collections → Wall type groups → Individual wall elements.

```
root
  elements[0]  → Collection (levels): LEVEL 01, LEVEL 02, ...
    elements[0] → Collection (LEVEL 01)
      elements[0] → Collection (wall type groups)
        elements[N] → Collection (one per wall type, named after type)
          elements[N] → Wall DataObject (leaf — has category, type, family, etc.)
  elements[1]  → Collection "definitionGeometry" (3563 objects, geometry only)
  levelProxies → [...]
```

### GraphQL traversal

```python
from specklepy.objects.graph_traversal.traversal import GraphTraversal
traversal = GraphTraversal([])
for context in traversal.traverse(root):
    obj = context.current
    if getattr(obj, "category", None) == "Walls":
        # process wall
```

---

## Speckle Automate SDK (speckle-automate, bundled in specklepy 3.1.0)

```python
from speckle_automate import AutomateBase, AutomationContext, execute_automate_function
```

### Key AutomationContext methods

```python
root = automate_context.receive_version()

automate_context.attach_info_to_objects(
    category="My Category",
    affected_objects=[wall_obj],   # list of Base objects, NOT string IDs
    message="...",
)

model = automate_context.create_new_model_in_project(
    model_name="Conditioned",
    model_description="...",
)  # → Model (has .id)

version = automate_context.create_new_version_in_project(
    root_object=root,
    model_id=model.id,
    version_message="...",
)  # → Version (has .id)

automate_context.store_file_result("path/to/file.md")  # attach file to run

automate_context.mark_run_success("Summary message")
automate_context.mark_run_failed("Reason")
```

---

## Turner Uniformat Code Structure

Source: `Turner - Uniformat Estimate Detail Structure.xlsx` (3394 rows, uploaded July 2026)

### Key finding: curtain walls are B2010.40 in Turner's system, NOT B2050

| Code | Turner Description |
|------|--------------------|
| `A2010` | Walls for Subgrade Enclosures |
| `A2010.10` | Subgrade Enclosure Wall Construction |
| `B2010` | Exterior Walls |
| `B2010.10` | Exterior Wall Veneer (masonry, precast, metal panels, GFRC, stone) |
| `B2010.20` | Exterior Wall Back-up Construction (CMU backup, metal stud) |
| `B2010.40` | Fabricated Exterior Wall Assemblies → **curtain walls go here** |
| `B2010.50` | Parapet Back-up Construction |
| `C1010` | Interior Partitions |
| `C1010.10` | Interior Fixed Partitions (CMU, GWB rated/non-rated) |
| `C1010.20` | Interior Glazed Partitions (interior storefront) |
| `B2050` | **Exterior Doors and Grilles** (NOT curtain walls — common mistake) |

### Primary prediction targets (sub-section level codes)

These are the codes the function predicts for uncoded walls:

```
A2010.10  Subgrade Enclosure Wall Construction
B2010.10  Exterior Wall Veneer
B2010.40  Fabricated Exterior Wall Assemblies (curtain walls)
C1010.10  Interior Fixed Partitions
C1010.20  Interior Glazed Partitions
```

---

## Model Observations (Henry Ford Hospital Shell)

- Most walls have **no Assembly Code** — this model is the target for conditioning
- Walls that do have codes use old ASTM Uniformat II format: `B2010160`, `B2010200`, etc.
  - These do not directly match Turner's dot-notation format (`B2010.10`)
  - For PoC: treat these as "coded" reference walls and learn from their type names
- Wall types observed: GFRC panels, CMU-backed masonry veneer, curtain walls (084400_CW series), metal panel walls, parapet walls
- Levels: LEVEL 01 through LEVEL 21 HELIPAD, plus "No Level"
- Wall Function parameter values seen: `"Exterior"`, `"Interior"` — very useful for heuristic

---

## Fingerprinting Approach

Weighted Jaccard similarity over these fields:

| Field | Source | Weight | Notes |
|-------|--------|--------|-------|
| `type_name` | `wall.type` | 40% | Most discriminating in this dataset |
| `function` | `tp["Construction"]["Function"]["value"]` | 25% | "Exterior"/"Interior" is a strong signal |
| `family` | `wall.family` | 15% | Less useful — nearly all are "Basic Wall" |
| `type_mark` | `tp["Identity Data"]["Type Mark"]["value"]` | 10% | e.g. "CMV-1", "ACM" |
| `width_mm` | `tp["Construction"]["Width"]["value"] * 304.8` | 10% | Stored in feet |

---

## Heuristic Prediction Order

1. **Revit Function parameter** → highest confidence, checked first
   - `"Exterior"` → `B2010.10`
   - `"Interior"` → `C1010.10`
   - `"Curtain"` → `B2010.40`
   - `"Retaining"` / `"Foundation"` → `A2010.10`
2. **Type name + family keyword search** → checked in order of specificity
   - `"curtain"`, `"glazing"`, `"storefront"` → `B2010.40`
   - `"retaining"`, `"basement"`, `"foundation"` → `A2010.10`
   - `"cmu"`, `"scmu"`, `"masonry"`, `"brick"`, `"exterior"` → `B2010.10`
   - `"interior"`, `"partition"`, `"demising"` → `C1010.10`
3. **Default** → `B2010.10` (most common wall type)

---

## Files

```
main.py              — Automate function (entry point)
pyproject.toml       — deps: specklepy==3.1.0 (speckle_automate bundled)
flatten.py           — template helper (unused, kept for compatibility)
docs/NOTES.md        — this file
```

---

## Session History

| Date | What happened |
|------|---------------|
| 2026-07-17 | Initial PoC built. Fetched 4 Speckle SDK docs. Discovered v3 uses DataObject + top-level category (not properties.category). |
| 2026-07-17 | Queried Henry Ford Hospital model via browser GraphQL. Found actual parameter paths (properties.Parameters.Type Parameters vs assumed wall.parameters). Fixed width units (feet not metres). Fixed curtain wall code (B2010.40 not B2050). |
| 2026-07-17 | Hardcoded Turner Uniformat Estimate Detail Structure. Sub-section codes used as prediction targets. |
| 2026-07-17 | **First successful test run.** `uv run pytest tests/ -v` → 1 passed in 11.59s. Python 3.14.6, specklepy 3.1.0. Results posted to Speckle: viewer annotations on coded/predicted walls, conditioning_report.md attached, "Conditioned" model version created. |
| 2026-07-17 | **Live demo on Turner call caught a bug**: predictions overwrote ASTM-coded walls (e.g. `B2010160` → `B2010.10`), discarding the specific sub-code. Flagged live, not fixed in the moment. |
| 2026-08-12 | **Root cause found + fixed.** `predict_codes()` defined `reference` as *only* Level-4 dot-format walls and `needs_pred` as *everything else* — so any wall with an ASTM code (not dot-format) was excluded from the reference pool AND re-run through the heuristic fallback as if blank, overwriting its real sub-code with a generic default. This is the opposite of what this file (above) already said to do ("treat these as coded reference walls and learn from their type names") — that intent was never actually implemented. Also explains the second live-demo issue: since Henry Ford Wall Takeoff has zero pre-existing dot-format walls, the reference pool was *always* empty, so every prediction fell to the heuristic with a hardcoded `confidence=0.0`, regardless of how reliable the actual signal was (e.g. a direct Revit `Function` param match). Confirmed via Speckle Admin querying the live `Conditioned` model (project `0b23109140`, model `20cd9048b5`): 175/580 walls (100× `C1010145`→`C1010.10`, 73× `B2010160`→`B2010.10`, 2× `B2010`→`B2010.10`) had been overwritten this way, and all 580 output records showed `Confidence = 0`. Fix: (1) `predict_codes()` reference pool is now any coded wall (ASTM or Level4), prediction targets are now *only* truly uncoded walls — ASTM-coded walls are never touched, instead flagged via `Turner Level 4 Code Review Needed` for manual crosswalk; (2) added `METHOD_CONFIDENCE` giving each heuristic method a real, method-specific confidence (`heuristic_function`=0.75, `heuristic_name`=0.50, `default`=0.0) instead of reusing a meaningless similarity score. Added `tests/test_predict_codes.py` — 9 offline unit tests (no live Speckle call) proving the regression can't reoccur. Not yet re-run against the live Turner models (see automate-trigger note below — deliberately out of scope for this pass). |

**Next step (explicitly not done in this pass):** re-run the fixed function against the `Henry Ford Wall Takeoff` shell model and the 3 new UKHC models Kevin Wanner uploaded 2026-07-21 (`UKHC_Fitout_Tower.rvt`, `UKHC_Fitout_Podium.rvt`, `UKHC_EXT_Core.rvt`) — none have been conditioned yet. Triggering the Automate run itself is a separate step from this code fix.
| 2026-08-12 | **Structural refactor: main.py split into a `src/conditioning` package.** main.py is now a thin orchestrator (~120 lines) — `FunctionInputs`, `automate_function`, and the `__main__` entry point only. Business logic moved to `src/conditioning/`: `codes.py` (Turner code reference data + format regexes), `walls.py` (`WallRecord`, extraction from Speckle DataObjects, `classify_walls()`), `predict.py` (fingerprint similarity + heuristic fallback, `predict_codes()`), `report.py` (`build_report()`), `speckle_io.py` (the only module touching `AutomationContext` — `imprint_predictions()`, `attach_viewer_annotations()`, `create_conditioned_version()`). `classify_walls()` also deduplicates a block that used to be copy-pasted between `build_report()` and `automate_function()`. Used the src layout (not a flat top-level package) per direction — main.py stays outside the installed package since it's a standalone script the Automate runtime invokes directly, not something that ships inside the wheel. This required two supporting fixes: (1) `pyproject.toml` had no `[build-system]` table at all, so `pip install .` was relying on an undocumented legacy pip fallback that doesn't support editable installs — added one (`setuptools.build_meta`) plus `package-dir`/`packages.find` config for the src layout; (2) the Dockerfile copied only `pyproject.toml` before running `pip install .` as a layer-caching trick — with a real local package now involved, that ordering would silently install an empty `conditioning` package (src/ doesn't exist yet at that COPY step) and ship a broken image. Reordered to copy full source before installing. Verified via `setuptools.find_packages(where="src")` (correctly discovers `['conditioning']`) and all 16 offline tests passing against the new module paths — couldn't do a true `pip install -e .` in the sandbox used for validation (repo requires Python ≥3.13, sandbox has 3.10), used `PYTHONPATH=src` instead; worth a real `pip install .[dev]` + `pytest` pass on an actual 3.13+/3.14 machine to confirm end to end.
| 2026-08-12 | **Output model namespaced per source model.** `create_conditioned_version()` was always writing to one shared `Conditioned` model regardless of which model triggered the run — with multiple source models now feeding this function (Henry Ford Wall Takeoff's SHELL, plus the 3 UKHC models Kevin uploaded 2026-07-21), that would mix unrelated walls together. Now writes to `Conditioned/<source model name>` (looked up via `automate_context.get_model(triggers[0].payload.model_id).name`), using Speckle's `/` model-name folder convention to keep all conditioned output grouped under one parent while keeping each source distinct. Not covered by the offline test suite — this only exercises against a live Speckle server, same testing boundary as the rest of `speckle_io.py`. |
| 2026-08-12 | **Switched tooling to uv** (team preference — `uv.lock` was already committed but unused by the actual build/CI path). `pyproject.toml` gained a `[build-system]` table (was missing entirely — `pip install .` was relying on an undocumented legacy pip fallback). Dockerfile now installs uv and runs `uv sync --frozen --no-dev` into the system interpreter (`UV_PROJECT_ENVIRONMENT=/usr/local`) instead of `pip install .`, so `python main.py` keeps working unchanged inside the container while the build now actually respects the lockfile. CI workflow (`.github/workflows/main.yml`) switched from `actions/setup-python` + `pip install .[dev]` to `astral-sh/setup-uv` + `uv sync --frozen`, with the schema-extraction step now `uv run python main.py generate_schema ...`. README's dev setup now leads with `uv sync`. Couldn't run a full `uv sync` in the validation sandbox — no network access to github.com (where uv fetches Python builds from) — confirmed uv at least accepts the project and resolves correctly against an existing interpreter modulo the Python-version floor; real validation of `uv sync --frozen` should happen on an actual dev machine or in CI. |
