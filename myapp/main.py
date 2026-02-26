from contextlib import asynccontextmanager
import shutil
from fastapi import FastAPI ,UploadFile,File
from myapp.database.session import engine, Base
from myapp.api.items import router as items
from myapp.api.customer import router as customers
from myapp.api.sales import router as sales
from myapp.api.udhar import router as udhar
from myapp.api.udhaar_item import router as udhaar_item
from myapp.api.bill import router as bill
from myapp.api.user import router as user
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware 
from myapp.api.shop import router as shop
from myapp.api.report import router as report
from myapp.api.forcasting import router as forcast


from myapp.api.bill_item import router as bill_item
from fastapi import FastAPI, Request, HTTPException 
from fastapi.responses import JSONResponse

import os
import torch 
import io
# from faster_whisper import WhisperModel
from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()

myapp = FastAPI(lifespan=lifespan)
origins = [  "http://127.0.0.1:5173", "http://localhost:5173","null" ]
myapp.add_middleware(
    CORSMiddleware,
    allow_origins=origins,     
    allow_credentials=True,
    allow_methods=["*"],       # Allows GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],       # Allows common headers
)



myapp.include_router(user)
myapp.include_router(shop)
myapp.include_router(items)
myapp.include_router(customers)
myapp.include_router(udhaar_item)
myapp.include_router(bill_item)
myapp.include_router(sales)
myapp.include_router(udhar)
myapp.include_router(bill)
myapp.include_router(report)
myapp.include_router(forcast)  







 