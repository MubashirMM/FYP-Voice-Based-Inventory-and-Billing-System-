# from fastapi import APIRouter, Depends, HTTPException, status
# from sqlalchemy.ext.asyncio import AsyncSession
# from myapp.database.session import get_db
# from myapp.crud.ai_models.ai_models_items import process_voice_items
# from myapp.crud.ai_models.ai_models_udhaar_items import process_voice_udhaar_items
# from myapp.crud.ai_models.ai_models_udhaars import process_voice_udhaars
# from myapp.crud.ai_models.ai_models_bills import process_voice_bills 


# from myapp.utils.security import get_current_user
# from myapp.models.user import User
# from pydantic import BaseModel

# router = APIRouter(tags=["AI Voice Commands"])

# class VoiceItemsRequest(BaseModel):
#     audio_base64: str

# @router.post("/voice-process-items")
# async def voice_process_endpoint(
#     payload: VoiceItemsRequest,
#     db: AsyncSession = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     """
#     آواز سے آئٹمز پروسیس کریں - بیس 64 آڈیو بھیجیں (وائس لاگین کی طرح)
#     """
#     try:
#         result = await process_voice_items(payload.audio_base64, current_user, db)
        
#         # Check if result contains error
#         if isinstance(result, dict) and "error" in result:
#             raise HTTPException(status_code=400, detail=result)
        
#         return result
        
#     except HTTPException as e:
#         raise e
#     except Exception as e:
#         print(f"Error in voice_process_endpoint: {str(e)}")
#         raise HTTPException(status_code=400, detail={"error": "آڈیو پروسیس کرنے میں خرابی ہوئی۔ دوبارہ کوشش کریں۔"})
    

# @router.post("/voice-process-udhar-items")
# async def voice_process_endpoint(
#     payload: VoiceItemsRequest,
#     db: AsyncSession = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     """
#     آواز سے آئٹمز پروسیس کریں - بیس 64 آڈیو بھیجیں (وائس لاگین کی طرح)
#     """
#     try:
#         result = await process_voice_udhaar_items(payload.audio_base64, current_user, db)
        
#         # Check if result contains error
#         if isinstance(result, dict) and "error" in result:
#             raise HTTPException(status_code=400, detail=result)
        
#         return result
        
#     except HTTPException as e:
#         raise e
#     except Exception as e:
#         print(f"Error in voice_process_endpoint: {str(e)}")
#         raise HTTPException(status_code=400, detail={"error": "آڈیو پروسیس کرنے میں خرابی ہوئی۔ دوبارہ کوشش کریں۔"})
    

# @router.post("/voice-process-udhaars")
# async def voice_process_endpoint(
#     payload: VoiceItemsRequest,
#     db: AsyncSession = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     """
#     آواز سے آئٹمز پروسیس کریں - بیس 64 آڈیو بھیجیں (وائس لاگین کی طرح)
#     """
#     try:
#         result = await process_voice_udhaars(payload.audio_base64, current_user, db)
        
#         # Check if result contains error
#         if isinstance(result, dict) and "error" in result:
#             raise HTTPException(status_code=400, detail=result)
        
#         return result
        
#     except HTTPException as e:
#         raise e
#     except Exception as e:
#         print(f"Error in voice_process_endpoint: {str(e)}")
#         raise HTTPException(status_code=400, detail={"error": "آڈیو پروسیس کرنے میں خرابی ہوئی۔ دوبارہ کوشش کریں۔"})
    
           
# @router.post("/voice-process-bills")
# async def voice_process_endpoint(
#     payload: VoiceItemsRequest,
#     db: AsyncSession = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     """
#     آواز سے آئٹمز پروسیس کریں - بیس 64 آڈیو بھیجیں (وائس لاگین کی طرح)
#     """
#     try:
#         result = await process_voice_bills(payload.audio_base64, current_user, db)
        
#         # Check if result contains error
#         if isinstance(result, dict) and "error" in result:
#             raise HTTPException(status_code=400, detail=result)
        
#         return result
        
#     except HTTPException as e:
#         raise e
#     except Exception as e:
#         print(f"Error in voice_process_endpoint: {str(e)}")
#         raise HTTPException(status_code=400, detail={"error": "آڈیو پروسیس کرنے میں خرابی ہوئی۔ دوبارہ کوشش کریں۔"})

# myapp/api/ai_models.py - Optimized router

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
import asyncio
import time
from typing import Optional, Dict, Any

from myapp.database.session import get_db
from myapp.utils.security import get_current_user
from myapp.models.user import User

# Import all voice processors
from myapp.crud.ai_models.ai_models_items import process_voice_items
from myapp.crud.ai_models.ai_models_udhaar_items import process_voice_udhaar_items
from myapp.crud.ai_models.ai_models_udhaars import process_voice_udhaars
from myapp.crud.ai_models.ai_models_bills import process_voice_bills
from myapp.crud.ai_models.ai_models_base import ClientPool, cleanup

router = APIRouter(tags=["AI Voice Commands"])

# ============================================
# Request/Response Models
# ============================================
class VoiceRequest(BaseModel):
    audio_base64: str = Field(..., description="Base64 encoded audio string")
    
    class Config:
        json_schema_extra = {
            "example": {
                "audio_base64": "UklGRiQAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQAAAAA="
            }
        }

class VoiceResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    processing_time_ms: Optional[float] = None
    module: Optional[str] = None

# ============================================
# Generic handler to reduce code duplication
# ============================================
async def handle_voice_request(
    payload: VoiceRequest,
    db: AsyncSession,
    current_user: User,
    processor_func,
    module_name: str
):
    """Generic handler for all voice processing endpoints"""
    start_time = time.time()
    
    try:
        # Process with 30-second timeout
        result = await asyncio.wait_for(
            processor_func(payload.audio_base64, current_user, db),
            timeout=30.0
        )
        
        processing_time = (time.time() - start_time) * 1000  # Convert to ms
        
        if isinstance(result, dict) and "error" in result:
            return VoiceResponse(
                success=False,
                error=result["error"],
                processing_time_ms=processing_time,
                module=module_name,
                data=result  # Include full error details
            )
        
        return VoiceResponse(
            success=True,
            data=result,
            processing_time_ms=processing_time,
            module=module_name
        )
        
    except asyncio.TimeoutError:
        return VoiceResponse(
            success=False,
            error="درخواست کا وقت ختم ہو گیا۔ براہ کرم دوبارہ کوشش کریں۔",
            processing_time_ms=30000,
            module=module_name
        )
    except Exception as e:
        return VoiceResponse(
            success=False,
            error=f"سرور کی خرابی: {str(e)}",
            module=module_name
        )

# ============================================
# Voice Processing Endpoints
# ============================================
@router.post("/voice-process-items", response_model=VoiceResponse)
async def voice_process_items(
    payload: VoiceRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """🎤 آواز سے آئٹمز پروسیس کریں (API Keys 1-3)"""
    return await handle_voice_request(
        payload, db, current_user, process_voice_items, "items"
    )

@router.post("/voice-process-udhar-items", response_model=VoiceResponse)
async def voice_process_udhar_items(
    payload: VoiceRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """🎤 آواز سے ادھار آئٹمز پروسیس کریں (API Keys 4-6)"""
    return await handle_voice_request(
        payload, db, current_user, process_voice_udhaar_items, "udhaar_items"
    )

@router.post("/voice-process-udhaars", response_model=VoiceResponse)
async def voice_process_udhaars(
    payload: VoiceRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """🎤 آواز سے ادھار پروسیس کریں (API Keys 7-9)"""
    return await handle_voice_request(
        payload, db, current_user, process_voice_udhaars, "udhaars"
    )

@router.post("/voice-process-bills", response_model=VoiceResponse)
async def voice_process_bills(
    payload: VoiceRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """🎤 آواز سے بل پروسیس کریں (API Keys 10-12)"""
    return await handle_voice_request(
        payload, db, current_user, process_voice_bills, "bills"
    )

# ============================================
# API Status & Health Check
# ============================================
@router.get("/voice-api-status")
async def voice_api_status():
    """Check voice API configuration and key distribution"""
    status = ClientPool.get_status()
    
    # Initialize clients to check all modules
    from myapp.crud.ai_models.ai_models_base import ClientPool
    for module in ["items", "udhaar_items", "udhaars", "bills"]:
        ClientPool.get_client(module)
    
    return {
        "service": "Groq AI Voice Processing",
        "modules": ClientPool.get_status(),
        "models": {
            "transcription": "whisper-large-v3-turbo",
            "llm": "llama-3.1-8b-instant"
        },
        "key_distribution": {
            "items": "Keys 1-3",
            "udhaar_items": "Keys 4-6",
            "udhaars": "Keys 7-9",
            "bills": "Keys 10-12"
        },
        "features": {
            "voice_verification": True,
            "parallel_processing": True,
            "per_module_keys": True,
            "key_rotation": True,
            "prompt_caching": True
        }
    }

@router.get("/voice-module-status/{module_name}")
async def voice_module_status(module_name: str):
    """Check status of a specific module"""
    if module_name not in ["items", "udhaar_items", "udhaars", "bills"]:
        raise HTTPException(status_code=404, detail=f"Module '{module_name}' not found")
    
    client = ClientPool.get_client(module_name)
    
    return {
        "module": module_name,
        "total_keys": len(client.api_keys),
        "keys_available": len(client.api_keys) > 0,
        "current_key_index": client._key_index,
        "keys_masked": [f"{k[:8]}..." if k else "empty" for k in client.api_keys]
    }

# ============================================
# Cleanup on shutdown
# ============================================
@router.on_event("shutdown")
async def shutdown_cleanup():
    """Clean up resources on shutdown"""
    await cleanup()