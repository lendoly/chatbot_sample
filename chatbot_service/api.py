from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from services import get_sessions, get_messages, save_message, generate_response, delete_session

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

@app.options("/chat")
async def chat_options():
    return {"ok": True}

@app.get("/sessions")
async def list_sessions():
    return {"sessions": get_sessions()}

@app.get("/sessions/{session_id}/messages")
async def get_session_messages(session_id: str):
    msgs = get_messages(session_id)
    return {"messages": [
        {"sender": m.sender, "text": m.text, "timestamp": m.timestamp.isoformat()} for m in msgs
    ]}

@app.delete("/sessions/{session_id}")
async def delete_session_endpoint(session_id: str):
    deleted = delete_session(session_id)
    if deleted:
        return {"status": "ok", "session_id": session_id}
    else:
        return {"status": "error", "message": "failed to delete"}

@app.post("/chat")
async def chat_endpoint(req: Request):
    data = await req.json()
    prompt = data.get("prompt", "")
    session_id = data.get("session_id", "default")
    # let generate_response handle persistence of both sides
    response = generate_response(session_id, prompt)
    return {"response": response, "session_id": session_id}
