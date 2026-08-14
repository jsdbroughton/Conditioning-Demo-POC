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
- **Registered function ID**: `0497988d3f`, under the [`tcco` (Turner Construction) workspace](https://app.speckle.systems/workspaces/tcco/functions) on `app.speckle.systems`.
- **POC deployment**: 5 automations (one per model) on the [Henry Ford Wall Takeoff](https://app.speckle.systems/projects/0b23109140) project, deployed and re-deployable via the sibling `Deploy Functions to Projects` tool's `manifests/turner.yaml` spec — see that project's README for the deployment log (`logs/0b23109140.jsonl`).
- **Runtime resources**: declared at publish time via `speckle_function_recommended_cpu_m` / `speckle_function_recommended_memory_mi` in `main.yml` (currently 4000m CPU / 4000Mi memory) — see `.github/workflows/main.yml`.

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
5. Rates every wall **Tier 0 / 1 / 2 / 3** — one unified scale for "how much
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

### Output

- A namespaced property (default key `Conditioned UF Code` — see "Using this
  function" below) written onto every wall object in a new version pushed to
  `Conditioned/<source model name>`. Already-correct (Tier 0) walls get
  `Status`, `Level 4 Code`, `Tier`. Predicted (Tier 1–3) walls additionally
  get `Confidence`, `Method`, and `Original Code` (the prior legacy code, or
  `null` if the wall was blank).
- Per-object viewer annotations (info for existing/high-confidence
  predictions, warnings for Tier 3) so results are visible without opening
  the properties panel.
- A markdown conditioning report (`conditioning_report.md`) attached as a
  run artifact, with a full breakdown by category, method, tier, and a
  dedicated "Needs a Closer Look (Tier 3)" section.
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
2026-08-14 because it described itself as gating a prediction *model* (there
isn't one, just a same-run similarity heuristic — see
`codes.SIMILARITY_MATCH_THRESHOLD`) and had no observable effect on any real
run: see that constant's comment in `codes.py` for the full reasoning. The
property-name input replaced it as the one input that actually changes
something visible on every run.

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
  codes.py                    — ACME code reference data, tier thresholds, format detection
  walls.py                    — WallRecord extraction from Speckle DataObjects, classify_walls()
  predict.py                  — Prediction engine: similarity match + heuristic fallback
  report.py                   — Markdown conditioning report builder
  speckle_io.py                — Everything that writes back to Speckle (imprint/annotate/version)
tests/                        — Offline unit tests (no live Speckle calls; hand-rolled fakes)
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
