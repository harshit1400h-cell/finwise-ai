import pytest

from src.database import init_db


@pytest.fixture
def db_path(tmp_path, monkeypatch):
    path = tmp_path / "test-finwise.db"
    monkeypatch.setenv("FINWISE_DB_PATH", str(path))
    init_db()
    return path
