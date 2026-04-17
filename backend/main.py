from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import openai
import os
import base64
import sys

load_dotenv()

from backend.database import init_db
from backend.database import get_trip_stats
from backend.database import get_dashboard_snapshot
from backend.rag import init_rag
from backend.agent import run_agent
from backend.openai_usage import log_openai_usage
from backend.tts import text_to_speech

app = FastAPI(title="VoiceAgent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.on_event("startup")
async def startup():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("🚀 Initializing VoiceAgent...")
    log_openai_usage("startup-check", "environment", "n/a")
    init_db()
    init_rag()
    print("✅ VoiceAgent ready!")

@app.post("/transcribe")
async def transcribe(audio: UploadFile = File(...), mode: str = Form("query")):
    """Transcribe audio using OpenAI Whisper"""
    api_key = log_openai_usage("transcribe", "audio.transcriptions.create", "whisper-1")
    client = openai.OpenAI(api_key=api_key)

    audio_bytes = await audio.read()
    print(
        f"[transcribe] received name={audio.filename!r} "
        f"type={audio.content_type!r} bytes={len(audio_bytes)} mode={mode!r}"
    )

    kwargs = {
        "model": "whisper-1",
        "file": ("audio.webm", audio_bytes, audio.content_type or "audio/webm"),
    }
    if mode == "wake":
        kwargs["prompt"] = "hey agent"
        print(f"[wake] using prompt hint: hey agent")
    else:
        kwargs["prompt"] = "Question about NYC taxi trips, fares, distance, payments, vendors"

    transcript = client.audio.transcriptions.create(**kwargs)
    print(f"[transcribe] text={transcript.text!r}")
    return {"text": transcript.text}

class QuestionRequest(BaseModel):
    question: str
    voice_speed: float = 1.0

@app.post("/ask")
async def ask(request: QuestionRequest):
    """Run LangGraph agent and return answer + audio"""
    print(f"[ask] question={request.question!r} voice_speed={request.voice_speed}")
    result = run_agent(request.question)
    audio_b64 = text_to_speech(result["answer"], speed=request.voice_speed)
    
    return {
        "answer": result["answer"],
        "trace": result["trace"],
        "audio": audio_b64
    }

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/stats")
def stats():
    return get_trip_stats()


@app.get("/dashboard")
def dashboard():
    return get_dashboard_snapshot()
