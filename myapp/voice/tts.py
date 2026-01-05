# voice/tts.py
import asyncio
import edge_tts
import uuid
from pathlib import Path

VOICE = "ur-PK-AsadNeural"

async def speak_urdu(text: str):
    output_file = Path(f"/tmp/{uuid.uuid4()}.mp3")
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(output_file)

    # play sound (server-side OR return file to frontend)
    # frontend usually plays this file
    return str(output_file)
