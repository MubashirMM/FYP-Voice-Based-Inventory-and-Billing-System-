# voice/command.py
from myapp.voice.noise import reduce_noise
from myapp.voice.speaker import extract_embedding, match_speaker
from myapp.voice.messages import urdu_response
from myapp.voice.asr import transcribe_urdu
from myapp.voice.ner import extract_entities
from myapp.voice.dispatcher import dispatch_action
from myapp.crud.user import get_user_embedding

async def process_voice_command(user_id: int, audio, sr: int):
    clean_audio = reduce_noise(audio, sr)

    # 1) Speaker embedding
    embedding = extract_embedding(clean_audio, sr)
    stored_embedding = await get_user_embedding(user_id)

    # 2) Match
    if not match_speaker(embedding, stored_embedding):
        return await urdu_response(
            "آپ کی آواز کی تصدیق نہیں ہو سکی"
        )

    # 3) ASR
    text = await transcribe_urdu(clean_audio)

    if not text:
        return await urdu_response(
            "آواز سمجھ میں نہیں آئی"
        )

    # 4) NER
    entities = extract_entities(text)

    # 5) Action execution
    result = await dispatch_action(user_id, entities)

    return await urdu_response(
        result["message"]
    )
