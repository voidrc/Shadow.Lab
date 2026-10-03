"""Shared test fixtures."""
import os
from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def _isolated_db(tmp_path, monkeypatch):
    """Use a temporary SQLite database for each test.

    Recreates the engine and session factory rather than deleting modules,
    so that module-level patches (e.g. check_tailscale) keep working.
    """
    db_path = tmp_path / "test.db"
    db_url = f"sqlite:///{db_path}"
    monkeypatch.setenv("DATABASE_URL", db_url)

    # Recreate the engine and session factory with the new URL
    from app import database
    from app.config import settings as _old_settings

    # Build a new Settings with the test DB URL
    import dataclasses
    new_settings = dataclasses.replace(_old_settings, database_url=db_url)
    # Patch the module-level settings so config.settings points to the test config
    import app.config
    monkeypatch.setattr(app.config, "settings", new_settings)

    # Recreate engine
    new_engine = database._make_engine(db_url)
    new_session = database.sessionmaker(bind=new_engine, expire_on_commit=False, future=True)
    monkeypatch.setattr(database, "engine", new_engine)
    monkeypatch.setattr(database, "SessionLocal", new_session)

    # Also patch get_session to use the new session
    from contextlib import contextmanager
    @contextmanager
    def new_get_session():
        session = new_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    monkeypatch.setattr(database, "get_session", new_get_session)

    yield


@pytest.fixture(autouse=True)
def _mock_tailscale():
    """Mock the Tailscale check so the lifespan doesn't hang on subprocess calls."""
    state = {"healthy": True, "message": "mocked; 100.64.0.1", "checked_at": "now"}
    with patch("app.main.check_tailscale", return_value=state):
        yield
