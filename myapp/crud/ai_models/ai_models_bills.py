

# myapp/crud/ai_models/ai_models_bills.py
from myapp.crud.ai_models.ai_models_base import process_voice_pipeline

async def process_voice_bills(audio_base64, current_user, db):
    """Process voice to bills - Uses API Keys 10,11,12"""
    return await process_voice_pipeline(
        audio_base64=audio_base64,
        current_user=current_user,
        db=db,
        prompt_filename="prompt_bills.txt",
        module_name="bills"
    )