import os

# These lines MUST run before the app is imported, so that the tests use a
# separate database and a fake API key, and never touch real data.
os.environ["POSTGRES_DB"] = "leadflow_test"
os.environ["WEBHOOK_API_KEY"] = "test-key-" + "x" * 40

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app import models  # noqa: E402,F401  (registers all tables)
from app.config import settings  # noqa: E402
from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def create_tables():
    # Safety check: never run tests against the real database.
    assert settings.postgres_db == "leadflow_test"
    Base.metadata.create_all(engine)
    yield


@pytest.fixture(autouse=True)
def clean_tables():
    """Empties all tables before every test."""
    with engine.begin() as conn:
        conn.execute(
            text("TRUNCATE lead_status_history, leads, users RESTART IDENTITY CASCADE")
        )
    yield


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers():
    return {"x-api-key": settings.webhook_api_key}