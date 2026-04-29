import requests
import json
import base64
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from myapp.config import settings
from myapp.models.user import User
from myapp.utils.voice import match_voice

# API Keys - 3 Groq keys for fallback
GROQ_API_KEY1 = settings.GROQ_API_KEY3
GROQ_API_KEY2 = settings.GROQ_API_KEY4
GROQ_API_KEY3 = settings.GROQ_API_KEY5

# List of API keys for rotation
GROQ_API_KEYS = [GROQ_API_KEY1, GROQ_API_KEY2, GROQ_API_KEY3]

# Endpoints
WHISPER_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"

def load_prompt_items():
    """Items ke liye prompt file load karein"""
    prompt_path = Path("myapp/utils/prompt_bills.txt")
    if not prompt_path.exists():
        return "You are an expert Data Extractor for Shop Management System. Extract item information. Return ONLY JSON."
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read().strip()

def call_groq_with_fallback(prompt):
    """
    Try all Groq API keys one by one with Llama 3.1 8B model
    Returns: JSON response or error
    """
    for key_index, api_key in enumerate(GROQ_API_KEYS):
        if not api_key or api_key == "null":
            print(f"Groq Key {key_index + 1} is empty, skipping...")
            continue
            
        try:
            print(f"Trying Groq Key {key_index + 1} with Llama 3.1 8B...")
            
            response = requests.post(
                CHAT_URL,
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": "llama-3.1-8b-instant",
                    "messages": [
                        {
                            "role": "system", 
                            "content": "You are a JSON data extractor. Extract information and return ONLY valid JSON. No explanations, no extra text."
                        },
                        {
                            "role": "user", 
                            "content": prompt
                        }
                    ],
                    "temperature": 0,
                    "max_tokens": 1000
                },
                timeout=20
            )
            
            if response.status_code == 200:
                content = response.json()["choices"][0]["message"]["content"]
                clean_json = content.replace("```json", "").replace("```", "").strip()
                return json.loads(clean_json)
                
            elif response.status_code == 429:
                print(f"Groq Key {key_index + 1} quota exceeded, trying next...")
                continue
                
            else:
                print(f"Groq Key {key_index + 1} error: {response.status_code}")
                continue
                
        except requests.exceptions.Timeout:
            print(f"Groq Key {key_index + 1} timeout, trying next...")
            continue
        except Exception as e:
            print(f"Groq Key {key_index + 1} exception: {str(e)}")
            continue
    
    # All keys failed
    return {"error": "سب API کیز ختم ہو چکی ہیں۔ براہ کرم تھوڑی دیر بعد کوشش کریں۔"}

def call_whisper_with_fallback(audio_base64):
    """
    Try all Groq API keys for Whisper transcription with Large V3 Turbo
    Accepts base64 audio string (same as voice login)
    Returns: Urdu text or error
    """
    for key_index, api_key in enumerate(GROQ_API_KEYS):
        if not api_key or api_key == "null":
            print(f"Whisper Key {key_index + 1} is empty, skipping...")
            continue
            
        try:
            print(f"Trying Whisper with Key {key_index + 1} (Large V3 Turbo)...")
            
            # Decode base64 to bytes
            audio_bytes = base64.b64decode(audio_base64)
            
            # Prepare files for upload
            files = {
                "file": ("audio.wav", audio_bytes, "audio/wav")
            }
            
            data = {
                "model": "whisper-large-v3-turbo",
                "language": "ur",
                "response_format": "json",
                "temperature": 0
            }
            
            response = requests.post(
                WHISPER_URL,
                headers={"Authorization": f"Bearer {api_key}"},
                files=files,
                data=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                urdu_text = result.get("text", "")
                if urdu_text:
                    print(f"✅ Voice transcribed successfully with Key {key_index + 1}")
                    print(f"Transcribed text: {urdu_text}")
                    return urdu_text
                else:
                    print(f"No text extracted with Key {key_index + 1}")
                    continue
                    
            elif response.status_code == 429:
                print(f"Whisper Key {key_index + 1} quota exceeded, trying next...")
                continue
                
            else:
                print(f"Whisper Key {key_index + 1} error: {response.status_code}")
                if response.text:
                    print(f"Response: {response.text[:200]}")
                continue
                
        except requests.exceptions.Timeout:
            print(f"Whisper Key {key_index + 1} timeout, trying next...")
            continue
        except Exception as e:
            print(f"Whisper Key {key_index + 1} exception: {str(e)}")
            continue
    
    return None

async def process_voice_bills(audio_base64: str, current_user: User, db: AsyncSession):
    """
    آواز سے آئٹمز پروسیس کریں - موجودہ لاگ ان صارف کے لیے
    Works exactly like voice login - accepts base64 audio string
    
    Parameters:
    - audio_base64: Base64 encoded audio string (same format as voice login)
    - current_user: Current logged in user
    - db: Database session
    
    Returns: Processed items or error
    """
    
    # Step 1: Voice verification - check if voice matches the user
    if not current_user.voice_embedding:
        return {
            "error": "آپ کی وائس رجسٹرڈ نہیں ہے۔",
            "message": "براہ کرم پہلے وائس رجسٹر کریں"
        }
    
    # Verify voice match (same as voice login)
    try:
        is_voice_match = match_voice(current_user.voice_embedding, audio_base64)
        
        if not is_voice_match:
            return {
                "error": "وائس میچ نہیں ہوئی۔ یہ آپ کی آواز نہیں لگتی۔",
                "message": "براہ کرم اپنی رجسٹرڈ آواز سے بولے یا پھر سے وائس رجسٹر کریں"
            }
            
        print(f"✅ Voice verified successfully for user: {current_user.email}")
        
    except ValueError as e:
        return {
            "error": f"وائس پروسیسنگ میں خرابی: {str(e)}",
            "message": "براہ کرم واضح آواز میں دوبارہ کوشش کریں"
        }
    except Exception as e:
        return {
            "error": f"وائس تصدیق میں خرابی: {str(e)}",
            "message": "کچھ غلط ہو گیا، براہ کرم دوبارہ کوشش کریں"
        }
    
    # Step 2: Voice to text with Whisper (only if voice matches)
    urdu_text = call_whisper_with_fallback(audio_base64)
    
    if not urdu_text:
        return {
            "error": "آواز کو متن میں تبدیل نہیں کر سکے۔ سب API کیز ختم ہو چکی ہیں۔",
            "message": "براہ کرم تھوڑی دیر بعد کوشش کریں یا واضح بولیں",
            "voice_verified": True
        }
    
    # Step 3: Text to items with Llama 3.1
    prompt_template = load_prompt_items()
    full_prompt = f"{prompt_template}\n\nصارف کا جملہ: {urdu_text}"
    
    items_result = call_groq_with_fallback(full_prompt)
    
    # Step 4: Add user info and original text
    if isinstance(items_result, dict):
        if "error" not in items_result:
            items_result["user_id"] = current_user.user_id
            items_result["user_email"] = current_user.email
            items_result["original_text"] = urdu_text
            items_result["voice_verified"] = True
        else:
            items_result["original_text"] = urdu_text
            items_result["voice_verified"] = True
    
    return items_result

def check_api_keys():
    """Check which Groq API keys are working"""
    working_keys = []
    
    for key_index, api_key in enumerate(GROQ_API_KEYS):
        if not api_key or api_key == "null":
            continue
            
        try:
            response = requests.post(
                CHAT_URL,
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": "llama-3.1-8b-instant",
                    "messages": [{"role": "user", "content": "Say OK"}],
                    "max_tokens": 5
                },
                timeout=5
            )
            
            if response.status_code == 200:
                working_keys.append(key_index + 1)
            elif response.status_code == 429:
                print(f"Key {key_index + 1} quota exceeded")
            else:
                print(f"Key {key_index + 1} not working: {response.status_code}")
                
        except:
            print(f"Key {key_index + 1} failed")
    
    return working_keys