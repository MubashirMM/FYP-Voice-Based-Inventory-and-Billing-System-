# # myapp/crud/ai_models/ai_models_base.py - Complete optimized base

# import json
# import base64
# import asyncio
# from pathlib import Path
# from typing import Optional, Dict, Any, List
# from functools import lru_cache
# import aiohttp
# from sqlalchemy.ext.asyncio import AsyncSession
# from myapp.config import settings
# from myapp.models.user import User
# from myapp.utils.voice import match_voice
# import traceback 

# # ============================================
# # OPTIMIZATION: Singleton HTTP Session Manager
# # ============================================
# class AiohttpSessionManager:
#     """Reuse HTTP sessions for better performance"""
#     _session: Optional[aiohttp.ClientSession] = None
#     _connector: Optional[aiohttp.TCPConnector] = None
    
#     @classmethod
#     async def get_session(cls) -> aiohttp.ClientSession:
#         if cls._session is None or cls._session.closed:
#             cls._connector = aiohttp.TCPConnector(
#                 limit=50,
#                 limit_per_host=10,
#                 ttl_dns_cache=300,
#                 use_dns_cache=True,
#                 enable_cleanup_closed=True
#             )
#             timeout = aiohttp.ClientTimeout(
#                 total=25,
#                 connect=5,
#                 sock_read=20
#             )
#             cls._session = aiohttp.ClientSession(
#                 connector=cls._connector,
#                 timeout=timeout
#             )
#         return cls._session
    
#     @classmethod
#     async def close(cls):
#         if cls._session and not cls._session.closed:
#             await cls._session.close()
#             cls._session = None

# # ============================================
# # OPTIMIZATION: API Key Manager per Module
# # ============================================
# class APIKeyManager:
#     """Manages API keys for different modules"""
    
#     # Module-specific key mappings
#     MODULE_KEYS = {
#         "items": [
#             settings.GROQ_API_KEY,
#             settings.GROQ_API_KEY8,
#             settings.GROQ_API_KEY13,
#         ],
#         "udhaar_items": [
#             settings.GROQ_API_KEY4,
#             settings.GROQ_API_KEY5,
#             settings.GROQ_API_KEY6,
#         ],
#         "udhaars": [
#             settings.GROQ_API_KEY7,
#             settings.GROQ_API_KEY8,
#             settings.GROQ_API_KEY9,
#         ],
#         "bills": [
#             settings.GROQ_API_KEY10,
#             settings.GROQ_API_KEY11,
#             settings.GROQ_API_KEY12,
#         ],
#     }
    
#     @classmethod
#     def get_keys(cls, module: str) -> List[str]:
#         """Get valid API keys for a specific module"""
#         keys = cls.MODULE_KEYS.get(module, [])
#         return [key for key in keys if key and key != "null"]
    
#     @classmethod
#     def get_all_modules(cls) -> List[str]:
#         """Get list of all available modules"""
#         return list(cls.MODULE_KEYS.keys())

# # ============================================
# # API Constants
# # ============================================
# WHISPER_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
# CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"

# # ============================================
# # OPTIMIZATION: Cached Prompt Loading
# # ============================================
# @lru_cache(maxsize=10)
# def load_prompt(prompt_filename: str) -> str:
#     """Cache prompts to avoid repeated file I/O"""
#     prompt_path = Path(f"myapp/prompts/{prompt_filename}")
#     if not prompt_path.exists():
#         print(f"⚠️  Warning: Prompt file {prompt_filename} not found, using default")
#         return "You are an expert Data Extractor for Shop Management System. Extract information. Return ONLY JSON."
#     with open(prompt_path, "r", encoding="utf-8") as f:
#         return f.read().strip()

# # ============================================
# # OPTIMIZATION: Per-Module Groq API Client
# # ============================================
# class GroqAPIClient:
#     """Optimized Groq API client with module-specific key rotation"""
    
#     def __init__(self, module_name: str):
#         self.module_name = module_name
#         self.api_keys = APIKeyManager.get_keys(module_name)
#         self._key_index = 0
        
#         if not self.api_keys:
#             print(f"⚠️  Warning: No API keys configured for module: {module_name}")
#         else:
#             print(f"✅ Module '{module_name}' initialized with {len(self.api_keys)} API keys")
    
#     async def call_llm(self, prompt: str, model: str = "llama-3.1-8b-instant") -> Dict:
#         """Call LLM with automatic key rotation for this module"""
#         if not self.api_keys:
#             return {"error": f"No API keys configured for {self.module_name}"}
        
#         session = await AiohttpSessionManager.get_session()
#         errors = []
        
#         for key in self._rotate_keys():
#             try:
#                 headers = {"Authorization": f"Bearer {key}"}
#                 json_data = {
#                     "model": model,
#                     "messages": [
#                         {
#                             "role": "system",
#                             "content": "Return ONLY valid JSON. No explanations, no extra text."
#                         },
#                         {"role": "user", "content": prompt}
#                     ],
#                     "temperature": 0,
#                     "max_tokens": 1000,
#                     "response_format": {"type": "json_object"}
#                 }
                
#                 async with session.post(CHAT_URL, headers=headers, json=json_data, timeout=20) as response:
#                     if response.status == 200:
#                         data = await response.json()
#                         content = data["choices"][0]["message"]["content"]
#                         clean_json = content.replace("```json", "").replace("```", "").strip()
#                         return json.loads(clean_json)
#                     elif response.status == 429:
#                         print(f"[{self.module_name}] Key rate limited, rotating...")
#                         continue
#                     else:
#                         error_text = await response.text()
#                         errors.append(f"Status {response.status}: {error_text[:100]}")
#                         continue
                        
#             except (aiohttp.ClientError, asyncio.TimeoutError) as e:
#                 errors.append(str(e)[:100])
#                 continue
        
#         return {
#             "error": f"All API keys exhausted for {self.module_name}",
#             "details": errors[:3]
#         }
    
#     async def call_whisper(self, audio_base64: str) -> Optional[str]:
#         """Call Whisper API with key rotation for this module"""
#         if not self.api_keys:
#             return None
        
#         session = await AiohttpSessionManager.get_session()
        
#         for key in self._rotate_keys():
#             try:
#                 # Decode audio
#                 audio_bytes = base64.b64decode(audio_base64)
                
#                 # Prepare form data
#                 form_data = aiohttp.FormData()
#                 form_data.add_field(
#                     "file", audio_bytes,
#                     filename="audio.wav",
#                     content_type="audio/wav"
#                 )
#                 form_data.add_field("model", "whisper-large-v3-turbo")
#                 form_data.add_field("language", "ur")
#                 form_data.add_field("response_format", "json")
#                 form_data.add_field("temperature", "0")
                
#                 headers = {"Authorization": f"Bearer {key}"}
                
#                 print(f"🎤 [{self.module_name}] Sending audio to Whisper...")  # ADD THIS
                
#                 async with session.post(WHISPER_URL, headers=headers, data=form_data, timeout=30) as response:
#                     if response.status == 200:
#                         result = await response.json()
#                         text = result.get("text", "")
#                         if text:
#                             print(f"✅ [{self.module_name}] Transcription successful")  # ADD THIS
#                             print(f"📝 [{self.module_name}] Transcribed text: {text}")  # ADD THIS
#                             print(f"📝 [{self.module_name}] Text length: {len(text)} characters")  # ADD THIS
#                             return text
#                     elif response.status == 429:
#                         print(f"[{self.module_name}] Whisper key rate limited, rotating...")
#                         continue
                            
#             except (aiohttp.ClientError, asyncio.TimeoutError) as e:
#                 print(f"[{self.module_name}] Whisper error: {str(e)[:100]}")
#                 continue
        
#         print(f"❌ [{self.module_name}] Whisper transcription failed - all keys exhausted")  # ADD THIS
#         return None
    
#     def _rotate_keys(self):
#         """Generator for key rotation within this module"""
#         if not self.api_keys:
#             return
        
#         start_idx = self._key_index % len(self.api_keys)
#         for i in range(len(self.api_keys)):
#             idx = (start_idx + i) % len(self.api_keys)
#             self._key_index = (idx + 1) % len(self.api_keys)
#             yield self.api_keys[idx]

# # ============================================
# # OPTIMIZATION: Client Pool (one client per module)
# # ============================================
# class ClientPool:
#     """Manages Groq API clients for all modules"""
#     _clients: Dict[str, GroqAPIClient] = {}
    
#     @classmethod
#     def get_client(cls, module_name: str) -> GroqAPIClient:
#         """Get or create client for a module"""
#         if module_name not in cls._clients:
#             cls._clients[module_name] = GroqAPIClient(module_name)
#         return cls._clients[module_name]
    
#     @classmethod
#     def get_status(cls) -> Dict[str, Any]:
#         """Get status of all module clients"""
#         status = {}
#         for module_name, client in cls._clients.items():
#             status[module_name] = {
#                 "total_keys": len(client.api_keys),
#                 "available": len(client.api_keys) > 0,
#                 "current_key_index": client._key_index
#             }
#         return status

# # ============================================
# # OPTIMIZATION: Unified Voice Processing Pipeline
# # ============================================
# async def process_voice_pipeline(
#     audio_base64: str,
#     current_user: User,
#     db: AsyncSession,
#     prompt_filename: str,
#     module_name: str
# ) -> Dict[str, Any]:
#     """
#     Unified pipeline for all voice processing tasks
#     Each module uses its own set of API keys
#     """
    
#     # Step 1: Quick validation
#     if not current_user.voice_embedding:
#         return {
#             "error": "آپ کی وائس رجسٹرڈ نہیں ہے۔",
#             "message": "براہ کرم پہلے وائس رجسٹر کریں",
#             "voice_verified": False,
#             "module": module_name
#         }
    
#     # Get module-specific client
#     client = ClientPool.get_client(module_name)
    
#     try:
#         # Step 2: PARALLEL - Voice verification + Whisper transcription
#         voice_task = asyncio.create_task(
#             match_voice(current_user.voice_embedding, audio_base64)
#         )
#         whisper_task = asyncio.create_task(
#             client.call_whisper(audio_base64)
#         )
        
#         # Wait for voice verification first (security priority)
#         is_match, similarity = await voice_task
        
#         if not is_match:
#             whisper_task.cancel()  # Cancel transcription if voice doesn't match
#             return {
#                 "error": "وائس میچ نہیں ہوئی۔",
#                 "message": f"مماثلت: {similarity:.2%} - یہ آپ کی آواز نہیں لگتی۔",
#                 "voice_verified": False,
#                 "similarity": float(similarity),
#                 "module": module_name
#             }
        
#         # Step 3: Get transcription (may already be complete from parallel execution)
#         urdu_text = await whisper_task
        
#         if not urdu_text:
#             return {
#                 "error": "آواز کو متن میں تبدیل نہیں کر سکے۔",
#                 "message": "براہ کرم واضح بولیں اور دوبارہ کوشش کریں",
#                 "voice_verified": True,
#                 "similarity": float(similarity),
#                 "module": module_name
#             }
        
#         # Step 4: Load prompt and call LLM
#         prompt_template = load_prompt(prompt_filename)
#         full_prompt = f"{prompt_template}\n\nصارف کا جملہ: {urdu_text}"
        
#         llm_result = await client.call_llm(full_prompt)
        
#         # Step 5: Add metadata
#         if isinstance(llm_result, dict):
#             llm_result.update({
#                 "user_id": current_user.user_id,
#                 "user_email": current_user.email,
#                 "original_text": urdu_text,
#                 "voice_verified": True,
#                 "similarity": float(similarity),
#                 "module": module_name
#             })
#         else:
#             llm_result = {
#                 "error": "Invalid LLM response format",
#                 "original_text": urdu_text,
#                 "voice_verified": True,
#                 "similarity": float(similarity),
#                 "module": module_name
#             }
        
#         return llm_result
        
#     except asyncio.CancelledError:
#         return {
#             "error": "درخواست منسوخ کر دی گئی۔",
#             "voice_verified": False,
#             "module": module_name
#         }
#     except Exception as e:
#         return {
#             "error": f"پروسیسنگ میں خرابی: {str(e)}",
#             "message": "براہ کرم دوبارہ کوشش کریں",
#             "voice_verified": False,
#             "module": module_name
#         }
# async def process_voice_pipeline(
#     audio_base64: str,
#     current_user: User,
#     db: AsyncSession,
#     prompt_filename: str,
#     module_name: str
# ) -> Dict[str, Any]:
#     """
#     Unified pipeline for all voice processing tasks
#     Each module uses its own set of API keys
#     """
    
#     # Step 1: Quick validation
#     if not current_user.voice_embedding:
#         return {
#             "error": "آپ کی وائس رجسٹرڈ نہیں ہے۔",
#             "message": "براہ کرم پہلے وائس رجسٹر کریں",
#             "voice_verified": False,
#             "module": module_name
#         }
    
#     # Get module-specific client
#     client = ClientPool.get_client(module_name)
    
#     try:
#         print(f"\n{'='*60}")  # ADD THIS
#         print(f"🚀 [{module_name}] Starting voice processing pipeline")  # ADD THIS
#         print(f"{'='*60}")  # ADD THIS
        
#         # Step 2: PARALLEL - Voice verification + Whisper transcription
#         print(f"🔄 [{module_name}] Starting parallel voice verification and transcription...")  # ADD THIS
#         voice_task = asyncio.create_task(
#             match_voice(current_user.voice_embedding, audio_base64)
#         )
#         whisper_task = asyncio.create_task(
#             client.call_whisper(audio_base64)
#         )
        
#         # Wait for voice verification first (security priority)
#         is_match, similarity = await voice_task
#         print(f"🔐 [{module_name}] Voice verification complete - Match: {is_match}, Similarity: {similarity:.4f}")  # ADD THIS
        
#         if not is_match:
#             whisper_task.cancel()  # Cancel transcription if voice doesn't match
#             print(f"❌ [{module_name}] Voice match failed")  # ADD THIS
#             return {
#                 "error": "وائس میچ نہیں ہوئی۔",
#                 "message": f"مماثلت: {similarity:.2%} - یہ آپ کی آواز نہیں لگتی۔",
#                 "voice_verified": False,
#                 "similarity": float(similarity),
#                 "module": module_name
#             }
        
#         # Step 3: Get transcription (may already be complete from parallel execution)
#         print(f"⏳ [{module_name}] Waiting for transcription...")  # ADD THIS
#         urdu_text = await whisper_task
        
#         if not urdu_text:
#             print(f"❌ [{module_name}] Transcription returned empty")  # ADD THIS
#             return {
#                 "error": "آواز کو متن میں تبدیل نہیں کر سکے۔",
#                 "message": "براہ کرم واضح بولیں اور دوبارہ کوشش کریں",
#                 "voice_verified": True,
#                 "similarity": float(similarity),
#                 "module": module_name
#             }
        
#         print(f"✅ [{module_name}] Final transcribed text: {urdu_text}")  # ADD THIS
        
#         # Step 4: Load prompt and call LLM
#         print(f"📄 [{module_name}] Loading prompt: {prompt_filename}")  # ADD THIS
#         prompt_template = load_prompt(prompt_filename)
#         full_prompt = f"{prompt_template}\n\nصارف کا جملہ: {urdu_text}"
        
#         print(f"🤖 [{module_name}] Sending to LLM...")  # ADD THIS
#         print(f"📤 [{module_name}] Prompt length: {len(full_prompt)} characters")  # ADD THIS
        
#         llm_result = await client.call_llm(full_prompt)
        
#         print(f"📥 [{module_name}] LLM Response: {json.dumps(llm_result, ensure_ascii=False, indent=2)}")  # ADD THIS
        
#         # Step 5: Add metadata
#         if isinstance(llm_result, dict):
#             llm_result.update({
#                 "user_id": current_user.user_id,
#                 "user_email": current_user.email,
#                 "original_text": urdu_text,
#                 "voice_verified": True,
#                 "similarity": float(similarity),
#                 "module": module_name
#             })
#         else:
#             llm_result = {
#                 "error": "Invalid LLM response format",
#                 "original_text": urdu_text,
#                 "voice_verified": True,
#                 "similarity": float(similarity),
#                 "module": module_name
#             }
        
#         print(f"✅ [{module_name}] Processing complete!")  # ADD THIS
#         print(f"{'='*60}\n")  # ADD THIS
        
#         return llm_result
        
#     except asyncio.CancelledError:
#         print(f"⚠️ [{module_name}] Request cancelled")  # ADD THIS
#         return {
#             "error": "درخواست منسوخ کر دی گئی۔",
#             "voice_verified": False,
#             "module": module_name
#         }
#     except Exception as e:
#         print(f"❌ [{module_name}] Error: {str(e)}")  # ADD THIS
#         import traceback
#         traceback.print_exc()  # ADD THIS - prints full error traceback
#         return {
#             "error": f"پروسیسنگ میں خرابی: {str(e)}",
#             "message": "براہ کرم دوبارہ کوشش کریں",
#             "voice_verified": False,
#             "module": module_name
#         }
    
# # Cleanup function
# async def cleanup():
#     """Clean up resources"""
#     await AiohttpSessionManager.close()
#     print("✅ AI Models cleanup complete")


# myapp/crud/ai_models/ai_models_base.py - Complete optimized base

import json
import base64
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List
from functools import lru_cache
import aiohttp
from sqlalchemy.ext.asyncio import AsyncSession
from myapp.config import settings
from myapp.models.user import User
from myapp.utils.voice import match_voice
import traceback 

# ============================================
# OPTIMIZATION: Singleton HTTP Session Manager
# ============================================
class AiohttpSessionManager:
    """Reuse HTTP sessions for better performance"""
    _session: Optional[aiohttp.ClientSession] = None
    _connector: Optional[aiohttp.TCPConnector] = None
    
    @classmethod
    async def get_session(cls) -> aiohttp.ClientSession:
        if cls._session is None or cls._session.closed:
            cls._connector = aiohttp.TCPConnector(
                limit=50,
                limit_per_host=10,
                ttl_dns_cache=300,
                use_dns_cache=True,
                enable_cleanup_closed=True
            )
            timeout = aiohttp.ClientTimeout(
                total=25,
                connect=5,
                sock_read=20
            )
            cls._session = aiohttp.ClientSession(
                connector=cls._connector,
                timeout=timeout
            )
        return cls._session
    
    @classmethod
    async def close(cls):
        if cls._session and not cls._session.closed:
            await cls._session.close()
            cls._session = None

# ============================================
# OPTIMIZATION: API Key Manager per Module
# ============================================
class APIKeyManager:
    """Manages API keys for different modules"""
    
    MODULE_KEYS = {
        "items": [
            settings.GROQ_API_KEY,
            settings.GROQ_API_KEY8,
            settings.GROQ_API_KEY13,
        ],
        "udhaar_items": [
            settings.GROQ_API_KEY4,
            settings.GROQ_API_KEY5,
            settings.GROQ_API_KEY6,
        ],
        "udhaars": [
            settings.GROQ_API_KEY7,
            settings.GROQ_API_KEY8,
            settings.GROQ_API_KEY9,
        ],
        "bills": [
            settings.GROQ_API_KEY10,
            settings.GROQ_API_KEY11,
            settings.GROQ_API_KEY12,
        ],
    }
    
    @classmethod
    def get_keys(cls, module: str) -> List[str]:
        """Get valid API keys for a specific module"""
        keys = cls.MODULE_KEYS.get(module, [])
        return [key for key in keys if key and key != "null"]
    
    @classmethod
    def get_all_modules(cls) -> List[str]:
        """Get list of all available modules"""
        return list(cls.MODULE_KEYS.keys())

# ============================================
# API Constants
# ============================================
WHISPER_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"

# ============================================
# OPTIMIZATION: Cached Prompt Loading
# ============================================
@lru_cache(maxsize=10)
def load_prompt(prompt_filename: str) -> str:
    """Cache prompts to avoid repeated file I/O"""
    prompt_path = Path(f"myapp/prompts/{prompt_filename}")
    if not prompt_path.exists():
        print(f"⚠️  Prompt file '{prompt_filename}' موجود نہیں ہے")
        return "You are an expert Data Extractor for Shop Management System. Extract information. Return ONLY JSON."
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read().strip()

# ============================================
# OPTIMIZATION: Per-Module Groq API Client
# ============================================
class GroqAPIClient:
    """Optimized Groq API client with module-specific key rotation"""
    
    def __init__(self, module_name: str):
        self.module_name = module_name
        self.api_keys = APIKeyManager.get_keys(module_name)
        self._key_index = 0
        
        if not self.api_keys:
            print(f"⚠️  ماڈیول '{module_name}' کے لیے کوئی API کی ترتیب نہیں ہے")
        else:
            print(f"✅ ماڈیول '{module_name}' {len(self.api_keys)} API کیز کے ساتھ تیار ہے")
    
    async def call_llm(self, prompt: str, model: str = "llama-3.1-8b-instant") -> Dict:
        """Call LLM with automatic key rotation for this module"""
        if not self.api_keys:
            return {"error": f"ماڈیول '{self.module_name}' کے لیے کوئی API کی ترتیب نہیں ہے"}
        
        session = await AiohttpSessionManager.get_session()
        errors = []
        
        for key in self._rotate_keys():
            try:
                headers = {"Authorization": f"Bearer {key}"}
                json_data = {
                    "model": model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "Return ONLY valid JSON. No explanations, no extra text."
                        },
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0,
                    "max_tokens": 1000,
                    "response_format": {"type": "json_object"}
                }
                
                async with session.post(CHAT_URL, headers=headers, json=json_data, timeout=20) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = data["choices"][0]["message"]["content"]
                        clean_json = content.replace("```json", "").replace("```", "").strip()
                        return json.loads(clean_json)
                    elif response.status == 429:
                        print(f"[{self.module_name}] API کی حد ختم، دوسری کلید استعمال کر رہے ہیں...")
                        continue
                    else:
                        error_text = await response.text()
                        errors.append(f"Status {response.status}: {error_text[:100]}")
                        continue
                        
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                errors.append(str(e)[:100])
                continue
        
        return {
            "error": f"آپ کی تمام درخواستیں ختم ہو چکی ہیں۔ براہ کرم 24 گھنٹے بعد دوبارہ کوشش کریں۔",
            "details": errors[:3]
        }
    
    async def call_whisper(self, audio_base64: str) -> Optional[str]:
        """Call Whisper API with key rotation for this module"""
        if not self.api_keys:
            return None
        
        session = await AiohttpSessionManager.get_session()
        
        for key in self._rotate_keys():
            try:
                audio_bytes = base64.b64decode(audio_base64)
                
                form_data = aiohttp.FormData()
                form_data.add_field(
                    "file", audio_bytes,
                    filename="audio.wav",
                    content_type="audio/wav"
                )
                form_data.add_field("model", "whisper-large-v3-turbo")
                form_data.add_field("language", "ur")
                form_data.add_field("response_format", "json")
                form_data.add_field("temperature", "0")
                
                headers = {"Authorization": f"Bearer {key}"}
                
                print(f"🎤 [{self.module_name}] آواز پروسیس ہو رہی ہے...")
                
                async with session.post(WHISPER_URL, headers=headers, data=form_data, timeout=30) as response:
                    if response.status == 200:
                        result = await response.json()
                        text = result.get("text", "")
                        if text:
                            print(f"✅ [{self.module_name}] آواز متن میں تبدیل ہو گئی")
                            print(f"📝 [{self.module_name}] تحریری متن: {text}")
                            return text
                    elif response.status == 429:
                        print(f"[{self.module_name}] آواز کی API حد ختم، دوسری کلید استعمال کر رہے ہیں...")
                        continue
                            
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                print(f"[{self.module_name}] آواز پروسیسنگ میں نیٹ ورک کی خرابی: {str(e)[:100]}")
                continue
        
        print(f"❌ [{self.module_name}] آواز کو متن میں تبدیل نہیں کیا جا سکا - تمام کیز ختم")
        return None
    
    def _rotate_keys(self):
        """Generator for key rotation within this module"""
        if not self.api_keys:
            return
        
        start_idx = self._key_index % len(self.api_keys)
        for i in range(len(self.api_keys)):
            idx = (start_idx + i) % len(self.api_keys)
            self._key_index = (idx + 1) % len(self.api_keys)
            yield self.api_keys[idx]

# ============================================
# OPTIMIZATION: Client Pool (one client per module)
# ============================================
class ClientPool:
    """Manages Groq API clients for all modules"""
    _clients: Dict[str, GroqAPIClient] = {}
    
    @classmethod
    def get_client(cls, module_name: str) -> GroqAPIClient:
        """Get or create client for a module"""
        if module_name not in cls._clients:
            cls._clients[module_name] = GroqAPIClient(module_name)
        return cls._clients[module_name]
    
    @classmethod
    def get_status(cls) -> Dict[str, Any]:
        """Get status of all module clients"""
        status = {}
        for module_name, client in cls._clients.items():
            status[module_name] = {
                "total_keys": len(client.api_keys),
                "available": len(client.api_keys) > 0,
                "current_key_index": client._key_index
            }
        return status

# ============================================
# OPTIMIZATION: Unified Voice Processing Pipeline
# ============================================
async def process_voice_pipeline(
    audio_base64: str,
    current_user: User,
    db: AsyncSession,
    prompt_filename: str,
    module_name: str
) -> Dict[str, Any]:
    """
    Unified pipeline for all voice processing tasks
    Each module uses its own set of API keys
    """
    
    # Step 1: Quick validation
    if not current_user.voice_embedding:
        return {
            "error": "آپ کی وائس رجسٹرڈ نہیں ہے۔",
            "message": "براہ کرم پہلے وائس رجسٹر کریں",
            "voice_verified": False,
            "module": module_name
        }
    
    # Get module-specific client
    client = ClientPool.get_client(module_name)
    
    try:
        print(f"\n{'='*60}")
        print(f"🚀 [{module_name}] وائس پروسیسنگ شروع ہو رہی ہے")
        print(f"{'='*60}")
        
        # Step 2: PARALLEL - Voice verification + Whisper transcription
        print(f"🔄 [{module_name}] وائس تصدیق اور تحریر بیک وقت ہو رہی ہے...")
        voice_task = asyncio.create_task(
            match_voice(current_user.voice_embedding, audio_base64)
        )
        whisper_task = asyncio.create_task(
            client.call_whisper(audio_base64)
        )
        
        # Wait for voice verification first (security priority)
        is_match, similarity = await voice_task
        print(f"🔐 [{module_name}] وائس تصدیق مکمل - مماثلت: {similarity:.4f}")
        
        if not is_match:
            whisper_task.cancel()
            print(f"❌ [{module_name}] وائس میچ نہیں ہوئی")
            return {
                "error": "وائس میچ نہیں ہوئی۔",
                "message": f"مماثلت: {similarity:.2%} - یہ آپ کی آواز نہیں لگتی۔",
                "voice_verified": False,
                "similarity": float(similarity),
                "module": module_name
            }
        
        # Step 3: Get transcription
        print(f"⏳ [{module_name}] تحریر کا انتظار ہو رہا ہے...")
        urdu_text = await whisper_task
        
        if not urdu_text:
            print(f"❌ [{module_name}] تحریر خالی ہے")
            return {
                "error": "آواز کو متن میں تبدیل نہیں کر سکے۔",
                "message": "براہ کرم واضح بولیں اور دوبارہ کوشش کریں",
                "voice_verified": True,
                "similarity": float(similarity),
                "module": module_name
            }
        
        print(f"✅ [{module_name}] تحریری متن: {urdu_text}")
        
        # Step 4: Load prompt and call LLM
        print(f"📄 [{module_name}] پرامپٹ لوڈ ہو رہا ہے: {prompt_filename}")
        prompt_template = load_prompt(prompt_filename)
        full_prompt = f"{prompt_template}\n\nصارف کا جملہ: {urdu_text}"
        
        print(f"🤖 [{module_name}] کمانڈ پروسیس ہو رہی ہے...")
        print(f"📤 [{module_name}] پرامپٹ کی لمبائی: {len(full_prompt)} حروف")
        
        llm_result = await client.call_llm(full_prompt)
        
        print(f"📥 [{module_name}] جواب: {json.dumps(llm_result, ensure_ascii=False, indent=2)}")
        
        # Step 5: Add metadata
        if isinstance(llm_result, dict):
            llm_result.update({
                "user_id": current_user.user_id,
                "user_email": current_user.email,
                "original_text": urdu_text,
                "voice_verified": True,
                "similarity": float(similarity),
                "module": module_name
            })
        else:
            llm_result = {
                "error": "کمانڈ سمجھ نہیں آئی",
                "original_text": urdu_text,
                "voice_verified": True,
                "similarity": float(similarity),
                "module": module_name
            }
        
        print(f"✅ [{module_name}] پروسیسنگ مکمل!")
        print(f"{'='*60}\n")
        
        return llm_result
        
    except asyncio.CancelledError:
        print(f"⚠️ [{module_name}] درخواست منسوخ کر دی گئی")
        return {
            "error": "درخواست منسوخ کر دی گئی۔",
            "voice_verified": False,
            "module": module_name
        }
    except Exception as e:
        print(f"❌ [{module_name}] خرابی: {str(e)}")
        traceback.print_exc()
        return {
            "error": f"پروسیسنگ میں خرابی: {str(e)}",
            "message": "براہ کرم دوبارہ کوشش کریں",
            "voice_verified": False,
            "module": module_name
        }

# Cleanup function
async def cleanup():
    """Clean up resources"""
    await AiohttpSessionManager.close()
    print("✅ AI ماڈلز بند کر دیے گئے")