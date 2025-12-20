from contextlib import asynccontextmanager
from fastapi import FastAPI
from myapp.database.session import engine, Base
from myapp.api.items import router as items
from myapp.api.customer import router as customers
from myapp.api.sales import router as sales
from myapp.api.udhar import router as udhar
from myapp.api.udhaar_item import router as udhaar_item
from myapp.api.bill import router as bill

from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


myapp = FastAPI(lifespan=lifespan)


origins = [
    "http://127.0.0.1:5173",
    # "http://192.168.1.5:3000", 
]

myapp.add_middleware(
    CORSMiddleware,
    allow_origins=origins,     
    allow_credentials=True,
    allow_methods=["*"],       # Allows GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],       # Allows common headers
)
myapp.include_router(items)
myapp.include_router(customers)
myapp.include_router(udhaar_item)
myapp.include_router(sales)
myapp.include_router(udhar)
myapp.include_router(bill)
