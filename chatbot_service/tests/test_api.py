import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

import services
from api import app


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------------------
# GET /sessions
# ---------------------------------------------------------------------------

def test_list_sessions_returns_empty_list_when_no_sessions(client):
    response = client.get("/sessions")
    assert response.status_code == 200
    assert response.json() == {"sessions": []}


def test_list_sessions_returns_existing_session_ids(client):
    services.save_message("session_a", "user", "hi")
    services.save_message("session_b", "user", "hey")
    response = client.get("/sessions")
    assert response.status_code == 200
    sessions = response.json()["sessions"]
    assert set(sessions) == {"session_a", "session_b"}


def test_list_sessions_returns_no_duplicates(client):
    services.save_message("dup", "user", "msg1")
    services.save_message("dup", "bot", "msg2")
    sessions = client.get("/sessions").json()["sessions"]
    assert sessions.count("dup") == 1


# ---------------------------------------------------------------------------
# GET /sessions/{session_id}/messages
# ---------------------------------------------------------------------------

def test_get_session_messages_returns_empty_for_unknown_session(client):
    response = client.get("/sessions/unknown/messages")
    assert response.status_code == 200
    assert response.json() == {"messages": []}


def test_get_session_messages_returns_all_messages(client):
    services.save_message("s1", "user", "hello")
    services.save_message("s1", "bot", "hi")
    response = client.get("/sessions/s1/messages")
    assert response.status_code == 200
    messages = response.json()["messages"]
    assert len(messages) == 2


def test_get_session_messages_shape(client):
    services.save_message("s1", "user", "hello")
    messages = client.get("/sessions/s1/messages").json()["messages"]
    msg = messages[0]
    assert msg["sender"] == "user"
    assert msg["text"] == "hello"
    assert "timestamp" in msg


def test_get_session_messages_preserves_order(client):
    services.save_message("s1", "user", "first")
    services.save_message("s1", "bot", "second")
    messages = client.get("/sessions/s1/messages").json()["messages"]
    assert messages[0]["text"] == "first"
    assert messages[1]["text"] == "second"


def test_get_session_messages_only_returns_own_session(client):
    services.save_message("s1", "user", "for s1")
    services.save_message("s2", "user", "for s2")
    messages = client.get("/sessions/s1/messages").json()["messages"]
    assert len(messages) == 1
    assert messages[0]["text"] == "for s1"


# ---------------------------------------------------------------------------
# DELETE /sessions/{session_id}
# ---------------------------------------------------------------------------

def test_delete_session_returns_ok(client):
    services.save_message("del", "user", "bye")
    response = client.delete("/sessions/del")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "session_id": "del"}


def test_delete_session_removes_messages(client):
    services.save_message("del", "user", "bye")
    client.delete("/sessions/del")
    assert services.get_messages("del") == []


def test_delete_session_removes_from_sessions_list(client):
    services.save_message("del", "user", "bye")
    client.delete("/sessions/del")
    sessions = client.get("/sessions").json()["sessions"]
    assert "del" not in sessions


def test_delete_nonexistent_session_returns_ok(client):
    response = client.delete("/sessions/ghost")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_delete_session_does_not_affect_other_sessions(client):
    services.save_message("keep", "user", "stay")
    services.save_message("remove", "user", "go")
    client.delete("/sessions/remove")
    assert len(services.get_messages("keep")) == 1


# ---------------------------------------------------------------------------
# POST /chat
# ---------------------------------------------------------------------------

def test_chat_returns_response_and_session_id(client):
    with patch("api.generate_response", return_value="bot reply") as mock_gen:
        response = client.post("/chat", json={"prompt": "hello", "session_id": "s1"})
    assert response.status_code == 200
    assert response.json() == {"response": "bot reply", "session_id": "s1"}


def test_chat_calls_generate_response_with_correct_args(client):
    with patch("api.generate_response", return_value="ok") as mock_gen:
        client.post("/chat", json={"prompt": "hi", "session_id": "s1"})
    mock_gen.assert_called_once_with("s1", "hi")


def test_chat_defaults_session_id_to_default(client):
    with patch("api.generate_response", return_value="ok") as mock_gen:
        client.post("/chat", json={"prompt": "hi"})
    mock_gen.assert_called_once_with("default", "hi")


def test_chat_defaults_prompt_to_empty_string(client):
    with patch("api.generate_response", return_value="ok") as mock_gen:
        client.post("/chat", json={"session_id": "s1"})
    mock_gen.assert_called_once_with("s1", "")


def test_chat_returns_correct_session_id_in_response(client):
    with patch("api.generate_response", return_value="ok"):
        response = client.post("/chat", json={"prompt": "hi", "session_id": "my_session"})
    assert response.json()["session_id"] == "my_session"
