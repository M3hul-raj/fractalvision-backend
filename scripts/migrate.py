"""Transactional SQL migration runner for local dev and CI PostgreSQL."""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import psycopg

DEFAULT_MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"
_FILENAME_RE = re.compile(r"^\d{4}_[a-z0-9_]+\.sql$")


@dataclass(frozen=True)
class MigrationFile:
    """Represents a single ordered SQL migration file on disk."""

    version: str
    path: Path
    sql: str
    checksum: str


def discover_migrations(migrations_dir: Path = DEFAULT_MIGRATIONS_DIR) -> list[MigrationFile]:
    """Load and validate ordered NNNN_name.sql files from *migrations_dir*."""
    if not migrations_dir.is_dir():
        raise FileNotFoundError(f"Migrations directory not found: {migrations_dir}")

    files: list[MigrationFile] = []
    for path in sorted(migrations_dir.glob("*.sql")):
        if not _FILENAME_RE.match(path.name):
            raise ValueError(
                f"Invalid migration filename {path.name!r}: expected NNNN_description.sql"
            )
        sql = path.read_text(encoding="utf-8")
        if not sql.strip():
            raise ValueError(f"Migration file {path.name!r} is empty")
        checksum = hashlib.sha256(sql.encode("utf-8")).hexdigest()
        files.append(
            MigrationFile(
                version=path.stem,
                path=path,
                sql=sql,
                checksum=checksum,
            )
        )
    return files


def apply_migrations(
    database_url: str,
    migrations_dir: Path = DEFAULT_MIGRATIONS_DIR,
) -> list[str]:
    """Apply pending migrations inside transactions and record checksums.

    Returns the list of newly applied migration version strings.
    """
    migrations = discover_migrations(migrations_dir)
    newly_applied: list[str] = []

    with psycopg.connect(database_url) as conn:
        with conn.transaction():
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version    TEXT PRIMARY KEY,
                    checksum   TEXT NOT NULL,
                    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )

        rows = conn.execute("SELECT version, checksum FROM schema_migrations").fetchall()
        applied = {version: checksum for version, checksum in rows}

        for mig in migrations:
            if mig.version in applied:
                if applied[mig.version] != mig.checksum:
                    raise RuntimeError(
                        f"Checksum mismatch for already-applied migration {mig.version!r}: "
                        f"expected {applied[mig.version]}, got {mig.checksum}"
                    )
                continue

            with conn.transaction():
                conn.execute(mig.sql)
                conn.execute(
                    "INSERT INTO schema_migrations (version, checksum) VALUES (%s, %s)",
                    (mig.version, mig.checksum),
                )
            newly_applied.append(mig.version)

    return newly_applied


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for applying local/CI SQL migrations."""
    parser = argparse.ArgumentParser(description="Apply versioned SQL migrations to PostgreSQL.")
    parser.add_argument(
        "--database-url",
        default=os.getenv("DATABASE_URL", ""),
        help="PostgreSQL connection string (defaults to DATABASE_URL env var).",
    )
    parser.add_argument(
        "--migrations-dir",
        type=Path,
        default=DEFAULT_MIGRATIONS_DIR,
        help="Directory containing ordered .sql migrations.",
    )
    args = parser.parse_args(argv)

    if not args.database_url:
        print("ERROR: DATABASE_URL is not set.", file=sys.stderr)
        return 1

    applied = apply_migrations(args.database_url, args.migrations_dir)
    if applied:
        print(f"Applied migrations: {', '.join(applied)}")
    else:
        print("Database schema is already up to date.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
