# voice/noise.py
import noisereduce as nr
import numpy as np

def reduce_noise(audio: np.ndarray, sr: int):
    return nr.reduce_noise(y=audio, sr=sr)
