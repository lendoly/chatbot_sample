from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from models import ChatRequest
from services import create_session, get_sessions, get_messages, generate_response, delete_session

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)


@app.post("/sessions")
async def create_session_endpoint():
    return {"session_id": create_session()}


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
    delete_session(session_id)
    return {"status": "ok", "session_id": session_id}


@app.post("/chat")
async def chat_endpoint(body: ChatRequest):
    response = generate_response(body.session_id, body.prompt)
    return {"response": response, "session_id": body.session_id}
