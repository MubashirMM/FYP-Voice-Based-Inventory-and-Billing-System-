import requests
import json
import os
from pathlib import Path
from myapp.config import settings

# API Keys
GROQ_API_KEY = settings.GROQ_API_KEY
GEMINI_API_KEY = settings.GEMINI_API_KEY  # Direct from settings, not os.getenv

# Endpoints
WHISPER_URL = "https://api.groq.com/openai/v1/audio/transcriptions"

def load_prompt_items():
    """Items ke liye prompt file load karein"""
    prompt_path = Path("myapp/utils/prompt_items.txt")
    if not prompt_path.exists():
        return "صرف JSON میں جواب دیں۔ آئٹم کا نام، قیمت، مقدار بتائیں۔"
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read().strip()

def process_text_items(text: str):
    """صرف متن سے آئٹمز پروسیس کریں - Gemini API استعمال ہوگی"""
    prompt_template = load_prompt_items()
    full_prompt = f"{prompt_template}\n\nصارف کا جملہ: {text}"
    
    try:
        # Gemini API call
        gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        
        payload = {
            "contents": [{
                "parts": [{"text": full_prompt}]
            }],
            "generationConfig": {
                "temperature": 0,
                "responseMimeType": "application/json"
            }
        }
        
        response = requests.post(gemini_url, json=payload, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            result_text = result['candidates'][0]['content']['parts'][0]['text']
            clean_json = result_text.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_json)
        else:
            return {"error": f"Gemini API خراب ہے: {response.status_code}"}
            
    except Exception as e:
        return {"error": f"پروسیسنگ میں خرابی: {str(e)}"}

def process_voice_items(audio_file):
    """آواز سے آئٹمز پروسیس کریں - پہلے ٹیکسٹ بنائیں پھر Gemini استعمال کریں"""
    try:
        # Step 1: Voice to text
        audio_file.seek(0)
        files = {"file": ("audio.wav", audio_file.read(), "audio/wav")}
        data = {"model": "whisper-large-v3-turbo", "language": "ur"}
        
        response = requests.post(
            WHISPER_URL, 
            headers={"Authorization": f"Bearer {GROQ_API_KEY}"}, 
            files=files, 
            data=data,
            timeout=15 
        )
        response.raise_for_status()
        voice_result = response.json()
        urdu_text = voice_result.get("text", "")
        
        if not urdu_text:
            return {"error": "آواز میں کوئی متن نہیں ملا، براہ کرم واضح بولیں"}
        
        # Step 2: Text to items
        return process_text_items(urdu_text)
        
    except requests.exceptions.Timeout:
        return {"error": "آواز پروسیسنگ کا وقت ختم ہو گیا، انٹرنیٹ چیک کریں"}
    except requests.exceptions.RequestException:
        return {"error": "آواز کو متن میں تبدیل نہیں کر سکے، نیٹورک چیک کریں"}
    except Exception:
        return {"error": "آواز پروسیسنگ میں مسئلہ، دوبارہ کوشش کریں"}
def full_voice_pipeline(audio_file):
    """مکمل پائپ لائن"""
    try:
        whisper_result = process_voice(audio_file)
        text = whisper_result.get("text", "").strip()

        if not text:
            return {"text": "", "command": {}, "error": "آواز سنائی نہیں دی، دوبارہ کوشش کریں۔"}

        command = process_text(text)
        return {"text": text, "command": command}
    except Exception as e:
        return {"error": str(e)}