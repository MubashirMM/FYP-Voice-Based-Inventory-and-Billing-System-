# api/voice_enroll.py
from fastapi import APIRouter, UploadFile, File, Depends
from myapp.voice.phrases.urdu_phrases import get_random_phrase
from myapp.crud.voice import save_phrase
from myapp.voice.enroll import enroll_voice_samples

router = APIRouter(prefix="/voice/enroll", tags=["Voice Enrollment"])

@router.get("/phrase")
async def get_enrollment_phrase(user_id: int):
    phrase = get_random_phrase()
    save_phrase(user_id, phrase)

    return {
        "phrase": phrase,
        "message": "براہِ کرم یہ جملہ واضح آواز میں پڑھیں"
    }

@router.post("/submit")
async def submit_voice_samples(
    user_id: int,
    audio1: UploadFile = File(...),
    audio2: UploadFile = File(...),
    audio3: UploadFile = File(...)
):
    # frontend must send WAV / PCM
    audios = []
    for audio in [audio1, audio2, audio3]:
        data = await audio.read()
        audios.append(data)  # decode to numpy later

    response = await enroll_voice_samples(
        user_id=user_id,
        audio_samples=audios,
        sample_rate=16000
    )

    return response
