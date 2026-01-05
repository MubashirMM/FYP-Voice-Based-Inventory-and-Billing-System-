
import numpy as np
from myapp.voice.noise import reduce_noise
from myapp.voice.vad import has_voice
from myapp.voice.speaker import (
    detect_speaker_count,
    extract_embedding
)
from myapp.voice.messages import urdu_response
# from myapp.crud.voice import get_phrase, clear_phrase
from myapp.crud.user import save_voice_embedding

REQUIRED_SAMPLES = 3


async def enroll_voice_samples(
    user_id: int,
    audio_samples: list,   
    sample_rate: int
):
    """
    Final enrollment pipeline (MULTI-SAMPLE)
    """

    if len(audio_samples) != REQUIRED_SAMPLES:
        return await urdu_response(
            f"براہِ کرم {REQUIRED_SAMPLES} آواز کی ریکارڈنگ فراہم کریں"
        )

    embeddings = []
    for idx, audio in enumerate(audio_samples, start=1):

        # Noise reduction
        clean_audio = reduce_noise(audio, sample_rate)

        # VAD check
        if not has_voice(clean_audio.tobytes()):
            return await urdu_response(
                f"ریکارڈنگ نمبر {idx} میں واضح آواز موجود نہیں"
            )

        # Speaker count check
        speaker_count = detect_speaker_count(clean_audio, sample_rate)
        if speaker_count != 1:
            return await urdu_response(
                "ریکارڈنگ میں ایک سے زیادہ آوازیں پائی گئیں، رجسٹریشن ممکن نہیں"
            )

        # Extract embedding
        embedding = extract_embedding(clean_audio, sample_rate)
        embeddings.append(embedding)

    # 3️⃣ Merge embeddings (average)
    final_embedding = np.mean(embeddings, axis=0)

    # 4️⃣ Save securely
    await save_voice_embedding(user_id, final_embedding)

    # # 5️⃣ Clear used phrase
    # clear_phrase(user_id)

    return await urdu_response(
        "آپ کی آواز کامیابی سے محفوظ کر لی گئی ہے"
    )
