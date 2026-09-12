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

# uvicorn directly instead of `fastapi run`: the latter doesn't expose
# --loop, which src/loop.py needs to keep native mode working on Windows
# (see that module's docstring).
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--loop", "src.loop:loop_factory"]
