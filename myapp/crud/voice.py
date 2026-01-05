# # crud/voice.py
# from datetime import datetime, timedelta

# _phrase_store = {}

# def save_phrase(user_id: int, phrase: str):
#     _phrase_store[user_id] = {
#         "phrase": phrase,
#         "expires_at": datetime.utcnow() + timedelta(seconds=60)
#     }

# def get_phrase(user_id: int):
#     data = _phrase_store.get(user_id)
#     if not data:
#         return None
#     if data["expires_at"] < datetime.utcnow():
#         del _phrase_store[user_id]
#         return None
#     return data["phrase"]

# def clear_phrase(user_id: int):
#     _phrase_store.pop(user_id, None)
