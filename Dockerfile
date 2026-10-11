# syntax=docker/dockerfile:1
# ---------- builder: uv bilan .venv tayyorlaymiz ----------
FROM python:3.12-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:0.13.0 /uv /bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0
WORKDIR /app

# Faqat lock o'zgarsa qayta quriladi (kod o'zgarishi bu qatlamni buzmaydi)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-dev --no-install-project

# ---------- runtime: faqat .venv va kod ----------
FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"
WORKDIR /app

RUN groupadd --system app && useradd --system --gid app --home /app app

COPY --from=builder /app/.venv /app/.venv
COPY --chown=app:app alembic.ini ./
COPY --chown=app:app migrations ./migrations
COPY --chown=app:app content ./content
COPY --chown=app:app src ./src

USER app
# Migratsiya va seed — alohida `migrate` servisi (docker-compose.yml)
CMD ["python", "-m", "src.main"]
