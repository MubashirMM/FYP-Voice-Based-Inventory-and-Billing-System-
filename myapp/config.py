
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):

    SECRET_KEY:str
    ALGORITHM:str
    ACCESS_TOKEN_EXPIRE_MINUTES:int
# 
    ALLOWED_ORIGINS: list[str] = ["http://localhost:5173"]
    # Database
    DB_USER: str 
    DB_PASSWORD: str 
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str

    # Add these 2 lines in your Settings class
    SMTP_EMAIL: str
    SMTP_PASSWORD: str 
    
    # Groq API
    GROQ_API_KEY: str
    GROQ_API_KEY1: str
    GROQ_API_KEY2: str
    GROQ_API_KEY3: str
    GROQ_API_KEY4: str
    GROQ_API_KEY5: str
    GROQ_API_KEY6: str
    GROQ_API_KEY7: str
    GROQ_API_KEY8: str
    GROQ_API_KEY9: str
    GROQ_API_KEY10: str
    GROQ_API_KEY11: str
    GROQ_API_KEY12: str
    GROQ_API_KEY13: str




    @property
    def DATABASE_URL(self) -> str:
        # Construct the async connection string
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # This tells Pydantic to look for .env in the root folder
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8')

settings = Settings()