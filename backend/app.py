from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.agent.profile import empty_profile
from backend.agent.conversation import run_conversation, stream_conversation

app = FastAPI(title="Halda AI College Counselor")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

profiles: dict[str, dict] = {}
conversations: dict[str, list] = {}


class ChatRequest(BaseModel):
    student_id: str
    message: str


class ChatResponse(BaseModel):
    response: str
    updated_profile: dict


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    if req.student_id not in profiles:
        profiles[req.student_id] = empty_profile(req.student_id)
        conversations[req.student_id] = []

    profile = profiles[req.student_id]
    history = conversations[req.student_id]

    response_text, updated_profile, updated_history = await run_conversation(
        student_id=req.student_id,
        user_message=req.message,
        profile=profile,
        history=history,
    )

    profiles[req.student_id] = updated_profile
    conversations[req.student_id] = updated_history

    return ChatResponse(response=response_text, updated_profile=updated_profile)


@app.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    if req.student_id not in profiles:
        profiles[req.student_id] = empty_profile(req.student_id)
        conversations[req.student_id] = []

    profile = profiles[req.student_id]
    history = conversations[req.student_id]

    async def event_generator():
        nonlocal profile
        async for event in stream_conversation(
            student_id=req.student_id,
            user_message=req.message,
            profile=profile,
            history=history,
        ):
            yield event
        profiles[req.student_id] = profile
        conversations[req.student_id] = history

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/profile/{student_id}")
async def get_profile(student_id: str):
    if student_id not in profiles:
        return {"error": "Student not found"}
    return profiles[student_id]
