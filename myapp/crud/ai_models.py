import requests
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Endpoints
WHISPER_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
LLM_URL = "https://api.groq.com/openai/v1/chat/completions"

# ------------------------------
# PROMPT LOADER
# ------------------------------
def load_prompt():
    """
    Load prompt template from utils/prompt.txt
    """
    prompt_path = Path("myapp/utils/prompt.txt")
    if not prompt_path.exists():
        raise FileNotFoundError("Prompt file not found at myapp/utils/prompt.txt")
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()


# ------------------------------
# TEXT → JSON COMMAND
# ------------------------------
def process_text(text: str):
    """
    Send text to Groq LLM to generate structured JSON
    """
    prompt_template = load_prompt()
    prompt = prompt_template + text

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": "Return valid JSON only."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0
    }

    response = requests.post(LLM_URL, headers=headers, json=payload)
    
    # ------------------------------
    # ERROR POINT #1: LLM 404 or model not found
    # Solution: Make sure the model name matches your account access
    # ------------------------------
    response.raise_for_status()

    data = response.json()
    # Extract assistant message safely
    return data["choices"][0]["message"]["content"]


# ------------------------------
# VOICE → TEXT
# ------------------------------
def process_voice(audio_file):
    """
    Send audio to Groq Whisper API and get text
    """
    # ------------------------------
    # ERROR POINT #2: 400 file empty
    # Cause: audio_file pointer may be at the end
    # Fix: seek(0) before reading
    # ------------------------------
    audio_file.seek(0)

    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    files = {"file": ("audio.wav", audio_file.read(), "audio/wav")}
    data = {"model": "whisper-large-v3"}

    try:
        response = requests.post(WHISPER_URL, headers=headers, files=files, data=data)
        # ------------------------------
        # ERROR POINT #3: 500 Internal Server Error
        # Cause: Groq transient issues
        # Fix: Retry on 500 errors
        # ------------------------------
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        if response.status_code >= 500:
            # Simple retry once
            response = requests.post(WHISPER_URL, headers=headers, files=files, data=data)
            response.raise_for_status()
        else:
            # Propagate other errors
            raise

    return response.json()


# ------------------------------
# FULL PIPELINE: VOICE → TEXT → JSON
# ------------------------------
def full_voice_pipeline(audio_file):
    """
    Full voice processing pipeline
    """
    whisper_result = process_voice(audio_file)
    text = whisper_result.get("text", "")

    # ------------------------------
    # SAFETY: if no text detected, return empty
    # ------------------------------
    if not text.strip():
        return {"text": "", "command": "{}", "error": "No text detected in audio."}

    command = process_text(text)

    return {"text": text, "command": command}