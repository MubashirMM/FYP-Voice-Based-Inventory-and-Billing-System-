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