# We use the official Python 3.14 image as our base image and will add our code to it. For more details, see https://hub.docker.com/_/python
FROM python:3.14-slim

# uv — see https://docs.astral.sh/uv/guides/integration/docker/
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# We set the working directory to be the /home/speckle directory; all of our files will be copied here.
WORKDIR /home/speckle

# Copy everything first, then install. This project uses a src/ layout —
# `uv sync` builds and installs the local `conditioning` package (not just
# third-party deps), which requires src/conditioning to already be present.
# Installing before copying the full source (as a pure dependency-caching
# optimisation would) would silently produce an image with no `conditioning`
# package on the path, breaking the function at runtime.
# This assumes that the Dockerfile is in the same directory as the rest of the code
COPY . /home/speckle

# Install into the system interpreter rather than a project-local .venv, so
# `python main.py` (what Speckle Automate and the CI workflow both invoke
# directly) keeps working unchanged with no `uv run` wrapper needed.
ENV UV_PROJECT_ENVIRONMENT=/usr/local

# --frozen: install exactly what's pinned in uv.lock, don't re-resolve — a
# build should fail loudly if the lock is stale rather than silently drift.
# --no-dev: production dependencies only (mypy/pytest/ruff/openpyxl stay out
# of the deployed image).
RUN uv sync --frozen --no-dev
