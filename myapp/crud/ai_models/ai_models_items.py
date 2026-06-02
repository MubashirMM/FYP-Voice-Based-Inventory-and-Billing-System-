

# myapp/crud/ai_models/ai_models_items.py
from myapp.crud.ai_models.ai_models_base import process_voice_pipeline

async def process_voice_items(audio_base64, current_user, db):
    """Process voice to items - Uses API Keys 1,2,3"""
    return await process_voice_pipeline(
        audio_base64=audio_base64,
        current_user=current_user,
        db=db,
        prompt_filename="prompt_items.txt",
        module_name="items"
    )