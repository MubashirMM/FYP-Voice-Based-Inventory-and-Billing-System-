# voice/vad.py
import webrtcvad

vad = webrtcvad.Vad(2)

def has_voice(frame_bytes, sample_rate=16000):
    return vad.is_speech(frame_bytes, sample_rate)
