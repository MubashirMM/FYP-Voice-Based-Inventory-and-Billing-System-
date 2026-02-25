import random
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from myapp.utils.security import hash_password, verify_password, create_access_token
from myapp.models.user import User
from myapp.schemas.user import ProfileUpdate
from myapp.services.email import send_email, get_registration_template, get_reset_template

# ---------------------------
# Register User
# ---------------------------
async def register_user(db: AsyncSession, email: str, username: str, password: str):
    # Ensure email uniqueness
    res = await db.execute(select(User).where(User.email == email))
    if res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="یہ ای میل پہلے سے رجسٹرڈ ہے۔"
        )

    hashed = hash_password(password)
    user = User(email=email, username=username, password_hash=hashed)

    db.add(user)
    try:
        await db.commit()
        await db.refresh(user)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="ڈیٹا بیس میں خرابی آگئی۔")

    # Send welcome email
    try:
        subject = "VBUGIMS میں خوش آمدید"
        body = get_registration_template()
        send_email(email, subject, body)
    except Exception as e:
        # Log but don’t break registration
        print(f"Email failed to send: {e}")

    return user

# ---------------------------
# Authenticate User
# ---------------------------
async def authenticate_user(db: AsyncSession, email: str, password: str):
    email = email.strip()
    res = await db.execute(select(User).where(User.email.ilike(email)))
    user = res.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ای میل نہیں ملی۔"
        )

    if not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="پاس ورڈ غلط ہے۔"
        )

    return create_access_token({"sub": str(user.user_id)})

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
    res = await db.execute(select(User).where(User.email == email))
    user = res.scalar_one_or_none()

    if user:
        code = f"VBUGIMS-{random.randint(100000, 999999)}"
        expiry = datetime.now(timezone.utc) + timedelta(minutes=15)  # 15 min expiry

        user.password_reset_code = code
        user.password_reset_expiry = expiry
        await db.commit()

        subject = "پاس ورڈ ری سیٹ کوڈ"
        body = get_reset_template(code)

        try:
            send_email(email, subject, body)
            return code
        except Exception as e:
            print(f"Failed to send reset email: {e}")

    return None

# ---------------------------
# Reset Password
# ---------------------------
async def reset_password_in_db(db: AsyncSession, email: str, reset_code: str, new_password: str):
    res = await db.execute(select(User).where(User.email == email))
    user = res.scalar_one_or_none()

    if not user or user.password_reset_code != reset_code:
        return False

    # Check expiry
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

async def get_all_users(db: AsyncSession):
    res = await db.execute(select(User))
    return res.scalars().all()

async def delete_user(db: AsyncSession, user_id: int):
    result = await db.execute(delete(User).where(User.user_id == user_id))
    await db.commit()
    return result.rowcount > 0
