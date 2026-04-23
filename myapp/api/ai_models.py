from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from myapp.database.session import get_db
from myapp.crud.ai_models.ai_models_items import process_voice_items
from myapp.crud.ai_models.ai_models_cart import process_voice_cart
from myapp.crud.ai_models.ai_models_udhaar_items import process_voice_udhaar_items
from myapp.crud.ai_models.ai_models_udhaars import process_voice_udhaars


from myapp.utils.security import get_current_user
from myapp.models.user import User
from pydantic import BaseModel

router = APIRouter(tags=["AI Voice Commands"])

class VoiceItemsRequest(BaseModel):
    audio_base64: str

@router.post("/voice-process-items")
async def voice_process_endpoint(
    payload: VoiceItemsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    آواز سے آئٹمز پروسیس کریں - بیس 64 آڈیو بھیجیں (وائس لاگین کی طرح)
    """
    try:
        result = await process_voice_items(payload.audio_base64, current_user, db)
        
        # Check if result contains error
        if isinstance(result, dict) and "error" in result:
            raise HTTPException(status_code=400, detail=result)
        
        return result
        
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Error in voice_process_endpoint: {str(e)}")
        raise HTTPException(status_code=400, detail={"error": "آڈیو پروسیس کرنے میں خرابی ہوئی۔ دوبارہ کوشش کریں۔"})
    

@router.post("/voice-process-udhar-items")
async def voice_process_endpoint(
    payload: VoiceItemsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    آواز سے آئٹمز پروسیس کریں - بیس 64 آڈیو بھیجیں (وائس لاگین کی طرح)
    """
    try:
        result = await process_voice_udhaar_items(payload.audio_base64, current_user, db)
        
        # Check if result contains error
        if isinstance(result, dict) and "error" in result:
            raise HTTPException(status_code=400, detail=result)
        
        return result
        
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Error in voice_process_endpoint: {str(e)}")
        raise HTTPException(status_code=400, detail={"error": "آڈیو پروسیس کرنے میں خرابی ہوئی۔ دوبارہ کوشش کریں۔"})
    

    
@router.post("/voice-process-cart")
async def voice_process_endpoint(
    payload: VoiceItemsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    آواز سے آئٹمز پروسیس کریں - بیس 64 آڈیو بھیجیں (وائس لاگین کی طرح)
    """
    try:
        result = await process_voice_cart(payload.audio_base64, current_user, db)
        
        # Check if result contains error
        if isinstance(result, dict) and "error" in result:
            raise HTTPException(status_code=400, detail=result)
        
        return result
        
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Error in voice_process_endpoint: {str(e)}")
        raise HTTPException(status_code=400, detail={"error": "آڈیو پروسیس کرنے میں خرابی ہوئی۔ دوبارہ کوشش کریں۔"})
    
        
@router.post("/voice-process-udhaars")
async def voice_process_endpoint(
    payload: VoiceItemsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    آواز سے آئٹمز پروسیس کریں - بیس 64 آڈیو بھیجیں (وائس لاگین کی طرح)
    """
    try:
        result = await process_voice_udhaars(payload.audio_base64, current_user, db)
        
        # Check if result contains error
        if isinstance(result, dict) and "error" in result:
            raise HTTPException(status_code=400, detail=result)
        
        return result
        
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Error in voice_process_endpoint: {str(e)}")
        raise HTTPException(status_code=400, detail={"error": "آڈیو پروسیس کرنے میں خرابی ہوئی۔ دوبارہ کوشش کریں۔"})