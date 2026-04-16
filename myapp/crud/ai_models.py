# import requests
# import json
# import os
# from pathlib import Path
# from myapp.config import settings

# # API Keys - اب یہ محفوظ طریقے سے لوڈ ہو رہی ہیں
# GROQ_API_KEY = settings.GROQ_API_KEY
# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# # Endpoints
# WHISPER_URL = "https://api.groq.com/openai/v1/audio/transcriptions"

# def load_prompt():
#     """Prompt فائل لوڈ کریں"""
#     prompt_path = Path("myapp/utils/prompt.txt")
#     if not prompt_path.exists():
#         return "صرف JSON میں جواب دیں۔" 
#     with open(prompt_path, "r", encoding="utf-8") as f:
#         return f.read().strip()
# def process_text(text: str):
#     prompt_template = load_prompt()
#     full_prompt = f"{prompt_template}\n\nصارف کا جملہ: {text}"
    
#     # 1. TRY GROQ
#     try:
#         groq_res = requests.post(
#             "https://api.groq.com/openai/v1/chat/completions",
#             headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
#             json={
#                 "model": "llama-3.1-8b-instant", 
#                 "messages": [{"role": "user", "content": full_prompt}],
#                 "temperature": 0
#             },
#             timeout=5
#         )
#         if groq_res.status_code == 200:
#             content = groq_res.json()["choices"][0]["message"]["content"]
#             clean_json = content.replace("```json", "").replace("```", "").strip()
#             return json.loads(clean_json)
#         else:
#             print(f"Groq Error: {groq_res.status_code} - {groq_res.text}")
#     except Exception as e:
#         print(f"Groq Exception: {e}")

# def process_text(text: str):
#     """Groq اور Gemini کے ذریعے اردو ٹیکسٹ پروسیسنگ"""
#     prompt_template = load_prompt()
#     full_prompt = f"{prompt_template}\n\nصارف کا جملہ: {text}"
    
#     # --- 1. TRY GROQ (Llama 3.1 8B) ---
#     try:
#         groq_res = requests.post(
#             "https://api.groq.com/openai/v1/chat/completions",
#             headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
#             json={
#                 "model": "llama-3.1-8b-instant", 
#                 "messages": [{"role": "user", "content": full_prompt}],
#                 "temperature": 0
#             },
#             timeout=5
#         )
#         if groq_res.status_code == 200:
#             content = groq_res.json()["choices"][0]["message"]["content"]
#             clean_json = content.replace("```json", "").replace("```", "").strip()
#             return json.loads(clean_json)
#     except:
#         pass # Groq فیل ہونے کی صورت میں خاموشی سے Gemini پر جائیں

#     # --- 2. GEMINI FALLBACK (REST API) ---
#     try:
#         gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
#         gemini_res = requests.post(
#             gemini_url,
#             json={
#                 "contents": [{"parts": [{"text": full_prompt}]}],
#                 "generationConfig": {"responseMimeType": "application/json"}
#             },
#             timeout=8
#         )
#         result_text = gemini_res.json()['candidates'][0]['content']['parts'][0]['text']
#         return json.loads(result_text)
#     except:
#         return {"error": "اے آئی سروس دستیاب نہیں ہے۔ براہ کرم دوبارہ کوشش کریں۔"}


import requests
import json
import os
from pathlib import Path
from myapp.config import settings

# API کیز کی لسٹ - بغیر انڈر اسکور کے
API_KEYS = [
    settings.GROQ_API_KEY,     # پہلی کی
    settings.GROQ_API_KEY1,    # دوسری کی
    settings.GROQ_API_KEY2,    # تیسری کی
    settings.GROQ_API_KEY3     # چوتھی کی
]

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
WHISPER_URL = "https://api.groq.com/openai/v1/audio/transcriptions"

def load_prompt():
    """پرامپٹ فائل لوڈ کرنے کا فنکشن"""
    prompt_path = Path("myapp/utils/prompt.txt")
    if not prompt_path.exists():
        return "صرف JSON میں جواب دیں۔" 
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read().strip()

def process_text(text: str):
    prompt_template = load_prompt()
    full_prompt = f"{prompt_template}\n\nصارف کا جملہ: {text}"
    
    # باری باری تمام کیز کو استعمال کرنے کی کوشش
    for i, api_key in enumerate(API_KEYS):
        try:
            print(f"کوشش نمبر {i+1}: اے پی آئی کی (Key) استعمال ہو رہی ہے...")
            
            res = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": "llama-3.1-8b-instant", 
                    "messages": [{"role": "user", "content": full_prompt}],
                    "temperature": 0
                },
                timeout=5
            )

            # اگر جواب درست (200) ہے
            if res.status_code == 200:
                content = res.json()["choices"][0]["message"]["content"]
                clean_json = content.replace("```json", "").replace("```", "").strip()
                return json.loads(clean_json)
            
            # اگر ریٹ لمٹ (429) یا سرور کا مسئلہ ہو تو اگلی کی پر جائیں
            elif res.status_code in [429, 500, 502, 503, 504]:
                print(f"کی نمبر {i+1} کی لمٹ ختم ہو گئی یا مسئلہ آیا۔ اگلی کی چیک کر رہے ہیں...")
                continue
            else:
                print(f"کی نمبر {i+1} میں خرابی: {res.status_code} - {res.text}")
                break # اگر غلطی ایسی ہے جو کی بدلنے سے ٹھیک نہیں ہوگی تو لوپ روک دیں

        except Exception as e:
            print(f"کی نمبر {i+1} میں کنکشن کا مسئلہ: {e}")
            continue

    # اگر تمام کیز ختم ہو جائیں
    print("تمام Groq API کیز ختم ہو گئیں یا کام نہیں کر رہی ہیں۔")
    return None

def process_voice(audio_file):
    """وائس ٹرانسکریپشن"""
    try:
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
        return response.json()
    except Exception:
        
        raise Exception("آواز کو متن میں تبدیل کرنے میں دشواری پیش آئی ہے۔")

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