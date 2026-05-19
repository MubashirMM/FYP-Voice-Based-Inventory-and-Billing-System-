# from fastapi import APIRouter, Depends, HTTPException, status
# from sqlalchemy.ext.asyncio import AsyncSession
# from typing import List, Annotated
# from fastapi.security import OAuth2PasswordRequestForm

# from myapp.models.user import User
# from myapp.crud.user import (
#     register_user,
#     authenticate_user,
#     get_all_users,
#     initiate_password_reset,
#     reset_password_in_db,
#     delete_user,
#     save_voice_samples,
#     authenticate_voice,
#     update_own_profile
# )

# from myapp.database.session import get_db
# from myapp.schemas.user import (
#     UserRegister,
#     UserRead,
#     UserReadWithUrduDate,
#     PasswordResetConfirm,
#     ProfileUpdate,
#     UserVoiceLogin,
#     VoiceSamplesSave
# )

# from myapp.utils.security import create_access_token, get_current_user
# from myapp.utils.urdu_date import format_full_date_urdu

# router = APIRouter(prefix="/auth", tags=["Authentication"])


# # ============================
# # REGISTER
# # ============================
# @router.post("/register", status_code=status.HTTP_201_CREATED)
# async def register(payload: UserRegister, db: AsyncSession = Depends(get_db)):
#     await register_user(db, payload.email, payload.username, payload.password)
#     return {"detail": "اکاؤنٹ کامیابی سے بنا دیا گیا ہے"}


# # ============================
# # LOGIN (PASSWORD)
# # ============================
# @router.post("/login")
# async def login(payload: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
#     token = await authenticate_user(db, payload.username, payload.password)
#     return {"access_token": token, "token_type": "bearer"}


# # ============================
# # FORGOT PASSWORD
# # ============================
# @router.post("/forgot-password")
# async def forgot_password(email: str, db: AsyncSession = Depends(get_db)):
#     code = await initiate_password_reset(db, email)

#     if not code:
#         raise HTTPException(status_code=404, detail="ای میل موجود نہیں ہے")

#     return {"پیغام": "ری سیٹ کوڈ آپ کی ای میل پر بھیج دیا گیا ہے"}


# # ============================
# # RESET PASSWORD
# # ============================
# @router.post("/reset-password-confirm")
# async def reset_password_confirm(payload: PasswordResetConfirm, db: AsyncSession = Depends(get_db)):
#     success = await reset_password_in_db(
#         db,
#         payload.email,
#         payload.reset_code,
#         payload.new_password
#     )

#     if not success:
#         raise HTTPException(status_code=400, detail="غلط کوڈ یا ای میل")

#     return {"پیغام": "پاس ورڈ کامیابی سے تبدیل کر دیا گیا ہے"}


# # ============================
# # SAVE VOICE
# # ============================
# @router.post("/save-voice-samples")
# async def save_voice(payload: VoiceSamplesSave, db: AsyncSession = Depends(get_db)):
#     user = await save_voice_samples(db, payload.email, payload.samples)

#     if not user:
#         raise HTTPException(status_code=404, detail="صارف نہیں ملا")

#     return {"پیغام": "وائس سیمپلز کامیابی سے محفوظ کر دیے گئے ہیں"}


# # ============================
# # VOICE LOGIN
# # ============================
# @router.post("/voice-login")
# async def voice_login(payload: UserVoiceLogin, db: AsyncSession = Depends(get_db)):
#     user = await authenticate_voice(db, payload.email, payload.audio_base64)

#     token = create_access_token({"sub": str(user.user_id)})

#     return {"access_token": token, "token_type": "bearer"}


# # ============================
# # GET CURRENT USER (with Urdu date)
# # ============================
# @router.get("/me", response_model=UserReadWithUrduDate)
# async def get_me(current_user: Annotated[User, Depends(get_current_user)]):
#     # Format the date in Urdu
#     formatted_date = format_full_date_urdu(current_user.created_at) if current_user.created_at else None
    
#     return UserReadWithUrduDate(
#         user_id=current_user.user_id,
#         email=current_user.email,
#         username=current_user.username,
#         created_at=formatted_date
#     )


# # ============================
# # UPDATE PROFILE - FIXED
# # ============================
# @router.patch("/profile")
# async def update_profile(
#     payload: ProfileUpdate,
#     current_user: Annotated[User, Depends(get_current_user)],
#     db: AsyncSession = Depends(get_db)
# ):
#     # Update the profile
#     updated_user = await update_own_profile(db, current_user.user_id, payload)

#     if not updated_user:
#         raise HTTPException(status_code=404, detail="صارف نہیں ملا")

#     # Return success response
#     return {
#         "detail": "پروفائل کامیابی سے اپ ڈیٹ ہو گئی",
#         "user": {
#             "id": updated_user.user_id,
#             "username": updated_user.username,
#             "email": updated_user.email
#         }
#     }


# # ============================
# # DELETE ACCOUNT
# # ============================
# @router.delete("/profile")
# async def delete_own_account(
#     current_user: Annotated[User, Depends(get_current_user)],
#     db: AsyncSession = Depends(get_db)
# ):
#     success = await delete_user(db, current_user.user_id)

#     if not success:
#         raise HTTPException(status_code=404, detail="صارف نہیں ملا")

#     return {"پیغام": "آپ کا اکاؤنٹ کامیابی سے حذف کر دیا گیا ہے"}


# # ============================
# # ADMIN: GET ALL USERS (with Urdu dates)
# # ============================
# @router.get("/users", response_model=List[UserReadWithUrduDate])
# async def get_all_users_admin(db: AsyncSession = Depends(get_db)):
#     users = await get_all_users(db)
    
#     # Format each user's date in Urdu
#     formatted_users = []
#     for user in users:
#         formatted_date = format_full_date_urdu(user.created_at) if user.created_at else None
#         formatted_users.append(
#             UserReadWithUrduDate(
#                 user_id=user.user_id,
#                 email=user.email,
#                 username=user.username,
#                 created_at=formatted_date
#             )
#         )
    
#     return formatted_users
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from typing import List, Annotated
from datetime import datetime, timezone
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from myapp.crud.user import (
    register_user, authenticate_user, get_all_users, initiate_password_reset,
    reset_password_in_db, delete_user, save_voice_samples, authenticate_voice,
    update_own_profile, get_user_by_email
)
from myapp.database.session import get_db
from myapp.schemas.user import (
    UserRegister, UserReadWithUrduDate, PasswordResetConfirm,
    ProfileUpdate, UserVoiceLogin, VoiceSamplesSave
)
from myapp.utils.security import create_access_token, get_current_user
from myapp.utils.urdu_date import format_full_date_urdu
from myapp.models.user import User
from myapp.services.email import send_email_async

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    payload: UserRegister,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user"""
    await register_user(db, payload.email, payload.username, payload.password, background_tasks)
    return {"detail": "اکاؤنٹ کامیابی سے بنا دیا گیا ہے"}

@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db)
):
    """Login with email and password"""
    if background_tasks is None:
        background_tasks = BackgroundTasks()
    
    token = await authenticate_user(db, form_data.username, form_data.password, background_tasks)
    return {"access_token": token, "token_type": "bearer"}

@router.post("/forgot-password")
async def forgot_password(
    email: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Request password reset - sends code to email"""
    logger.info(f"Forgot password request for email: {email}")
    
    code = await initiate_password_reset(db, email, background_tasks)
    
    if not code:
        # Security: Don't reveal if email exists
        logger.warning(f"Password reset requested for non-existent email: {email}")
        return {"پیغام": "اگر ای میل رجسٹرڈ ہے تو ری سیٹ کوڈ بھیج دیا گیا ہے"}
    
    return {"پیغام": "ری سیٹ کوڈ آپ کی ای میل پر بھیج دیا گیا ہے"}

@router.post("/reset-password-confirm")
async def reset_password_confirm(
    payload: PasswordResetConfirm,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Confirm password reset with code"""
    logger.info(f"Password reset confirmation for email: {payload.email}")
    
    # First check if user exists
    user = await get_user_by_email(db, payload.email)
    if not user:
        logger.warning(f"Password reset failed - user not found: {payload.email}")
        raise HTTPException(status_code=404, detail="ای میل رجسٹرڈ نہیں ہے")
    
    # Check if code matches
    if user.password_reset_code != payload.reset_code:
        logger.warning(f"Password reset failed - wrong code for {payload.email}")
        raise HTTPException(status_code=400, detail="غلط کوڈ")
    
    # Check if code is expired
    if user.password_reset_expiry < datetime.now(timezone.utc):
        logger.warning(f"Password reset failed - expired code for {payload.email}")
        raise HTTPException(status_code=400, detail="کوڈ کی میعاد ختم ہو چکی ہے")
    
    # Reset password
    success = await reset_password_in_db(db, payload.email, payload.reset_code, payload.new_password, background_tasks)
    
    if not success:
        logger.error(f"Password reset failed for {payload.email}")
        raise HTTPException(status_code=400, detail="پاس ورڈ ری سیٹ نہیں ہو سکا")
    
    logger.info(f"Password reset successful for {payload.email}")
    return {"پیغام": "پاس ورڈ کامیابی سے تبدیل کر دیا گیا ہے"}

@router.post("/save-voice-samples")
async def save_voice(
    payload: VoiceSamplesSave,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Save voice samples for user"""
    user = await save_voice_samples(db, payload.email, payload.samples, background_tasks)
    if not user:
        raise HTTPException(status_code=404, detail="صارف نہیں ملا")
    return {"پیغام": "وائس سیمپلز کامیابی سے محفوظ کر دیے گئے ہیں"}

@router.post("/voice-login")
async def voice_login(
    payload: UserVoiceLogin,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Login with voice authentication"""
    user = await authenticate_voice(db, payload.email, payload.audio_base64, background_tasks)
    token = create_access_token({"sub": str(user.user_id)})
    return {"access_token": token, "token_type": "bearer"}

@router.patch("/profile")
async def update_profile(
    payload: ProfileUpdate,
    background_tasks: BackgroundTasks,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Update user profile"""
    updated_user = await update_own_profile(db, current_user.user_id, payload, background_tasks)
    if not updated_user:
        raise HTTPException(status_code=404, detail="صارف نہیں ملا")
    return {
        "detail": "پروفائل کامیابی سے اپ ڈیٹ ہو گئی",
        "user": {
            "id": updated_user.user_id,
            "username": updated_user.username,
            "email": updated_user.email
        }
    }

@router.delete("/profile")
async def delete_own_account(
    background_tasks: BackgroundTasks,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Delete user account"""
    success = await delete_user(db, current_user.user_id, background_tasks)
    if not success:
        raise HTTPException(status_code=404, detail="صارف نہیں ملا")
    return {"پیغام": "آپ کا اکاؤنٹ کامیابی سے حذف کر دیا گیا ہے"}

@router.get("/me", response_model=UserReadWithUrduDate)
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)]
):
    """Get current user profile"""
    formatted_date = format_full_date_urdu(current_user.created_at) if current_user.created_at else None
    return UserReadWithUrduDate(
        user_id=current_user.user_id,
        email=current_user.email,
        username=current_user.username,
        created_at=formatted_date
    )

@router.get("/users", response_model=List[UserReadWithUrduDate])
async def get_all_users_admin(
    db: AsyncSession = Depends(get_db)
):
    """Get all users (admin only)"""
    users = await get_all_users(db)
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

@router.post("/test-email")
async def test_email_endpoint(
    email: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Test endpoint to verify email sending"""
    logger.info(f"Test email requested for: {email}")
    
    try:
        # Check if user exists
        user = await get_user_by_email(db, email)
        if user:
            background_tasks.add_task(
                send_email_async, 
                email, 
                "ٹیسٹ ای میل - VBUGIMS", 
                f"""
                <h1>✅ ٹیسٹ ای میل کامیاب</h1>
                <p>پیارے {user.username}،</p>
                <p>یہ ایک ٹیسٹ ای میل ہے جس سے یہ ثابت ہوتا ہے کہ آپ کا ای میل سسٹم صحیح طریقے سے کام کر رہا ہے۔</p>
                <p>اگر آپ یہ پیغام دیکھ رہے ہیں تو:</p>
                <ul>
                    <li>✅ SMTP کنکشن درست ہے</li>
                    <li>✅ ای میل بھیجنے کا عمل کام کر رہا ہے</li>
                    <li>✅ آپ کا ای میل ایڈریس درست ہے</li>
                </ul>
                <p><strong>تاریخ:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <br>
                <p>شکریہ،<br>VBUGIMS ٹیم</p>
                """
            )
            return {"message": "Test email queued successfully", "email": email, "user_found": True}
        else:
            # Send test email even if user doesn't exist
            background_tasks.add_task(
                send_email_async, 
                email, 
                "ٹیسٹ ای میل - VBUGIMS", 
                f"""
                <h1>✅ ٹیسٹ ای میل کامیاب</h1>
                <p>یہ ایک ٹیسٹ ای میل ہے۔</p>
                <p>اگر آپ یہ پیغام دیکھ رہے ہیں تو ای میل سسٹم صحیح طریقے سے کام کر رہا ہے۔</p>
                <p><strong>نوٹ:</strong> یہ ای میل ایڈریس ہمارے سسٹم میں رجسٹرڈ نہیں ہے۔</p>
                <p><strong>تاریخ:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <br>
                <p>شکریہ،<br>VBUGIMS ٹیم</p>
                """
            )
            return {"message": "Test email queued successfully", "email": email, "user_found": False}
    except Exception as e:
        logger.error(f"Test email failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Email error: {str(e)}")

