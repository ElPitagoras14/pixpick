FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:0.10.9 /uv /uvx /bin/

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

# Install dependencies before copying the source so this layer only
# rebuilds when pyproject.toml/uv.lock change, not on every code edit.
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-install-project

COPY src ./src
RUN uv sync --locked

EXPOSE 8000

# Runs main.py itself instead of the `uvicorn` CLI (see its own
# `if __name__ == "__main__":` block): that's what lets it hand uvicorn
# the loop factory Windows native mode needs directly, with no `--loop`
# flag to remember here or in README.md.
CMD ["python", "-m", "src.main"]
