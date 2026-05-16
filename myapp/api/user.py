from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Annotated
from fastapi.security import OAuth2PasswordRequestForm

from myapp.models.user import User
from myapp.crud.user import (
    register_user,
    authenticate_user,
    get_all_users,
    initiate_password_reset,
    reset_password_in_db,
    delete_user,
    save_voice_samples,
    authenticate_voice,
    update_own_profile
)

from myapp.database.session import get_db
from myapp.schemas.user import (
    UserRegister,
    UserRead,
    UserReadWithUrduDate,
    PasswordResetConfirm,
    ProfileUpdate,
    UserVoiceLogin,
    VoiceSamplesSave
)

from myapp.utils.security import create_access_token, get_current_user
from myapp.utils.urdu_date import format_full_date_urdu

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ============================
# REGISTER
# ============================
@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(payload: UserRegister, db: AsyncSession = Depends(get_db)):
    await register_user(db, payload.email, payload.username, payload.password)
    return {"detail": "اکاؤنٹ کامیابی سے بنا دیا گیا ہے"}


# ============================
# LOGIN (PASSWORD)
# ============================
from fastapi import Response

@router.post("/login")
async def login(
    response: Response,
    payload: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    token = await authenticate_user(db, payload.username, payload.password)

    # Set HttpOnly cookie
    response.set_cookie(
        key="token",
        value=token,
        httponly=True,
        secure=True,       # only over HTTPS
        samesite="Strict", # prevent CSRF
        max_age=1800       # 30 minutes
    )

    return {"detail": "Login successful"}

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("token")
    return {"detail": "Logged out"}


# ============================
# FORGOT PASSWORD
# ============================
@router.post("/forgot-password")
async def forgot_password(email: str, db: AsyncSession = Depends(get_db)):
    code = await initiate_password_reset(db, email)

    if not code:
        raise HTTPException(status_code=404, detail="ای میل موجود نہیں ہے")

    return {"پیغام": "ری سیٹ کوڈ آپ کی ای میل پر بھیج دیا گیا ہے"}


# ============================
# RESET PASSWORD
# ============================
@router.post("/reset-password-confirm")
async def reset_password_confirm(payload: PasswordResetConfirm, db: AsyncSession = Depends(get_db)):
    success = await reset_password_in_db(
        db,
        payload.email,
        payload.reset_code,
        payload.new_password
    )

    if not success:
        raise HTTPException(status_code=400, detail="غلط کوڈ یا ای میل")

    return {"پیغام": "پاس ورڈ کامیابی سے تبدیل کر دیا گیا ہے"}


# ============================
# SAVE VOICE
# ============================
@router.post("/save-voice-samples")
async def save_voice(payload: VoiceSamplesSave, db: AsyncSession = Depends(get_db)):
    user = await save_voice_samples(db, payload.email, payload.samples)

    if not user:
        raise HTTPException(status_code=404, detail="صارف نہیں ملا")

    return {"پیغام": "وائس سیمپلز کامیابی سے محفوظ کر دیے گئے ہیں"}


# ============================
# VOICE LOGIN
# ============================
@router.post("/voice-login")
async def voice_login(payload: UserVoiceLogin, db: AsyncSession = Depends(get_db)):
    user = await authenticate_voice(db, payload.email, payload.audio_base64)

    token = create_access_token({"sub": str(user.user_id)})

    return {"access_token": token, "token_type": "bearer"}


# ============================
# GET CURRENT USER (with Urdu date)
# ============================
@router.get("/me", response_model=UserReadWithUrduDate)
async def get_me(current_user: Annotated[User, Depends(get_current_user)]):
    # Format the date in Urdu
    formatted_date = format_full_date_urdu(current_user.created_at) if current_user.created_at else None
    
    return UserReadWithUrduDate(
        user_id=current_user.user_id,
        email=current_user.email,
        username=current_user.username,
        created_at=formatted_date
    )


# ============================
# UPDATE PROFILE - FIXED
# ============================
@router.patch("/profile")
async def update_profile(
    payload: ProfileUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    # Update the profile
    updated_user = await update_own_profile(db, current_user.user_id, payload)

    if not updated_user:
        raise HTTPException(status_code=404, detail="صارف نہیں ملا")

    # Return success response
    return {
        "detail": "پروفائل کامیابی سے اپ ڈیٹ ہو گئی",
        "user": {
            "id": updated_user.user_id,
            "username": updated_user.username,
            "email": updated_user.email
        }
    }


# ============================
# DELETE ACCOUNT
# ============================
@router.delete("/profile")
async def delete_own_account(
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    success = await delete_user(db, current_user.user_id)

    if not success:
        raise HTTPException(status_code=404, detail="صارف نہیں ملا")

    return {"پیغام": "آپ کا اکاؤنٹ کامیابی سے حذف کر دیا گیا ہے"}


# ============================
# ADMIN: GET ALL USERS (with Urdu dates)
# ============================
@router.get("/users", response_model=List[UserReadWithUrduDate])
async def get_all_users_admin(db: AsyncSession = Depends(get_db)):
    users = await get_all_users(db)
    
    # Format each user's date in Urdu
    formatted_users = []
    for user in users:
        formatted_date = format_full_date_urdu(user.created_at) if user.created_at else None
        formatted_users.append(
            UserReadWithUrduDate(
                user_id=user.user_id,
                email=user.email,
                username=user.username,
                created_at=formatted_date
            )
        )
    
    return formatted_users