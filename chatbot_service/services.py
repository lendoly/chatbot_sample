import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from sqlmodel import Session, select, delete
from db import engine
from models import ChatMessage

# load model and tokenizer once
tokenizer = AutoTokenizer.from_pretrained("microsoft/DialoGPT-small")
model = AutoModelForCausalLM.from_pretrained("microsoft/DialoGPT-small")

# in-memory cache of token history
chat_histories = {}


def get_sessions():
    with Session(engine) as db:
        result = db.exec(select(ChatMessage.session_id).distinct())
        sessions = [row[0] if isinstance(row, tuple) else row for row in result.fetchall()]
    return sessions

def delete_session(session_id: str):
    """Remove all messages for a given session."""
    with Session(engine) as db:
        db.exec(delete(ChatMessage).where(ChatMessage.session_id == session_id))
        db.commit()
    # also clear in-memory history cache
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
    return msg


def build_history(session_id: str):
    if session_id in chat_histories and chat_histories[session_id] is not None:
        return chat_histories[session_id]
    msgs = get_messages(session_id)
    history_ids = None
    for m in msgs:
        enc = tokenizer.encode(m.text + tokenizer.eos_token, return_tensors='pt')
        history_ids = enc if history_ids is None else torch.cat([history_ids, enc], dim=-1)
    chat_histories[session_id] = history_ids
    return history_ids


def generate_response(session_id: str, prompt: str) -> str:
    # persist user message first
    save_message(session_id, "user", prompt)
    history = build_history(session_id)
    # encode only once (prompt already part of history if saved)
    if history is not None:
        bot_input_ids = history
    else:
        bot_input_ids = tokenizer.encode(prompt + tokenizer.eos_token, return_tensors='pt')
    # generate
    chat_histories[session_id] = model.generate(bot_input_ids, max_length=1000, pad_token_id=tokenizer.eos_token_id)
    response = tokenizer.decode(chat_histories[session_id][:, bot_input_ids.shape[-1]:][0], skip_special_tokens=True)
    # persist bot response
    save_message(session_id, "bot", response)
    return response
