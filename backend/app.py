import json
from pathlib import Path

from fastapi import FastAPI, Query
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

schools_path = Path(__file__).parent / "schools.json"
with open(schools_path) as f:
    SCHOOLS_DATA = json.load(f)

GRADE_TO_STAGE = {
    "9th": "sophomore",
    "10th": "sophomore",
    "11th": "junior",
    "12th": "senior",
}


class ChatRequest(BaseModel):
    student_id: str
    message: str


class ChatResponse(BaseModel):
    response: str
    updated_profile: dict


class OnboardRequest(BaseModel):
    student_id: str
    name: str
    grade: str
    zip: str
    high_school: str


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


@app.post("/api/onboard")
async def onboard(req: OnboardRequest):
    profile = empty_profile(req.student_id)

    parts = req.name.split(None, 1)
    profile["contact"]["first_name"] = parts[0]
    profile["contact"]["last_name"] = parts[1] if len(parts) > 1 else ""
    profile["contact"]["zip"] = req.zip
    profile["contact"]["high_school"] = req.high_school
    profile["academic"]["grade"] = req.grade
    profile["stage"] = GRADE_TO_STAGE.get(req.grade, "sophomore")

    profiles[req.student_id] = profile
    conversations[req.student_id] = []

    return {"profile": profile}


@app.get("/api/schools/search")
async def search_schools(q: str = Query(""), zip: str = Query("")):
    if len(q) < 2:
        return {"schools": []}

    q_lower = q.lower()
    results = []

    for school in SCHOOLS_DATA:
        score = 0
        name_lower = school["name"].lower()

        if q_lower in name_lower:
            score += 10
            if name_lower.startswith(q_lower):
                score += 5
        else:
            words = name_lower.split()
            if any(w.startswith(q_lower) for w in words):
                score += 6

        if score == 0:
            continue

        if zip and len(zip) >= 3 and school["zip"][:3] == zip[:3]:
            score += 3
        elif zip and len(zip) >= 2 and school["zip"][:2] == zip[:2]:
            score += 1

        results.append({
            "name": school["name"],
            "city": school["city"],
            "state": school["state"],
            "zip": school["zip"],
            "_score": score,
        })

    results.sort(key=lambda x: -x["_score"])
    for r in results:
        del r["_score"]

    return {"schools": results[:10]}


@app.get("/profile/{student_id}")
async def get_profile(student_id: str):
    if student_id not in profiles:
        return {"error": "Student not found"}
    return profiles[student_id]
