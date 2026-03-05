import sys
import os
from unittest.mock import MagicMock, patch

# Ensure chatbot_service/ is on sys.path so all modules resolve correctly.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ---------------------------------------------------------------------------
# Patch transformers.pipeline at module level — before any test module
# triggers the import of services.py, which calls pipeline(...) at the top.
# ---------------------------------------------------------------------------
_pipeline_patcher = patch("transformers.pipeline")
_mock_pipeline_cls = _pipeline_patcher.start()

# This is the mock pipe *instance* that services.pipe will be bound to.
mock_pipe = MagicMock()
mock_pipe.return_value = [
    {"generated_text": [{"role": "assistant", "content": "test response"}]}
]
_mock_pipeline_cls.return_value = mock_pipe

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
import pytest
from sqlmodel import SQLModel, create_engine
from sqlalchemy.pool import StaticPool

import services


@pytest.fixture()
def test_engine():
    """In-memory SQLite engine, isolated per test."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(autouse=True)
def isolate(test_engine, monkeypatch):
    """Applied to every test: swap in the test engine and reset shared state."""
    monkeypatch.setattr(services, "engine", test_engine)
    monkeypatch.setattr(services, "pipe", mock_pipe)
    services.chat_histories.clear()
    mock_pipe.reset_mock()
    mock_pipe.return_value = [
        {"generated_text": [{"role": "assistant", "content": "test response"}]}
    ]
    yield
