from contextlib import asynccontextmanager
from fastapi import FastAPI
from myapp.database.session import engine, Base
from myapp.api.items import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()

myapp = FastAPI(lifespan=lifespan)
myapp.include_router(router)
