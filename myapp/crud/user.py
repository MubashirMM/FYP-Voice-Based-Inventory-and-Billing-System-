# import random
# from datetime import datetime, timedelta, timezone
# from sqlalchemy import select, func
# from sqlalchemy.ext.asyncio import AsyncSession
# from fastapi import HTTPException

# from myapp.utils.security import hash_password, verify_password, create_access_token
# from myapp.utils.voice import combine_embeddings, match_voice
# from myapp.models.user import User
# from myapp.schemas.user import ProfileUpdate

# from myapp.services.email import *


# # ============================
# # REGISTER - FIXED (store email in lowercase)
# # ============================
# async def register_user(db: AsyncSession, email: str, username: str, password: str):
#     # Normalize email to lowercase before checking and storing
#     normalized_email = email.strip().lower()
    
#     # Check if email already exists (case-insensitive)
#     res = await db.execute(select(User).where(func.lower(User.email) == normalized_email))
#     if res.scalar_one_or_none():
#         raise HTTPException(400, "یہ ای میل پہلے سے رجسٹرڈ ہے۔")

#     # Create user with normalized email
#     user = User(
#         email=normalized_email, 
#         username=username, 
#         password_hash=hash_password(password)
#     )
#     db.add(user)
#     await db.commit()
#     await db.refresh(user)

#     send_email(normalized_email, "خوش آمدید", registration_template(username))
#     return user


# # ============================
# # LOGIN - FIXED (case-insensitive)
# # ============================
# async def authenticate_user(db: AsyncSession, email: str, password: str):
#     # Normalize email to lowercase for comparison
#     normalized_email = email.strip().lower()
    
#     res = await db.execute(select(User).where(func.lower(User.email) == normalized_email))
#     user = res.scalar_one_or_none()

#     if not user:
#         raise HTTPException(401, 
#                         detail="ای میل رجسٹرڈ نہیں ہے۔ براہ مہربانی پہلے رجسٹر کریں۔")

#     if not verify_password(password, user.password_hash):
#         raise HTTPException(401, "پاس ورڈ غلط ہے۔")

#     send_email(user.email, "لاگ ان", login_template(user.username))

#     return create_access_token({"sub": str(user.user_id)})


# # ============================
# # VOICE SAVE - FIXED
# # ============================
# async def save_voice_samples(db: AsyncSession, email: str, samples: list[str]):
#     # Normalize email to lowercase
#     normalized_email = email.strip().lower()
    
#     res = await db.execute(select(User).where(func.lower(User.email) == normalized_email))
#     user = res.scalar_one_or_none()

#     if not user:
#         return None

#     user.voice_embedding = combine_embeddings(samples)
#     await db.commit()

#     send_email(user.email, "وائس محفوظ", voice_samples_template(user.username))
#     return user


# # ============================
# # VOICE LOGIN - FIXED
# # ============================
# async def authenticate_voice(db: AsyncSession, email: str, audio_base64: str):
#     # Normalize email to lowercase
#     normalized_email = email.strip().lower()
    
#     res = await db.execute(select(User).where(func.lower(User.email) == normalized_email))
#     user = res.scalar_one_or_none()

#     if not user:
#         raise HTTPException(404, "ای میل رجسٹرڈ نہیں ہے۔")

#     if not user.voice_embedding:
#         raise HTTPException(400, "وائس موجود نہیں۔")

#     if match_voice(user.voice_embedding, audio_base64):
#         send_email(user.email, "وائس لاگ ان", voice_login_template(user.username))
#         return user

#     raise HTTPException(401, "وائس میچ نہیں ہوئی۔")


# # ============================
# # UPDATE PROFILE - FIXED (also normalize email if being updated)
# # ============================
# async def update_own_profile(db: AsyncSession, user_id: int, update_data: ProfileUpdate):
#     # Get the user
#     user = await db.get(User, user_id)
#     if not user:
#         return None

#     # Convert to dict, excluding unset values
#     data = update_data.model_dump(exclude_unset=True)
    
#     # Update each field
#     for key, value in data.items():
#         if key == "password":
#             # Hash the new password
#             hashed = hash_password(value)
#             setattr(user, "password_hash", hashed)
#         elif key == "email":
#             # Normalize email to lowercase
#             normalized_email = value.strip().lower()
#             # Check if new email already exists (excluding current user)
#             existing = await db.execute(
#                 select(User).where(
#                     func.lower(User.email) == normalized_email,
#                     User.user_id != user_id
#                 )
#             )
#             if existing.scalar_one_or_none():
#                 raise HTTPException(400, "یہ ای میل پہلے سے رجسٹرڈ ہے۔")
#             setattr(user, key, normalized_email)
#         else:
#             setattr(user, key, value)
    
#     # Commit changes
#     await db.commit()
#     await db.refresh(user)
    
#     # Send email notification
#     send_email(user.email, "پروفائل اپڈیٹ", profile_update_template(user.username, user.email))
    
#     return user


# # ============================
# # RESET PASSWORD REQUEST - FIXED
# # ============================
# async def initiate_password_reset(db: AsyncSession, email: str):
#     # Normalize email to lowercase
#     normalized_email = email.strip().lower()
    
#     res = await db.execute(select(User).where(func.lower(User.email) == normalized_email))
#     user = res.scalar_one_or_none()

#     if not user:
#         return None

#     code = f"VBUGIMS-{random.randint(100000, 999999)}"
#     user.password_reset_code = code
#     user.password_reset_expiry = datetime.now(timezone.utc) + timedelta(minutes=15)

#     await db.commit()

#     send_email(user.email, "پاس ورڈ ری سیٹ", password_reset_template(code))
#     return code


# # ============================
# # RESET PASSWORD - FIXED
# # ============================
# async def reset_password_in_db(db: AsyncSession, email: str, reset_code: str, new_password: str):
#     # Normalize email to lowercase
#     normalized_email = email.strip().lower()
    
#     res = await db.execute(select(User).where(func.lower(User.email) == normalized_email))
#     user = res.scalar_one_or_none()

#     if not user or user.password_reset_code != reset_code:
#         return False

#     if datetime.now(timezone.utc) > user.password_reset_expiry:
#         return False

#     user.password_hash = hash_password(new_password)
#     user.password_reset_code = None
#     user.password_reset_expiry = None

#     await db.commit()

#     send_email(user.email, "پاس ورڈ تبدیل", password_changed_template(user.username))
#     return True


# # ============================
# # GET USERS - FIXED (case-insensitive search)
# # ============================
# async def get_all_users(db: AsyncSession):
#     res = await db.execute(select(User))
#     return res.scalars().all()


# async def get_user_by_id(db: AsyncSession, user_id: int):
#     res = await db.execute(select(User).where(User.user_id == user_id))
#     return res.scalar_one_or_none()


# async def get_user_by_email(db: AsyncSession, email: str):
#     # Normalize email to lowercase
#     normalized_email = email.strip().lower()
#     res = await db.execute(select(User).where(func.lower(User.email) == normalized_email))
#     return res.scalar_one_or_none()


# # ============================
# # DELETE USER - FIXED (case-insensitive and proper deletion)
# # ============================
# async def delete_user(db: AsyncSession, user_id: int):
#     # First check if user exists with cascade consideration
#     res = await db.execute(select(User).where(User.user_id == user_id))
#     user = res.scalar_one_or_none()

#     if not user:
#         return False

#     # Store user info for email before deletion
#     email = user.email
#     username = user.username

#     try:
#         # Delete the user (cascade should handle related records if configured)
#         await db.delete(user)
#         await db.commit()
        
#         # Send deletion confirmation email
#         send_email(email, "اکاؤنٹ ڈیلیٹ", account_deleted_template(username))
#         return True
        
#     except Exception as e:
#         # Rollback in case of error
#         await db.rollback()
#         print(f"Error deleting user: {e}")
#         raise HTTPException(500, f"اکاؤنٹ حذف کرنے میں خرابی: {str(e)}")


# # ============================
# # CLEANUP DUPLICATE EMAILS (Run this once to fix existing data)
# # ============================
# async def cleanup_duplicate_emails(db: AsyncSession):
#     """Remove duplicate emails keeping only the first one"""
#     from sqlalchemy import text
    
#     # Find duplicate emails
#     result = await db.execute(
#         text("""
#             SELECT LOWER(email) as normalized_email, COUNT(*) as count, array_agg(user_id) as user_ids
#             FROM users 
#             GROUP BY LOWER(email)
#             HAVING COUNT(*) > 1
#         """)
#     )
    
#     duplicates = result.fetchall()
    
#     deleted_count = 0
#     for dup in duplicates:
#         user_ids = dup[2]  # array of user_ids
#         # Keep the first user, delete others
#         keep_id = user_ids[0]
#         delete_ids = user_ids[1:]
        
#         for delete_id in delete_ids:
#             await db.execute(
#                 text("DELETE FROM users WHERE user_id = :user_id"),
#                 {"user_id": delete_id}
#             )
#             deleted_count += 1
    
#     await db.commit()
#     return deleted_count


import random
import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, func, update, text
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, BackgroundTasks
from concurrent.futures import ThreadPoolExecutor
import asyncio

from myapp.utils.security import hash_password, verify_password, create_access_token
from myapp.models.user import User
from myapp.schemas.user import ProfileUpdate
from myapp.services.email import (
    send_email_async, registration_template, login_template, 
    voice_samples_template, voice_login_template, profile_update_template,
    password_reset_template, password_changed_template, account_deleted_template
)
from myapp.utils.voice import combine_embeddings, match_voice, preload_encoder

# Set up logging
logger = logging.getLogger(__name__)

_cpu_executor = ThreadPoolExecutor(max_workers=8)
_voice_executor = ThreadPoolExecutor(max_workers=4)

async def run_cpu_bound(func, *args, **kwargs):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_cpu_executor, lambda: func(*args, **kwargs))

async def run_voice_bound(func, *args, **kwargs):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_voice_executor, lambda: func(*args, **kwargs))

# User cache
_user_cache = {}
_CACHE_TTL = 60

# Voice embedding cache
_voice_embedding_cache = {}
_EMBEDDING_CACHE_TTL = 300

def _get_cached_user(email: str):
    key = email.strip().lower()
    if key in _user_cache:
        user, timestamp = _user_cache[key]
        if (datetime.now(timezone.utc) - timestamp).seconds < _CACHE_TTL:
            return user
        del _user_cache[key]
    return None

def _cache_user(email: str, user):
    key = email.strip().lower()
    _user_cache[key] = (user, datetime.now(timezone.utc))

def _invalidate_cache(email: str):
    key = email.strip().lower()
    _user_cache.pop(key, None)

def _cache_voice_embedding(email: str, embedding):
    key = email.strip().lower()
    _voice_embedding_cache[key] = (embedding, datetime.now(timezone.utc))

def _get_cached_voice_embedding(email: str):
    key = email.strip().lower()
    if key in _voice_embedding_cache:
        emb, timestamp = _voice_embedding_cache[key]
        if (datetime.now(timezone.utc) - timestamp).seconds < _EMBEDDING_CACHE_TTL:
            return emb
        del _voice_embedding_cache[key]
    return None

def _invalidate_voice_cache(email: str):
    key = email.strip().lower()
    _voice_embedding_cache.pop(key, None)

async def register_user(db: AsyncSession, email: str, username: str, password: str, background_tasks: BackgroundTasks):
    normalized_email = email.strip().lower()
    
    query = text("SELECT 1 FROM users WHERE LOWER(email) = :email LIMIT 1")
    exists = await db.execute(query, {"email": normalized_email})
    
    if exists.scalar():
        raise HTTPException(400, "یہ ای میل پہلے سے رجسٹرڈ ہے۔")
    
    hashed_password = await run_cpu_bound(hash_password, password)
    
    insert_query = text("""
        INSERT INTO users (email, username, password_hash, created_at)
        VALUES (:email, :username, :password_hash, :created_at)
        RETURNING user_id, email, username, created_at
    """)
    
    result = await db.execute(insert_query, {
        "email": normalized_email,
        "username": username,
        "password_hash": hashed_password,
        "created_at": datetime.now(timezone.utc)
    })
    
    row = result.fetchone()
    user = User(
        user_id=row[0],
        email=row[1],
        username=row[2],
        created_at=row[3],
        password_hash=hashed_password
    )
    
    await db.commit()
    _cache_user(normalized_email, user)
    
    # Send welcome email
    background_tasks.add_task(send_email_async, normalized_email, "خوش آمدید", registration_template(username))
    logger.info(f"Welcome email queued for {normalized_email}")
    
    return user

async def authenticate_user(db: AsyncSession, email: str, password: str, background_tasks: BackgroundTasks):
    normalized_email = email.strip().lower()
    
    user = _get_cached_user(normalized_email)
    if not user:
        result = await db.execute(select(User).where(func.lower(User.email) == normalized_email))
        user = result.scalar_one_or_none()
        if user:
            _cache_user(normalized_email, user)
    
    if not user:
        raise HTTPException(401, "ای میل رجسٹرڈ نہیں ہے۔")
    
    is_valid = await run_cpu_bound(verify_password, password, user.password_hash)
    
    if not is_valid:
        raise HTTPException(401, "پاس ورڈ غلط ہے۔")
    
    # Send login notification
    background_tasks.add_task(send_email_async, user.email, "لاگ ان", login_template(user.username))
    logger.info(f"Login notification queued for {user.email}")
    
    return create_access_token({"sub": str(user.user_id)})

async def update_own_profile(db: AsyncSession, user_id: int, update_data: ProfileUpdate, background_tasks: BackgroundTasks):
    data = update_data.model_dump(exclude_unset=True)
    
    data.pop("confirm_password", None)
    
    if not data:
        return await db.get(User, user_id)
    
    update_fields = []
    update_values = {}
    email_changed = False
    new_email = None
    
    for key, value in data.items():
        if key == "password":
            hashed = await run_cpu_bound(hash_password, value)
            update_fields.append("password_hash = :password_hash")
            update_values["password_hash"] = hashed
        elif key == "email":
            new_email = value.strip().lower()
            check_query = text("SELECT 1 FROM users WHERE LOWER(email) = :email AND user_id != :user_id LIMIT 1")
            exists = await db.execute(check_query, {"email": new_email, "user_id": user_id})
            if exists.scalar():
                raise HTTPException(400, "یہ ای میل پہلے سے رجسٹرڈ ہے۔")
            update_fields.append("email = :email")
            update_values["email"] = new_email
            email_changed = True
        elif key == "username":
            update_fields.append("username = :username")
            update_values["username"] = value
    
    if not update_fields:
        return await db.get(User, user_id)
    
    update_values["user_id"] = user_id
    
    update_query = text(f"""
        UPDATE users 
        SET {', '.join(update_fields)}
        WHERE user_id = :user_id
    """)
    
    await db.execute(update_query, update_values)
    await db.commit()
    
    user = await db.get(User, user_id)
    
    if email_changed and new_email:
        _invalidate_cache(new_email)
    
    # Send profile update notification
    background_tasks.add_task(send_email_async, user.email, "پروفائل اپڈیٹ", profile_update_template(user.username, user.email))
    logger.info(f"Profile update notification queued for {user.email}")
    
    return user

async def delete_user(db: AsyncSession, user_id: int, background_tasks: BackgroundTasks):
    user = await db.get(User, user_id)
    
    if not user:
        return False
    
    email = user.email
    username = user.username
    
    await db.delete(user)
    await db.commit()
    
    _invalidate_cache(email)
    _invalidate_voice_cache(email)
    
    # Send account deletion notification
    background_tasks.add_task(send_email_async, email, "اکاؤنٹ ڈیلیٹ", account_deleted_template(username))
    logger.info(f"Account deletion notification queued for {email}")
    
    return True

async def get_all_users(db: AsyncSession):
    result = await db.execute(select(User))
    return result.scalars().all()

async def get_user_by_id(db: AsyncSession, user_id: int):
    result = await db.execute(select(User).where(User.user_id == user_id))
    return result.scalar_one_or_none()

async def get_user_by_email(db: AsyncSession, email: str):
    normalized_email = email.strip().lower()
    result = await db.execute(select(User).where(func.lower(User.email) == normalized_email))
    return result.scalar_one_or_none()

async def save_voice_samples(db: AsyncSession, email: str, samples: list[str], background_tasks: BackgroundTasks):
    normalized_email = email.strip().lower()
    
    user = _get_cached_user(normalized_email)
    if not user:
        result = await db.execute(select(User).where(func.lower(User.email) == normalized_email))
        user = result.scalar_one_or_none()
        if user:
            _cache_user(normalized_email, user)
    
    if not user:
        return None
    
    voice_embedding = await combine_embeddings(samples)
    
    user.voice_embedding = voice_embedding
    await db.commit()
    
    _cache_voice_embedding(normalized_email, voice_embedding)
    
    # Send voice saved notification
    background_tasks.add_task(send_email_async, user.email, "وائس محفوظ", voice_samples_template(user.username))
    logger.info(f"Voice saved notification queued for {user.email}")
    
    return user

async def authenticate_voice(db: AsyncSession, email: str, audio_base64: str, background_tasks: BackgroundTasks):
    normalized_email = email.strip().lower()
    
    user = _get_cached_user(normalized_email)
    if not user:
        result = await db.execute(select(User).where(func.lower(User.email) == normalized_email))
        user = result.scalar_one_or_none()
        if user:
            _cache_user(normalized_email, user)
    
    if not user:
        raise HTTPException(404, detail="ای میل رجسٹرڈ نہیں ہے۔")
    
    if not user.voice_embedding:
        raise HTTPException(400, detail="آپ کی آواز رجسٹرڈ نہیں ہے۔ براہ کرم پہلے وائس رجسٹر کریں۔")
    
    cached_embedding = _get_cached_voice_embedding(normalized_email)
    stored_embedding = cached_embedding if cached_embedding is not None else user.voice_embedding
    
    is_match, similarity = await match_voice(stored_embedding, audio_base64)
    
    if cached_embedding is None and is_match:
        _cache_voice_embedding(normalized_email, stored_embedding)
    
    if is_match:
        # Send voice login notification
        background_tasks.add_task(send_email_async, user.email, "وائس لاگ ان", voice_login_template(user.username))
        logger.info(f"Voice login notification queued for {user.email}")
        return user
    
    raise HTTPException(
        status_code=401, 
        detail=f"آواز کی مطابقت درست نہیں پائی گئی۔ مماثلت {similarity*100:.1f} فیصد ہے، جبکہ کم از کم 70 فیصد ہونا ضروری ہے۔ براہ کرم دوبارہ کوشش کریں۔"
    )

async def initiate_password_reset(db: AsyncSession, email: str, background_tasks: BackgroundTasks):
    """Initiate password reset - Sends reset code to email"""
    normalized_email = email.strip().lower()
    logger.info(f"Password reset requested for email: {normalized_email}")
    
    result = await db.execute(select(User).where(func.lower(User.email) == normalized_email))
    user = result.scalar_one_or_none()
    
    if not user:
        logger.warning(f"Password reset requested for non-existent email: {normalized_email}")
        return None
    
    # Generate reset code
    code = f"VBUGIMS-{random.randint(100000, 999999)}"
    user.password_reset_code = code
    user.password_reset_expiry = datetime.now(timezone.utc) + timedelta(minutes=15)
    await db.commit()
    
    logger.info(f"Reset code generated for {user.email}: {code}")
    
    # Send password reset email
    try:
        background_tasks.add_task(send_email_async, user.email, "پاس ورڈ ری سیٹ", password_reset_template(code))
        logger.info(f"Password reset email queued for {user.email}")
        return code
    except Exception as e:
        logger.error(f"Failed to queue password reset email for {user.email}: {str(e)}")
        # Still return the code, but log the error
        return code

async def reset_password_in_db(db: AsyncSession, email: str, reset_code: str, new_password: str, background_tasks: BackgroundTasks):
    """Reset password with validation"""
    normalized_email = email.strip().lower()
    logger.info(f"Password reset attempt for email: {normalized_email}")
    
    # First check if user exists
    result = await db.execute(select(User).where(func.lower(User.email) == normalized_email))
    user = result.scalar_one_or_none()
    
    if not user:
        logger.warning(f"Password reset failed - user not found: {normalized_email}")
        return False
    
    # Check if reset code matches
    if user.password_reset_code != reset_code:
        logger.warning(f"Password reset failed - invalid code for {normalized_email}. Expected: {user.password_reset_code}, Got: {reset_code}")
        return False
    
    # Check if code is expired
    if datetime.now(timezone.utc) > user.password_reset_expiry:
        logger.warning(f"Password reset failed - expired code for {normalized_email}. Expiry: {user.password_reset_expiry}")
        return False
    
    # Reset password
    hashed_password = await run_cpu_bound(hash_password, new_password)
    
    await db.execute(
        update(User)
        .where(User.user_id == user.user_id)
        .values(
            password_hash=hashed_password,
            password_reset_code=None,
            password_reset_expiry=None
        )
    )
    await db.commit()
    
    logger.info(f"Password reset successful for {user.email}")
    
    _invalidate_cache(normalized_email)
    _invalidate_voice_cache(normalized_email)
    
    # Send password changed notification
    background_tasks.add_task(send_email_async, user.email, "پاس ورڈ تبدیل", password_changed_template(user.username))
    logger.info(f"Password changed notification queued for {user.email}")
    
    return True

async def preload_voice_model():
    """Preload voice encoder model on startup"""
    print("🔄 Preloading voice encoder model...")
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, preload_encoder)
    print("✅ Voice encoder preloaded successfully!")