
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

EMBEDDING_SIZE = 192
SPEAKER_MATCH_THRESHOLD = 0.75


def detect_speaker_count(audio: np.ndarray, sr: int) -> int:
    """
    Lightweight speaker count estimation.
    This does NOT identify who is who,
    only estimates number of speakers.
    """

    # Split audio into frames (e.g. 1 sec)
    frame_size = sr
    energies = []

    for i in range(0, len(audio), frame_size):
        frame = audio[i:i + frame_size]
        if len(frame) == 0:
            continue

        energy = np.sum(frame ** 2) / len(frame)
        energies.append(energy)

    if not energies:
        return 0

    energies = np.array(energies)

    # Normalize
    energies = (energies - energies.min()) / (energies.max() + 1e-9)

    # Heuristic:
    # Large variance → likely multiple speakers
    variance = np.var(energies)

    if variance > 0.02:
        return 2  # multiple speakers detected

    return 1

def extract_embedding(audio: np.ndarray, sr: int) -> np.ndarray:
    """
    Extract speaker embedding.
    Placeholder logic that mimics a real embedding model.

    Replace this with:
    - SpeechBrain ECAPA
    - NeMo speaker model
    """

    # Normalize audio
    audio = audio / (np.max(np.abs(audio)) + 1e-9)

    # ---- MOCK FEATURE EXTRACTION ----
    # In real model, MFCCs + deep net
    mfcc_like = np.mean(
        audio.reshape(-1, 160), axis=1
    )[:EMBEDDING_SIZE]

    # Ensure fixed length
    if len(mfcc_like) < EMBEDDING_SIZE:
        mfcc_like = np.pad(
            mfcc_like,
            (0, EMBEDDING_SIZE - len(mfcc_like))
        )

    embedding = mfcc_like.astype(np.float32)

    # L2 normalization (VERY IMPORTANT)
    norm = np.linalg.norm(embedding)
    if norm > 0:
        embedding = embedding / norm

    return embedding


def match_speaker(
    embedding: np.ndarray,
    stored_embedding: np.ndarray
) -> bool:
    """
    Compare live voice with stored voice.
    """

    similarity = cosine_similarity(
        embedding.reshape(1, -1),
        stored_embedding.reshape(1, -1)
    )[0][0]

    return similarity >= SPEAKER_MATCH_THRESHOLD
