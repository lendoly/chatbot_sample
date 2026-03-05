from transformers import pipeline
from sqlmodel import Session, select, delete
from db import engine
from models import ChatMessage

pipe = pipeline(
    "text-generation",
    model="HuggingFaceTB/SmolLM2-1.7B-Instruct",
    device_map="auto",
)
chat_histories = {}


def get_sessions():
    with Session(engine) as db:
        return db.exec(select(ChatMessage.session_id).distinct()).all()


def delete_session(session_id: str):
    with Session(engine) as db:
        db.exec(delete(ChatMessage).where(ChatMessage.session_id == session_id))
        db.commit()
    if session_id in chat_histories:
        del chat_histories[session_id]
    return True


def get_messages(session_id: str):
    with Session(engine) as db:
        msgs = db.exec(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.id)
        ).all()
    return msgs


def save_message(session_id: str, sender: str, text: str):
    with Session(engine) as db:
        msg = ChatMessage(session_id=session_id, sender=sender, text=text)
        db.add(msg)
        db.commit()
        db.refresh(msg)
    return msg


def build_history(session_id: str) -> list:
    """Reconstruct conversation history from DB as message dicts (used after restart)."""
    msgs = get_messages(session_id)
    return [
        {"role": "user" if m.sender == "user" else "assistant", "content": m.text}
        for m in msgs
    ]


def generate_response(session_id: str, prompt: str) -> str:
    # Restore history from DB if is not present
    if session_id not in chat_histories:
        chat_histories[session_id] = build_history(session_id)

    # Append the new user input and generate response
    chat_histories[session_id].append({"role": "user", "content": prompt})
    output = pipe(list(chat_histories[session_id]), max_new_tokens=256)
    response = output[0]["generated_text"][-1]["content"]

    # Append bot turn to in-memory history
    chat_histories[session_id].append({"role": "assistant", "content": response})
    
    # Persist both user and bot messages to DB
    save_message(session_id, "user", prompt)
    save_message(session_id, "bot", response)
    return response
