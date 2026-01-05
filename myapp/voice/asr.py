# voice/asr.py
import whisper

model = whisper.load_model("medium")

async def transcribe_urdu(audio):
    result = model.transcribe(audio, language="ur")
    return result["text"]
