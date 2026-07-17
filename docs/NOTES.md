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
