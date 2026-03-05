import base64
import io
import numpy as np
import soundfile as sf
from resemblyzer import VoiceEncoder, preprocess_wav

encoder = VoiceEncoder()

def audio_to_embedding(audio_b64: str) -> np.ndarray:
    audio_bytes = base64.b64decode(audio_b64)
    audio_file = io.BytesIO(audio_bytes)
    wav, sampling_rate = sf.read(audio_file)

    if wav.size == 0:
        raise ValueError("Audio file is empty or unreadable")

    if len(wav.shape) > 1:
        wav = np.mean(wav, axis=1)

    wav = preprocess_wav(wav, source_sr=sampling_rate).astype(np.float32)
    emb = encoder.embed_utterance(wav)
    return emb

def combine_embeddings(samples: list[str]) -> bytes:
    embs = [audio_to_embedding(s) for s in samples]
    print("[combine_embeddings] collected embeddings:", [e.shape for e in embs])
    avg_emb = np.mean(embs, axis=0)
    print("[combine_embeddings] avg_emb shape:", avg_emb.shape, "dtype:", avg_emb.dtype)
    return avg_emb.astype(np.float32).tobytes()

def match_voice(stored_bytes: bytes, new_sample_b64: str, threshold: float = 0.8) -> bool:
    stored_emb = np.frombuffer(stored_bytes, dtype=np.float32)
    new_emb = audio_to_embedding(new_sample_b64)

    if stored_emb.ndim == 0 or new_emb.ndim == 0:
        raise ValueError("Invalid embedding: got scalar instead of vector")

    print("[match_voice] stored_emb:", stored_emb.shape, "len bytes:", len(stored_bytes))
    print("[match_voice] new_emb:", new_emb.shape)

    sim = np.dot(stored_emb, new_emb) / (np.linalg.norm(stored_emb) * np.linalg.norm(new_emb))
    print("[match_voice] similarity:", sim)
    return sim > threshold
