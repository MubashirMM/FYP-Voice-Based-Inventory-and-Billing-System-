# api/voice.py
from fastapi import APIRouter
from myapp.voice.phrases.urdu_phrases import get_random_phrase

router = APIRouter(prefix="/voice", tags=["voice"])

@router.get("/enrollment-phrase")
async def get_enrollment_phrase():
    phrase = get_random_phrase()
    return {
        "phrase": phrase,
        "message": "براہِ کرم یہ جملہ واضح آواز میں پڑھیں"
    }
