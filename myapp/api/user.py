from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from myapp.database.session import get_db
from myapp.schemas.user import (
    UserRegister, UserRead, UserLogin, UserVoiceAdd, UserVoiceLogin, PasswordResetConfirm
)
from myapp.crud.user import (
    register_user, authenticate_user, get_all_users,
    initiate_password_reset, reset_password_in_db, delete_user,
    # add_user_voice_samples, login_with_voice
)
from myapp.services.email import send_email, get_registration_template

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(payload: UserRegister, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    user = await register_user(db, payload.email, payload.username, payload.password)
    background_tasks.add_task(send_email, user.email, "VBUGIMS میں خوش آمدید", get_registration_template())
    return {"پیغام": "اکاؤنٹ کامیابی سے بنا دیا گیا ہے"}

from fastapi.security import OAuth2PasswordRequestForm

@router.post("/login")
async def login(
    payload: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    try:
        token = await authenticate_user(db, payload.username, payload.password)
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="غلط ای میل یا پاس ورڈ"
            )
        return {"access_token": token, "token_type": "bearer"}
    except HTTPException:
        # re-raise known errors
        raise
    except Exception as e:
        # catch unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"لاگ ان کے دوران خرابی: {str(e)}"
        )

# @router.post("/login")
# async def login(payload: UserLogin, db: AsyncSession = Depends(get_db)):
#     token = await authenticate_user(db, payload.email, payload.password)
#     if not token:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="غلط ای میل یا پاس ورڈ")
#     return {"access_token": token, "token_type": "bearer"}

@router.post("/forgot-password")
async def forgot_password(email: str, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    code = await initiate_password_reset(db, email)
    if not code:
        return {"پیغام": "اگر یہ ای میل موجود ہے تو آپ کو کوڈ موصول ہو جائے گا"}
    return {"پیغام": "ری سیٹ کوڈ آپ کی ای میل پر بھیج دیا گیا ہے"}

@router.post("/reset-password-confirm")
async def reset_password_confirm(payload: PasswordResetConfirm, db: AsyncSession = Depends(get_db)):
    success = await reset_password_in_db(db, payload.email, payload.reset_code, payload.new_password)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="غلط کوڈ یا ای میل۔ براہ کرم دوبارہ کوشش کریں۔")
    return {"پیغام": "پاس ورڈ کامیابی سے تبدیل کر دیا گیا ہے"}

@router.get("/users", response_model=List[UserRead])
async def get_users(db: AsyncSession = Depends(get_db)):
    return await get_all_users(db)

@router.delete("/delete_user")
async def delete_user_endpoint(user_id: int, db: AsyncSession = Depends(get_db)):
    try:
        result = await delete_user(db, user_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="صارف موجود نہیں ہے یا پہلے ہی حذف کر دیا گیا ہے"
            )
        return {"پیغام": f"صارف {user_id} کامیابی سے حذف کر دیا گیا ہے"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"صارف کو حذف کرنے کے دوران خرابی: {str(e)}"
        )


# @router.post("/register-voice")
# async def add_voice_samples(data: UserVoiceAdd, db: AsyncSession = Depends(get_db)):
#     success = await add_user_voice_samples(db, data.user_id, data.voice_samples)
#     if not success:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not found or failed to save voice samples")
#     return {"message": f"Voice samples added successfully for user {data.user_id}. Voice login activated."}

# @router.post("/voice-login")
# async def voice_login(data: UserVoiceLogin, db: AsyncSession = Depends(get_db)):
#     token = await login_with_voice(db, data.email, data.audio_base64)
#     if not token:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Voice authentication failed")
#     return {"access_token": token, "token_type": "bearer"}
