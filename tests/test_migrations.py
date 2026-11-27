"""Tests for version-controlled SQL migrations and the migration runner."""

from __future__ import annotations

import os
from pathlib import Path

import psycopg
import pytest

from scripts.migrate import apply_migrations, discover_migrations


def test_migration_files_are_ordered_and_non_empty() -> None:
    """Repository migrations must follow NNNN_name.sql ordering and be non-empty."""
    migrations = discover_migrations()
    assert len(migrations) >= 2
    versions = [m.version for m in migrations]
    assert versions == sorted(versions)
    assert versions[0].startswith("0001_")
    assert versions[1].startswith("0002_")


def test_discover_migrations_rejects_bad_filename(tmp_path: Path) -> None:
    """Invalid filenames must fail discovery rather than applying out-of-order SQL."""
    bad = tmp_path / "bad_name.sql"
    bad.write_text("SELECT 1;", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid migration filename"):
        discover_migrations(tmp_path)


def test_migrations_apply_and_are_idempotent_against_postgres(tmp_path: Path) -> None:
    """Integration test against real PostgreSQL when DATABASE_URL is provided."""
    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        pytest.skip("DATABASE_URL not set; skipping live PostgreSQL migration test")

    # Reset public schema tables cleanly for a deterministic local/CI test run
    with psycopg.connect(database_url) as conn:
        with conn.transaction():
            conn.execute(
                """
                DROP TABLE IF EXISTS specimens CASCADE;
                DROP TABLE IF EXISTS standard_fractals CASCADE;
                DROP TABLE IF EXISTS schema_migrations CASCADE;
                """
            )

    first_run = apply_migrations(database_url)
    assert first_run == ["0001_initial_schema", "0002_seed_reference_data"]

    second_run = apply_migrations(database_url)
    assert second_run == []

    with psycopg.connect(database_url) as conn:
        specimens_count = conn.execute("SELECT COUNT(*) FROM specimens").fetchone()[0]
        fractals_count = conn.execute("SELECT COUNT(*) FROM standard_fractals").fetchone()[0]
        assert specimens_count == 12
        assert fractals_count == 5

    # Copy migrations and tamper with 0001 checksum to prove drift detection
    copied = tmp_path / "migrations"
    copied.mkdir()
    for mig in discover_migrations():
        (copied / mig.path.name).write_text(mig.sql, encoding="utf-8")
    (copied / "0001_initial_schema.sql").write_text("-- tampered\nSELECT 1;", encoding="utf-8")

    with pytest.raises(RuntimeError, match="Checksum mismatch"):
        apply_migrations(database_url, copied)
