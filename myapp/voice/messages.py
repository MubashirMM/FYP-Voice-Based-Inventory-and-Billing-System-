# voice/messages.py
from myapp.voice.tts import speak_urdu

async def urdu_response(text: str, speak: bool = True):
    """
    Returns Urdu message and optionally speaks it
    """
    if speak:
        await speak_urdu(text)
    return {"message": text}
