# voice/phrases/urdu_phrases.py
import random

PHRASES = [
    "میں اپنی آواز سے سسٹم استعمال کر رہا ہوں",
    "یہ آواز کی تصدیق کے لیے ایک جملہ ہے",
    "آج میں اپنی دکان کا حساب کر رہا ہوں",
    "میری آواز میری شناخت ہے",
    "میں اُردو میں بات کر رہا ہوں",
    # ... add 50–100
]

def get_random_phrase():
    return random.choice(PHRASES)
