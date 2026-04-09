import requests
import os
from dotenv import load_dotenv
from pathlib import Path
from fastapi import HTTPException

# Load environment variables
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Endpoints
WHISPER_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
LLM_URL = "https://api.groq.com/openai/v1/chat/completions"


# ------------------------------
# PROMPT LOADER (from service folder)
# ------------------------------
def load_prompt():
    """prompt.txt فائل کو service فولڈر سے لوڈ کریں"""
    prompt_path = Path("myapp/services/prompt.txt")
    if not prompt_path.exists():
        raise FileNotFoundError("prompt.txt فائل myapp/service/ فولڈر میں موجود نہیں ہے")
    
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read().strip()


# ------------------------------
# TEXT → JSON COMMAND
# ------------------------------
def process_text(text: str):
    """ٹیکسٹ کو LLM کو بھیجو اور JSON کمانڈ واپس لو"""
    try:
        prompt_template = load_prompt()
        full_prompt = prompt_template + "\n\nUser Command: " + text

        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": "صرف درست JSON واپس کریں۔ کوئی اضافی ٹیکسٹ نہ لکھیں۔"},
                {"role": "user", "content": full_prompt}
            ],
            "temperature": 0.0,
            "max_tokens": 1024
        }

        response = requests.post(LLM_URL, headers=headers, json=payload)
        response.raise_for_status()

        data = response.json()
        return data["choices"][0]["message"]["content"]

    except requests.exceptions.HTTPError as e:
        raise Exception(f"LLM سروس میں خرابی: {e.response.status_code}")
    except Exception as e:
        raise Exception(f"ٹیکسٹ پروسیسنگ میں خرابی: {str(e)}")


# ------------------------------
# VOICE → TEXT (Whisper)
# ------------------------------
def process_voice(audio_file):
    """آڈیو فائل کو Whisper سے ٹیکسٹ میں تبدیل کریں"""
    try:
        audio_file.seek(0)

        headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
        files = {"file": ("audio.wav", audio_file.read(), "audio/wav")}
        data = {
            "model": "whisper-large-v3-turbo", 
            "language": "ur",
            "response_format": "json"
        }

        response = requests.post(WHISPER_URL, headers=headers, files=files, data=data)
        response.raise_for_status()

        return response.json()

    except requests.exceptions.HTTPError as e:
        if e.response.status_code >= 500:
            # Retry once
            response = requests.post(WHISPER_URL, headers=headers, files=files, data=data)
            response.raise_for_status()
        raise Exception(f"آڈیو ٹرانسکریپشن میں خرابی: {e.response.status_code}")
    except Exception as e:
        raise Exception(f"وائس پروسیسنگ میں خرابی: {str(e)}")


# ------------------------------
# FULL PIPELINE: VOICE → TEXT → JSON
# ------------------------------
def full_voice_pipeline(audio_file):
    """مکمل پائپ لائن"""
    try:
        whisper_result = process_voice(audio_file)
        text = whisper_result.get("text", "").strip()

        if not text:
            return {
                "text": "",
                "command": "{}",
                "error": "آڈیو میں کوئی بات سمجھ نہیں آئی۔"
            }

        command = process_text(text)

        return {
            "text": text,
            "command": command
        }

    except Exception as e:
        raise Exception(f"مکمل وائس پائپ لائن میں خرابی: {str(e)}")