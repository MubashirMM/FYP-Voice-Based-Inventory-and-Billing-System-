# import base64
# import numpy as np
# import tempfile
# from speechbrain.inference.speaker import SpeakerRecognition

# # Load model once
# model = SpeakerRecognition.from_hparams(source="speechbrain/spkrec-ecapa-voxceleb")

# def audio_to_embedding(audio_bytes: bytes) -> np.ndarray:
#     """Convert raw audio bytes to embedding vector safely."""
#     with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
#         tmp.write(audio_bytes)
#         tmp.flush()
#         emb = model.encode_file(tmp.name)
#     return emb.squeeze().numpy()
