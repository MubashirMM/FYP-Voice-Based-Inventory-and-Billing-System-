import random
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from myapp.utils.security import hash_password
# from myapp.utils.audio_to_embedding import audio_to_embedding
from myapp.models.user import User
from myapp.utils.security import verify_password
from sqlalchemy.ext.asyncio import AsyncSession
import numpy as np
import io,base64
from myapp.schemas.user import ProfileUpdate
from myapp.utils.security import hash_password, verify_password, create_access_token
from myapp.services.email import send_email, get_registration_template, get_reset_template

async def register_user(db: AsyncSession, email: str, username: str, password: str):
    res = await db.execute(select(User).where(User.email == email))
    if res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="یہ ای میل پہلے سے رجسٹرڈ ہے۔"
        )

   
    hashed = hash_password(password)
    user = User(
        email=email, 
        username=username, 
        password_hash=hashed, 
    )
    
    db.add(user)
    try:
        await db.commit()
        await db.refresh(user)
    except Exception as e:
        await db.rollback()
        print(f"Database Error: {e}")
        raise HTTPException(status_code=500, detail="ڈیٹا بیس میں خرابی آگئی۔")
    try:
        subject = "VBUGIMS میں خوش آمدید"
        body = get_registration_template()
        send_email(email, subject, body)
    except Exception as e:
        # We log the error but do NOT raise an HTTPException
        print(f"Email failed to send (Credentials issue): {e}")
        # Optionally return a note that the user is created but email failed

    return user

# async def save_voice_embedding(db: AsyncSession, user_id: int, embedding: np.ndarray):
    """Saves a numpy array as bytes into the database."""
    res = await db.execute(select(User).where(User.user_id == user_id))
    user = res.scalar_one_or_none()
    
    if user:
        # Convert numpy array to bytes for storage
        user.voice_embedding = embedding.tobytes()
        await db.commit()
        return True
    return False

# async def add_user_voice_samples(db: AsyncSession, user_id: int, samples: list[str]):
#     """Add 3 voice samples for a user and store averaged embedding."""
#     res = await db.execute(select(User).where(User.user_id == user_id))
#     user = res.scalar_one_or_none()
#     if not user:
#         return None

#     embeddings = []
#     for sample in samples:
#         audio_bytes = base64.b64decode(sample)
#         embeddings.append(audio_to_embedding(audio_bytes))

#     if embeddings:
#         avg_embedding = np.mean(embeddings, axis=0)
#         user.voice_embedding = avg_embedding.astype(np.float32).tobytes()
#         await db.commit()
#         return True
#     return False

# async def login_with_voice(db: AsyncSession, email: str, audio_base64: str):
#     """Authenticate user by comparing voice embedding."""
#     res = await db.execute(select(User).where(User.email == email))
#     user = res.scalar_one_or_none()
#     if not user or not user.voice_embedding:
#         return None

#     # Convert login audio to embedding
#     audio_bytes = base64.b64decode(audio_base64)
#     current_emb = audio_to_embedding(audio_bytes)

#     # Load stored embedding
#     stored_emb = np.frombuffer(user.voice_embedding, dtype=np.float32)

#     # Cosine similarity
#     similarity = np.dot(stored_emb, current_emb) / (
#         np.linalg.norm(stored_emb) * np.linalg.norm(current_emb)
#     )

#     if similarity > 0.85:  # threshold
#         return create_access_token({"sub": str(user.user_id)})
#     return None

async def authenticate_user(db: AsyncSession, email: str, password: str):
    """Verifies email/password and returns a JWT token."""
    res = await db.execute(select(User).where(User.email == email))
    user = res.scalar_one_or_none()
    
    if not user or not verify_password(password, user.password_hash):
        return None
    return create_access_token({"sub": str(user.user_id)})

async def update_user_by_id(db: AsyncSession, user_id: int, update_data: ProfileUpdate):
    # 1. Fetch the user by ID
    # In SQLAlchemy 2.0, db.get() is the most efficient way to find by Primary Key
    user = await db.get(User, user_id)

    if not user:
        return None

    # 2. Convert schema to dictionary
    # exclude_unset=True ensures we only loop over fields the user actually sent
    update_dict = update_data.model_dump(exclude_unset=True)

    for key, value in update_dict.items():
        # Only hash the password field, not all fields
        if key == "password" and value:
            value = hash_password(value)
        setattr(user, key, value)

    # 3. Commit the changes
    await db.commit()
    await db.refresh(user)
    return user

# async def authenticate_user(db: AsyncSession, email: str, password: str):
#     # Check if user exists
#     stmt = select(User).where(User.email == email)
#     result = await db.execute(stmt)
#     user = result.scalar_one_or_none()

#     if not user:
#         # Email not found
#         raise HTTPException(
#             status_code=401,
#             detail="ای میل موجود نہیں ہے"
#         )

#     # Check password
#     if not verify_password(password, user.hashed_password):
#         raise HTTPException(
#             status_code=401,
#             detail="پاس ورڈ غلط ہے"
#         )

#     # If both are correct, return token
#     from myapp.utils.security import create_access_token
#     token = create_access_token({"sub": str(user.user_id)})
#     return token


async def initiate_password_reset(db: AsyncSession, email: str):
    """Generates a reset code and sends the Urdu reset email if user exists."""
    res = await db.execute(select(User).where(User.email == email))
    user = res.scalar_one_or_none()
    
    if user:
        # Generate Code
        code = f"VBUGIMS-{random.randint(100000, 999999)}"
        
        user.password_reset_code=code
        await db.commit()
        subject = "پاس ورڈ ری سیٹ کوڈ"
        body = get_reset_template(code)
        
        try:
            send_email(email, subject, body)
            return code
        except Exception as e:
            print(f"Failed to send reset email: {e}")
            
    return None

async def reset_password_in_db(db: AsyncSession, email: str, reset_code: str, new_password: str):
    # 1. Find user by email
    res = await db.execute(select(User).where(User.email == email))
    user = res.scalar_one_or_none()
    
    # 2. Check if user exists AND the code matches exactly
    if not user or user.password_reset_code != reset_code:
        return False
        
    # 3. Update password and CLEAR the code so it can't be used again
    user.password_hash = hash_password(new_password)
    user.password_reset_code = None 
    
    await db.commit()
    return True

async def get_user_by_id(db: AsyncSession, user_id: int):
    res = await db.execute(select(User).where(User.user_id == user_id))
    return res.scalar_one_or_none()

async def get_all_users(db: AsyncSession):
    res = await db.execute(select(User))
    return res.scalars().all()

async def delete_user(db: AsyncSession, user_id: int):
    result = await db.execute(delete(User).where(User.user_id == user_id))
    await db.commit()
    # Return True if a row was deleted, False otherwise
    return result.rowcount > 0
  