# Conditioning Demo POC

A Speckle Automate function, built for Turner, that predicts [Uniformat
Assembly Codes](https://en.wikipedia.org/wiki/Uniformat) for Revit wall and
curtain-wall elements — specifically Turner's own Level 4 dot-notation
sub-codes (e.g. `B2010.10`, `C1010.40`), using their Estimate Detail
Structure as the reference code set.

## What it does

On every triggered version, the function:

1. Collects all `Walls` + curtain wall family elements (`Curtain Systems`,
   `Curtain Panels`, `Curtain Wall Mullions` — Revit models these as separate
   categories from `Walls`).
2. Classifies each one: already a Turner Level 4 code, a legacy/non-Turner
   code (e.g. an ASTM Uniformat II 3-digit suffix like `B2010160`), or blank.
3. Predicts a Level 4 code for everything that isn't already one — via
   similarity matching against other already-coded walls where possible,
   falling back to a heuristic reading of the wall's own Revit category,
   `Function` parameter, and type name/family keywords.
4. Auto-applies every prediction. Nothing is left untouched or silently
   dropped — a wall with an existing legacy code keeps it recorded as
   `Original Code` alongside the new prediction.
5. Rates every prediction **Tier 1 / 2 / 3** based on confidence:
   - **Tier 1** — high confidence, candidate for auto-accept (an
     authoritative signal like Revit's own category assignment, or two or
     more independent signals on the same wall agreeing).
   - **Tier 2** — medium confidence, propagate but flag for a quick check.
   - **Tier 3** — low/no confidence (a coin-toss single signal, conflicting
     signals, or no signal at all) — genuinely needs a human to look at it.

   Tiers are recorded on every object but not currently used to gate
   anything — that's the direction of travel, not yet implemented.

### Output

- A **`Turner UF Code`** property (namespaced dict — `Status`, `Level 4
  Code`/`Level 4 Code Predicted`, `Confidence`, `Tier`, `Method`, `Original
  Code`) written onto every wall object in a new version pushed to
  `Conditioned/<source model name>`.
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
4. Optionally adjust **Confidence Threshold** (0–1, default `0.65`) — the
   minimum similarity score accepted for a model-based prediction before it
   falls back to the heuristic. It does not affect the heuristic's own
   confidence/tier values.
5. Click `Create Automation`.

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
  codes.py                    — Turner code reference data, tier thresholds, format detection
  walls.py                    — WallRecord extraction from Speckle DataObjects, classify_walls()
  predict.py                  — Prediction engine: similarity match + heuristic fallback
  report.py                   — Markdown conditioning report builder
  speckle_io.py                — Everything that writes back to Speckle (imprint/annotate/version)
tests/                        — Offline unit tests (no live Speckle calls; hand-rolled fakes)
fixtures/                     — Source Turner Uniformat spreadsheet (guards TURNER_CODES against drift)
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
- Dev tools: `mypy`, `ruff`, `pytest`, `openpyxl` (reads the Turner reference
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

All tests are offline — they exercise `src/conditioning` directly against
hand-rolled fake Speckle objects, no live server call required. `tests/
test_turner_codes_fixture.py` is the one exception in spirit: it doesn't call
Speckle, but it does open the source `fixtures/Turner - Uniformat Estimate
Detail Structure.xlsx` spreadsheet and diffs it against the hardcoded
`TURNER_CODES` dict in `codes.py`, so that dict can't silently drift from
Turner's own reference data.

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
    '{"confidence_threshold": 0.65}' \
    yourSpeckleServerAuthenticationToken
    ```

Let's explain this in more detail:

`docker run --rm conditioning-demo-poc` tells Docker to run the Docker Container Image we built earlier. `conditioning-demo-poc` is the name of the Docker Container Image. The `--rm` flag tells Docker to remove the container after it has finished running, freeing up space on your machine.

The line `python -u main.py run` is the command run inside the Docker Container Image. The rest of the command is the arguments passed to the command. The arguments are:

- `'{"projectId": "1234", ...}'` - the metadata that describes the automation and the function.
- `'{"confidence_threshold": 0.65}'` - the function's input parameters. `confidence_threshold` (0–1, default `0.65`) is the minimum similarity score accepted for a model-based prediction before it falls back to the heuristic; it does not affect the heuristic's own `METHOD_CONFIDENCE`/tier values.
- `yourSpeckleServerAuthenticationToken` — the authentication token for the Speckle Server that the Automation can connect to. This is required to interact with the Speckle Server, for example, to get data from the Model.

To ship a code change, create a new [GitHub release](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository) in this repository — that's what publishes a new Function version to Automate.

## Resources

- [Learn](https://speckle.guide/dev/python.html) more about SpecklePy and interacting with Speckle from Python.
- `docs/NOTES.md` — full development log for this project: every bug found, direction change, and the reasoning behind current thresholds/behaviour.
