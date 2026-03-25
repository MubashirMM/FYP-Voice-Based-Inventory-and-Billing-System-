from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from fastapi.security import OAuth2PasswordRequestForm

from myapp.crud.user import (
    authenticate_voice, register_user, authenticate_user, get_all_users,
    initiate_password_reset, reset_password_in_db, delete_user, save_voice_samples,
    update_user_by_id
)
from myapp.database.session import get_db
from myapp.schemas.user import (
    UserRegister, UserRead, PasswordResetConfirm, ProfileUpdate,
    UserVoiceLogin, VoiceSamplesSave
)
from myapp.services.email import send_email, get_registration_template, get_reset_template
from myapp.utils.security import create_access_token 
router = APIRouter(prefix="/auth", tags=["Authentication"])

# ---------------------------
# Register
# ---------------------------
@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(payload: UserRegister, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    user = await register_user(db, payload.email, payload.username, payload.password)
    background_tasks.add_task(send_email, user.email, "VBUGIMS میں خوش آمدید", get_registration_template())
    return {"detail": "اکاؤنٹ کامیابی سے بنا دیا گیا ہے"}

# ---------------------------
# Login (Password)
# ---------------------------
@router.post("/login")
async def login(payload: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    try:
        token = await authenticate_user(db, payload.username, payload.password)
        return {"access_token": token, "token_type": "bearer"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"لاگ ان کے دوران خرابی: {str(e)}"
        )

# ---------------------------
# Update Profile
# ---------------------------
@router.patch("/users/{user_id}", status_code=status.HTTP_200_OK)
async def patch_user_profile(user_id: int, payload: ProfileUpdate, db: AsyncSession = Depends(get_db)):
    updated_user = await update_user_by_id(db, user_id, payload)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"صارف {user_id} نہیں ملا"
        )
    return {
        "detail": "پروفائل کامیابی سے اپ ڈیٹ کر دیا گیا ہے",
        "صارف": {
            "id": updated_user.user_id,
            "username": updated_user.username,
            "email": updated_user.email
        }
    }

# ---------------------------
# Forgot Password
# ---------------------------
@router.post("/forgot-password")
async def forgot_password(email: str, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    code = await initiate_password_reset(db, email)
    if not code:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ای میل موجود نہیں ہے"
        )
    background_tasks.add_task(send_email, email, "پاس ورڈ ری سیٹ کوڈ", get_reset_template(code))
    return {"پیغام": "ری سیٹ کوڈ آپ کی ای میل پر بھیج دیا گیا ہے"}

# ---------------------------
# Reset Password Confirm
# ---------------------------
@router.post("/reset-password-confirm")
async def reset_password_confirm(payload: PasswordResetConfirm, db: AsyncSession = Depends(get_db)):
    success = await reset_password_in_db(db, payload.email, payload.reset_code, payload.new_password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="غلط کوڈ یا ای میل۔ براہ کرم دوبارہ کوشش کریں۔"
        )
    return {"پیغام": "پاس ورڈ کامیابی سے تبدیل کر دیا گیا ہے"}

# ---------------------------
# Get Users
# ---------------------------
@router.get("/users", response_model=List[UserRead])
async def get_users(db: AsyncSession = Depends(get_db)):
    return await get_all_users(db)

# ---------------------------
# Delete User
# ---------------------------
@router.delete("/users/{user_id}", status_code=status.HTTP_200_OK)
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

# ---------------------------
# Save Voice Samples
# ---------------------------
@router.post("/save-voice-samples")
async def save_voice(payload: VoiceSamplesSave, db: AsyncSession = Depends(get_db)):
    user = await save_voice_samples(db, payload.email, payload.samples)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="صارف نہیں ملا"
        )
    return {"پیغام": "وائس سیمپلز کامیابی سے محفوظ کر دیے گئے ہیں"}

# ---------------------------
# Voice Login
# ---------------------------
@router.post("/voice-login")
async def voice_login(payload: UserVoiceLogin, db: AsyncSession = Depends(get_db)):
    try:
        print("[voice_login] email:", payload.email)
        user = await authenticate_voice(db, payload.email, payload.audio_base64)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="آواز میل نہیں کھاتی۔ دوبارہ کوشش کریں۔"
            )
       # Wrap the user_id in a dictionary
        token = create_access_token(data={"sub": str(user.user_id)})
        print("[voice_login] success for user_id:", user.user_id)
        return {"access_token": token, "token_type": "bearer"}
    except HTTPException:
        raise
    except Exception as e:
        print("[voice_login] ERROR:", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"وائس لاگ ان کے دوران خرابی: {str(e)}"
        )
