
# import base64
# import io
# import numpy as np
# import soundfile as sf
# from resemblyzer import VoiceEncoder, preprocess_wav

# # Model being used: Resemblyzer VoiceEncoder
# # This is a pre-trained deep learning model for speaker verification
# # It creates 256-dimensional voice embeddings from audio samples

# encoder = VoiceEncoder()

# def audio_to_embedding(audio_b64: str) -> np.ndarray:
#     """Convert base64 audio to voice embedding"""
#     audio_bytes = base64.b64decode(audio_b64)
#     audio_file = io.BytesIO(audio_bytes)
#     wav, sampling_rate = sf.read(audio_file)

#     if wav.size == 0:
#         raise ValueError("Audio file is empty or unreadable")

#     if len(wav.shape) > 1:
#         wav = np.mean(wav, axis=1)

#     wav = preprocess_wav(wav, source_sr=sampling_rate).astype(np.float32)
#     emb = encoder.embed_utterance(wav)
#     return emb

# def combine_embeddings(samples: list[str]) -> bytes:
#     """Average multiple voice embeddings and store as bytes"""
#     embs = [audio_to_embedding(s) for s in samples]
#     avg_emb = np.mean(embs, axis=0)
#     return avg_emb.astype(np.float32).tobytes()

# def match_voice(stored_bytes: bytes, new_sample_b64: str, threshold: float = 0.7) -> tuple[bool, float]:
#     """
#     Match voice with 70% threshold requirement
#     Returns: (is_match, similarity_score)
#     """
#     stored_emb = np.frombuffer(stored_bytes, dtype=np.float32)
#     new_emb = audio_to_embedding(new_sample_b64)

#     if stored_emb.ndim == 0 or new_emb.ndim == 0:
#         raise ValueError("Invalid embedding: got scalar instead of vector")

#     # Calculate cosine similarity
#     similarity = np.dot(stored_emb, new_emb) / (np.linalg.norm(stored_emb) * np.linalg.norm(new_emb))
    
#     is_match = similarity > threshold
    
#     print(f"[match_voice] Similarity: {similarity:.4f} | Threshold: {threshold} | Match: {is_match}")
    
#     return is_match, similarity

import base64
import io
import asyncio
import numpy as np
import soundfile as sf
from resemblyzer import VoiceEncoder, preprocess_wav
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor

# Thread pool for CPU-bound operations
_voice_executor = ThreadPoolExecutor(max_workers=4)

# Singleton pattern for VoiceEncoder (load once, reuse forever)
_encoder = None

def get_encoder():
    """Get or create singleton VoiceEncoder instance"""
    global _encoder
    if _encoder is None:
        # VoiceEncoder loads a pretrained model (~100MB)
        # This happens only once at startup
        _encoder = VoiceEncoder()
    return _encoder

def audio_to_embedding_sync(audio_b64: str, target_sr: int = 16000) -> np.ndarray:
    """
    Convert base64 audio to voice embedding (synchronous version)
    Optimized with lower sample rate for faster processing
    """
    try:
        # Decode base64 to audio bytes
        audio_bytes = base64.b64decode(audio_b64)
        audio_file = io.BytesIO(audio_bytes)
        
        # Read audio file
        wav, sampling_rate = sf.read(audio_file)
        
        if wav.size == 0:
            raise ValueError("Audio file is empty or unreadable")
        
        # Convert to mono if stereo
        if len(wav.shape) > 1:
            wav = np.mean(wav, axis=1)
        
        # Optional: Resample to lower rate for faster processing
        # Uncomment if you want faster but slightly less accurate
        # if sampling_rate > target_sr:
        #     from scipy import signal
        #     wav = signal.resample(wav, int(len(wav) * target_sr / sampling_rate))
        #     sampling_rate = target_sr
        
        # Preprocess for Resemblyzer
        wav = preprocess_wav(wav, source_sr=sampling_rate).astype(np.float32)
        
        # Get voice encoder (singleton)
        encoder = get_encoder()
        
        # Generate embedding
        emb = encoder.embed_utterance(wav)
        
        return emb
        
    except Exception as e:
        raise ValueError(f"Failed to process audio: {str(e)}")

async def audio_to_embedding(audio_b64: str) -> np.ndarray:
    """
    Async wrapper for CPU-bound audio processing
    Runs in thread pool to not block the event loop
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_voice_executor, audio_to_embedding_sync, audio_b64)

def combine_embeddings_sync(samples: list[str]) -> bytes:
    """Average multiple voice embeddings and store as bytes (synchronous)"""
    if not samples:
        raise ValueError("No voice samples provided")
    
    embs = [audio_to_embedding_sync(s) for s in samples]
    avg_emb = np.mean(embs, axis=0)
    return avg_emb.astype(np.float32).tobytes()

async def combine_embeddings(samples: list[str]) -> bytes:
    """Async version for registering multiple voice samples"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_voice_executor, combine_embeddings_sync, samples)

def match_voice_sync(stored_bytes: bytes, new_sample_b64: str, threshold: float = 0.7) -> tuple[bool, float]:
    """
    Match voice with threshold requirement (synchronous)
    Returns: (is_match, similarity_score)
    """
    try:
        # Reconstruct stored embedding
        stored_emb = np.frombuffer(stored_bytes, dtype=np.float32)
        
        # Generate embedding for new sample
        new_emb = audio_to_embedding_sync(new_sample_b64)
        
        if stored_emb.ndim == 0 or new_emb.ndim == 0:
            raise ValueError("Invalid embedding: got scalar instead of vector")
        
        # Calculate cosine similarity
        similarity = np.dot(stored_emb, new_emb) / (np.linalg.norm(stored_emb) * np.linalg.norm(new_emb))
        
        is_match = similarity > threshold
        
        return is_match, similarity
        
    except Exception as e:
        raise ValueError(f"Voice matching failed: {str(e)}")

async def match_voice(stored_bytes: bytes, new_sample_b64: str, threshold: float = 0.7) -> tuple[bool, float]:
    """
    Async version for voice login matching
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_voice_executor, match_voice_sync, stored_bytes, new_sample_b64, threshold)

# Optional: Preload the encoder at module load
def preload_encoder():
    """Call this during app startup to preload the model"""
    get_encoder()

# LRU cache for frequently used embeddings (optional)
@lru_cache(maxsize=100)
def get_cached_embedding(audio_hash: str) -> bytes:
    """Cache embeddings by audio hash for repeated logins"""
    # Note: This requires you to generate a hash of the audio
    # Implementation depends on your use case
    pass