from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Database
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    
    # Groq API
    GROQ_API_KEY: str
    GROQ_API_KEY1: str
    GROQ_API_KEY2: str
    GROQ_API_KEY3: str

    # GEMINI_API_KEY:str

    @property
    def DATABASE_URL(self) -> str:
        # Construct the async connection string
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # This tells Pydantic to look for .env in the root folder
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8')

settings = Settings()