import random
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException,status

from myapp.utils.security import hash_password, verify_password, create_access_token
from myapp.utils.voice import combine_embeddings, match_voice
from myapp.models.user import User
from myapp.schemas.user import ProfileUpdate
from myapp.services.email import send_email, get_registration_template, get_reset_template

# --------------------------- 
# Register User
# ---------------------------
async def register_user(db: AsyncSession, email: str, username: str, password: str):
    res = await db.execute(select(User).where(User.email == email))
    if res.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="یہ ای میل پہلے سے رجسٹرڈ ہے۔")

    hashed = hash_password(password)
    user = User(email=email, username=username, password_hash=hashed)
    db.add(user)
    await db.commit()
    await db.refresh(user)

    try:
        send_email(email, "VBUGIMS میں خوش آمدید", get_registration_template())
    except Exception as e:
        print(f"Email failed: {e}")

    return user

# ---------------------------
# Authenticate User (Password)
# ---------------------------
async def authenticate_user(db: AsyncSession, email: str, password: str):
    res = await db.execute(select(User).where(User.email.ilike(email.strip())))
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="ای میل نہیں ملی۔")
    if not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="پاس ورڈ غلط ہے۔")
    return create_access_token({"sub": str(user.user_id)})

# ---------------------------
# Voice Functions
# ---------------------------
async def save_voice_samples(db: AsyncSession, email: str, samples: list[str]):
    res = await db.execute(select(User).where(User.email == email))
    user = res.scalar_one_or_none()
    if not user:
        return None
    user.voice_embedding = combine_embeddings(samples)
    await db.commit()
    await db.refresh(user)
    return user

async def authenticate_voice(db: AsyncSession, email: str, audio_base64: str):
    res = await db.execute(select(User).where(User.email == email))
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ای میل رجسٹرڈ نہیں ہے۔"
        )
    if not user.voice_embedding:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="اس صارف کے لئے وائس سیمپل محفوظ نہیں ہیں۔"
        )
    if match_voice(user.voice_embedding, audio_base64):
        return user
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="آواز میل نہیں کھاتی۔ دوبارہ کوشش کریں۔"
    )


# ---------------------------
# Update User
# ---------------------------
async def update_user_by_id(db: AsyncSession, user_id: int, update_data: ProfileUpdate):
    user = await db.get(User, user_id)
    if not user:
        return None

    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        if key == "password" and value:
            value = hash_password(value)
        setattr(user, key, value)

    await db.commit()
    await db.refresh(user)
    return user

# ---------------------------
# Initiate Password Reset
# ---------------------------
async def initiate_password_reset(db: AsyncSession, email: str):
    email = email.strip().lower()

    res = await db.execute(
        select(User).where(User.email == email)
    )
    user = res.scalar_one_or_none()

    if user:
        code = f"VBUGIMS-{random.randint(100000, 999999)}"
        expiry = datetime.now(timezone.utc) + timedelta(minutes=15)

        user.password_reset_code = code
        user.password_reset_expiry = expiry
        await db.commit()

        return code

    return None

# ---------------------------
# Reset Password
# ---------------------------
async def reset_password_in_db(db: AsyncSession, email: str, reset_code: str, new_password: str):
    res = await db.execute(select(User).where(User.email == email))
    user = res.scalar_one_or_none()

    if not user or user.password_reset_code != reset_code:
        return False

    if not user.password_reset_expiry or datetime.now(timezone.utc) > user.password_reset_expiry:
        return False

    user.password_hash = hash_password(new_password)
    user.password_reset_code = None
    user.password_reset_expiry = None

    await db.commit()
    return True

# ---------------------------
# Utility Getters
# ---------------------------
async def get_user_by_id(db: AsyncSession, user_id: int):
    res = await db.execute(select(User).where(User.user_id == user_id))
    return res.scalar_one_or_none()

async def get_user_by_email(db: AsyncSession, email: str):
    res = await db.execute(select(User).where(User.email.ilike(email.strip())))
    return res.scalar_one_or_none()

async def get_all_users(db: AsyncSession):
    res = await db.execute(select(User))
    return res.scalars().all()

# ---------------------------
# Delete User
# ---------------------------
async def delete_user(db: AsyncSession, user_id: int):
    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        return False

    await db.delete(user)
    await db.commit()
    return True
