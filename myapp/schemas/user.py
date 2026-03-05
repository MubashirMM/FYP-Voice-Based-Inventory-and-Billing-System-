from pydantic import BaseModel, EmailStr, ConfigDict
from pydantic import field_validator
from typing import Optional

class UserRegister(BaseModel):
    email: EmailStr
    username: str
    password: str
    voice_samples: list[str] | None

class ProfileUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None

class PasswordResetConfirm(BaseModel):
    email: EmailStr
    reset_code: str  
    new_password: str
    confirm_password: str

    @field_validator("confirm_password")
    def passwords_match(cls, v, info):
        if "new_password" in info.data and v != info.data["new_password"]:
            raise ValueError("پاس ورڈ مماثلت نہیں رکھتے") # Passwords do not match
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserRead(BaseModel):
    user_id: int
    email: EmailStr
    username: str
    model_config = ConfigDict(from_attributes=True)

class PasswordResetRequest(BaseModel):
    email: EmailStr 

class VoiceSamplesSave(BaseModel):
    email: EmailStr
    samples: list[str] 

class UserVoiceLogin(BaseModel):
    email: EmailStr
    audio_base64: str




