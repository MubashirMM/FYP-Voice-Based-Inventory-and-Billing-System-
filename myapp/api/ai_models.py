from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from myapp.crud.ai_models import process_voice, process_text, full_voice_pipeline

router = APIRouter(tags=["AI Voice Commands"])


class TextRequest(BaseModel):
    text: str


@router.post("/voice-process")
async def voice_process_endpoint(audio: UploadFile = File(...)):
    """آڈیو اپلوڈ کریں اور ٹیکسٹ حاصل کریں"""
    try:
        audio.file.seek(0)
        result = process_voice(audio.file)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail="آڈیو پروسیس کرنے میں خرابی ہوئی۔ دوبارہ کوشش کریں۔")


@router.post("/text-process")
async def text_process_endpoint(data: TextRequest):
    """ٹیکسٹ بھیجیں اور JSON کمانڈ حاصل کریں"""
    try:
        result = process_text(data.text)
        return {"command": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail="ٹیکسٹ پروسیس کرنے میں مسئلہ پیش آیا۔")


@router.post("/voice-command")
async def voice_command_endpoint(audio: UploadFile = File(...)):
    """مکمل پائپ لائن: آڈیو → ٹیکسٹ → کمانڈ"""
    try:
        audio.file.seek(0)
        result = full_voice_pipeline(audio.file)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=400, 
            detail="وائس کمانڈ پروسیس کرنے میں خرابی آئی ہے۔ براہ مہربانی دوبارہ ٹرائی کریں۔"
        )