

# myapp/crud/ai_models/ai_models_udhaars.py
from myapp.crud.ai_models.ai_models_base import process_voice_pipeline

async def process_voice_udhaars(audio_base64, current_user, db):
    """Process voice to udhaars - Uses API Keys 7,8,9"""
    return await process_voice_pipeline(
        audio_base64=audio_base64,
        current_user=current_user,
        db=db,
        prompt_filename="prompt_udhaars.txt",
        module_name="udhaars"
    )