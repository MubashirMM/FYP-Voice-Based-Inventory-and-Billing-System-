

# myapp/crud/ai_models/ai_models_udhaar_items.py
from myapp.crud.ai_models.ai_models_base import process_voice_pipeline

async def process_voice_udhaar_items(audio_base64, current_user, db):
    """Process voice to udhaar items - Uses API Keys 4,5,6"""
    return await process_voice_pipeline(
        audio_base64=audio_base64,
        current_user=current_user,
        db=db,
        prompt_filename="prompt_udhaar_items.txt",
        module_name="udhaar_items"
    )