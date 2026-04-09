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

import json
import requests
from myapp.config import settings

def process_text(text: str):
    """
    اردو ٹیکسٹ کو Groq پر بھیجتا ہے اور JSON واپس کرتا ہے
    """
    try:
        # پرامپٹ فائل لوڈ کریں
        prompt_template = load_prompt()
        full_prompt = f"{prompt_template}\n\nصارف کا جملہ: {text}"

        headers = {
            "Authorization": f"Bearer {settings.GROQ_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {
                    "role": "system", 
                    "content": "آپ ایک ڈیٹا ایکسٹریکٹر ہیں جو صرف JSON میں جواب دیتا ہے۔"
                },
                {"role": "user", "content": full_prompt}
            ],
            "temperature": 0.0,  # درستگی کے لیے اسے صفر رکھا گیا ہے
            "max_tokens": 512
        }

        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=15
        )
        response.raise_for_status()

        # AI کے جواب کو صاف کریں
        raw_content = response.json()["choices"][0]["message"]["content"]
        clean_json_str = raw_content.replace("```json", "").replace("```", "").strip()

        # JSON کو پائتھن ڈکشنری میں بدلیں
        return json.loads(clean_json_str)

    except json.JSONDecodeError:
        return {"error": "ڈیٹا کو سمجھنے میں غلطی ہوئی (Invalid JSON)"}
    except Exception as e:
        print(f"Error: {str(e)}")
        raise Exception("ٹیکسٹ پروسیسنگ کے دوران مسئلہ پیش آیا۔")
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