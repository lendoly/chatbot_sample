"""
Unit tests for chatbot_service/services.py.

The pipeline and DB engine are replaced by test doubles in conftest.py so no
model weights are loaded and no files are written to disk.
"""
import services


# ---------------------------------------------------------------------------
# save_message
# ---------------------------------------------------------------------------

def test_save_message_returns_message():
    msg = services.save_message("s1", "user", "hello")
    assert msg.session_id == "s1"
    assert msg.sender == "user"
    assert msg.text == "hello"
    assert msg.timestamp is not None


def test_save_message_assigns_id():
    msg = services.save_message("s1", "user", "hello")
    assert msg.id is not None


# ---------------------------------------------------------------------------
# get_messages
# ---------------------------------------------------------------------------

def test_get_messages_empty_for_unknown_session():
    assert services.get_messages("unknown") == []


def test_get_messages_returns_messages_in_insertion_order():
    services.save_message("s1", "user", "first")
    services.save_message("s1", "bot", "second")
    msgs = services.get_messages("s1")
    assert len(msgs) == 2
    assert msgs[0].text == "first"
    assert msgs[1].text == "second"


def test_get_messages_only_returns_own_session():
    services.save_message("a", "user", "for a")
    services.save_message("b", "user", "for b")
    msgs = services.get_messages("a")
    assert len(msgs) == 1
    assert msgs[0].text == "for a"


# ---------------------------------------------------------------------------
# get_sessions
# ---------------------------------------------------------------------------

def test_get_sessions_empty_when_no_messages():
    assert services.get_sessions() == []


def test_get_sessions_returns_distinct_session_ids():
    services.save_message("a", "user", "hi")
    services.save_message("a", "bot", "hello")
    services.save_message("b", "user", "hey")
    sessions = services.get_sessions()
    assert set(sessions) == {"a", "b"}


def test_get_sessions_no_duplicates():
    for _ in range(3):
        services.save_message("dup_session", "user", "msg")
    sessions = services.get_sessions()
    assert sessions.count("dup_session") == 1


# ---------------------------------------------------------------------------
# delete_session
# ---------------------------------------------------------------------------

def test_delete_session_removes_messages():
    services.save_message("del", "user", "bye")
    services.delete_session("del")
    assert services.get_messages("del") == []


def test_delete_session_removes_session_from_list():
    services.save_message("del", "user", "bye")
    services.delete_session("del")
    assert "del" not in services.get_sessions()


def test_delete_session_clears_in_memory_cache():
    services.chat_histories["del"] = [{"role": "user", "content": "hi"}]
    services.delete_session("del")
    assert "del" not in services.chat_histories


def test_delete_session_on_nonexistent_session_returns_true():
    assert services.delete_session("ghost") is True


def test_delete_session_does_not_affect_other_sessions():
    services.save_message("keep", "user", "stay")
    services.save_message("remove", "user", "go")
    services.delete_session("remove")
    assert len(services.get_messages("keep")) == 1


# ---------------------------------------------------------------------------
# build_history
# ---------------------------------------------------------------------------

def test_build_history_returns_empty_list_for_new_session():
    assert services.build_history("new") == []


def test_build_history_maps_user_sender_to_user_role():
    services.save_message("h", "user", "hello")
    history = services.build_history("h")
    assert history[0]["role"] == "user"


def test_build_history_maps_bot_sender_to_assistant_role():
    services.save_message("h", "bot", "hi there")
    history = services.build_history("h")
    assert history[0]["role"] == "assistant"


def test_build_history_preserves_content():
    services.save_message("h", "user", "hello")
    services.save_message("h", "bot", "hi there")
    history = services.build_history("h")
    assert history == [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "hi there"},
    ]


def test_build_history_preserves_insertion_order():
    for i in range(4):
        sender = "user" if i % 2 == 0 else "bot"
        services.save_message("ordered", sender, f"msg{i}")
    history = services.build_history("ordered")
    assert [h["content"] for h in history] == ["msg0", "msg1", "msg2", "msg3"]


# ---------------------------------------------------------------------------
# generate_response
# ---------------------------------------------------------------------------

def test_generate_response_returns_pipe_output():
    response = services.generate_response("g", "hello")
    assert response == "test response"


def test_generate_response_calls_pipe_with_user_message():
    services.generate_response("g", "hello")
    call_history = services.pipe.call_args[0][0]
    assert call_history[-1] == {"role": "user", "content": "hello"}


def test_generate_response_persists_user_message():
    services.generate_response("g", "hello")
    msgs = services.get_messages("g")
    user_msgs = [m for m in msgs if m.sender == "user"]
    assert len(user_msgs) == 1
    assert user_msgs[0].text == "hello"


def test_generate_response_persists_bot_message():
    services.generate_response("g", "hello")
    msgs = services.get_messages("g")
    bot_msgs = [m for m in msgs if m.sender == "bot"]
    assert len(bot_msgs) == 1
    assert bot_msgs[0].text == "test response"


def test_generate_response_updates_in_memory_cache():
    services.generate_response("g", "hello")
    history = services.chat_histories["g"]
    assert {"role": "user", "content": "hello"} in history
    assert {"role": "assistant", "content": "test response"} in history


def test_generate_response_rebuilds_history_from_db_on_cache_miss():
    # Populate the DB directly (simulates a prior session from before a restart).
    services.save_message("r", "user", "previous")
    services.save_message("r", "bot", "prior reply")
    # Cache is empty — generate_response must rebuild from DB.
    services.generate_response("r", "new message")
    call_history = services.pipe.call_args[0][0]
    assert call_history[0] == {"role": "user", "content": "previous"}
    assert call_history[1] == {"role": "assistant", "content": "prior reply"}
    assert call_history[2] == {"role": "user", "content": "new message"}


def test_generate_response_multi_turn_passes_full_history():
    services.generate_response("m", "turn one")
    # Change the mock return for the second turn.
    services.pipe.return_value = [
        {"generated_text": [{"role": "assistant", "content": "turn two reply"}]}
    ]
    services.generate_response("m", "turn two")
    call_history = services.pipe.call_args[0][0]
    assert call_history[0] == {"role": "user", "content": "turn one"}
    assert call_history[1] == {"role": "assistant", "content": "test response"}
    assert call_history[2] == {"role": "user", "content": "turn two"}


def test_generate_response_multi_turn_persists_all_messages():
    services.generate_response("m", "turn one")
    services.generate_response("m", "turn two")
    msgs = services.get_messages("m")
    assert len(msgs) == 4
