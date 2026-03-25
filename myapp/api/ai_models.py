from fastapi import APIRouter, UploadFile, File
from pydantic import BaseModel
from myapp.crud.ai_models import process_voice, process_text, full_voice_pipeline

router = APIRouter(tags=["AI Models"])
 

class TextRequest(BaseModel):
    text: str


@router.post("/voice-process")
async def voice_process_endpoint(audio: UploadFile = File(...)):
    """
    Upload audio and get text
    """
    # ERROR FIX: always seek to start
    audio.file.seek(0) 
    result = process_voice(audio.file)
    return result


@router.post("/text-process")
async def text_process_endpoint(data: TextRequest):
    """
    Send text to LLM to get JSON command
    """
    result = process_text(data.text)
    return {"command": result}


@router.post("/voice-command")
async def voice_command_endpoint(audio: UploadFile = File(...)):
    """
    Full pipeline: audio → text → JSON command
    """
    audio.file.seek(0)
    result = full_voice_pipeline(audio.file)
    return result