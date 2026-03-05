import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from myapp.database.session import Base

DATABASE_URL = "postgresql+asyncpg://postgres:password@localhost:5432/test_db"

@pytest_asyncio.fixture(scope="function")   # <-- use pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine(DATABASE_URL, future=True)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
