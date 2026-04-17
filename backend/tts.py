from openai import OpenAI
import base64

from backend.openai_usage import log_openai_usage

def text_to_speech(text: str, speed: float = 1.0) -> str:
    """Convert text to speech using OpenAI TTS, return base64 audio"""
    api_key = log_openai_usage("tts", "audio.speech.create", "tts-1")
    client = OpenAI(api_key=api_key)
    print(f"[tts] chars={len(text)} speed={speed}")
    
    response = client.audio.speech.create(
        model="tts-1",
        voice="nova",       # nova is clear and natural
        input=text,
        response_format="mp3",
        speed=speed,
    )
    
    audio_bytes = response.content
    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
    return audio_b64
