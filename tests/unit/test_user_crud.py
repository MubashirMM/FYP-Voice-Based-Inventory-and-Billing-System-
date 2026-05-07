# C:\FYP\Backend\fast-api\tests\test_user_crud.py
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from fastapi import HTTPException
from unittest.mock import patch

# Import your actual CRUD functions
from myapp.crud.user import (
    register_user,
    authenticate_user,
    save_voice_samples,
    authenticate_voice,
    update_own_profile,
    initiate_password_reset,
    reset_password_in_db,
    get_user_by_id,
    get_user_by_email,
    get_all_users,
    delete_user
)
from myapp.schemas.user import ProfileUpdate


# ============================================
# REGISTER USER TESTS
# ============================================
@pytest.mark.asyncio
async def test_register_user_success(db_session):
    """Test successful user registration"""
    user = await register_user(db_session, "ali@example.com", "Ali", "secret123")
    assert user.email == "ali@example.com"
    assert user.username == "Ali"
    assert user.password_hash is not None
    assert user.password_hash != "secret123"  # Should be hashed


@pytest.mark.asyncio
async def test_register_user_duplicate_email(db_session):
    """Test registration with existing email - should raise 400"""
    await register_user(db_session, "ali@example.com", "Ali", "secret123")
    with pytest.raises(HTTPException) as exc:
        await register_user(db_session, "ali@example.com", "Ali2", "secret456")
    assert exc.value.status_code == 400
    assert "رجسٹرڈ" in exc.value.detail


@pytest.mark.asyncio
async def test_register_user_multiple_users(db_session):
    """Test registering multiple different users"""
    user1 = await register_user(db_session, "user1@example.com", "User1", "pass1")
    user2 = await register_user(db_session, "user2@example.com", "User2", "pass2")
    
    assert user1.email == "user1@example.com"
    assert user2.email == "user2@example.com"
    assert user1.user_id != user2.user_id


# ============================================
# AUTHENTICATE USER TESTS
# ============================================
@pytest.mark.asyncio
async def test_authenticate_user_success(db_session):
    """Test successful login returns JWT token"""
    await register_user(db_session, "ali@example.com", "Ali", "secret123")
    token = await authenticate_user(db_session, "ali@example.com", "secret123")
    assert isinstance(token, str)
    assert len(token) > 20  # JWT token should be substantial


@pytest.mark.asyncio
async def test_authenticate_user_wrong_password(db_session):
    """Test login with wrong password - should raise 401"""
    await register_user(db_session, "ali@example.com", "Ali", "secret123")
    with pytest.raises(HTTPException) as exc:
        await authenticate_user(db_session, "ali@example.com", "wrongpass")
    assert exc.value.status_code == 401
    assert "پاس ورڈ غلط" in exc.value.detail


@pytest.mark.asyncio
async def test_authenticate_user_nonexistent_email(db_session):
    """Test login with email that doesn't exist - should raise 401"""
    with pytest.raises(HTTPException) as exc:
        await authenticate_user(db_session, "nonexistent@example.com", "anypass")
    assert exc.value.status_code == 401
    assert exc.value.detail == "ای میل رجسٹرڈ نہیں ہے۔ براہ مہربانی پہلے رجسٹر کریں۔"


@pytest.mark.asyncio
async def test_authenticate_user_case_insensitive_email(db_session):
    """Test that email login is case insensitive"""
    await register_user(db_session, "Ali@Example.com", "Ali", "secret123")
    token = await authenticate_user(db_session, "ali@example.com", "secret123")
    assert isinstance(token, str)


# ============================================
# VOICE FUNCTIONS TESTS (Using dummy strings)
# ============================================
@pytest.mark.asyncio
async def test_save_voice_samples_success(db_session):
    """Test saving voice samples for a user"""
    # First register a user
    user = await register_user(db_session, "voice@example.com", "VoiceUser", "pass123")
    
    # Mock the voice utility functions with dummy data
    with patch('myapp.crud.user.combine_embeddings') as mock_combine:
        # Create a dummy bytes embedding (like real voice embedding would be)
        dummy_embedding = b"dummy_voice_embedding_bytes_12345"
        mock_combine.return_value = dummy_embedding
        
        # Save voice samples with dummy string samples
        dummy_samples = ["dummy_audio_sample_1_base64", "dummy_audio_sample_2_base64"]
        result = await save_voice_samples(db_session, "voice@example.com", dummy_samples)
        
        assert result is not None
        assert result.voice_embedding == dummy_embedding
        mock_combine.assert_called_once_with(dummy_samples)


@pytest.mark.asyncio
async def test_save_voice_samples_user_not_found(db_session):
    """Test saving voice samples for non-existent user"""
    dummy_samples = ["sample1", "sample2"]
    result = await save_voice_samples(db_session, "nonexistent@example.com", dummy_samples)
    assert result is None


@pytest.mark.asyncio
async def test_authenticate_voice_success(db_session):
    """Test successful voice authentication"""
    # Register user
    user = await register_user(db_session, "voice@example.com", "VoiceUser", "pass123")
    
    # Save voice samples first (mocked)
    with patch('myapp.crud.user.combine_embeddings') as mock_combine:
        dummy_embedding = b"stored_voice_embedding"
        mock_combine.return_value = dummy_embedding
        await save_voice_samples(db_session, "voice@example.com", ["sample1"])
    
    # Now authenticate with voice (mocked)
    with patch('myapp.crud.user.match_voice') as mock_match:
        mock_match.return_value = True
        
        # Dummy audio string (base64 encoded dummy audio)
        dummy_audio = "dummy_base64_audio_string_for_testing"
        auth_user = await authenticate_voice(db_session, "voice@example.com", dummy_audio)
        
        assert auth_user is not None
        assert auth_user.email == "voice@example.com"
        mock_match.assert_called_once_with(dummy_embedding, dummy_audio)


@pytest.mark.asyncio
async def test_authenticate_voice_wrong_match(db_session):
    """Test voice authentication with mismatched voice"""
    # Register user
    await register_user(db_session, "voice@example.com", "VoiceUser", "pass123")
    
    # Save voice samples
    with patch('myapp.crud.user.combine_embeddings') as mock_combine:
        mock_combine.return_value = b"stored_embedding"
        await save_voice_samples(db_session, "voice@example.com", ["sample1"])
    
    # Authenticate with wrong voice
    with patch('myapp.crud.user.match_voice') as mock_match:
        mock_match.return_value = False
        
        with pytest.raises(HTTPException) as exc:
            await authenticate_voice(db_session, "voice@example.com", "wrong_audio_string")
        assert exc.value.status_code == 401
        assert "وائس میچ نہیں ہوئی" in exc.value.detail


@pytest.mark.asyncio
async def test_authenticate_voice_no_voice_stored(db_session):
    """Test voice authentication when user hasn't stored voice"""
    # Register user but don't save any voice samples
    await register_user(db_session, "voice@example.com", "VoiceUser", "pass123")
    
    # Try to authenticate with voice (no voice stored)
    with pytest.raises(HTTPException) as exc:
        await authenticate_voice(db_session, "voice@example.com", "any_audio_string")
    assert exc.value.status_code == 400
    assert "وائس موجود نہیں" in exc.value.detail


@pytest.mark.asyncio
async def test_authenticate_voice_user_not_found(db_session):
    """Test voice authentication for non-existent user"""
    with pytest.raises(HTTPException) as exc:
        await authenticate_voice(db_session, "nonexistent@example.com", "dummy_audio")
    assert exc.value.status_code == 404


# ============================================
# UPDATE PROFILE TESTS
# ============================================
@pytest.mark.asyncio
async def test_update_profile_username_success(db_session):
    """Test updating just username"""
    user = await register_user(db_session, "update@example.com", "OldName", "pass123")
    update_data = ProfileUpdate(username="NewName")
    
    updated = await update_own_profile(db_session, user.user_id, update_data)
    
    assert updated is not None
    assert updated.username == "NewName"
    assert updated.email == "update@example.com"  # Email unchanged


@pytest.mark.asyncio
async def test_update_profile_email_success(db_session):
    """Test updating email"""
    user = await register_user(db_session, "old@example.com", "User", "pass123")
    update_data = ProfileUpdate(email="new@example.com")
    
    updated = await update_own_profile(db_session, user.user_id, update_data)
    
    assert updated is not None
    assert updated.email == "new@example.com"
    assert updated.username == "User"


@pytest.mark.asyncio
async def test_update_profile_multiple_fields(db_session):
    """Test updating multiple fields at once"""
    user = await register_user(db_session, "multi@example.com", "OldName", "oldpass")
    update_data = ProfileUpdate(
        username="NewName",
        email="newemail@example.com",
        password="newpass"
    )
    
    updated = await update_own_profile(db_session, user.user_id, update_data)
    
    assert updated.username == "NewName"
    assert updated.email == "newemail@example.com"
    assert updated.password_hash != "oldpass"


@pytest.mark.asyncio
async def test_update_profile_user_not_found(db_session):
    """Test updating non-existent user"""
    update_data = ProfileUpdate(username="NewName")
    result = await update_own_profile(db_session, 99999, update_data)
    assert result is None


# ============================================
# PASSWORD RESET TESTS
# ============================================
@pytest.mark.asyncio
async def test_password_reset_flow_success(db_session):
    """Test complete password reset flow"""
    await register_user(db_session, "reset@example.com", "ResetUser", "oldpass")
    
    code = await initiate_password_reset(db_session, "reset@example.com")
    assert code is not None
    assert code.startswith("VBUGIMS-")
    assert len(code) > 10
    
    success = await reset_password_in_db(db_session, "reset@example.com", code, "newpass123")
    assert success is True


@pytest.mark.asyncio
async def test_password_reset_invalid_code(db_session):
    """Test reset with wrong reset code"""
    await register_user(db_session, "reset@example.com", "ResetUser", "oldpass")
    await initiate_password_reset(db_session, "reset@example.com")
    
    success = await reset_password_in_db(db_session, "reset@example.com", "WRONGCODE", "newpass123")
    assert success is False


@pytest.mark.asyncio
async def test_password_reset_user_not_found(db_session):
    """Test initiating reset for non-existent user"""
    result = await initiate_password_reset(db_session, "nonexistent@example.com")
    assert result is None


@pytest.mark.asyncio
async def test_reset_password_user_not_found(db_session):
    """Test reset password for non-existent user"""
    success = await reset_password_in_db(db_session, "nonexistent@example.com", "code123", "newpass")
    assert success is False


# ============================================
# GETTER FUNCTIONS TESTS
# ============================================
@pytest.mark.asyncio
async def test_get_user_by_id_success(db_session):
    """Test fetching user by ID"""
    user = await register_user(db_session, "get@example.com", "GetUser", "pass123")
    found = await get_user_by_id(db_session, user.user_id)
    assert found is not None
    assert found.email == "get@example.com"


@pytest.mark.asyncio
async def test_get_user_by_id_not_found(db_session):
    """Test fetching non-existent user by ID"""
    result = await get_user_by_id(db_session, 99999)
    assert result is None


@pytest.mark.asyncio
async def test_get_user_by_email_success(db_session):
    """Test fetching user by email"""
    user = await register_user(db_session, "get@example.com", "GetUser", "pass123")
    found = await get_user_by_email(db_session, "get@example.com")
    assert found is not None
    assert found.user_id == user.user_id


@pytest.mark.asyncio
async def test_get_user_by_email_case_insensitive(db_session):
    """Test email lookup is case insensitive"""
    await register_user(db_session, "Case@Example.com", "User", "pass123")
    found = await get_user_by_email(db_session, "case@example.com")
    assert found is not None


@pytest.mark.asyncio
async def test_get_user_by_email_not_found(db_session):
    """Test fetching non-existent email"""
    result = await get_user_by_email(db_session, "nonexistent@example.com")
    assert result is None


@pytest.mark.asyncio
async def test_get_all_users_empty(db_session):
    """Test getting all users when none exist"""
    users = await get_all_users(db_session)
    assert isinstance(users, list)
    assert len(users) == 0


@pytest.mark.asyncio
async def test_get_all_users_multiple(db_session):
    """Test getting all users with multiple records"""
    await register_user(db_session, "user1@example.com", "User1", "pass1")
    await register_user(db_session, "user2@example.com", "User2", "pass2")
    await register_user(db_session, "user3@example.com", "User3", "pass3")
    
    users = await get_all_users(db_session)
    assert len(users) == 3
    emails = [u.email for u in users]
    assert "user1@example.com" in emails


# ============================================
# DELETE USER TESTS
# ============================================
@pytest.mark.asyncio
async def test_delete_user_success(db_session):
    """Test successful user deletion"""
    user = await register_user(db_session, "delete@example.com", "DeleteUser", "pass123")
    deleted = await delete_user(db_session, user.user_id)
    assert deleted is True
    
    # Verify user no longer exists
    found = await get_user_by_id(db_session, user.user_id)
    assert found is None


@pytest.mark.asyncio
async def test_delete_user_not_found(db_session):
    """Test deleting non-existent user"""
    deleted = await delete_user(db_session, 99999)
    assert deleted is False


@pytest.mark.asyncio
async def test_delete_user_then_recreate_same_email(db_session):
    """Test that after deletion, same email can be reused"""
    user = await register_user(db_session, "reuse@example.com", "User1", "pass123")
    await delete_user(db_session, user.user_id)
    
    # Should be able to register same email again
    new_user = await register_user(db_session, "reuse@example.com", "User2", "newpass")
    assert new_user is not None
    assert new_user.email == "reuse@example.com"


# ============================================
# EDGE CASES & ADDITIONAL TESTS
# ============================================
@pytest.mark.asyncio
async def test_register_user_very_long_email(db_session):
    """Test registration with very long email"""
    long_email = "a" * 100 + "@example.com"
    user = await register_user(db_session, long_email, "User", "pass123")
    assert user.email == long_email


@pytest.mark.asyncio
async def test_update_profile_same_values(db_session):
    """Test updating profile with same values (should work)"""
    user = await register_user(db_session, "same@example.com", "SameUser", "pass123")
    update_data = ProfileUpdate(username="SameUser", email="same@example.com")
    
    updated = await update_own_profile(db_session, user.user_id, update_data)
    
    assert updated is not None
    assert updated.username == "SameUser"
    assert updated.email == "same@example.com"

@pytest.mark.asyncio
async def test_update_profile_password_success(db_session):
    """Test updating password"""
    user = await register_user(db_session, "pass@example.com", "User", "oldpass123")
    
    # Store the old hash BEFORE update
    old_hash = user.password_hash
    
    # Update with NEW password (different from old)
    update_data = ProfileUpdate(password="newSecurePass456!")
    updated = await update_own_profile(db_session, user.user_id, update_data)
    
    assert updated is not None
    # Verify password was hashed (not stored as plain text)
    assert updated.password_hash != "newSecurePass456!"
    # Verify password hash changed from old hash
    assert updated.password_hash != old_hash


@pytest.mark.asyncio
async def test_update_profile_empty_update(db_session):
    """Test updating with no fields - should raise validation error"""
    from pydantic import ValidationError
    
    user = await register_user(db_session, "empty@example.com", "User", "pass123")
    
    # Empty update should be rejected by Pydantic validator
    with pytest.raises(ValidationError) as exc_info:
        update_data = ProfileUpdate()  # Empty update
    
    # Verify the error message matches your schema's validation
    assert "At least one field must be provided" in str(exc_info.value)