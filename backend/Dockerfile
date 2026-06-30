# syntax=docker/dockerfile:1

FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# uv for fast, reproducible installs
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# Install deps in a separate layer so code edits don't reinstall packages.
# Dev tools (pytest, ruff, ...) are included by default so tests and lint run
# in-container per the README; set INSTALL_DEV=0 for a lean production image.
COPY pyproject.toml ./
ARG INSTALL_DEV=1
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system . \
    && if [ "$INSTALL_DEV" = "1" ]; then uv pip install --system --group dev; fi

# Bake the multilingual embedding model into the image so the first match
# isn't blocked on a download. Set BAKE_MODEL=0 for faster local rebuilds
# (the model is downloaded lazily on first use instead).
ARG BAKE_MODEL=1
RUN --mount=type=cache,target=/root/.cache/huggingface \
    if [ "$BAKE_MODEL" = "1" ]; then \
      python -c "from model2vec import StaticModel; \
        StaticModel.from_pretrained('minishlab/potion-multilingual-128M')"; \
    fi

COPY . .

# Use sh explicitly so dev volume mounts (./backend:/app) work even when the
# host file lacks the executable bit.
ENTRYPOINT ["sh", "./entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
