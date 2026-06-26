"""Shared database configuration for TechJob AI runtime services.

End users never connect to the warehouse directly. Frontend calls FastAPI,
and FastAPI/AI tools read these server-side environment variables.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote_plus

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*_args, **_kwargs):
        return False


PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class DatabaseConfig:
    host: str
    port: int
    dbname: str
    user: str
    password: str
    sslmode: str
    source: str


def get_database_config() -> DatabaseConfig:
    """Return the DB config used by API, MCP, ML, and embedding code.

    NEON_* wins when present so production/cloud runtime only needs one set of
    variables. POSTGRES_* remains supported for local Docker development.
    """
    use_neon = bool(os.getenv("NEON_HOST"))

    if use_neon:
        return DatabaseConfig(
            host=os.getenv("NEON_HOST", ""),
            port=int(os.getenv("NEON_PORT", "5432")),
            dbname=os.getenv("NEON_DB", "neondb"),
            user=os.getenv("NEON_USER", ""),
            password=os.getenv("NEON_PASSWORD", ""),
            sslmode=os.getenv("NEON_SSLMODE", "require"),
            source="neon",
        )

    return DatabaseConfig(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        dbname=os.getenv("POSTGRES_DB", "techjob_ai"),
        user=os.getenv("POSTGRES_USER", "techjob"),
        password=os.getenv("POSTGRES_PASSWORD", "techjob123"),
        sslmode=(
            os.getenv("POSTGRES_SSLMODE")
            or os.getenv("PGSSLMODE")
            or "prefer"
        ),
        source="postgres",
    )


def psycopg2_kwargs(**extra) -> dict:
    cfg = get_database_config()
    return {
        "host": cfg.host,
        "port": cfg.port,
        "user": cfg.user,
        "password": cfg.password,
        "dbname": cfg.dbname,
        "sslmode": cfg.sslmode,
        **extra,
    }


def psycopg3_kwargs(**extra) -> dict:
    cfg = get_database_config()
    return {
        "host": cfg.host,
        "port": cfg.port,
        "user": cfg.user,
        "password": cfg.password,
        "dbname": cfg.dbname,
        "sslmode": cfg.sslmode,
        **extra,
    }


def sqlalchemy_url(driver: str = "postgresql+psycopg2") -> str:
    cfg = get_database_config()
    user = quote_plus(cfg.user)
    password = quote_plus(cfg.password)
    host = cfg.host
    dbname = quote_plus(cfg.dbname)
    return (
        f"{driver}://{user}:{password}@{host}:{cfg.port}/{dbname}"
        f"?sslmode={quote_plus(cfg.sslmode)}"
    )


def public_config() -> dict:
    """Safe DB metadata for health checks/logging. Never includes password."""
    cfg = get_database_config()
    return {
        "source": cfg.source,
        "host": cfg.host,
        "port": cfg.port,
        "database": cfg.dbname,
        "user": cfg.user,
        "sslmode": cfg.sslmode,
    }
