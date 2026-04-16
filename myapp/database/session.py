from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from ..config import settings 

# OPTIMIZED ENGINE FOR POSTGRES
engine = create_async_engine(
    settings.DATABASE_URL, 
    echo=False,           # Set to False during load testing to save CPU/Memory
    pool_size=20,         # Increase base connections from default 5 to 20
    max_overflow=10,      # Allow 10 extra temporary connections during "bursts"
    pool_timeout=30,      # Wait 30 seconds for a connection before failing
    pool_recycle=1800     # Refresh connections every 30 mins to prevent "stale" DB errors
)

class Base(DeclarativeBase):
    pass

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession, 
    expire_on_commit=False
)

# Dependency to get DB session in FastAPI routes
async def get_db():
    async with AsyncSessionLocal() as session:
        try: 
            yield session
        finally:
            await session.close() # Explicitly close to ensure it returns to the pool