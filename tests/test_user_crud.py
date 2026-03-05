import pytest
from fastapi import HTTPException
from datetime import datetime, timedelta, timezone

from myapp.crud.user import (
    register_user, authenticate_user, save_voice_samples, authenticate_voice,
    update_user_by_id, initiate_password_reset, reset_password_in_db,
    get_user_by_id, get_user_by_email, get_all_users, delete_user
)
from myapp.schemas.user import ProfileUpdate

# ---------------------------
# Register User
# ---------------------------
@pytest.mark.asyncio
async def test_register_user_success(db_session):
    user = await register_user(db_session, "ali@example.com", "Ali", "secret123")
    assert user.email == "ali@example.com"
    assert user.username == "Ali"

@pytest.mark.asyncio
async def test_register_user_duplicate_email(db_session):
    await register_user(db_session, "ali@example.com", "Ali", "secret123")
    with pytest.raises(HTTPException) as exc:
        await register_user(db_session, "ali@example.com", "Ali2", "secret456")
    assert exc.value.status_code == 400
    assert "رجسٹرڈ" in exc.value.detail

# ---------------------------
# Authenticate User
# ---------------------------
@pytest.mark.asyncio
async def test_authenticate_user_success(db_session):
    await register_user(db_session, "ali@example.com", "Ali", "secret123")
    token = await authenticate_user(db_session, "ali@example.com", "secret123")
    assert isinstance(token, str)

@pytest.mark.asyncio
async def test_authenticate_user_wrong_password(db_session):
    await register_user(db_session, "ali@example.com", "Ali", "secret123")
    with pytest.raises(HTTPException) as exc:
        await authenticate_user(db_session, "ali@example.com", "wrongpass")
    assert exc.value.status_code == 401
    assert "پاس ورڈ غلط" in exc.value.detail

# ---------------------------
# Voice Functions
# ---------------------------
# @pytest.mark.asyncio
# async def test_save_and_authenticate_voice(db_session, monkeypatch):
#     await register_user(db_session, "ali@example.com", "Ali", "secret123")

#     # Mock embeddings
#     monkeypatch.setattr("myapp.utils.voice.combine_embeddings", lambda samples: "fake_embedding")
#     monkeypatch.setattr("myapp.utils.voice.match_voice", lambda emb, audio: True)

#     user = await save_voice_samples(db_session, "ali@example.com", ["sample1", "sample2"])
#     assert user.voice_embedding == "fake_embedding"

#     auth_user = await authenticate_voice(db_session, "ali@example.com", "audio_base64")
#     assert auth_user.email == "ali@example.com"
# @pytest.mark.asyncio
# async def test_save_and_authenticate_voice(db_session, monkeypatch):
#     await register_user(db_session, "ali@example.com", "Ali", "secret123")

#     # Fake embedding must be bytes, since DB column is bytes
#     fake_embedding = b"fakebytes"

#     # Monkeypatch both functions so they don’t decode base64
#     monkeypatch.setattr("myapp.utils.voice.combine_embeddings", lambda samples: fake_embedding)
#     monkeypatch.setattr("myapp.utils.voice.match_voice", lambda emb, audio: True)

#     user = await save_voice_samples(db_session, "ali@example.com", ["sample1", "sample2"])
#     assert user.voice_embedding == fake_embedding

#     auth_user = await authenticate_voice(db_session, "ali@example.com", "audio_base64")
#     assert auth_user.email == "ali@example.com"

# ---------------------------
# Update User
# ---------------------------
@pytest.mark.asyncio
async def test_update_user_success(db_session):
    user = await register_user(db_session, "ali@example.com", "Ali", "secret123")
    update_data = ProfileUpdate(username="AliUpdated")
    updated = await update_user_by_id(db_session, user.user_id, update_data)
    assert updated.username == "AliUpdated"

# ---------------------------
# Password Reset
# ---------------------------
@pytest.mark.asyncio
async def test_password_reset_flow(db_session):
    await register_user(db_session, "ali@example.com", "Ali", "secret123")
    code = await initiate_password_reset(db_session, "ali@example.com")
    assert code.startswith("VBUGIMS-")

    success = await reset_password_in_db(db_session, "ali@example.com", code, "newpass123")
    assert success is True

@pytest.mark.asyncio
async def test_password_reset_invalid_code(db_session):
    await register_user(db_session, "ali@example.com", "Ali", "secret123")
    success = await reset_password_in_db(db_session, "ali@example.com", "wrongcode", "newpass123")
    assert success is False

# ---------------------------
# Utility Getters
# ---------------------------
@pytest.mark.asyncio
async def test_get_user_by_id_and_email(db_session):
    user = await register_user(db_session, "ali@example.com", "Ali", "secret123")
    by_id = await get_user_by_id(db_session, user.user_id)
    by_email = await get_user_by_email(db_session, "ali@example.com")
    assert by_id.email == "ali@example.com"
    assert by_email.username == "Ali"

@pytest.mark.asyncio
async def test_get_all_users(db_session):
    await register_user(db_session, "ali@example.com", "Ali", "secret123")
    await register_user(db_session, "fatima@example.com", "Fatima", "secret456")
    users = await get_all_users(db_session)
    assert len(users) == 2

# ---------------------------
# Delete User
# ---------------------------
@pytest.mark.asyncio
async def test_delete_user_success(db_session):
    user = await register_user(db_session, "ali@example.com", "Ali", "secret123")
    deleted = await delete_user(db_session, user.user_id)
    assert deleted is True

@pytest.mark.asyncio
async def test_delete_user_not_found(db_session):
    deleted = await delete_user(db_session, 999)
    assert deleted is False
