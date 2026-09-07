# Conditioning Demo POC

A Speckle Automate function, built for a construction firm (anonymized here
as "ACME Studios" — see `docs/NOTES.md` for the 2026-08-14 anonymization
pass), that predicts [Uniformat Assembly
Codes](https://en.wikipedia.org/wiki/Uniformat) for Revit wall and
curtain-wall elements — specifically that firm's own Level 4 dot-notation
sub-codes (e.g. `B2010.10`, `C1010.40`), using their Estimate Detail
Structure as the reference code set.

## Where this function lives

- **Source**: [`jsdbroughton/Conditioning-Demo-POC`](https://github.com/jsdbroughton/Conditioning-Demo-POC) on GitHub. Publishing a new version is done by cutting a [GitHub release](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository) — see `.github/workflows/main.yml`.
- **Registered function**: published to the client's own workspace on `app.speckle.systems`. The function ID, workspace slug and project IDs are deployment details rather than source, and are deliberately not recorded here — see "A note on client details" below.
- **POC deployment**: 5 automations, one per source model, deployed and re-deployable via the sibling `Deploy Functions to Projects` tool's per-client manifest spec — see that project's README for the deployment log.
- **Runtime resources**: declared at publish time via `speckle_function_recommended_cpu_m` / `speckle_function_recommended_memory_mi` in `main.yml` (currently 4000m CPU / 4000Mi memory) — see `.github/workflows/main.yml`.

## A note on client details

This repository is shareable and must stay that way. It carries **no client
name, no project or building name, no workspace slug, and no live Speckle
project, model, version or function ID.** The reference code data in
`codes.py` is real — that is the classification the function needs to work —
but it is attributed to the fictional "ACME Studios", and the source
spreadsheet in `fixtures/` has had its document metadata cleared.

This is easy to undo by accident. An earlier pass scrubbed the repo
thoroughly, and a later commit adding deployment documentation reintroduced a
client name, a building name, a workspace URL and two live IDs in a single
section — none of which the source needs in order to build, run or be
understood. Deployment specifics belong in the deployment tooling, not here.

Worth checking before any commit that touches documentation:

```bash
grep -rEi "client-name|building-name|workspace-slug" --include=*.md --include=*.py .
```

## What it does

On every triggered version, the function:

1. Collects all `Walls` + curtain wall family elements (`Curtain Systems`,
   `Curtain Panels`, `Curtain Wall Mullions` — Revit models these as separate
   categories from `Walls`).
2. Classifies each one: already an ACME Level 4 code, a legacy/non-ACME
   code (e.g. an ASTM Uniformat II 3-digit suffix like `B2010160`), or blank.
3. Predicts a Level 4 code for everything that isn't already one — via
   similarity matching against other already-coded walls where possible,
   falling back to a heuristic reading of the wall's own Revit category,
   `Function` parameter, and type name/family keywords.
4. Auto-applies every prediction. Nothing is left untouched or silently
   dropped — a wall with an existing legacy code keeps it recorded as
   `Original Code` alongside the new prediction.
5. Reads **fire rating, wall tag, height, acoustic rating and stud size**
   for each wall. Fire rating and wall tag prefer the wall's own Revit
   parameters (`Fire Rating`, `Type Mark` — verified 2026-09-07 against live
   Turner models). All Revit parameter reads — including `Function`,
   `Assembly Code`, `Width` and `Unconnected Height` — go through
   `walls._param()`/`_param_double()`, which try both the
   `Parameters.Instance Parameters.<Group>.<Param>` and
   `Parameters.Type Parameters.<Group>.<Param>` fully-qualified paths this
   connector's bundle export actually uses; a bare `<Group>.<Param>` path
   never matches either table and silently returns nothing (fixed
   2026-09-07 — see `docs/NOTES.md`, this had been quietly sending every
   interior wall through the "no signal" fallback and onto an exterior-wall
   code). Fire rating and wall tag fall back to the element type name only
   where the parameter is blank; acoustic rating and stud size still come
   from the type name (a type called
   `Type H6 - Single Layer GWB - SMOKE - STC-35 - 6" Stud` yields
   `SMOKE · STC-35 · 6" Stud`). Height is read per-instance from
   `Unconnected Height` and rounded to the nearest foot, so two walls at
   3000mm and 3005mm read as one 10' entry while 4500mm reads as 15' — see
   `attributes.bucket_height_ft`. Where neither a parameter nor the name
   yields a value, the property is simply absent rather than guessed, and
   each run reports its own coverage so you can tell which case you're in.
   See `attributes.py`.
6. **Groups similar element types** within each Level 4 code, so a code
   covering thousands of walls breaks into recognisable families — at
   **three granularities**, not one, because a group can honestly be more
   or less coarse depending on the question being asked:
   - **Coarse** — pure type-name similarity, deliberately blind to fire
     rating, acoustic rating and height. Answers "which architect types
     basically resemble each other at all." Can span a fire-rating or
     acoustic boundary — see "What this cannot do" below — which is exactly
     why the finer tiers exist rather than a reason to drop this one.
   - **Fire/Acoustic** — each coarse cluster re-partitioned by (Fire
     Rating, Acoustic STC), because the estimators who cost these groups
     need those two to come out as different costs, and name-similarity
     alone cannot guarantee that.
   - **Full** — each Fire/Acoustic slice re-partitioned again by a
     **height band** (short: under 4'; standard: 4' up to 6m/~19'8"; tall:
     over 6m). This is an **opinionated, unvalidated-against-Turner's-own-
     pricing** stand-in for where an interior stud wall typically needs a
     heavier gauge or added bracing — picked to unblock delivery without a
     follow-up call, not measured against this client's numbers. Correct
     `attributes.HEIGHT_BAND_SHORT_MAX_MM`/`HEIGHT_BAND_TALL_MIN_MM` the
     moment real thresholds are known.

   A finer tier only grows a row distinct from its parent where that tier's
   split actually found more than one value — a coarse cluster already
   uniform on fire/acoustic/height never gains a meaningless sub-row, so a
   wall's key stays as coarse as it honestly can. Within any tier,
   remaining type-name variation is still what serves models whose naming
   carries no other convention at all (`CW_Unitized_Spandrel`, `CW1D`,
   `20d panel`). Every row also reports a plain-English **description**
   and, where present, the distinct Type Marks / Stud Sizes its members
   carry — one value where the row's members agree, `varies (...)` listing
   every value where they don't (a real cluster of near-identical type
   names has been seen spanning six different Type Marks, so "varies" is
   the norm for Type Mark/Stud Size on a large group, not an edge case —
   Fire Rating, Acoustic STC and Height Band, by contrast, are guaranteed
   uniform on a **Full**-tier row by construction; "varies" on any of those
   three can only appear on a coarser row). Groups are our observation, not
   a classification, and Type Mark cannot become a group's *identity* for
   the same reason — see the caveat in "Output" below and `grouping.py`.
7. Records, on every element, **whether the model authored the code or the
   function derived it** (`Requires Verification`), and in plain terms
   **what evidence it was derived from** (`Level 4 Code Source`).
8. Rates every wall **Tier 0 / 1 / 2 / 3** — one unified scale for "how much
   attention does this element need," covering both already-correct and
   predicted walls:
   - **Tier 0** — no work to be done. The wall already carried a genuine
     ACME Level 4 code; nothing was predicted.
   - **Tier 1** — high confidence, candidate for auto-accept (an
     authoritative signal like Revit's own category assignment, or two or
     more independent signals on the same wall agreeing).
   - **Tier 2** — medium confidence, propagate but flag for a quick check.
   - **Tier 3** — the bottom: not enough confidence to trust. Two different
     things land here — genuinely no signal at all (nothing about the wall
     resembled anything else in the model), or a signal that did fire but is
     a lone coin-toss keyword match or actively contradicts another signal
     on the same wall. Either way, genuinely needs a human to look at it.

   Tiers are recorded on every object but not currently used to gate
   anything — that's the direction of travel, not yet implemented.

   **Tier is not the same question as `Requires Verification`.** Tier asks
   how confident we are that a code is right; `Requires Verification` asks
   whether the building told us or the function worked it out. A
   high-confidence result still needs a person to accept it. Keeping them
   apart matters: on one real model 91% of elements sat at Tier 1, including
   an element whose type name was literally `Empty`, so reading Tier alone
   as "already checked" would be badly wrong.

### Output

A single namespaced property (default key `Conditioned UF Code` — see "Using
this function" below) written onto every wall object. Everything goes in
that one dict: one place to look in the viewer, one thing to select in Power
BI, and no chance of colliding with a real Revit parameter name.

That property lands in **two** new versions per run, published from the same
`create_conditioned_version()` call (2026-09-07, later still) — check either
independently, since one can publish without the other:

- **`Conditioned/Walls/<source model name>`** — every conditioned wall and curtain-wall/
  curtain-panel element, nothing else. Smaller and faster to open when the
  only question is what conditioning did to the walls.
- **`Conditioned/All/<source model name>`** — a genuine like-for-like republish of the
  *entire* received scene (doors, floors, rooms, MEP, stairs, everything),
  with each conditioned wall's result patched onto its own properties and
  the original collection hierarchy, level, material and color carried over.
  This is the one that looks like the source model, not a walls-only subset
  of it — added because the walls-only model, for a while the only output,
  read as data loss to a reviewer opening it directly rather than through
  the run report's merged viewer. Geometry is copied structurally
  (definitions and placements rebuilt, not flattened — the first cut put
  every instanced door/panel/equipment item at the origin). Every object
  the function did *not* classify carries the same namespaced property
  with either a derived code or `Status: not conditioned` — so nothing in
  this model is silently blank. Non-wall objects are coded by the
  **category engine** (`categories.py`): the wall engine's own mechanism —
  every independent signal collected (Revit category, `Function`, a
  type-name keyword, the section of any existing Assembly Code, and the
  nearest already-coded neighbour of the same category), strongest decides,
  agreement lifts confidence and contradiction lowers it, same constants —
  applied to a per-category rule table. **That table is a set of judgements
  made without the estimator** (same status as the height bands); every
  result carries `Requires Verification: True` and a plain-English source,
  and the report says so up front. Categories with no rule, or where no
  signal fires (Rooms, Generic Models, unrecognised Mechanical Equipment, a
  Door with no Function and no telling name), stay `not conditioned` rather
  than guessed. Codes come from `acme_reference.py` — the client's full
  structure, 679 codes generated from the fixture spreadsheet. Host/room/connection/assembly
  relationships are not carried over (see `_build_full_bundle()`'s
  docstring in `speckle_io.py`).

The run report's "View Results" viewer loads both, overlaid on the host
model, via `set_context_view`.

| Key | On | Meaning |
|-----|-----|---------|
| `Status` | all | `existing` (model already had a valid code), `predicted`, or — on non-wall objects in `Conditioned/All/…` that no rule could place — `not conditioned` |
| `Level 4 Code` | all | The code the element ends up carrying |
| `Level 4 Code Description` | all | ACME's own description text for that code, straight from the Estimate Detail Structure (e.g. `Exterior Wall Veneer`) |
| `Level 4 Code Source` | all | Plain English: authored by the model, or derived by the function and from what evidence |
| `Requires Verification` | all | `False` only where the model authored a valid code — today `True` on everything |
| `Tier` | all | Tier 0–3, see above |
| `Confidence` | predicted | 0.0–0.95 |
| `Method` | predicted | `heuristic_category`, `heuristic_function`, `similarity`, … |
| `Original Code` | predicted | The prior legacy code, or `null` if the element was blank |
| `Observed Type Attributes` | where named | e.g. `SMOKE · STC-35 · 6" Stud` |
| `Observed Fire Rating` / `Observed Acoustic STC` / `Observed Stud Size` | where named | The same three, separately, for filtering |
| `Observed Fire Rating Source` | where a fire rating is present | `parameter` or `name` — which one it was read from |
| `Observed Wall Tag` | where the wall has a Type Mark | The wall's own `Type Mark`, e.g. `H6` |
| `Observed Height` | where the wall has an `Unconnected Height` | Rounded to the nearest foot, e.g. `10'` — a per-instance value, not part of `Observed Type Attributes` |
| `Observed Height Band` | where the wall has an `Unconnected Height` | `short (<4')`, `standard`, or `tall (>6m)` — the same height read as the band the `Full`-tier group hard-splits on, see `attributes.height_band` |
| `Inferred Type Group` | all | The **Full**-tier group — the most specific of the three, e.g. `C1010.10 · inferred group A2a`. This is the group actually guaranteed never to mix two differently fire-rated, differently-acoustic-rated or differently-heighted walls |
| `Inferred Group Label` / `Inferred Group Size` | all | What the Full-tier group's members share, and how many elements |
| `Inferred Type Group (Coarse)` / `Inferred Group Label (Coarse)` | all | The same wall's **Coarse**-tier group — pure name similarity, e.g. `C1010.10 · inferred group A` — for rolling up to "which architect types basically resemble each other" regardless of fire/acoustic/height |
| `Inferred Type Group (Fire/Acoustic)` / `Inferred Group Label (Fire/Acoustic)` | all | The same wall's **Fire/Acoustic**-tier group, e.g. `C1010.10 · inferred group A2` — Coarse re-split by (Fire Rating, Acoustic STC) only, before height |
| `Inferred Group Description` | all | Plain-English rollup for the Full-tier group, e.g. `5 elements — Type Mark H6, Fire Rating SMOKE, Acoustic STC 35, Stud Size 6, Height Band standard` |
| `Inferred Group Wall Tags` / `Fire Ratings` / `Acoustic STC` / `Stud Sizes` / `Height Bands` | where the group has any | Comma-joined distinct values across the Full-tier group's members. Wall Tags and Stud Sizes can list several values where members don't agree; Fire Ratings, Acoustic STC and Height Bands are hard-split (2026-09-07 and 2026-09-07 later still), so each of those three always reports exactly one value at this tier — "varies" on any of them is only possible reading the Coarse or Fire/Acoustic keys instead |

**`Observed` and `Inferred` mean different things, deliberately.**
*Observed* values are read from the wall itself — from a real Revit
parameter where one exists (`Fire Rating`, `Type Mark`; `Observed Fire
Rating Source` records which), or transcribed from the architect's own
type name where it doesn't. *Inferred* values are the function's judgement
about which elements resemble each other, at whichever of the three
granularities you read — `Inferred Type Group (Coarse)` is judgement that
can span a Fire Rating, Acoustic STC, Height Band, Type Mark or Stud Size
boundary all at once (it's blind to all five); `(Fire/Acoustic)` still
spans Type Mark, Stud Size and Height Band but never Fire Rating/Acoustic
STC; the default `Inferred Type Group` (Full) never spans any of Fire
Rating, Acoustic STC or Height Band, only Type Mark/Stud Size — which is
exactly what its `Inferred Group *` rollups report ("varies (...)") rather
than hide. Neither `Observed` nor `Inferred` is a client classification,
neither carries any authority, and the letters/digits in a group key are
ours — assigned by size, and they renumber when the model changes.

**Nothing here involves a trained model or any AI service.** The function is
rules over Revit parameters plus a text comparison between elements. No data
leaves Speckle. The word "predicted" is used in its ordinary sense — a rule
mapping evidence to a likely value is making a prediction — and
`Level 4 Code Source` states the mechanism on every element so there is no
room to assume otherwise.
- Per-object viewer annotations (info for existing/high-confidence
  predictions, warnings for Tier 3) so results are visible without opening
  the properties panel.
- A markdown conditioning report (`conditioning_report.md`) attached as a
  run artifact: breakdowns by category, method and tier, a "Needs a Closer
  Look (Tier 3)" section, an "Observed type attributes" section that leads
  with its own coverage percentage, and a "Wall type groups" section. Every
  table is aggregated with a count column rather than one row per element —
  an earlier per-element version ran to 62,000 rows and 10 MB, which nobody
  read and which duplicated data already queryable on the objects
  themselves.
- Per-stage timing and peak memory in the run log, e.g.
  `[ConditioningPOC][timing] create_conditioned_version: 61.2s, peak RSS
  1834 MiB` — so a failed deployment can be attributed rather than guessed
  at.
- The run report's viewer links to both the host model (where the
  interactive per-object annotations resolve) and the new conditioned
  version, via `set_context_view`.

## Using this function

1. [Create](https://automate.speckle.dev/) a new Speckle Automation.
2. Select your Speckle Project and Speckle Model.
3. Select this deployed Function.
4. Optionally set **Conditioned Code Property Name** (default `Conditioned
   UF Code`) — the literal property key written onto every wall object.
   Set this to match your own organisation's naming convention (e.g. a real
   ACME Studios deployment might use `ACME UF Code`).
5. Click `Create Automation`.

An earlier version exposed a "Confidence Threshold" input instead — removed
2026-08-14 because it described itself as gating a prediction *model*, which
overstated what it gated (a same-run similarity comparison — see
`codes.SIMILARITY_MATCH_THRESHOLD`), and because it had no observable effect
on any real run: see that constant's comment in `codes.py` for the full
reasoning. The property-name input replaced it as the one input that
actually changes something visible on every run.

To be precise, since the distinction matters when talking to anyone running
a security review: there is no *trained* model here and nothing is a
language model or an external service. The similarity path is
nearest-neighbour matching against other elements in the same run — an
algorithm with no training phase and no data leaving Speckle.

> This is a proof-of-concept. Every prediction is currently auto-applied
> regardless of tier — Tier 3 results are flagged, not withheld. See "What it
> does" above for the current tiering behaviour.

---

*The sections below are for developers working on this function's code, not
required reading to use it.*

## Project layout

```
main.py                       — Automate function entry point (thin orchestrator only)
src/conditioning/
  codes.py                    — ACME code reference data, tier thresholds, format detection,
                                 plain-English method descriptions
  walls.py                    — WallRecord extraction from Speckle DataObjects, classify_walls()
  predict.py                  — Prediction engine: similarity match + heuristic fallback
  attributes.py               — Fire rating / wall tag (parameter-first, name fallback) / STC /
                                 stud size / height bucketing
  grouping.py                 — Clusters similar element types within each Level 4 code, plus
                                 each group's description and Type Mark/Fire Rating/etc. rollups
  report.py                   — Markdown conditioning report builder
  speckle_io.py                — Everything that writes back to Speckle (imprint/annotate/version)
  instrumentation.py          — Per-stage timing and peak-RSS logging
tests/                        — Offline unit tests (no live Speckle calls; hand-rolled fakes)
  conftest.py                 — --code-property-name option for the live integration run
fixtures/                     — Source Uniformat spreadsheet (guards ACME_CODES against drift)
docs/NOTES.md                 — Running development log — the detailed history of every design
                                 decision, bug found, and direction change on this project
```

For anything not covered here — why a threshold is set where it is, what a
past bug looked like, what's deliberately out of scope for this pass — check
`docs/NOTES.md` first.

## Developer Requirements

We use [uv](https://docs.astral.sh/uv/) for dependency management — it reads
`pyproject.toml` and the committed `uv.lock` directly, so there's no separate
requirements file to keep in sync, and installs are reproducible (`uv.lock`
pins exact versions; `mise.toml` pins the Python version).

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/).
2. Run the following to set up your development environment:
    ```bash
    uv sync
    ```

**What this installs:**
- Production dependencies (currently just `specklepy`)
- Dev tools: `mypy`, `ruff`, `pytest`, `openpyxl` (reads the source reference
  spreadsheet in the fixture-drift test)
- The local `conditioning` package itself (this project uses a `src/` layout —
  see `src/conditioning/__init__.py` for the module map; `main.py` at the repo
  root stays a standalone orchestrator script outside the installed package)

Prefix commands with `uv run` to run them inside the managed environment
without activating it, e.g. `uv run pytest`, `uv run python main.py ...`.

### Adding new dependencies

Edit `pyproject.toml`:

**For packages your function needs to run:**
```toml
dependencies = [
    "specklepy==2026.6.0",
    "pandas==2.1.0",  # Add production dependencies here
]
```

**For development tools** (testing, linting, etc.):
```toml
[project.optional-dependencies]
dev = [
    "mypy==2.3.0",
    "ruff==0.16.2",
    "pytest==9.1.1",  # Add development dependencies here
]
```

**How to decide which section?**
- If `main.py` or anything under `src/conditioning` imports it → `dependencies`
- If it's just a tool to help you code/test → `dev`

Then re-run `uv sync` to update `uv.lock`.

**Why separate `dependencies` / `dev` sections?**
- `dependencies`: what actually ships with the function — this is what
  `uv sync --frozen --no-dev` (and the Dockerfile) install
- `dev`: extra tools to help you write and verify code locally, kept out of
  the deployed image

## Building and Testing

```bash
uv run pytest
```

`pytest tests/` runs offline by default — every test exercises
`src/conditioning` directly against hand-rolled fake Speckle objects, no live
server call required. `tests/test_acme_codes_fixture.py` is one exception in
spirit: it doesn't call Speckle, but it does open the source
`fixtures/ACME Studios - Uniformat Estimate Detail Structure.xlsx`
spreadsheet and diffs it against the hardcoded `ACME_CODES` dict in
`codes.py`, so that dict can't silently drift from the source reference data.

The other exception is real, not in spirit: `tests/test_function.py` makes
an actual live run against whatever project/model/token is configured in
your `.env`, including writing a new `Conditioned/<model>` version. It's
marked `integration` and excluded by the default `addopts` in
`pyproject.toml`, so a bare `pytest`/`pytest tests/` never touches your live
project — run it deliberately with `pytest tests/ -m integration` when you
want to exercise the real end-to-end path.

### Alternative dependency managers

This project uses the standard **PEP 621** format in `pyproject.toml`, which
also works with other dependency managers if you'd rather not use uv — though
note the committed `uv.lock` won't be respected by these, so pinned versions
may drift:

#### Using Poetry
```bash
poetry install  # Automatically reads pyproject.toml
```

#### Using pip-tools
```bash
pip-compile pyproject.toml  # Generate requirements.txt from pyproject.toml
pip install -r requirements.txt
```

#### Using pdm
```bash
pdm install  # Automatically reads pyproject.toml
```

### Building and running the Docker Container Image

Running and testing your code on your machine is a great way to develop your Function; the following instructions are a bit more in-depth and only required if you are having issues with your Function in GitHub Actions or on Speckle Automate.

#### Building the Docker Container Image

The GitHub Action packages your code into the format required by Speckle Automate. This is done by building a Docker Image, which Speckle Automate runs. You can attempt to build the Docker Image locally to test the building process.

To build the Docker Container Image, you must have [Docker](https://docs.docker.com/get-docker/) installed.

Once you have Docker running on your local machine:

1. Open a terminal
2. Navigate to the directory in which you cloned this repository
3. Run the following command:

    ```bash
    docker build -f ./Dockerfile -t conditioning-demo-poc .
    ```

#### Running the Docker Container Image

Once the GitHub Action has built the image, it is sent to Speckle Automate. When Speckle Automate runs your Function as part of an Automation, it will run the Docker Container Image. You can test that your Docker Container Image runs correctly locally.

1. To then run the Docker Container Image, run the following command:

    ```bash
    docker run --rm conditioning-demo-poc \
    python -u main.py run \
    '{"projectId": "1234", "modelId": "1234", "branchName": "myBranch", "versionId": "1234", "speckleServerUrl": "https://speckle.xyz", "automationId": "1234", "automationRevisionId": "1234", "automationRunId": "1234", "functionId": "1234", "functionName": "my function", "functionLogo": "base64EncodedPng"}' \
    '{"code_property_name": "Conditioned UF Code"}' \
    yourSpeckleServerAuthenticationToken
    ```

Let's explain this in more detail:

`docker run --rm conditioning-demo-poc` tells Docker to run the Docker Container Image we built earlier. `conditioning-demo-poc` is the name of the Docker Container Image. The `--rm` flag tells Docker to remove the container after it has finished running, freeing up space on your machine.

The line `python -u main.py run` is the command run inside the Docker Container Image. The rest of the command is the arguments passed to the command. The arguments are:

- `'{"projectId": "1234", ...}'` - the metadata that describes the automation and the function.
- `'{"code_property_name": "Conditioned UF Code"}'` - the function's input parameters. `code_property_name` is optional and defaults to `codes.DEFAULT_CONDITIONING_KEY`; override it to match your organisation's own naming convention (see "Using this function" above).
- `yourSpeckleServerAuthenticationToken` — the authentication token for the Speckle Server that the Automation can connect to. This is required to interact with the Speckle Server, for example, to get data from the Model.

To ship a code change, create a new [GitHub release](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository) in this repository — that's what publishes a new Function version to Automate.

## Resources

- [Learn](https://speckle.guide/dev/python.html) more about SpecklePy and interacting with Speckle from Python.
- `docs/NOTES.md` — full development log for this project: every bug found, direction change, and the reasoning behind current thresholds/behaviour.
- `docs/STATE.md` — current-state snapshot (purpose, main loop, flags, deployment, module map, testing) for anyone getting oriented without reading the full log.
