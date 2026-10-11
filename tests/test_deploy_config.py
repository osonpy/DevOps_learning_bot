"""docker-compose.yml va .env.example: deploy xavfsizligi qoidalari."""
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
COMPOSE = yaml.safe_load((ROOT / "docker-compose.yml").read_text(encoding="utf-8"))
SERVICES = COMPOSE["services"]


def env_example() -> dict[str, str]:
    pairs = {}
    for line in (ROOT / ".env.example").read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.lstrip().startswith("#"):
            k, _, v = line.partition("=")
            pairs[k.strip()] = v.strip()
    return pairs


def test_postgres_password_has_no_fallback():
    assert SERVICES["db"]["environment"]["POSTGRES_PASSWORD"] == "${POSTGRES_PASSWORD:?POSTGRES_PASSWORD kerak}"


def test_database_url_built_from_postgres_vars():
    url = SERVICES["bot"]["environment"]["DATABASE_URL"]
    assert "${POSTGRES_PASSWORD:?" in url and "${POSTGRES_USER" in url and "${POSTGRES_DB" in url
    assert "@db:5432/" in url


def test_env_example_has_password_once_and_placeholder():
    env = env_example()
    assert env["POSTGRES_PASSWORD"] == "CHANGE_ME"
    assert "DATABASE_URL" not in env  # parol ikki marta yozilmasin
    assert "openssl rand -base64 32" in (ROOT / ".env.example").read_text(encoding="utf-8")


def test_migrate_is_one_shot_service_before_bot():
    migrate = SERVICES["migrate"]
    assert migrate["image"] == SERVICES["bot"]["image"]
    cmd = " ".join(migrate["command"]) if isinstance(migrate["command"], list) else migrate["command"]
    assert "alembic upgrade head && python -m src.scripts.seed" in cmd
    assert migrate["restart"] == "no"
    assert migrate["depends_on"]["db"]["condition"] == "service_healthy"
    assert SERVICES["bot"]["depends_on"]["migrate"]["condition"] == "service_completed_successfully"


def test_bot_image_does_not_migrate_on_start():
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert "ENTRYPOINT" not in dockerfile and "docker-entrypoint" not in dockerfile
    assert not (ROOT / "docker-entrypoint.sh").exists()


def test_postgres_image_pinned_by_digest():
    image = SERVICES["db"]["image"]
    assert image.startswith("postgres:16-alpine@sha256:") and len(image.split("@sha256:")[1]) == 64


def test_db_has_memory_limit():
    assert SERVICES["db"]["deploy"]["resources"]["limits"]["memory"]
