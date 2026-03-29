from pydantic import BaseModel, EmailStr, ConfigDict, field_validator, model_validator
from typing import Optional, List
from datetime import datetime

class UserRegister(BaseModel):
    email: EmailStr
    username: str
    password: str
    voice_samples: Optional[List[str]] = None

class ProfileUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    
    @model_validator(mode='after')
    def at_least_one_field(self):
        if not any([self.username, self.email, self.password]):
            raise ValueError("At least one field must be provided for update")
        return self

class PasswordResetConfirm(BaseModel):
    email: EmailStr
    reset_code: str  
    new_password: str
    confirm_password: str

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v, info):
        if "new_password" in info.data and v != info.data["new_password"]:
            raise ValueError("Passwords do not match")
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserRead(BaseModel):
    user_id: int
    email: EmailStr
    username: str
    created_at: Optional[datetime] = None 
    model_config = ConfigDict(from_attributes=True)

# Response model with Urdu formatted date
class UserReadWithUrduDate(BaseModel):
    user_id: int
    email: EmailStr
    username: str
    created_at: Optional[str] = None  # This will be the formatted Urdu date string
    model_config = ConfigDict(from_attributes=True)

class PasswordResetRequest(BaseModel):
    email: EmailStr 

class VoiceSamplesSave(BaseModel):
    email: EmailStr
    samples: List[str] 

class UserVoiceLogin(BaseModel):
    email: EmailStr
    audio_base64: str